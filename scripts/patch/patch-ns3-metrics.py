#!/usr/bin/env python3
"""
patch-ns3-metrics.py
Patch fanet-sim NS-3 scratch file để output thêm metrics:
  avgDelay, routingOverhead, energyConsumed, throughput

Chạy:  python3 ~/patch-ns3-metrics.py [--dry-run]
       python3 ~/patch-ns3-metrics.py --find-only   (chỉ tìm file, không sửa)

Sau khi patch:
  cd ~/hsaqmaodv-ns3
  ./ns3 build scratch/fanet-sim 2>&1 | tail -20
"""
import re, os, sys, shutil, glob

DRY_RUN   = "--dry-run"   in sys.argv
FIND_ONLY = "--find-only" in sys.argv

# ── 1. Tìm scratch file ───────────────────────────────────────────────────────
def find_scratch():
    candidates = glob.glob(os.path.expanduser("~/hsaqmaodv-ns3/scratch/*.cc"))
    candidates += glob.glob(os.path.expanduser("~/hsaqmaodv-ns3/scratch/**/*.cc"))
    if not candidates:
        print("[ERROR] Không tìm thấy scratch/*.cc trong ~/hsaqmaodv-ns3")
        sys.exit(1)
    # ưu tiên file có chứa "pdr" hoặc "fanet"
    for c in candidates:
        with open(c) as f:
            txt = f.read()
        if any(k in txt.lower() for k in ["pdr", "fanet", "protocol", "aodv"]):
            return c
    return candidates[0]

src_path = find_scratch()
print(f"[INFO] Source file: {src_path}")
if FIND_ONLY:
    sys.exit(0)

with open(src_path) as f:
    src = f.read()

# ── 2. Kiểm tra đã patch chưa ────────────────────────────────────────────────
if "avgDelay" in src and "routingOverhead" in src and "energyConsumed" in src:
    print("[INFO] Already patched — nothing changed.")
    sys.exit(0)

backup = src_path + ".bak-metrics"
shutil.copy(src_path, backup)
print(f"[INFO] Backup: {backup}")

# ── 3. Các biến tracking cần thêm ────────────────────────────────────────────
TRACKING_VARS = """
// ─── Full-metrics tracking (patched by patch-ns3-metrics.py) ───────────────
static uint64_t g_totalDelayUs   = 0;  // tổng delay (microseconds)
static uint32_t g_rxCount        = 0;  // số packet nhận được (cho delay avg)
static uint32_t g_ctrlPktCount   = 0;  // số control packet (RREQ+RREP+RERR)
static uint64_t g_ctrlBytesTotal = 0;  // tổng bytes control
static double   g_energyConsumed = 0.0;// tổng energy tiêu thụ (Joules)
// ─────────────────────────────────────────────────────────────────────────────
"""

# ── 4. Callback đo delay khi packet đến ──────────────────────────────────────
DELAY_CALLBACK = """
// ─── Delay measurement callback (patched) ───────────────────────────────────
static void RxDelayCb(Ptr<const Packet> pkt, const Address& from)
{
    TimestampTag tsTag;
    if (pkt->FindFirstMatchingByteTag(tsTag)) {
        Time sendTime = tsTag.GetTimestamp();
        int64_t delayUs = (Simulator::Now() - sendTime).GetMicroSeconds();
        if (delayUs >= 0) {
            g_totalDelayUs += (uint64_t)delayUs;
            g_rxCount++;
        }
    }
}

// ─── Control packet counter (patched) ───────────────────────────────────────
static void CtrlPktTxCb(Ptr<const Packet> pkt)
{
    g_ctrlPktCount++;
    g_ctrlBytesTotal += pkt->GetSize();
}
// ─────────────────────────────────────────────────────────────────────────────
"""

