#!/usr/bin/env python3
"""
patch-hsaqmaodv-v3.py
Apply 3 new improvements to H-SAQMAODV:
  5. Void Region Detection + Emergency Recovery
  6. AODV-assisted Dual Q-update (inspired by HQA)
  7. Adaptive Hello Interval based on TVI

Usage: python3 patch-hsaqmaodv-v3.py
"""

import re, shutil, sys
from pathlib import Path

NS3 = Path.home() / "ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model"
QH  = NS3 / "saqmaodv-qtable.h"
QCC = NS3 / "saqmaodv-qtable.cc"
RCC = NS3 / "saqmaodv-routing-protocol.cc"

def backup(p):
    shutil.copy(p, str(p) + ".bak-v3")
    print(f"  Backed up {p.name}")

def patch(path, old, new, desc):
    text = path.read_text()
    if old in text:
        path.write_text(text.replace(old, new, 1))
        print(f"  [OK] {desc}")
    else:
        print(f"  [MISS] {desc}")

# ============================================================
# qtable.h — add new method declarations and members
# ============================================================
print("\nPatching saqmaodv-qtable.h:")
backup(QH)

# Add new method declarations after SetErrorWindow
patch(QH,
"    void SetErrorWindow(Time w) { m_errorWindow = w; }",
"""    void SetErrorWindow(Time w) { m_errorWindow = w; }
    // Improvement 5: Void detection
    void OnVoidDetected();
    void SetVoidEpsBump(double v) { m_voidEpsBump = v; }
    // Improvement 6: AODV-assisted dual Q-update
    void UpdateFromAODVRoute(const RoutingTableEntry& rt,
                             uint32_t hopCount, double energyFrac);
    // Improvement 7: Adaptive hello — expose TVI thresholds
    double GetTVIHigh() const { return m_tviHigh; }
    double GetTVILow()  const { return m_tviLow; }""",
"qtable.h: add new method declarations")

# Add new member variable m_voidEpsBump
patch(QH,
"    double m_w4{0.1};",
"""    double m_w4{0.1};
    // Improvement 5: void bump strength
    double m_voidEpsBump{0.35};""",
"qtable.h: add m_voidEpsBump member")

# ============================================================
# qtable.cc — implement new methods
# ============================================================
print("\nPatching saqmaodv-qtable.cc:")
backup(QCC)

# Improvement 5: OnVoidDetected — after OnRouteError definition
patch(QCC,
"// §4.3 — Adaptive Learning Rate",
"""// ── Improvement 5: Void Region Detection ────────────────────────────────
void
QTable::OnVoidDetected()
{
    // Strong ε bump to aggressively explore new paths
    m_errorEvents.push_back(Simulator::Now());
    Time thresh = Simulator::Now() - m_errorWindow;
    while (!m_errorEvents.empty() && m_errorEvents.front() < thresh)
        m_errorEvents.pop_front();
    double bump = std::min(0.45, m_voidEpsBump * 1.5);
    m_epsilon = std::min(m_epsilonMax, m_epsilon + bump);
    // Force EXPLORE mode — override hysteresis
    m_currentMode = 1;
    m_tickHigh = 0;
    m_tickLow  = 0;
    NS_LOG_DEBUG("SAQM VOID detected: ε→" << m_epsilon << " mode→EXPLORE");
}

// ── Improvement 6: AODV-assisted Dual Q-update ───────────────────────────
void
QTable::UpdateFromAODVRoute(const RoutingTableEntry& rt,
                            uint32_t hopCount, double energyFrac)
{
    if (hopCount == 0) return;
    // Estimate delay from hop count (5ms per hop)
    double estDelay = static_cast<double>(hopCount) * 0.005;
    // Use half alpha for AODV-assisted samples — softer update
    // to not overwrite learned Q-values aggressively
    double savedAlpha = m_alpha;
    m_alpha = std::max(0.05, m_alpha * 0.5);
    UpdateQValueOrCreate(rt, 1.0, estDelay, energyFrac);
    m_alpha = savedAlpha;
    NS_LOG_DEBUG("SAQM AODV dual-update: dst=" << rt.GetDestination()
                 << " via=" << rt.GetNextHop()
                 << " HC=" << hopCount);
}

// §4.3 — Adaptive Learning Rate""",
"qtable.cc: implement OnVoidDetected and UpdateFromAODVRoute")

