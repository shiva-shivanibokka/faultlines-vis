// Parse-check every inline <script> in the tool and the deck.
//
// The deck is prerendered, so a syntax error there fails export_web.py loudly.
// The TOOL is not: its script only runs in a browser, so a broken edit ships
// silently and is discovered by a person opening the link. This closes that
// gap. `new Function` parses without executing, so no DOM is needed.
import { readFileSync } from "node:fs";

const files = [
  ["tool", "faultlines-tool/index.html"],
  ["deck", "faultlines-web/index.html"],
  ["walkthroughs", "faultlines-web/walkthroughs.html"],
  ["pipeline", "faultlines-web/pipeline.html"],
];

let bad = 0;
for (const [name, rel] of files) {
  const html = readFileSync(rel, "utf8");
  const blocks = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
    .map((m) => m[1])
    .filter((b) => b.trim());
  let i = 0;
  for (const body of blocks) {
    i++;
    try {
      new Function(body);
    } catch (e) {
      bad++;
      console.log(`  FAIL  ${name} block ${i}/${blocks.length}: ${e.message}`);
      const line = Number((e.stack.match(/<anonymous>:(\d+)/) || [])[1]);
      if (line) {
        const src = body.split("\n");
        for (let n = Math.max(0, line - 3); n < Math.min(src.length, line + 2); n++)
          console.log(`        ${n + 1 === line ? ">>" : "  "} ${src[n]}`);
      }
    }
  }
  console.log(`  ${bad ? "    " : "ok  "}  ${name.padEnd(14)} ${blocks.length} script block(s), ${(html.length / 1024).toFixed(0)} KB`);
}
console.log(bad ? `\n  ${bad} BLOCK(S) FAILED TO PARSE` : "\n  every inline script parses");
process.exit(bad ? 1 : 0);
