// Render LaTeX equations to self-contained SVGs using MathJax.
//
// GitHub's mobile app renders images but not $$...$$ math. Every equation in
// README.md and docs/science/README.md is pre-rendered here and referenced as
// an <img>. Re-run this script after editing any equation.
//
// Usage:
//   node docs/assets/render-math.js

const fs = require("fs");
const path = require("path");

const MJ_PATH = path.join(__dirname, "node_modules", "mathjax-full");
require(path.join(MJ_PATH, "js", "util", "asyncLoad", "node.js"));

const { mathjax } = require(path.join(MJ_PATH, "js", "mathjax.js"));
const { TeX } = require(path.join(MJ_PATH, "js", "input", "tex.js"));
const { SVG } = require(path.join(MJ_PATH, "js", "output", "svg.js"));
const { liteAdaptor } = require(path.join(MJ_PATH, "js", "adaptors", "liteAdaptor.js"));
const { RegisterHTMLHandler } = require(path.join(MJ_PATH, "js", "handlers", "html.js"));
const { AllPackages } = require(path.join(MJ_PATH, "js", "input", "tex", "AllPackages.js"));

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);

const tex = new TeX({ packages: AllPackages });
const svg = new SVG({ fontCache: "none" });
const html = mathjax.document("", { InputJax: tex, OutputJax: svg });

const FG = "#e6edf3";
const OUT = path.join(__dirname, "math");
fs.mkdirSync(OUT, { recursive: true });

// [filename, TeX source]
const EQUATIONS = [
  // M1 Cousot Interval Propagation — lattice domain + widening
  ["m1-interval",
   String.raw`\text{Int}_v = [\text{lo},\, \text{hi}] \;\sqcup\; \text{Null}(v) \;\sqcup\; \text{Shape}(v), \qquad \text{widen after } N=3 \text{ iterations}`],

  // M2 Falleri Structural Diff — GumTree two-phase AST matching
  ["m2-ast-diff",
   String.raw`\text{match}(T_1,\, T_2) = \text{top-down-hash}(T_1,\, T_2) \;\cup\; \text{bottom-up-dice}(T_1,\, T_2,\, \theta_{\text{sim}})`],

  // M5 Bounded Subprocess Dry-Run — resource limits + timeout
  ["m5-sandbox",
   String.raw`\text{verdict}(w) = \begin{cases} \text{CONFIRM} & \text{subprocess crashes within limits} \\ \text{DISCARD} & \text{exceeds rlimit or alarm} \\ \text{UNKNOWN} & \text{otherwise} \end{cases}`],

  // M6 Bayesian Preference Accumulation — posterior + Thompson sample + floor
  ["m6-preference",
   String.raw`P(\text{surface rule } r \mid \text{dev } d) = \max\bigl(0.05,\; \theta \sim \text{Beta}(\alpha_{d,r},\, \beta_{d,r})\bigr)`],

  // M7 Zheng Pairwise Rubric Judgment — inter-judge agreement via Cohen's kappa
  ["m7-rubric",
   String.raw`\kappa = \dfrac{p_o - p_e}{1 - p_e}, \qquad \text{swap-debiased over } (a,\, b) \text{ and } (b,\, a) \text{ orderings}`],
];

function render(name, source) {
  const node = html.convert(source, { display: true, em: 16, ex: 8, containerWidth: 1200 });
  let svgStr = adaptor.innerHTML(node);
  svgStr = svgStr.replace(/currentColor/g, FG);
  svgStr = `<?xml version="1.0" encoding="UTF-8"?>\n` + svgStr;
  const outPath = path.join(OUT, `${name}.svg`);
  fs.writeFileSync(outPath, svgStr, "utf8");
  console.log(`  docs/assets/math/${name}.svg`);
}

console.log(`Rendering ${EQUATIONS.length} equations...`);
for (const [name, src] of EQUATIONS) {
  try {
    render(name, src);
  } catch (err) {
    console.error(`FAILED: ${name}\n  ${err.message}`);
    process.exitCode = 1;
  }
}
console.log("Done.");