# ============================================================
# routing-protocol.cc — wire improvements
# ============================================================
print("\nPatching saqmaodv-routing-protocol.cc:")
backup(RCC)

rcc_text = RCC.read_text()

# ── Improvement 5: Void detection in DeferredRouteOutput ────────────────
# Add OnVoidDetected call at start of DeferredRouteOutput
old5 = '''void
RoutingProtocol::DeferredRouteOutput(Ptr<const Packet> p,
                                     const Ipv4Header& header,
                                     UnicastForwardCallback ucb,
                                     ErrorCallback ecb)
{'''
new5 = '''void
RoutingProtocol::DeferredRouteOutput(Ptr<const Packet> p,
                                     const Ipv4Header& header,
                                     UnicastForwardCallback ucb,
                                     ErrorCallback ecb)
{
    // Improvement 5: Notify Q-table of void/no-route condition
    m_qtable.OnVoidDetected();'''

if old5 in rcc_text:
    rcc_text = rcc_text.replace(old5, new5, 1)
    print("  [OK] routing-protocol.cc: OnVoidDetected in DeferredRouteOutput")
else:
    print("  [MISS] routing-protocol.cc: OnVoidDetected in DeferredRouteOutput")

# ── Improvement 6: AODV dual update after successful forwarding ──────────
# In RecvReply / Forwarding: after ucb(route, p, header) success
old6 = '''        m_nb.Update(route->GetGateway(), m_activeRouteTimeout);
        m_nb.Update(toOrigin.GetNextHop(), m_activeRouteTimeout);

        ucb(route, p, header);
        return true;'''
new6 = '''        m_nb.Update(route->GetGateway(), m_activeRouteTimeout);
        m_nb.Update(toOrigin.GetNextHop(), m_activeRouteTimeout);

        // Improvement 6: AODV-assisted dual Q-update
        {
            double eFrac = GetEnergyFraction();
            m_qtable.UpdateFromAODVRoute(toDst, toDst.GetHop(), eFrac);
        }
        ucb(route, p, header);
        return true;'''

if old6 in rcc_text:
    rcc_text = rcc_text.replace(old6, new6, 1)
    print("  [OK] routing-protocol.cc: AODV dual-update in Forwarding")
else:
    print("  [MISS] routing-protocol.cc: AODV dual-update — trying RecvReply location")
    # Try alternative location in RecvReply
    old6b = '''        m_nb.Update(toOrigin.GetNextHop(), m_activeRouteTimeout);

        ucb(route, p, header);
        return true;'''
    new6b = '''        m_nb.Update(toOrigin.GetNextHop(), m_activeRouteTimeout);

        // Improvement 6: AODV-assisted dual Q-update
        {
            double eFrac = GetEnergyFraction();
            m_qtable.UpdateFromAODVRoute(toDst, toDst.GetHop(), eFrac);
        }
        ucb(route, p, header);
        return true;'''
    if old6b in rcc_text:
        rcc_text = rcc_text.replace(old6b, new6b, 1)
        print("  [OK] routing-protocol.cc: AODV dual-update (alt location)")
    else:
        print("  [MISS] routing-protocol.cc: AODV dual-update — both patterns missed")

# ── Improvement 7: Adaptive Hello in PeriodicAdaptiveTick ───────────────
old7 = '''void
RoutingProtocol::PeriodicAdaptiveTick()
{'''
new7 = '''void
RoutingProtocol::PeriodicAdaptiveTick()
{
    // Improvement 7: Adaptive hello interval based on TVI
    {
        double tvi = m_qtable.GetTVI();
        if (tvi > m_qtable.GetTVIHigh())
            m_helloInterval = Seconds(0.5);   // fast — topology very dynamic
        else if (tvi < m_qtable.GetTVILow())
            m_helloInterval = Seconds(2.0);   // slow — stable, save energy
        else
            m_helloInterval = Seconds(1.0);   // default
    }'''

if old7 in rcc_text:
    rcc_text = rcc_text.replace(old7, new7, 1)
    print("  [OK] routing-protocol.cc: Adaptive hello in PeriodicAdaptiveTick")
else:
    print("  [MISS] routing-protocol.cc: Adaptive hello")

RCC.write_text(rcc_text)

print("\n=== Done. Build với: ===")
print("cmake --build ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/cmake-cache -j$(nproc) 2>&1 | grep 'error:' | head -10")
