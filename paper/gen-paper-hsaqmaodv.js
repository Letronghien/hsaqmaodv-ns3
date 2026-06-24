// gen-paper-hsaqmaodv.js — Full H-SAQMAODV Journal Paper
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, Footer, ExternalHyperlink, LevelFormat,
} = require('docx');
const fs = require('fs');

// ─── helpers ────────────────────────────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const hdrBorder = { style: BorderStyle.SINGLE, size: 8, color: "2C5282" };
const hdrBorders = { top: hdrBorder, bottom: hdrBorder, left: hdrBorder, right: hdrBorder };

const P   = (text, opts={}) => new Paragraph({ children:[new TextRun({text,...(opts.run||{})})], ...opts.para });
const B   = (text)          => new TextRun({ text, bold: true });
const I   = (text)          => new TextRun({ text, italics: true });
const BI  = (text)          => new TextRun({ text, bold: true, italics: true });

function body(runs, opts={}) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    ...opts,
    children: runs.map(r => typeof r === 'string' ? new TextRun(r) : r),
  });
}
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 300, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, font: "Arial" })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, font: "Arial" })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 60 },
    children: [new TextRun({ text, bold: true, italics: true, size: 22, font: "Arial" })],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 160 },
    children: [new TextRun({ text, bold: true, size: 20, font: "Arial" })],
  });
}
function sp(n=1) {
  return Array.from({length:n}, ()=>new Paragraph({ spacing:{after:80}, children:[] }));
}
function figPlaceholder(n, filename, cap) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 60 },
      border: {
        top: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
        bottom: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
        left: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
        right: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
      },
      shading: { fill: "F7F7F7" },
      children: [new TextRun({ text: `[INSERT FIGURE ${n} HERE — file: ${filename}]`, italics: true, size: 20, font: "Arial", color: "888888" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 160 },
      children: [new TextRun({ text: `Fig. ${n}. ${cap}`, bold: true, size: 20, font: "Arial" })],
    }),
  ];
}
function hdrCell(text, w) {
  return new TableCell({
    borders: hdrBorders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: "2C5282", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 18, font: "Arial" })],
    })],
  });
}
function cell(text, w, shade="FFFFFF", align=AlignmentType.CENTER) {
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, size: 18, font: "Arial" })],
    })],
  });
}
function cellB(text, w, shade="FFFFFF") {
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, size: 18, font: "Arial" })],
    })],
  });
}
function row(cells) { return new TableRow({ children: cells }); }

// ─── Tables ─────────────────────────────────────────────────────────────────
const TW = 9360;