# ── 5. TimestampTag (nếu chưa có) ────────────────────────────────────────────
TIMESTAMP_TAG = """
// ─── TimestampTag for per-packet delay (patched) ────────────────────────────
class TimestampTag : public Tag {
public:
    static TypeId GetTypeId() {
        static TypeId tid = TypeId("TimestampTag")
            .SetParent<Tag>().AddConstructor<TimestampTag>();
        return tid;
    }
    TypeId GetInstanceTypeId() const override { return GetTypeId(); }
    uint32_t GetSerializedSize() const override { return 8; }
    void Serialize(TagBuffer i) const override { i.WriteDouble(m_ts.GetDouble()); }
    void Deserialize(TagBuffer i) override { m_ts = Time::FromDouble(i.ReadDouble(), Time::NS); }
    void Print(std::ostream& os) const override { os << "ts=" << m_ts; }
    void SetTimestamp(Time t) { m_ts = t; }
    Time GetTimestamp() const { return m_ts; }
private:
    Time m_ts;
};
// ─────────────────────────────────────────────────────────────────────────────
"""

# ── 6. Tìm chỗ ghi CSV và patch header + data row ────────────────────────────

# Pattern tìm header CSV ghi vào file
HDR_PATTERNS = [
    # dạng: ofs << "scenario,protocol,seed,pdr"
    (r'(ofs\s*<<\s*"[^"]*(?:pdr|PDR|scenario|protocol)[^"]*")',
     None),
    # dạng: fprintf / cout << "pdr"  
    (r'((?:fprintf|printf|std::cout)\s*[<(][^;]*(?:pdr|PDR)[^;]*;)',
     None),
]

# Thêm columns vào CSV header
def patch_header(src):
    # Tìm dòng header CSV — nhận ra bằng "pdr" trong string literal << hoặc fprintf
    pattern = r'((?:ofs|outFile|csvFile|fout|f)\s*<<\s*"([^"]*(?:pdr|PDR|seed|Seed)[^"]*)")'
    m = re.search(pattern, src)
    if m:
        old_hdr = m.group(0)
        hdr_str = m.group(2)
        # Thêm các column mới vào cuối header (trước \n nếu có)
        if "avgDelay" not in hdr_str:
            new_hdr_str = hdr_str.rstrip("\\n").rstrip("\\r\\n") + \
                          ",avgDelayMs,routingOverhead,nrl,energyConsumedJ,throughputKbps\\n"
            new_hdr = old_hdr.replace(hdr_str, new_hdr_str)
            src = src.replace(old_hdr, new_hdr)
            print(f"[PATCH] Header: added avgDelayMs,routingOverhead,nrl,energyConsumedJ,throughputKbps")
        return src, True
    return src, False

# Thêm values vào CSV data row
def patch_datarow(src):
    # Tìm dòng ghi data — nhận ra bằng biến pdr / PDR trong << chain
    pattern = r'((?:ofs|outFile|csvFile|fout|f)\s*<<\s*[^;]*(?:pdr|PDR|pktDeliveryRatio)[^;]*;)'
    m = re.search(pattern, src)
    if m:
        old_row = m.group(0)
        if "avgDelay" not in old_row and "g_totalDelayUs" not in old_row:
            # Thêm computed values trước dấu ;
            extra = (
                ' << "," << (g_rxCount > 0 ? (double)g_totalDelayUs/g_rxCount/1000.0 : 0.0)'
                ' << "," << g_ctrlPktCount'
                ' << "," << (g_rxCount > 0 ? (double)g_ctrlPktCount/g_rxCount : 0.0)'
                ' << "," << g_energyConsumed'
                ' << "," << (simTime > 0 ? g_rxCount * pktSize * 8.0 / simTime / 1000.0 : 0.0)'
            )
            new_row = old_row.rstrip(';') + extra + ';'
            src = src.replace(old_row, new_row)
            print(f"[PATCH] Data row: appended 5 metric columns")
        return src, True
    return src, False