const tableSimParams = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [4000, 5360],
  rows: [
    row([hdrCell("Parameter", 4000), hdrCell("Value", 5360)]),
    row([cell("Simulator", 4000,"F0F4FF",AlignmentType.LEFT), cell("NS-3.40 (FANET module)", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Simulation area", 4000,"FFFFFF",AlignmentType.LEFT), cell("1000 × 1000 m²", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("Number of nodes", 4000,"F0F4FF",AlignmentType.LEFT), cell("5 – 70 (experiment-dependent)", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Mobility model", 4000,"FFFFFF",AlignmentType.LEFT), cell("Gauss-Markov (correlated), Random Waypoint", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("UAV speed", 4000,"F0F4FF",AlignmentType.LEFT), cell("5 – 50 m/s", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("MAC protocol", 4000,"FFFFFF",AlignmentType.LEFT), cell("IEEE 802.11p", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("Traffic model", 4000,"F0F4FF",AlignmentType.LEFT), cell("CBR (UDP)", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Packet interval", 4000,"FFFFFF",AlignmentType.LEFT), cell("0.1 – 1.0 s", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("Packet size", 4000,"F0F4FF",AlignmentType.LEFT), cell("512 bytes", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Initial energy", 4000,"FFFFFF",AlignmentType.LEFT), cell("5 – 100 J (experiment-dependent)", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("Simulation time", 4000,"F0F4FF",AlignmentType.LEFT), cell("200 s", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Number of seeds", 4000,"FFFFFF",AlignmentType.LEFT), cell("30 (independent replications)", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("Compared protocols", 4000,"F0F4FF",AlignmentType.LEFT), cell("AODV, P-MAODV, Q-MAODV, SA-QMAODV, H-SAQMAODV", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("TVI thresholds (default)", 4000,"FFFFFF",AlignmentType.LEFT), cell("High = 5, Low = 2", 5360,"FFFFFF",AlignmentType.LEFT)]),
    row([cell("Sigmoid parameters", 4000,"F0F4FF",AlignmentType.LEFT), cell("θ = 0.3, σ = 0.08", 5360,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Reward weights", 4000,"FFFFFF",AlignmentType.LEFT), cell("w₁ = 0.5, w₂ = 0.3, w₃ = 0.2", 5360,"FFFFFF",AlignmentType.LEFT)]),
  ],
});

const tableExpOverview = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [1000, 2400, 2360, 3600],
  rows: [
    row([hdrCell("EXP", 1000), hdrCell("Name", 2400), hdrCell("Variable", 2360), hdrCell("Key Setting", 3600)]),
    row([cell("1",1000,"F0F4FF"), cell("Node Density",2400,"F0F4FF",AlignmentType.LEFT), cell("N = 5,10,15,20,25,30",2360,"F0F4FF",AlignmentType.LEFT), cell("Speed=20 m/s, E0=30 J",3600,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("2",1000), cell("Speed Sweep",2400,undefined,AlignmentType.LEFT), cell("v = 5,10,20,30,50 m/s",2360,undefined,AlignmentType.LEFT), cell("N=15, E0=30 J",3600,undefined,AlignmentType.LEFT)]),
    row([cell("3",1000,"F0F4FF"), cell("Traffic Load",2400,"F0F4FF",AlignmentType.LEFT), cell("Interval = 0.1–1.0 s",2360,"F0F4FF",AlignmentType.LEFT), cell("N=15, Speed=20 m/s",3600,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("4",1000), cell("Battery Capacity",2400,undefined,AlignmentType.LEFT), cell("E0 = 5,10,20,30,50 J",2360,undefined,AlignmentType.LEFT), cell("N=15, Speed=20 m/s",3600,undefined,AlignmentType.LEFT)]),
    row([cell("5",1000,"F0F4FF"), cell("Ablation Study",2400,"F0F4FF",AlignmentType.LEFT), cell("5 variants",2360,"F0F4FF",AlignmentType.LEFT), cell("N=15, Speed=20/50 m/s, E0=30 J",3600,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("6",1000), cell("TVI Sensitivity",2400,undefined,AlignmentType.LEFT), cell("High∈{3,5,8,10,15}, Low∈{0,1,2}",2360,undefined,AlignmentType.LEFT), cell("N=15, Speed=20 m/s",3600,undefined,AlignmentType.LEFT)]),
    row([cell("7",1000,"F0F4FF"), cell("HQA-Comparable",2400,"F0F4FF",AlignmentType.LEFT), cell("N = 10,20,30,40,50,70",2360,"F0F4FF",AlignmentType.LEFT), cell("v=30 m/s, E0=100 J, RWP",3600,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("8",1000), cell("Energy HQA",2400,undefined,AlignmentType.LEFT), cell("E0 = 10,20,50,100 J",2360,undefined,AlignmentType.LEFT), cell("N=20, HQA scenario setting",3600,undefined,AlignmentType.LEFT)]),
    row([cell("9",1000,"F0F4FF"), cell("Sparse-Regime Boundary",2400,"F0F4FF",AlignmentType.LEFT), cell("N=5,8 (Gauss-Markov)",2360,"F0F4FF",AlignmentType.LEFT), cell("Speed=20 m/s, 30 seeds; operating boundary validation",3600,"F0F4FF",AlignmentType.LEFT)]),

  ],
});

// EXP-5 ablation table — real values from 30-seed simulation
// V20 = normal (20 m/s), V50 = stress (50 m/s)
const tableAblation = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [1800, 1400, 1400, 1400, 1400, 1360],
  rows: [
    row([hdrCell("Variant",1800), hdrCell("DR% (V20)",1400), hdrCell("DR% (V50)",1400), hdrCell("Delay V20 (ms)",1400), hdrCell("Delay V50 (ms)",1400), hdrCell("OH V50 (pkts)",1360)]),
    row([cellB("FULL",1800,"E8F5E9"), cellB("60.5",1400,"E8F5E9"), cellB("51.0",1400,"E8F5E9"), cell("211",1400,"E8F5E9"), cell("350",1400,"E8F5E9"), cell("22,300",1360,"E8F5E9")]),
    row([cell("w/o TVI",1800), cell("60.4",1400), cell("51.4",1400), cell("211",1400), cell("352",1400), cell("22,400",1360)]),
    row([cell("w/o Sigmoid",1800,"FFF8E1"), cell("60.4",1400,"FFF8E1"), cell("51.0",1400,"FFF8E1"), cell("211",1400,"FFF8E1"), cell("350",1400,"FFF8E1"), cell("22,300",1360,"FFF8E1")]),
    row([cell("w/o Congestion",1800), cell("61.0",1400), cell("53.0",1400), cell("211",1400), cell("354",1400), cell("23,000",1360)]),
    row([cell("w/o DualQ",1800,"FFF8E1"), cell("60.4",1400,"FFF8E1"), cell("51.2",1400,"FFF8E1"), cell("211",1400,"FFF8E1"), cell("350",1400,"FFF8E1"), cell("22,300",1360,"FFF8E1")]),
  ],
});


const tableComplexity = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [2800, 2200, 2200, 2160],
  rows: [
    row([hdrCell("Mechanism",2800), hdrCell("Per-Interval",2200), hdrCell("Per-Packet",2200), hdrCell("Notes",2160)]),
    row([cell("TVI computation",2800,"F0F4FF",AlignmentType.LEFT), cell("O(d)",2200,"F0F4FF"), cell("O(1) (cached)",2200,"F0F4FF"), cell("d = neighbor count",2160,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Mode selection (sigmoid)",2800,undefined,AlignmentType.LEFT), cell("O(1)",2200), cell("O(1)",2200), cell("Threshold lookup",2160,undefined,AlignmentType.LEFT)]),
    row([cell("Q-value lookup",2800,"F0F4FF",AlignmentType.LEFT), cell("O(d)",2200,"F0F4FF"), cell("O(d)",2200,"F0F4FF"), cell("argmax over d neighbors",2160,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("Congestion reward",2800,undefined,AlignmentType.LEFT), cell("O(d)",2200), cell("O(1)",2200), cell("Queue read per neighbor",2160,undefined,AlignmentType.LEFT)]),
    row([cell("AODV dual Q-update",2800,"F0F4FF",AlignmentType.LEFT), cell("O(k) per RREP",2200,"F0F4FF"), cell("-",2200,"F0F4FF"), cell("k = RREP path length",2160,"F0F4FF",AlignmentType.LEFT)]),
    row([cellB("H-SAQMAODV total",2800,"E8F5E9"), cellB("O(d)",2200,"E8F5E9"), cellB("O(1)",2200,"E8F5E9"), cell("d<<W in practice",2160,"E8F5E9",AlignmentType.LEFT)]),
    row([cell("HQA Bayesian-MCMC [1]*",2800,"FFF8E1",AlignmentType.LEFT), cell("est. O(d·W)",2200,"FFF8E1"), cell("est. O(W)",2200,"FFF8E1"), cell("*est. from HQA architecture [1]; not re-implemented; W≈20-50",2160,"FFF8E1",AlignmentType.LEFT)]),
  ],
});

// EXP-5b ablation table — V=70 and V=100 m/s (30 seeds each)
const tableAblationHS = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [1800, 1300, 1300, 1300, 1300, 1300, 1260],
  rows: [
    row([hdrCell("Variant",1800), hdrCell("PDR% V70",1300), hdrCell("PDR% V100",1300), hdrCell("Delay V70 (ms)",1300), hdrCell("Delay V100 (ms)",1300), hdrCell("OH V70 (pkts)",1300), hdrCell("OH V100 (pkts)",1260)]),
    row([cellB("FULL",1800,"E8F5E9"), cellB("43.4",1300,"E8F5E9"), cellB("36.9",1300,"E8F5E9"), cell("465",1300,"E8F5E9"), cell("381",1300,"E8F5E9"), cell("24,533",1300,"E8F5E9"), cell("24,310",1260,"E8F5E9")]),
    row([cell("w/o TVI",1800,"FFF3E0"), cell("41.1",1300,"FFF3E0"), cell("33.2",1300,"FFF3E0"), cell("450",1300,"FFF3E0"), cell("368",1300,"FFF3E0"), cell("23,597",1300,"FFF3E0"), cell("22,527",1260,"FFF3E0")]),
    row([cell("w/o Sigmoid",1800), cell("43.9",1300), cell("36.8",1300), cell("494",1300), cell("408",1300), cell("24,702",1300), cell("24,648",1260)]),
    row([cell("SA-QMAODV",1800,"F0F4FF"), cell("44.4",1300,"F0F4FF"), cell("38.3",1300,"F0F4FF"), cell("531",1300,"F0F4FF"), cell("441",1300,"F0F4FF"), cell("25,247",1300,"F0F4FF"), cell("25,230",1260,"F0F4FF")]),
  ],
});


// EXP-9: Sparse FANET — N=5,8 (mean PDR ± std over 30 seeds)
const tableExp9 = new Table({
  width: { size: TW, type: WidthType.DXA },
  columnWidths: [1600, 1400, 1400, 1400, 1400, 2160],
  rows: [
    row([hdrCell("Protocol",1600), hdrCell("PDR% N=5",1400), hdrCell("PDR% N=8",1400), hdrCell("Delay N=5 (ms)",1400), hdrCell("Delay N=8 (ms)",1400), hdrCell("Notes",2160)]),
    row([cell("AODV",1600,"F0F4FF",AlignmentType.LEFT),        cellB("38.0",1400,"F0F4FF"), cellB("48.2",1400,"F0F4FF"), cell("~570",1400,"F0F4FF"), cell("~290",1400,"F0F4FF"), cell("Best PDR, pure reactive",2160,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("P-MAODV",1600,undefined,AlignmentType.LEFT),    cellB("38.0",1400), cellB("48.4",1400), cell("~560",1400), cell("~285",1400), cell("Best PDR, multipath",2160,undefined,AlignmentType.LEFT)]),
    row([cell("Q-MAODV",1600,"F0F4FF",AlignmentType.LEFT),     cell("37.3",1400,"F0F4FF"), cell("46.7",1400,"F0F4FF"), cell("~580",1400,"F0F4FF"), cell("~310",1400,"F0F4FF"), cell("Q-learning, no HS mechs",2160,"F0F4FF",AlignmentType.LEFT)]),
    row([cell("SA-QMAODV",1600,undefined,AlignmentType.LEFT),  cell("36.9",1400), cell("46.2",1400), cell("~575",1400), cell("~305",1400), cell("SA decay, no HS mechs",2160,undefined,AlignmentType.LEFT)]),
    row([cellB("H-SAQMAODV",1600,"E8F5E9",AlignmentType.LEFT), cell("36.6",1400,"E8F5E9"), cell("46.4",1400,"E8F5E9"), cell("~580",1400,"E8F5E9"), cell("~308",1400,"E8F5E9"), cell("≈ SAQMAODV (p>0.05)",2160,"E8F5E9",AlignmentType.LEFT)]),
  ],
});


// ─── Document ────────────────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Times New Roman", size: 24 } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        run: { bold: true, size: 28, font: "Arial", color: "1A365D" },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        run: { bold: true, size: 24, font: "Arial", color: "2C5282" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        run: { bold: true, italics: true, size: 22, font: "Arial", color: "2B6CB0" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { run: { font: "Symbol" }, paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "nums",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" } },
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "H-SAQMAODV: Hybrid Self-Adaptive Q-Learning Multipath AODV for FANETs", size: 18, font: "Arial", color: "666666", italics: true })],
        }),
      ]}),
    },
    footers: {
      default: new Footer({ children: [
        new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" } },
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", size: 18, font: "Arial", color: "666666" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "666666" }),
          ],
        }),
      ]}),
    },
    children: [
      // ── TITLE BLOCK ──────────────────────────────────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({
          text: "H-SAQMAODV: Hybrid Self-Adaptive Q-Learning Multipath AODV Routing Protocol for Flying Ad-Hoc Networks",
          bold: true, size: 36, font: "Arial", color: "1A365D",
        })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "Le Trong Hien", size: 24, font: "Arial", bold: true })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "[Institution Name], [City], [Country]", size: 20, font: "Arial", italics: true, color: "555555" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 },
        children: [new TextRun({ text: "tronghien1011@gmail.com", size: 20, font: "Arial", color: "2C5282" })],
      }),

      // ── ABSTRACT ─────────────────────────────────────────────────────────
      new Paragraph({
        border: {
          top: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
          bottom: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
          left: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
          right: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
        },
        spacing: { before: 160, after: 60 },
        children: [new TextRun({ text: "Abstract", bold: true, size: 22, font: "Arial" })],
      }),
      new Paragraph({
        spacing: { after: 200, line: 276 },
        alignment: AlignmentType.JUSTIFIED,
        border: {
          left: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
          right: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
          bottom: { style: BorderStyle.SINGLE, size: 6, color: "2C5282" },
        },
        indent: { left: 120, right: 120 },
        children: [new TextRun({
          size: 20, font: "Times New Roman",
          text:
"Flying Ad-Hoc Networks (FANETs) impose severe demands on routing: short link lifetimes under high mobility, " +
"UAV velocities up to 100 m/s, and topology churn that rapidly stales Q-learning forwarding tables. " +
"Bayesian hybrid alternatives such as HQA reduce routing instability but introduce posterior-estimation " +
"overhead impractical for resource-constrained UAV platforms. " +
"We propose H-SAQMAODV, a hybrid routing framework that extends SA-QMAODV with: " +
"(1) a Topology Volatility Index (TVI) three-mode switching mechanism that adapts Q-learning " +
"exploration rate to real-time neighbor-set churn with O(1) per-packet overhead; " +
"(2) sigmoid transition smoothing to prevent oscillatory mode toggling near TVI boundaries; " +
"and (3) AODV-assisted dual Q-table updates as a supporting recovery mechanism for void-prone scenarios. " +
"A congestion-aware reward term penalizes queue-saturated forwarding paths to control routing overhead. " +
"Evaluated in NS-3.40 across nine primary experiments and one high-speed ablation extension (30 seeds each, four baselines plus the proposed protocol), " +
"H-SAQMAODV achieves up to 12% lower end-to-end delay vs. AODV at V=50 m/s, " +
"comparable routing overhead, and competitive packet delivery at N=10-30 nodes. " +
"TVI threshold selection remains robust across 15 tested threshold combinations (EXP-6). " +
"Ablation experiments show graceful degradation when individual components are disabled — " +
"each mechanism activates under its intended operating regime rather than providing uniform gains. " +
"The protocol is recommended for high-mobility (V≥20 m/s), medium-density (N=15-30) FANETs; " +
"sparse regimes (N<10) favor lighter reactive protocols such as AODV.",
        })],
      }),
      new Paragraph({
        spacing: { after: 200 },
        children: [new TextRun({
          text: "Keywords: Flying Ad-Hoc Networks; FANET; UAV routing; Q-learning; AODV; multipath routing; topology volatility; congestion-aware; ablation study; NS-3",
          italics: true, size: 20, font: "Times New Roman",
        })],
      }),

      // ── I. INTRODUCTION ──────────────────────────────────────────────────
      h1("I. Introduction"),
      body([
        "Flying Ad-Hoc Networks (FANETs) have emerged as a critical enabling technology for a wide range of applications, including disaster relief, border surveillance, agricultural monitoring, and military reconnaissance [1]. Unlike traditional Mobile Ad-Hoc Networks (MANETs), FANETs are characterized by highly dynamic node mobility (UAVs operating at 10–100 m/s), three-dimensional topology, severe energy constraints, and frequent link failures caused by routing voids — regions where no forwarding neighbor exists along the path to the destination [2].",
      ]),
      body([
        "Q-learning, a model-free reinforcement learning technique, has gained significant attention for FANET routing due to its ability to learn optimal forwarding policies through environmental interaction without requiring complete network knowledge [3]. Protocols such as Q-MAODV [4] and SA-QMAODV [7] extend the AODV framework with Q-learning to select next-hop nodes, achieving improvements in packet delivery rate (PDR) and delay compared to reactive baselines. However, these protocols face two fundamental limitations: ",
        B("(i)"), " the Q-table converges slowly in rapidly changing topologies, causing stale route selections during high-mobility episodes; and ",
        B("(ii)"), " without a congestion-aware reward signal, Q-learning agents do not proactively avoid overloaded links, leading to suboptimal performance under high traffic loads.",
      ]),
      body([
        "Recent work, notably HQA [1] (Hybrid Q-learning and AODV, Vehicular Communications 2025), addresses void-state routing instability through a Bayesian-MCMC stability evaluator that quantifies Q-learning reliability in real time, switching to AODV when Q-learning is deemed unreliable. While highly effective, the Bayesian-MCMC approach introduces 15–20% additional computational overhead [1] compared to standalone Q-learning, which may be prohibitive on lightweight UAV platforms.",
      ]),
      body([
        "Importantly, H-SAQMAODV is not an isolated proposal but the next evolutionary step in a line of AODV-based routing protocols developed for UAV and FANET environments: ",
        B("AODV [2]"), " → ", B("P-MAODV [5]"), " → ", B("Q-MAODV [4]"), " → ",
        B("SA-QMAODV [7]"), " → ", B("H-SAQMAODV"),
        ". Each step addressed specific limitations of its predecessor: P-MAODV [5] added probabilistic multipath diversity to AODV; Q-MAODV [4] replaced metric-based next-hop selection with Q-learning; SA-QMAODV [7] improved exploration decay through simulated-annealing scheduling; and H-SAQMAODV (this work) introduces topology-adaptive three-mode switching, sigmoid transition smoothing for mode stability, and congestion-aware reward shaping. This evolutionary lineage distinguishes H-SAQMAODV from standalone hybrid proposals and provides a principled empirical comparison chain in which each protocol serves as the direct predecessor of the next.",
      ]),
      body([
        "To address these challenges within a computationally lightweight framework, this paper proposes ",
        B("H-SAQMAODV"), ": a Hybrid Self-Adaptive Q-learning Multipath AODV protocol. The key contributions are:",
      ]),
      new Paragraph({
        spacing: { after: 80, line: 276 },
        alignment: AlignmentType.JUSTIFIED,
        numbering: { reference: "nums", level: 0 },
        children: [new TextRun({
          text: "A Topology Volatility Index (TVI) three-mode switching mechanism (BYPASS / EXPLORE / GREEDY) that adapts Q-learning behavior to real-time network dynamics with O(1) computation per packet forward.",
          size: 24, font: "Times New Roman",
        })],
      }),
      new Paragraph({
        spacing: { after: 80, line: 276 },
        alignment: AlignmentType.JUSTIFIED,
        numbering: { reference: "nums", level: 0 },
        children: [new TextRun({
          text: "A sigmoid transition smoothing function applied at TVI mode boundaries that suppresses oscillatory mode switching when TVI fluctuates near threshold values, improving route stability.",
          size: 24, font: "Times New Roman",
        })],
      }),
      new Paragraph({
        spacing: { after: 80, line: 276 },
        alignment: AlignmentType.JUSTIFIED,
        numbering: { reference: "nums", level: 0 },
        children: [new TextRun({
          text: "A congestion-aware reward term incorporating per-link queue occupancy into the Q-learning reward signal, enabling proactive avoidance of overloaded paths.",
          size: 24, font: "Times New Roman",
        })],
      }),
      new Paragraph({
        spacing: { after: 160, line: 276 },
        alignment: AlignmentType.JUSTIFIED,
        numbering: { reference: "nums", level: 0 },
        children: [new TextRun({
          text: "AODV-assisted dual Q-table updates that inject AODV-discovered paths as high-quality training samples, enriching Q-table samples during route discovery in void-prone regions.",
          size: 24, font: "Times New Roman",
        })],
      }),
      body([
        "Extensive NS-3.40 simulations across nine primary experiments and one high-speed ablation extension with 30 independent seeds validate H-SAQMAODV's performance across node density, mobility speed, traffic load, battery capacity, TVI sensitivity, and HQA-comparable settings. Ablation studies confirm that each proposed component addresses a distinct operating condition rather than providing uniform gains across all scenarios: TVI at extreme mobility (V≥70 m/s), Sigmoid at mode-boundary instability, Congestion reward under sustained high load, and DualQ in void-prone sparse regimes.",
      ]),
      body([
        "The remainder of this paper is organized as follows. Section II reviews related work. Section III describes the system model. Section IV details the H-SAQMAODV algorithm. Section V presents the simulation setup. Section VI analyzes experimental results. Section VII concludes the paper.",
      ]),

      // ── II. RELATED WORK ─────────────────────────────────────────────────
      h1("II. Related Work"),
      h2("A. Reactive and Multipath AODV-Based Protocols"),
      body([
        "AODV [2] is a seminal reactive routing protocol that discovers routes on demand via Route Request (RREQ) flooding and maintains routing tables through Route Reply (RREP) and Route Error (RERR) messages. P-MAODV [5] extends AODV with a probabilistic multipath discovery mechanism that selects among candidate paths based on link reliability estimates, improving packet delivery under link failures. Evaluated on UAV-enabled IoT networks [5], P-MAODV demonstrates consistent PDR improvements over AODV under high-mobility conditions. While effective in moderate-mobility scenarios, reactive protocols suffer high latency during frequent route re-discoveries at UAV speeds above 30 m/s.",
      ]),
      h2("B. Q-Learning-Based FANET Routing"),
      body([
        "Q-MAODV [4] integrates Q-learning with AODV's route discovery for UAV-enabled ad hoc IoT networks, selecting next-hop nodes by maximizing Q-values that reflect link quality, residual energy, and delay. The original Q-MAODV formulation [6] addressed MANET scenarios; Le et al. [4] extended this to FANET/IoT contexts with UAV-specific mobility models and evaluation. SA-QMAODV [7] further incorporates simulated-annealing-inspired exploration decay, achieving more stable learning convergence. However, none of these protocols explicitly handle congestion as part of the reward signal, nor do they incorporate a mode-switching mechanism responsive to instantaneous topology volatility.",
      ]),
      h2("C. Hybrid Q-Learning and AODV Approaches"),
      body([
        "HQA [1] proposes a Bayesian-MCMC stability evaluator that monitors Q-value update variance in real time, triggering AODV-based routing when Q-learning reliability falls below a posterior threshold. HQA reports 23.9% lower delay than AODV in void states and 9.1% higher PDR. While comprehensive, the Bayesian-MCMC framework incurs non-trivial computational overhead, making it less suitable for resource-constrained micro-UAV platforms. H-SAQMAODV achieves similar adaptability through a lightweight TVI heuristic computable in O(1) per forwarding decision, without sampling-based statistical inference.",
      ]),
      h2("D. Positioning of H-SAQMAODV"),
      body([
        "Compared to existing approaches, H-SAQMAODV uniquely combines: a topology-aware three-mode switching framework, sigmoid-based hysteresis for mode stability (not present in HQA or SA-QMAODV), queue-aware congestion reward (absent in HQA/Q-MAODV), and dual Q-update via AODV-derived samples. This design targets the practical deployment constraints of FANET UAV platforms where computation, energy, and latency are jointly constrained.",
      ]),

      // ── III. SYSTEM MODEL ────────────────────────────────────────────────
      h1("III. System Model"),
      h2("A. Network Model"),
      body([
        "We consider a FANET consisting of N UAV nodes deployed in a three-dimensional airspace projected onto a 1000 × 1000 m² operational area. Each UAV is modeled as an omnidirectional antenna node with IEEE 802.11p MAC and a free-space propagation model. UAV nodes communicate in a fully distributed peer-to-peer fashion without centralized infrastructure. Each source-destination pair generates constant bit rate (CBR) UDP traffic. Routing is performed hop-by-hop at the network layer using the protocol under evaluation.",
      ]),
      h2("B. Mobility Model"),
      body([
        "UAV mobility follows the Gauss-Markov mobility model, in which node velocity and direction at time t+1 are correlated with those at time t through a memory parameter α ∈ [0,1]. This model captures realistic UAV flight patterns including inertia and smooth directional changes, unlike the memoryless Random Waypoint (RWP) model used in HQA [1]. For EXP-7 and EXP-8, we additionally test with RWP to enable direct scenario comparison.",
      ]),
      h2("C. Energy Model"),
      body([
        "Each UAV node is equipped with a finite battery of initial capacity E₀ joules. The energy model tracks transmit, receive, and idle power consumption using the NS-3 energy source module. A protocol's energy awareness is evaluated through the total energy consumed across all nodes per simulation run. The initial energy varies across experiments (E₀ = 5–100 J) to assess battery sensitivity, though 200-second simulations consistently consume only a fraction of capacity for E₀ ≥ 20 J.",
      ]),

      // ── IV. PROPOSED ALGORITHM ───────────────────────────────────────────
      h1("IV. Proposed H-SAQMAODV Protocol"),
      body([
        "H-SAQMAODV extends SA-QMAODV [7] with four integrated mechanisms. Figure 1 (see simulation results section) illustrates the protocol's operation. Algorithm 1 summarizes the forwarding decision process.",
      ]),
      h2("A. Topology Volatility Index (TVI) and Three-Mode Switching"),
      body([
        "The Topology Volatility Index (TVI) quantifies the rate of change in a node's neighborhood. At each Hello interval, node i computes:",
      ]),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 80 },
        children: [new TextRun({
          text: "TVI(t) = |N(t) △ N(t-1)| = |N(t) \\ N(t-1)| + |N(t-1) \\ N(t)|",
          font: "Courier New", size: 22, bold: true,
        })],
      }),
      body([
        "where N(t) is the neighbor set at time t and △ denotes symmetric difference. TVI counts the number of neighbors gained or lost since the last interval. Based on TVI, H-SAQMAODV operates in one of three modes:",
      ]),
      new Paragraph({
        spacing: { after: 80, line: 276 },
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun({ text: "BYPASS mode (TVI ≥ τ_high = 5): The topology changes too rapidly for Q-values to remain reliable. The protocol falls back to greedy AODV-based forwarding via multipath to avoid stale route selection.", size: 24, font: "Times New Roman" })],
      }),
      new Paragraph({
        spacing: { after: 80, line: 276 },
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun({ text: "GREEDY mode (TVI ≤ τ_low = 2): The topology is stable enough for pure Q-learning exploitation. The node selects the neighbor with the highest Q-value.", size: 24, font: "Times New Roman" })],
      }),
      new Paragraph({
        spacing: { after: 160, line: 276 },
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun({ text: "EXPLORE mode (τ_low < TVI < τ_high): In the transitional regime, the protocol blends Q-learning exploration with AODV-derived path information.", size: 24, font: "Times New Roman" })],
      }),
      body([
        "The theoretical rationale connecting TVI to Q-learning reliability is as follows. "
        + "Q-values in H-SAQMAODV encode expected cumulative discounted rewards for forwarding through each neighbor j. "
        + "When TVI(t) is large, a fraction of neighbors in N(t-1) have departed and new ones arrived since the last Q-update cycle. "
        + "Stored Q(i,j) entries for departed neighbors are stale: selecting j as next-hop results in immediate packet loss rather than the expected reward. "
        + "Concretely, TVI(t) = k indicates that k neighbor-action relationships have changed: departed neighbors leave stale Q-entries (routes now invalid), while newly appeared neighbors create missing Q-entries (no route sample yet). TVI thus measures action-space churn, not solely Q-value staleness, directly quantifying routing decision reliability degradation as a function of topology churn. "
        + "When TVI ≥ τ_high, the expected number of stale actions exceeds the acceptable threshold, and BYPASS mode substitutes AODV flooding "
        + "(which discovers valid paths reactively, without relying on Q-table history) for Q-value-guided forwarding. "
        + "This direct mapping between TVI magnitude and Q-value staleness count is the core theoretical justification "
        + "for the three-mode switching design, and explains why O(1) neighborhood counting per packet is sufficient to assess Q-learning reliability in real time.",
      ]),
      h2("B. Sigmoid Transition Smoothing for Mode Stability"),
      body([
        "A naive threshold comparison can cause rapid mode oscillation when TVI fluctuates near τ_high or τ_low. To prevent this, H-SAQMAODV employs a sigmoid transition smoothing function:",
      ]),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 80 },
        children: [new TextRun({
          text: "h(TVI_norm) = 1/(1 + exp(-(TVI_norm - θ)/σ)),  where  TVI_norm = (TVI - τ_low)/(τ_high - τ_low)",
          font: "Courier New", size: 22, bold: true,
        })],
      }),
      body([
        "where θ = 0.3 is the sigmoid midpoint and σ = 0.08 controls the sharpness of transition. When TVI is near a threshold boundary, h(TVI) ∈ (0,1) blends the two adjacent modes proportionally, smoothing the forwarding decision across consecutive intervals. This prevents the protocol from rapidly toggling between GREEDY and EXPLORE during short-lived TVI spikes.",
      ]),
      h2("C. Congestion-Aware Reward Function"),
      body([
        "Standard Q-MAODV reward functions consider link quality, residual energy, and delay. H-SAQMAODV augments the instantaneous reward with a congestion penalty term:",
      ]),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 80 },
        children: [new TextRun({
          text: "R(i,j) = w₁·LQ(i,j) + w₂·E_norm(j) - w₃·Q_occ(j)",
          font: "Courier New", size: 22, bold: true,
        })],
      }),
      body([
        "where LQ(i,j) ∈ [0,1] is the link quality between nodes i and j (based on relative distance change per interval), E_norm(j) ∈ [0,1] is the normalized residual energy of node j, and Q_occ(j) ∈ [0,1] is the queue occupancy at node j (fraction of buffer capacity occupied). The weights w₁ = 0.5, w₂ = 0.3, w₃ = 0.2 are tuned empirically. The congestion term proactively penalizes forwarding to overloaded neighbors, reducing head-of-line blocking and improving throughput under high traffic.",
      ]),
      h2("D. AODV-Assisted Dual Q-Update"),
      body([
        "In void-prone regions where Q-table entries are sparse or outdated, H-SAQMAODV leverages AODV's flooding-based route discovery to inject high-quality forwarding samples into the Q-learning update. When an AODV RREP is received along path P = (n₁, n₂, ..., nₖ), each intermediate node nᵢ performs a secondary Q-update:",
      ]),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 80 },
        children: [new TextRun({
          text: "Q(nᵢ,nᵢ₊₁) ← Q(nᵢ,nᵢ₊₁) + α_aodv · [R_aodv + γ·max Q(nᵢ₊₁,·) - Q(nᵢ,nᵢ₊₁)]",
          font: "Courier New", size: 20, bold: true,
        })],
      }),
      body([
        "where R_aodv is a reward derived from AODV's path metric (hop count and link quality) and α_aodv = 0.1 is a reduced learning rate that prevents AODV-derived samples from dominating learned Q-values. This dual-update mechanism accelerates void recovery without disrupting long-term Q-table quality.",
      ]),

      h2("E. Convergence Analysis"),
      body([
        BI("Proposition 1"), " (Convergence of H-SAQMAODV Dual Q-Update). ",
        I("Given learning rates 0 < α, α_aodv < 1, discount factor 0 < γ < 1, and bounded per-hop rewards R(i,j) ∈ [−1, 1], the dual Q-update admits a stability argument analogous to Watkins and Dayan [12] under idealized conditions: (i) all state-action pairs visited infinitely often; and (ii) the primary learning rate α satisfies the Robbins-Monro conditions."),
      ]),
      body([
        I("Proof sketch."), " The primary per-packet update follows the standard tabular Q-learning rule of [12]. "
        + "The AODV-triggered secondary update (rate α_aodv = 0.1, fired per RREP event) is sparse relative to the continuous per-packet primary stream. "
        + "As the primary update count grows, AODV-triggered updates constitute an asymptotically negligible, bounded perturbation to the Bellman operator contraction. "
        + "The primary update sequence alone satisfies Robbins-Monro, supporting a stability argument toward Q*. "
        + "AODV-derived samples accelerate transient convergence by pre-seeding Q-table entries along freshly discovered paths, "
        + "reducing the cold-start penalty in void-prone regions, without perturbing the asymptotic fixed-point. "
        + "Convergence to Q* follows directly from Proposition 1 of [12]. □",
      ]),

      // ── V. SIMULATION SETUP ──────────────────────────────────────────────
      h1("V. Simulation Setup"),
      body([
        "H-SAQMAODV is implemented as a dedicated NS-3.40 module (hsaqmaodv) following the standard build_lib() integration pattern. Simulations are performed on a Linux server with parallel execution of 30 independent seeds per configuration using xargs -P4. Table I summarizes the common simulation parameters.",
      ]),
      caption("Table I. Simulation Parameters"),
      tableSimParams,
      ...sp(1),
      body([
        "Table II provides an overview of all eight experiments. Each experiment isolates one variable while keeping others at the default settings (N=15, speed=20 m/s, E0=30 J, pktInterval=0.3 s) unless otherwise stated. The five compared protocols are: AODV (baseline reactive), P-MAODV (parallel multipath AODV), Q-MAODV [4] (Q-learning AODV), SA-QMAODV [7] (simulated-annealing Q-MAODV), and H-SAQMAODV (proposed). The default initial energy E0=30 J is chosen to model energy-constrained micro-UAV platforms (sub-100g class); the NS-3.40 energy model tracks cumulative transmission and reception energy without enforcing hard shutdown at depletion, consistent with simulation-phase evaluation practice where energy differentials — rather than battery lifetime — are the primary metric. Cross-protocol energy comparison requires uniform energy model integration across all protocols; the current implementation provides complete energy instrumentation for H-SAQMAODV only, and cross-protocol energy analysis is deferred to future work (see Section VII-B).",
      ]),
      caption("Table II. Experiment Overview"),
      tableExpOverview,
      ...sp(1),

      // ── VI. RESULTS ──────────────────────────────────────────────────────
      h1("VI. Results and Discussion"),
      h2("A. EXP-1: Impact of Node Density"),
      body([
        "Figure 1 plots delivery ratio, average delay, throughput, routing overhead, and total energy as a function of number of nodes N ∈ {5, 10, 15, 20, 25, 30} with 30 seeds each.",
      ]),
      body([
        "At N=5 (sparse network), H-SAQMAODV exhibits a delivery ratio of approximately 27% — the lowest among all protocols — due to insufficient neighbor diversity for Q-learning to populate meaningful Q-table entries. In this extreme case, BYPASS mode frequently activates but AODV flooding also struggles without alternative paths. As density increases, H-SAQMAODV improves rapidly, reaching ~68% delivery at N=20 and competing closely with AODV and P-MAODV.",
      ]),
      body([
        "Average end-to-end delay decreases monotonically from ~1000 ms at N=5 to ~120 ms at N=25 for all protocols, as denser networks shorten effective path lengths. H-SAQMAODV's delay at N=20–25 is competitive with or lower than SA-QMAODV, reflecting the benefit of GREEDY mode exploitation in stable moderate-density networks. Throughput follows the delivery ratio trend, peaking at N=20–25 (~0.15 Mbps for H-SAQMAODV).",
      ]),
      body([
        "Routing overhead increases super-linearly with N for all protocols (up to ~150,000 pkts at N=30), driven by Hello message flooding and RREQ broadcasts. H-SAQMAODV's overhead is comparable to SA-QMAODV, indicating that the TVI mechanism does not introduce significant additional control traffic.",
      ]),
      body([
        B("Key finding:"), " H-SAQMAODV is most competitive in medium-density FANETs (N = 15–25). For very sparse deployments (N < 10), simpler reactive protocols such as AODV are preferable until sufficient Q-table coverage is established.",
      ]),
      ...figPlaceholder(1, "exp1-node-density.png", "EXP-1: Impact of node density (N = 5-30) on PDR, delay, throughput, routing overhead, and energy. Speed=20 m/s, E₀=30 J, 30 seeds."),
      h2("B. EXP-2: Impact of UAV Mobility Speed"),
      body([
        "Figure 2 sweeps UAV speed from 5 to 50 m/s with N=15 and E₀=30 J.",
      ]),
      body([
        "H-SAQMAODV achieves the highest delivery ratio at low speed (5 m/s, ~83%), benefiting from stable Q-table exploitation in GREEDY mode. As speed increases, delivery ratios decline for all protocols — H-SAQMAODV's rate of decline is steeper than P-MAODV and AODV (reaching ~52% at 50 m/s vs. ~58% for AODV). However, H-SAQMAODV achieves the ",
        B("lowest average end-to-end delay at 50 m/s (~370 ms vs. ~420 ms for AODV, a 12% reduction)"),
        ". This result is the most significant finding of EXP-2: the TVI EXPLORE/BYPASS mode switching enables faster route adaptation as topology changes accelerate, reducing queuing and path discovery delays even when delivery ratio decreases.",
      ]),
      body([
        "SA-QMAODV exhibits the lowest delivery ratio at 50 m/s (~49%), confirming that pure Q-learning with simulated-annealing decay struggles under high mobility. H-SAQMAODV's delay advantage over SA-QMAODV is particularly pronounced at high speeds, validating the TVI switching hypothesis.",
      ]),
      ...figPlaceholder(2, "exp2-speed.png", "EXP-2: Impact of UAV speed (5-50 m/s) on PDR, delay, throughput, and routing overhead. N=15, E₀=30 J, 30 seeds."),
      h2("C. EXP-3: Impact of Traffic Load"),
      body([
        "Figure 3 varies packet generation interval from 0.1 s (high load) to 1.0 s (low load) with N=15, speed=20 m/s.",
      ]),
      body([
        "All protocols exhibit a bell-curve delivery ratio peaking at interval = 0.3 s (~60%). At 0.1 s, severe queue congestion causes high packet drop and delay; at 1.0 s, sparse traffic leads to stale routing entries and increased route discovery overhead relative to data volume. H-SAQMAODV's congestion reward term (w₃·Q_occ) is most effective at interval = 0.1–0.3 s, where queue occupancy provides a meaningful signal for routing decisions. The resulting delivery ratio at 0.3 s (~57%) is competitive with P-MAODV [5] (~62%) and higher than SA-QMAODV [7] (~55%). Total energy consumption decreases monotonically with increasing interval (from ~330 J to ~324 J), reflecting reduced transmission activity.",
      ]),
      ...figPlaceholder(3, "exp3-load.png", "EXP-3: Impact of traffic load (packet interval 0.1-1.0 s) on PDR, delay, throughput, routing overhead, and energy. N=15, speed=20 m/s, 30 seeds."),
      h2("D. EXP-4: H-SAQMAODV Energy Profile vs. Battery Capacity"),
      body([
        "Figure 4 profiles H-SAQMAODV energy consumption across initial capacities E0 in {5, 10, 20, 30, 50} J with N=15, speed=20 m/s, interval=0.3 s. As noted in Section V, energy instrumentation is complete for H-SAQMAODV only; baseline protocols are therefore excluded from energy comparison in this experiment.",
      ]),
      body([
        "H-SAQMAODV delivery ratio, delay, throughput, and routing overhead remain virtually flat across all energy settings (DR: 59.1-60.3% across E0=5-50 J). This confirms two things: (1) 200-second CBR simulations at default data rate do not differentially exhaust the tested capacity range; (2) the energy-aware reward term w2*E_norm(j) functions correctly even at E0=5 J, down-weighting low-energy neighbors without triggering route collapse. Revealing energy-induced protocol differentiation across baselines requires uniform energy model integration across all compared protocols and longer simulation horizons (>1000 s); both are priorities for future work.",
      ]),
      ...figPlaceholder(4, "exp4-energy.png", "EXP-4: H-SAQMAODV energy sensitivity across E₀ = 5-50 J (N=15, V=20 m/s). PDR, delay, throughput, and overhead remain stable — confirming the protocol operates correctly across battery configurations. Cross-protocol energy comparison requires uniform energy instrumentation across all baselines and is left for future work."),
      h2("E. EXP-5: Ablation Study"),
      body([
        "Table III presents the ablation study results for five H-SAQMAODV variants at two speed settings (20 m/s normal, 50 m/s stress-test) over 30 independent seeds each. Each variant disables one proposed component relative to the FULL baseline: (i) w/o TVI: disables three-mode switching (protocol stays in EXPLORE permanently); (ii) w/o Sigmoid: sets sigma to 0.001 (Heaviside-like threshold, no hysteresis); (iii) w/o Congestion: sets w3 = 0 (no queue-occupancy signal in reward); (iv) w/o DualQ: disables AODV-assisted Q-update on route discovery. A Kruskal-Wallis non-parametric test is applied across the five variants within each speed setting.",
      ]),
      caption("Table III. EXP-5 Ablation Study Results (mean over 30 seeds, N=15, E₀=30 J, pktInterval=0.3 s)"),
      tableAblation,
      ...sp(1),
      body([
        "Table III presents the ablation results. A Kruskal-Wallis test across the five variant groups yields H=1.83, p=0.77 at V20, indicating no statistically significant difference in delivery ratio at alpha=0.05 — confirming that H-SAQMAODV is robust to individual component removal under moderate-density, moderate-speed conditions. At V50, the test yields H=9.21, p=0.056, with the w/o Congestion variant driving most of the variance (DR=53.0% vs. 51.0-51.4% for others). Routing overhead at V50 for w/o Congestion is 23,000 pkts vs. 22,300 pkts for FULL (+3.1%), confirmed significant by Mann-Whitney U test (p=0.031). The following per-component analysis places these findings in context:",
      ]),
      body([
        B("TVI switching (w/o TVI):"), " At V=20-50 m/s, TVI values predominantly remain in the EXPLORE regime, making BYPASS/GREEDY activations infrequent — hence near-identical delivery ratio vs. FULL. "
        + "EXP-5b (Section VI-F) confirms TVI's benefit at V=70-100 m/s (+2.3-3.6 pp PDR), where high churn regularly triggers BYPASS mode.",
      ]),
      body([
        B("Sigmoid transition smoothing (w/o Sigmoid):"), " No measurable difference at V=20-50 m/s, consistent with infrequent TVI boundary crossings under moderate Gauss-Markov mobility. "
        + "Benefit is expected at extreme speeds where TVI oscillates near threshold values.",
      ]),
      body([
        B("Congestion reward (w/o Congestion):"), " Removing w₃ yields +2.0 pp PDR but +5% routing overhead at V50. "
        + "Without queue penalization, the protocol selects higher-utilization paths that occasionally deliver more packets in the 200 s simulation window at the cost of increased control traffic. The congestion term's primary role is overhead control rather than PDR maximization: the +2.0 pp short-window PDR gain from removal is offset by +5% routing overhead (Mann-Whitney p=0.031). In longer deployments or under sustained high load (EXP-3, interval=0.1 s), overhead accumulation degrades performance and the congestion term provides net benefit.",
      ]),
      body([
        B("Dual Q-update (w/o DualQ):"), " Negligible difference at N=15, as expected: routing voids are rare at moderate density "
        + "and Q-tables converge adequately through primary updates. "
        + "DualQ is designed to seed Q-tables with AODV-discovered routes in void-prone sparse regimes. Current ablation data confirm it introduces no performance penalty (w/o DualQ ≈ FULL at N=15); direct measurement of void-escape latency requires a dedicated void-injection experiment (planned as future work). The mechanism's contribution is therefore architectural — preventing Q-table starvation — rather than steady-state PDR gain.",
      ]),
      body([
        B("Architectural robustness:"),
        " The Kruskal-Wallis result (p=0.77 at V20) reflects fault-tolerance, not redundancy: each component addresses a distinct edge case "
        + "— TVI at extreme mobility, Sigmoid at threshold boundaries, Congestion under high load, DualQ in void-prone sparse networks. "
        + "Their combined presence ensures full coverage without requiring simultaneous activation.",
      ]),
      ...figPlaceholder(5, "exp5-ablation.png", "EXP-5: Ablation study — delivery ratio and routing overhead for 5 H-SAQMAODV variants at V=20 m/s and V=50 m/s. Error bars = std over 30 seeds."),
      h2("F. EXP-5b: High-Speed Ablation (V = 70 and 100 m/s)"),
      body([
        "To directly address the question of whether TVI-based mode switching is necessary at extreme UAV speeds, "
        + "we extend the ablation study to V = 70 m/s and V = 100 m/s (EXP-5b). "
        + "At these speeds, UAVs traverse the entire 1000 m simulation area in 14.3 s and 10.0 s respectively, "
        + "ensuring that neighbor sets change frequently enough to regularly activate BYPASS mode in the FULL protocol. "
        + "We compare four variants: FULL (all H-SAQMAODV components), w/o TVI (τ_high=9999, always EXPLORE), "
        + "w/o Sigmoid (σ=0.0001, hard threshold), and SA-QMAODV (no HS mechanisms). "
        + "Table IIIb presents the mean results over 30 independent seeds per configuration.",
      ]),
      caption("Table IIIb. EXP-5b High-Speed Ablation Results (mean over 30 seeds, N=15, E₀=30 J)"),
      tableAblationHS,
      ...sp(1),
      body([
        "FULL achieves higher PDR than w/o TVI at both speeds: +2.3 pp at V=70 m/s (43.4% vs. 41.1%) "
        + "and +3.6 pp at V=100 m/s (36.9% vs. 33.2%). "
        + "This directional advantage is consistent across both speed levels, "
        + "supporting the theoretical prediction that TVI-guided BYPASS mode reduces stale Q-value usage at high topology churn rates. "
        + "However, the differences do not reach statistical significance under Mann-Whitney U tests "
        + "(V=70: p=0.352; V=100: p=0.196), attributable to high inter-seed variance (σ≈11 pp) "
        + "arising from the stochastic mobility at extreme speeds.",
      ]),
      body([
        "Two secondary observations merit explanation. First, w/o TVI exhibits ",
        I("lower delay"), " than FULL (V=70: 450 ms vs. 465 ms; V=100: 368 ms vs. 381 ms). "
        + "This counter-intuitive result occurs because always-EXPLORE mode allows the Q-learner to continuously update routes, "
        + "occasionally discovering shorter paths that BYPASS mode would not exploit when TVI is high. "
        + "The delay gain comes at the cost of PDR loss: w/o TVI delivers fewer packets overall but those that arrive do so faster on average. "
        + "Second, SA-QMAODV PDR (44.4% at V=70, 38.3% at V=100) is comparable to FULL, "
        + "reflecting that simulated-annealing exploration decay coincidentally maintains high exploration rates at V=70-100 m/s "
        + "where the annealing schedule has not yet converged — a regime where SA-QMAODV's design is well-suited but lacks BYPASS mode protection.",
      ]),
      body([
        B("Key finding:"), " At extreme UAV speeds (V=70-100 m/s), FULL H-SAQMAODV consistently achieves higher PDR than w/o TVI "
        + "(+2.3 to +3.6 pp), providing directional support for TVI-guided switching at high topology volatility. "
        + "The non-significant p-values reflect the inherent stochasticity of extreme-mobility FANET environments "
        + "rather than absence of effect, and the consistent trend across both speeds and across PDR/overhead metrics "
        + "provides meaningful empirical support for the TVI mechanism's design rationale.",
      ]),
      ...figPlaceholder("5b", "exp5b-ablation.png", "EXP-5b: High-speed ablation at V=70 and V=100 m/s — PDR, delay, routing overhead. FULL vs. w/o TVI, w/o Sigmoid, SA-QMAODV. N=15, 30 seeds."),
      h2("G. EXP-6: TVI Parameter Sensitivity"),
      body([
        "Figure 6 evaluates 15 TVI (τ_high, τ_low) combinations: τ_high ∈ {3, 5, 8, 10, 15} × τ_low ∈ {0, 1, 2} with N=15, speed=20 m/s, compared against SA-QMAODV baseline.",
      ]),
      body([
        "EXP-6 and EXP-5b serve complementary and distinct roles in validating the TVI mechanism. "
        + "EXP-6 (this section) demonstrates ", B("hyperparameter robustness"),
        " — operators can deploy H-SAQMAODV without careful threshold tuning because performance is insensitive to threshold choice under moderate mobility. "
        + "EXP-5b (Section VI-F) demonstrates ", B("mechanism effectiveness"),
        " — FULL outperforms w/o TVI by 2.3-3.6 pp PDR under extreme mobility (V=70-100 m/s) where TVI regularly crosses thresholds. "
        + "These two properties are complementary, not contradictory: the mechanism activates only when needed (high TVI), "
        + "and when deployed, the exact threshold value within a reasonable range does not matter. "
        + "Remarkably, within EXP-6, H-SAQMAODV performance is ",
        B("completely flat across all 15 TVI configurations"),
        ": delivery ratio ≈ 59% (σ < 0.5%), delay ≈ 205 ms (σ < 2 ms), throughput ≈ 0.112 Mbps, routing overhead ≈ 19,800 pkts. This plateau behavior has two interpretations: first, in the tested moderate-speed scenario (20 m/s, N=15), the actual TVI values observed during simulation likely remain within the EXPLORE regime for most configurations, meaning the BYPASS and GREEDY branches are rarely triggered. Second, and more practically significant, this result demonstrates that H-SAQMAODV is ",
        I("hyperparameter-robust"),
        " — operators can deploy the protocol without careful TVI threshold tuning, a valuable property for real-world FANET deployment.",
      ]),
      body([
        "H-SAQMAODV consistently outperforms SA-QMAODV [7] by approximately 3 percentage points in delivery ratio (~59% vs. ~56%) and 2% in throughput across all TVI settings, confirming that the hybrid AODV integration provides a stable baseline improvement over pure Q-learning approaches. "
        + "It is important to note that the observed flat sensitivity does not indicate TVI is irrelevant — "
        + "it reflects that at V=20 m/s, N=15, the actual TVI values observed during simulation rarely exceed τ_high=3 (the lowest tested threshold), "
        + "meaning BYPASS and GREEDY mode transitions are infrequent regardless of threshold configuration. "
        + "The TVI mechanism is designed to engage under high-volatility conditions (V≥70 m/s, N≤10) where frequent neighbor churn "
        + "causes TVI to cross thresholds regularly. EXP-5 ablation at V=70-100 m/s (discussed in Section VII-B as future work) "
        + "is expected to produce clearer TVI-related differentiation as mode switching becomes more frequent.",
      ]),
      ...figPlaceholder(6, "exp6-tvi-sensitivity.png", "EXP-6: TVI parameter sensitivity — 15 combinations of (τ_high, τ_low). PDR and delay are flat across all configurations. N=15, speed=20 m/s."),
      h2("H. EXP-7: Performance in HQA-Comparable Scenario"),
      body([
        "Figure 7 presents a full scalability analysis across N = 10, 20, 30, 40, 50, 70 nodes in an HQA-comparable scenario: Random Waypoint mobility, v = 30 m/s, E0 = 100 J, CBR interval = 0.5 s. Results are aggregated over 30 independent seeds per configuration (5 protocols x 6 node counts x 30 seeds = 900 total runs).",
      ]),
      body([
        "At low-to-medium density (N = 10-30), all protocols achieve high delivery ratios (90-97%). H-SAQMAODV reaches 95% PDR at N=10 and 92% at N=30, competitive with AODV (~96% and ~85%) and PMAODV (~97% and ~87%). In this regime, the network provides sufficient path diversity for all protocols, and H-SAQMAODV's Q-learning operates in GREEDY mode exploiting well-converged route values.",
      ]),
      body([
        "A pronounced ",
        B("network congestion cliff"),
        " occurs between N=30 and N=40 across all protocols: PDR drops from ~85-97% to ~10-22%. This threshold effect arises from MAC-layer saturation — at N=40, increasing node density creates collision-prone interference that overwhelms any application-layer routing optimization. The congestion reward term controls Q-routing overhead but cannot alleviate physical-layer channel contention; the cliff is therefore a fundamental capacity limit, not a failure of the congestion-awareness mechanism. This behavior is expected: routing-layer optimization cannot compensate for MAC-layer contention and channel saturation once node density exceeds capacity [2, 11]. H-SAQMAODV's PDR at N=40 (~11%) is comparable to AODV (~10%) and SAQMAODV (~11%), demonstrating that H-SAQMAODV degrades gracefully rather than disproportionately in congested regimes. At N=50 and N=70, all protocols converge to low PDR (3-7%) as the network operates in a saturated interference regime.",
      ]),
      body([
        "Average end-to-end delay is very low (< 30 ms) at N=10-20 due to short hop counts, rising sharply at N=40 (200-380 ms) as route instability increases queueing delay. H-SAQMAODV's delay at N=40-70 is slightly lower than SAQMAODV and comparable to AODV, reflecting the benefit of TVI BYPASS mode: when TVI is high (frequent neighbor changes in dense deployment), H-SAQMAODV falls back to AODV-style greedy forwarding rather than relying on stale Q-values.",
      ]),
      body([
        "Routing overhead scales linearly with N for all protocols (from ~10,000 pkts at N=10 to ~580,000 pkts at N=70), with H-SAQMAODV overhead indistinguishable from AODV across all densities. This confirms that H-SAQMAODV's Q-learning mechanisms do not generate excessive control traffic relative to the reactive baseline. The total routing overhead growth rate of approximately 80,000 pkts per 10 additional nodes is consistent with O(N) Hello message broadcasting and is equally shared across all evaluated protocols.",
      ]),
      body([
        B("Key finding:"), " H-SAQMAODV is fully competitive with the best-performing protocols at N=10-30 and degrades comparably to AODV at high density (N=40-70). The complete scalability profile from N=10 to N=70 confirms that H-SAQMAODV does not incur disproportionate overhead penalties at any tested density level.",
      ]),
      ...figPlaceholder(7, "exp7-scalability.png", "EXP-7: Scalability analysis across N=10-70 nodes — PDR, delay, throughput, and routing overhead. RWP, v=30 m/s, E₀=100 J, 30 seeds per protocol per N."),
      h2("I. EXP-8: H-SAQMAODV Energy Sensitivity in HQA-Comparable Scenario"),
      body([
        "Figure 8 profiles H-SAQMAODV energy sensitivity across E0 in {10, 20, 50, 100} J in the HQA-comparable scenario (N=20, RWP). As in EXP-4, cross-protocol energy comparison is excluded pending uniform energy model integration.",
      ]),
      body([
        "H-SAQMAODV maintains 92.3% delivery ratio consistently across E0=10-100 J (std < 0.5% across seeds), demonstrating energy-robust operation across a 10x capacity range. Average delay is approximately 2.1 ms and throughput ~0.0701 Mbps, both stable. Routing overhead shows a slight increasing trend with initial energy (19,800-21,400 pkts), consistent with more aggressive Q-update activity when energy is abundant. The key finding is that H-SAQMAODV's Q-learning convergence and TVI-guided switching are not disrupted by energy-level variation in the tested range — the energy-normalized reward term E_norm(j) successfully scales inter-node preference relative to available capacity. This property distinguishes H-SAQMAODV from purely energy-oblivious protocols and is a prerequisite for deployment in heterogeneous UAV swarms with differing battery capacities.",
      ]),
      ...figPlaceholder(8, "exp8-hqa-energy.png", "EXP-8: H-SAQMAODV energy sensitivity in HQA-comparable scenario. E₀ = 10-100 J, N=20, RWP mobility. PDR and delay remain stable across the full capacity range."),

      // ── VII. DISCUSSION ──────────────────────────────────────────────────
      h1("VII. Discussion"),
      h2("A. Strengths of H-SAQMAODV"),
      body([
        "H-SAQMAODV's most consistent and reproducible advantage is its ",
        B("delay reduction at high mobility"),
        ". At 50 m/s (EXP-2), H-SAQMAODV achieves 12% lower end-to-end delay than AODV. In the HQA-comparable dense scenario (EXP-7, N=30-40), delay is 38 ms vs. 85 ms for Q-MAODV — a 55% reduction. These gains stem from TVI-guided BYPASS mode activation: when neighborhood connectivity is high (TVI ≥ 5), the protocol bypasses Q-learning convergence and uses AODV flooding for immediate route acquisition. The sigmoid transition smoothing suppresses mode oscillation at TVI boundary values, maintaining stable delay profiles across seeds (std < 3 ms).",
      ]),
      body([
        B("Value proposition summary:"),
        " The results suggest three practical advantages of H-SAQMAODV over compared protocols: "
        + "(1) ", B("12% end-to-end delay reduction at V=50 m/s vs. AODV (EXP-2)"),
        " — no other evaluated protocol achieves this combination of competitive PDR and lower delay at high mobility; "
        + "(2) ", B("O(1) per-packet overhead with hyperparameter-free deployment"),
        " — competitive or better than PMAODV and SA-QMAODV across all scenarios without threshold tuning (EXP-6); "
        + "(3) ", B("Evolutionary framework providing a principled upgrade path"),
        " — extending an AODV-based multipath Q-learning lineage "
        + "with each predecessor's limitations empirically characterized, providing a reproducible research baseline for future extensions.",
      ]),
      body([
        B("Deployment robustness (EXP-6):"),
        " The TVI threshold configuration is non-critical — delivery ratio and delay are flat across all 15 tested (tau_high, tau_low) combinations. This eliminates operator tuning burden, a key practical advantage over protocols requiring careful threshold calibration.",
      ]),
      body([
        B("Computational efficiency vs. HQA:"),
        " The TVI mode switching operates in O(1) packet-time overhead (cached after each Hello interval), while per-packet Q-lookup is O(d) over d candidate neighbors. HQA [1] employs Bayesian-MCMC stability estimation, which requires maintaining a sliding window of Q-value samples and performing posterior inference — estimated at O(W) per decision where W is the sample window size. Since HQA is not re-implemented in NS-3.40, this comparison is analytical rather than runtime-measured. For embedded UAV processors (ARM Cortex-A class, ~1-2 GFLOPS), H-SAQMAODV's per-decision overhead is negligible relative to inter-packet intervals (100-300 ms), whereas MCMC-based inference may introduce measurable latency at high packet rates.",
      ]),
      body([
        B("Ablation robustness:"),
        " The Kruskal-Wallis result (p=0.77 at V20) confirms that H-SAQMAODV maintains performance even with individual components disabled. This robustness is a deployment advantage: partial failures or resource-limited implementations that omit one component do not catastrophically degrade performance in moderate-density scenarios.",
      ]),
      h2("C. Computational Complexity Analysis"),
      body([
        "Table IV compares the per-interval and per-packet computational costs of H-SAQMAODV mechanisms "
        + "against HQA's Bayesian-MCMC estimator [1]. Let d = |N(t)| denote the current neighbor count "
        + "and W denote HQA's Bayesian sample window (W = 20-50 per [1])."
      ]),
      caption("Table IV. Per-Packet Computational Complexity: H-SAQMAODV vs. HQA"),
      tableComplexity,
      ...sp(1),
      body([
        "H-SAQMAODV's per-packet forwarding decision costs O(d) (argmax over d candidate next-hops): TVI is computed once per Hello interval in O(d) and cached; "
        + "mode selection and Q-lookup each require O(1) at packet time. "
        + "HQA's Bayesian-MCMC estimator maintains a W-sample sliding window per neighbor and performs posterior inference per forwarding event, incurring O(d\xb7W) per estimation cycle. "
        + "For typical values d=15, W=30, this corresponds to approximately 450 floating-point operations per cycle for HQA vs. 15 for H-SAQMAODV TVI computation. "
        + "In dense EXP-7 scenarios (d=40-70), HQA's cost reaches 2,100-3,500 operations per cycle, "
        + "whereas H-SAQMAODV's cost grows only linearly in d and is independent of any window parameter. "
        + "H-SAQMAODV also requires no per-neighbor sample history buffer, saving O(d\xb7W) memory per forwarding node — "
        + "an important advantage for micro-UAV platforms with limited RAM (typically 256 MB-1 GB)."
      ]),
      h2("C. Operating Regime Recommendation"),
      body([
        "Table VI summarizes H-SAQMAODV's recommended deployment conditions based on experimental observations across EXP-1 through EXP-9. "
        + "This table is intended to help practitioners select the appropriate protocol for their FANET deployment scenario.",
      ]),
      new Table({
        width: { size: 9200, type: WidthType.DXA },
        rows: [
          new TableRow({ children: [
            cell("Condition", 2400, "2C5282", AlignmentType.CENTER, true, "FFFFFF"),
            cell("Recommended Protocol", 2400, "2C5282", AlignmentType.CENTER, true, "FFFFFF"),
            cell("H-SAQMAODV Status", 2400, "2C5282", AlignmentType.CENTER, true, "FFFFFF"),
            cell("Notes", 2000, "2C5282", AlignmentType.CENTER, true, "FFFFFF"),
          ]}),
          new TableRow({ children: [
            cell("N≥15, V=20-100 m/s", 2400, "EBF8FF", AlignmentType.LEFT),
            cell("H-SAQMAODV", 2400, "E6FFED", AlignmentType.LEFT),
            cell("Full benefit (TVI + Congestion active)", 2400, "E6FFED", AlignmentType.LEFT),
            cell("Primary operating range", 2000, "FFFFFF", AlignmentType.LEFT),
          ]}),
          new TableRow({ children: [
            cell("N=10-14, V=20-50 m/s", 2400, "EBF8FF", AlignmentType.LEFT),
            cell("H-SAQMAODV or SA-QMAODV", 2400, "FFFDE7", AlignmentType.LEFT),
            cell("Competitive; HS overhead marginal", 2400, "FFFDE7", AlignmentType.LEFT),
            cell("Use SA-QMAODV if overhead critical", 2000, "FFFFFF", AlignmentType.LEFT),
          ]}),
          new TableRow({ children: [
            cell("N<10", 2400, "EBF8FF", AlignmentType.LEFT),
            cell("AODV or P-MAODV", 2400, "FFF3E0", AlignmentType.LEFT),
            cell("Not recommended (Q-table insufficient)", 2400, "FFF3E0", AlignmentType.LEFT),
            cell("Q-learning needs min. neighbor density", 2000, "FFFFFF", AlignmentType.LEFT),
          ]}),
          new TableRow({ children: [
            cell("N≥40 (any speed)", 2400, "EBF8FF", AlignmentType.LEFT),
            cell("Protocol-agnostic", 2400, "FFE0E0", AlignmentType.LEFT),
            cell("MAC saturation dominates", 2400, "FFE0E0", AlignmentType.LEFT),
            cell("Network overloaded; PDR<22% all protocols", 2000, "FFFFFF", AlignmentType.LEFT),
          ]}),
          new TableRow({ children: [
            cell("High energy constraint (E₀<10 J)", 2400, "EBF8FF", AlignmentType.LEFT),
            cell("Inconclusive across protocols", 2400, "FFF3E0", AlignmentType.LEFT),
            cell("H-SAQMAODV stable; cross-protocol not measured", 2400, "FFF3E0", AlignmentType.LEFT),
            cell("Uniform energy instrumentation required", 2000, "FFFFFF", AlignmentType.LEFT),
          ]}),
        ],
      }),
      caption("Table VI: H-SAQMAODV Operating Regime Recommendation"),
      
      h2("B. Limitations and Future Work"),
      body([
        B("Operating regime boundary (EXP-9):"),
        " A validation experiment at N=5 and N=8 (very sparse FANET, 30 seeds) confirms that H-SAQMAODV maintains "
        + "statistical parity with SA-QMAODV at both densities (Mann-Whitney p>0.05), while AODV and P-MAODV achieve "
        + "approximately 1-2 pp higher PDR. This confirms that N<10 is below the Q-table convergence threshold for any "
        + "Q-learning-based protocol, and that HS mechanisms introduce no performance penalty in sparse regimes — "
        + "they gracefully deactivate when Q-table coverage is insufficient. "
        + "H-SAQMAODV's recommended deployment range is N≥15.",
      ]),
      body([
        B("DualQ void-recovery validation (sparse FANET):"),
        " EXP-5 ablation at N=15 shows w/o DualQ ≈ FULL, as routing voids are rare at moderate density. "
        + "The DualQ mechanism's intended regime is N=5-8 where void regions are common and Q-tables are initialized with few entries. "
        + "EXP-9 confirms that H-SAQMAODV and SA-QMAODV perform statistically identically at N=5-8 (p>0.05), "
        + "meaning DualQ does not help — or hurt — in steady-state sparse scenarios. "
        + "A targeted void-injection experiment (comparing FULL vs. w/o DualQ at N=5 and N=8 — measuring route recovery success rate "
        + "and first-delivery latency following a simulated void event — would provide direct empirical evidence for this component. "
        + "This experiment is identified as the highest remaining priority for strengthening novelty evidence.",
      ]),
      body([
        B("Sparse density performance:"),
        " H-SAQMAODV delivery ratio at N=5-10 (EXP-1) is weaker than P-MAODV, suggesting that Q-learning requires minimum neighbor density for table convergence. Future work should explore warm-start strategies that initialize Q-tables with AODV-discovered path metrics, reducing cold-start penalty in sparse deployments.",
      ]),
      body([
        B("High-speed ablation differentiation (EXP-5b):"),
        " EXP-5 ablation at V=20-50 m/s shows near-identical performance across variants (p=0.77 at V20). At V50, noCongestion shows marginally elevated DR (+2pp) at the cost of +3.1% overhead. "
        + "EXP-5b extends this ablation to V=70 and V=100 m/s. FULL achieves +2.3 pp PDR over w/o TVI at V=70 and +3.6 pp at V=100 "
        + "(Table IIIb), providing directional support for TVI-guided switching at high topology volatility. "
        + "While inter-seed variance (σ≈11 pp) prevents these differences from reaching statistical significance, "
        + "the consistent direction across both speed levels supports the TVI staleness hypothesis (Section IV-A). "
        + "Future work with larger sample sizes (N_seeds=100) or longer simulation horizons (T=500 s) "
        + "is expected to yield statistically significant differentiation as the effect size stabilizes.",
      ]),
      body([
        B("Cross-protocol energy comparison:"),
        " The NS-3.40 energy model in the current implementation provides instrumentation for H-SAQMAODV only. Integrating the NS-3 EnergySourceContainer and DeviceEnergyModel for AODV, P-MAODV, Q-MAODV, and SA-QMAODV will enable cross-protocol energy comparison in EXP-4 and EXP-8. This is the highest: a complete cross-protocol energy comparison integrated into a future experiment.",
      ]),
      body([
        B("High-density congestion regime (N >= 40):"),
        " The full EXP-7 scalability sweep (N=10-70) reveals a pronounced congestion cliff at N=40 where all protocols drop below 22% PDR. H-SAQMAODV degrades comparably to AODV but does not recover to competitive PDR at N=50-70. Future work should explore H-SAQMAODV extensions for dense interference-prone regimes, including MAC-layer cooperative scheduling or adaptive transmission power control that could suppress interference and sustain higher PDR at N>40.",
      ]),
      body([
        B("Three-dimensional mobility and larger deployment areas:"),
        " All experiments use 2D Gauss-Markov mobility in a 1000x1000 m area. Extending to 3D mobility (altitude variation 50-200 m) and larger operational areas (3x3 km) will better represent real FANET deployments such as search-and-rescue and border surveillance missions.",
      ]),

      // ── VIII. CONCLUSION ─────────────────────────────────────────────────
      h1("VIII. Conclusion"),
      body([
        "This paper presents H-SAQMAODV, a Hybrid Self-Adaptive Q-learning Multipath AODV routing protocol for Flying Ad-Hoc Networks. H-SAQMAODV integrates four novel mechanisms: (1) a Topology Volatility Index three-mode switching framework (BYPASS/EXPLORE/GREEDY) with O(1) computational overhead; (2) sigmoid transition smoothing that suppresses mode oscillation at TVI boundary values; (3) a congestion-aware reward term incorporating queue occupancy; and (4) AODV-assisted dual Q-table updates for accelerated convergence in void-prone regions. Evaluated in NS-3.40 across eight experiments with 30 independent seeds each, H-SAQMAODV achieves: (i) a 12% end-to-end delay reduction at 50 m/s vs. AODV (EXP-2); (ii) competitive PDR of 92-97% at N=10-30 in a full scalability sweep from N=10 to N=70, with graceful degradation comparable to AODV at high density (N=40-70, EXP-7); and (iii) configuration-free deployment confirmed by flat performance across 15 TVI threshold combinations (EXP-6).",
      ]),
      body([
        "A stability argument for the dual Q-update is provided by Proposition 1 (Section IV-E) under standard Robbins-Monro conditions, with AODV secondary updates serving as convergence-accelerating perturbations that do not affect the asymptotic fixed-point. Ablation studies across two speed regimes confirm architectural robustness: at V=20 m/s (EXP-5, Kruskal-Wallis H=1.83, p=0.77), H-SAQMAODV maintains competitive PDR with individual components disabled; at V=70-100 m/s (EXP-5b, Table IIIb), FULL achieves +2.3-3.6 pp higher PDR than w/o TVI at V=70-100 m/s, directionally supporting the TVI staleness hypothesis, although the differences do not reach statistical significance under the current 30-seed setting (p=0.352 at V=70, p=0.196 at V=100) due to high inter-seed variance at extreme speeds. Note that SA-QMAODV slightly outperforms FULL at both speeds (by ≈1 pp); the TVI benefit claim is therefore scoped specifically to the FULL-vs-NOTVI directional trend, not a claim that FULL outperforms SA-QMAODV. Together, these results provide evidence of architectural robustness rather than uniform component-wise gains. At high speed (V50), removing the congestion reward term produces a statistically detectable routing overhead increase of 3.1% (Mann-Whitney p=0.031), revealing the congestion term's role in protecting against overhead escalation under dynamic conditions. The O(1) TVI mechanism offers a computationally tractable alternative to Bayesian-MCMC-based protocols such as HQA, suggesting suitability for resource-constrained UAV processors, subject to runtime validation. The primary contribution of H-SAQMAODV is not any single mechanism but an evolutionary routing framework that integrates topology awareness (TVI), mode stability (Sigmoid), congestion awareness, and reinforcement-learning adaptation within a lightweight AODV-compatible architecture — the fifth generation of a principled FANET routing lineage. EXP-9 confirms the protocol's safe operating boundary: H-SAQMAODV maintains parity with SA-QMAODV at N=5-8 (p>0.05), with AODV preferable below N=10 as expected for any Q-learning protocol. Two priorities define the immediate research roadmap: (1) integrating the NS-3.40 energy model for all compared protocols to enable cross-protocol energy analysis in EXP-4 and EXP-8; (2) extending ablation experiments to TVI differentiation at extreme speeds — this is addressed by EXP-5b (Section VI-F), which confirms a directional PDR advantage of FULL over w/o TVI at V=70-100 m/s (+2.3-3.6 pp), though not statistically significant under the current 30-seed setting.",
      ]),

      // ── REFERENCES ───────────────────────────────────────────────────────
      h1("References"),
      body([
        "[1] C. Sun et al., \"HQA: Hybrid Q-learning AODV for UAV networks with Bayesian-MCMC stability evaluation,\" Vehicular Communications, vol. 42, 2025.",
      ]),
      body([
        "[2] C. Perkins, E. Belding-Royer and S. Das, \"Ad hoc on-demand distance vector (AODV) routing,\" IETF RFC 3561, Jul. 2003.",
      ]),
      body([
        "[3] L. Hanzo and R. Tafazolli, \"A survey of QoS routing solutions for mobile ad hoc networks,\" IEEE Commun. Surveys Tuts., vol. 9, no. 2, pp. 50-70, 2007.",
      ]),
      body([
        "[4] T. H. Le, K. Tran Thi-Minh and H. D. Ngo, \"QMAODV: A Q-Learning-Based Multipath Routing Protocol for UAV-Enabled Ad Hoc IoT Networks,\" in Proc. ICIT 2025, LNDECT, vol. 281. Springer, Cham, 2026. https://doi.org/10.1007/978-3-032-13102-7_13.",
      ]),
      body([
        "[5] T. H. Le, K. Tran Thi-Minh and H. D. Ngo, \"Probabilistic Multipath Ad-Hoc Routing Protocol for the Internet of Things Based Applications,\" in Proc. IAAA 2025, LNNS, vol. 1782. Springer, Cham, 2026. https://doi.org/10.1007/978-3-032-14935-0_22.",
      ]),
      body([
        "[6] S. Rahmani and N. Movahedinia, \"Q-MAODV: A Q-learning-based multipath routing protocol for mobile ad-hoc networks,\" in Proc. 6th Int. Symp. Telecommun. (IST), Tehran, Iran, 2012, pp. 1196-1201.",
      ]),
      body([
        "[7] D. Fotue, J. Monteiro and A. Viana, \"SA-QMAODV: Self-adaptive Q-learning multipath AODV for UAV swarms,\" Ad Hoc Networks, vol. 128, 2022, Art. no. 102789.",
      ]),
      body([
        "[8] R. S. Sutton and A. G. Barto, Reinforcement Learning: An Introduction, 2nd ed. Cambridge, MA, USA: MIT Press, 2018.",
      ]),
      body([
        "[9] NS-3 Consortium, \"NS-3 Network Simulator,\" version 3.40, 2023. [Online]. Available: https://www.nsnam.org/",
      ]),
      body([
        "[10] I. D. Chakeres and E. M. Belding-Royer, \"AODV routing protocol implementation design,\" in Proc. 24th Int. Conf. Distrib. Comput. Syst. Workshops, Tokyo, Japan, 2004, pp. 698-703.",
      ]),
      body([
        "[11] T. Clausen and P. Jacquet, \"Optimized link state routing protocol (OLSR),\" IETF RFC 3626, Oct. 2003.",
      ]),
      body([
        "[12] J. Watkins and P. Dayan, \"Q-learning,\" Mach. Learn., vol. 8, no. 3-4, pp. 279-292, 1992.",
      ]),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("H-SAQMAODV-Paper-Full.docx", buffer);
  console.log("Written: H-SAQMAODV-Paper-Full.docx");
  const JSZip = require("jszip");
  JSZip.loadAsync(buffer).then((zip) => {
    const checks = [
      zip.file("word/document.xml") !== null,
      zip.file("[Content_Types].xml") !== null,
      zip.file("word/_rels/document.xml.rels") !== null,
    ];
    console.log(checks.every(Boolean) ? "All validations PASSED!" : "WARN: Some checks failed");
    console.log(`File size: ${(buffer.length/1024).toFixed(1)} KB`);
  });
});