# ── 7. Tìm chỗ reset biến trước mỗi run ──────────────────────────────────────
RESET_SNIPPET = """
    // Reset per-run metrics (patched)
    g_totalDelayUs   = 0;
    g_rxCount        = 0;
    g_ctrlPktCount   = 0;
    g_ctrlBytesTotal = 0;
    g_energyConsumed = 0.0;
"""

def patch_reset(src):
    # Tìm chỗ Simulator::Run() — reset trước đó
    if "Simulator::Run()" in src and "g_totalDelayUs = 0" not in src:
        src = src.replace("Simulator::Run()", RESET_SNIPPET + "    Simulator::Run()", 1)
        print("[PATCH] Reset: added per-run metric reset before Simulator::Run()")
    return src

# ── 8. Thêm energy tracking nếu dùng EnergySourceContainer ──────────────────
ENERGY_SNIPPET = """
    // Collect energy consumed (patched)
    {
        NodeContainer allNodes = NodeContainer::GetGlobal();
        for (uint32_t i = 0; i < allNodes.GetN(); i++) {
            Ptr<EnergySourceContainer> esc =
                allNodes.Get(i)->GetObject<EnergySourceContainer>();
            if (esc) {
                for (EnergySourceContainer::Iterator it = esc->Begin();
                     it != esc->End(); ++it) {
                    g_energyConsumed += (*it)->GetInitialEnergy()
                                      - (*it)->GetRemainingEnergy();
                }
            }
        }
    }
"""

def patch_energy(src):
    # Tìm chỗ sau Simulator::Stop hoặc trước ghi CSV
    if "g_energyConsumed" not in src or "GetRemainingEnergy" not in src:
        # Thêm trước dòng ghi CSV (trước ofs <<)
        pattern = r'(// Reset per-run metrics \(patched\))'
        if re.search(pattern, src):
            src = re.sub(pattern, ENERGY_SNIPPET + r'\1', src, count=1)
            print("[PATCH] Energy: added EnergySourceContainer collection")
    return src

# ── 9. Apply patches ──────────────────────────────────────────────────────────
# Thêm includes nếu cần
if "TimestampTag" not in src:
    # Tìm vị trí sau các #include
    last_include = max(
        (m.end() for m in re.finditer(r'^#include\s+[<"][^>"]+[>"]', src, re.MULTILINE)),
        default=0
    )
    if last_include:
        src = src[:last_include] + "\n" + TIMESTAMP_TAG + "\n" + src[last_include:]
        print("[PATCH] TimestampTag: added after includes")

if "g_totalDelayUs" not in src:
    # Thêm global vars sau includes/namespace
    pos = src.find("int main(")
    if pos == -1:
        pos = src.find("static void ")
    if pos > 0:
        src = src[:pos] + TRACKING_VARS + "\n" + src[pos:]
        print("[PATCH] Global vars: added tracking variables")

if "RxDelayCb" not in src:
    pos = src.find("int main(")
    if pos > 0:
        src = src[:pos] + DELAY_CALLBACK + "\n" + src[pos:]
        print("[PATCH] Callbacks: added RxDelayCb and CtrlPktTxCb")

src = patch_reset(src)
src = patch_energy(src)
src, hdr_ok = patch_header(src)
src, row_ok = patch_datarow(src)

if not hdr_ok:
    print("[WARN] Could not auto-patch CSV header — check source manually")
    print("       Add: avgDelayMs,routingOverhead,nrl,energyConsumedJ,throughputKbps")
if not row_ok:
    print("[WARN] Could not auto-patch CSV data row — check source manually")

# ── 10. Write ─────────────────────────────────────────────────────────────────
if DRY_RUN:
    print("[DRY-RUN] Changes NOT written.")
else:
    with open(src_path, 'w') as f:
        f.write(src)
    print(f"[OK] Written: {src_path}")
    print("     Now rebuild: cd ~/hsaqmaodv-ns3 && ./ns3 build scratch/fanet-sim")

