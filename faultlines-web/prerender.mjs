#!/usr/bin/env node
/* Bake each page's JavaScript-rendered body into the HTML it ships.
 *
 * index.html, walkthroughs.html and pipeline.html draw themselves from
 * summary.json AFTER the page loads, so every client that does not run
 * JavaScript -- a crawler, a link preview, an agent fetching the URL, a reader
 * with scripts off -- received the <title> and an empty shell. The pages were
 * invisible to exactly the readers who cannot press a key to fix it.
 *
 * This runs each page's own <script> in node:vm against the same summary.json,
 * calls the same template function the browser calls, and writes the markup back
 * between the <!--baked--> markers at the mount point. Nothing here is a second
 * copy of anything: the numbers still come from summary.json and the markup
 * still comes from the page's own templates. Rendering twice -- once here, once
 * again in the browser on load -- is deliberate, and the browser's pass wins, so
 * a baked copy can never contradict what an interactive reader sees.
 *
 *   node prerender.mjs
 *
 * scripts/export_web.py calls this after it writes summary.json, because a baked
 * page that is not re-baked on every export IS the stale-number bug this whole
 * project was built to stop.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

/* One entry per page. `expr` is appended to the page's OWN script and evaluated
   in that script's scope, so `slides`, `render` and `allLevels` below are the
   page's functions, not copies -- this file writes no markup.

   `cut`, where present, is a literal from the page's script: everything from it
   onward is dropped before evaluating. pipeline.html wraps itself in an IIFE
   whose tail grabs the canvas, observes a resize and starts an animation loop;
   none of that survives outside a browser and none of it is needed to render the
   levels as text. Cutting is smaller and steadier than stubbing a canvas.

   Markers are scoped to the mount -- <!--baked:deck--> -- so one file can carry
   several baked regions. pipeline.html carries three: the levels, and the two
   figures its footer used to state as literal {{tokens}}, because sub() was only
   ever applied to the level prose and never to the static markup around it.

   `min` is the shortest output that is not a symptom. It defaults to a whole
   page's worth; a single figure is six characters, so those say so. */
const PIPE_CUT = 'var cv=document.getElementById("cv")';
const PAGES = [
  { file: 'index.html',        mount: 'deck',      expr: 'S = __S, slides().join("")' },
  { file: 'walkthroughs.html', mount: 'app',       expr: 'render(__S)' },
  { file: 'pipeline.html',     mount: 'alllevels', expr: 'S = __S, allLevels()', cut: PIPE_CUT },
  { file: 'pipeline.html',     mount: 'figQ', min: 1, cut: PIPE_CUT, expr: 'S = __S, F("questions")' },
  { file: 'pipeline.html',     mount: 'figG', min: 1, cut: PIPE_CUT, expr: 'S = __S, F("gens")' },
];

const here = (name) => new URL('./' + name, import.meta.url);
const __S = JSON.parse(readFileSync(here('summary.json'), 'utf8'));

let failed = 0;

for (const { file: name, mount, expr, cut, min = 2000 } of PAGES) {
  const src = readFileSync(here(name), 'utf8');
  /* lastIndexOf, not indexOf: index.html carries a one-line script above the
     slides that claims the document for the deck before they are parsed, and
     the templates live in the block after it. Every page keeps its render code
     in the LAST script block; taking the first one silently extracted a
     one-liner and rendered nothing. */
  let js = src.slice(src.lastIndexOf('<script>') + '<script>'.length,
                     src.lastIndexOf('</script>'));

  /* Cutting mid-IIFE leaves `(function(){ ...` unbalanced, so the tail closes it
     and hands back the expression as the script's completion value. With no cut
     the script is top-level and the expression is simply its last statement. */
  let tail = ';' + expr + ';';
  if (cut) {
    const at = js.indexOf(cut);
    if (at < 1) {
      console.error(`prerender: ${name} no longer contains its cut point -- ${cut}`);
      failed = 1;
      continue;
    }
    js = js.slice(0, at);
    tail = 'return (' + expr + ');\n})();';
  }

  /* A recording DOM. getElementById hands back a node that remembers whatever is
     assigned to its innerHTML and shrugs off every other call, so the page's
     event wiring runs into stubs instead of a crash. walkthroughs' render()
     assigns rather than returns, which is why the assignment is captured at all. */
  const seen = {};
  const node = (id) => ({
    get innerHTML() { return seen[id] ?? ''; },
    set innerHTML(v) { seen[id] = v; },
    children: [], style: {}, dataset: {}, hidden: false,
    classList: { add() {}, remove() {} },
    querySelectorAll: () => [], addEventListener() {},
  });

  const ctx = {
    __S, console,
    /* Inert on purpose. The page's own fetch(...).then(render) chain must not
       run: it would race the expression above and wire up a DOM that is not
       here. The data reaches the templates as __S instead. */
    fetch: () => new Promise(() => {}),
    location: { hostname: 'faultlines-peach.vercel.app', hash: '' },
    matchMedia: () => ({ matches: false }),
    /* pipeline.html reads its palette out of the stylesheet at boot. The colours
       only ever reach the canvas, which is cut away here, so empty strings are
       enough -- they just must not throw on the way past. */
    getComputedStyle: () => ({ getPropertyValue: () => '' }),
    addEventListener() {},
    document: {
      getElementById: node, querySelectorAll: () => [],
      documentElement: {}, addEventListener() {},
    },
  };

  const out = runInNewContext(js + '\n' + tail, ctx, { filename: name });
  const html = (typeof out === 'string' && out) || seen[mount] || '';

  /* The check. If a mount id moves, or a render entry point is renamed, or a
     template throws on a key summary.json stopped carrying, this notices instead
     of quietly baking an empty page -- which would look exactly like the bug it
     was written to fix. Every page here is tens of KB; 2000 is "something broke". */
  if (html.length < min) {
    console.error(`prerender: ${name} rendered ${html.length} chars into #${mount} -- refusing to bake.`);
    failed = 1;
    continue;
  }

  /* Test for the markers rather than for "did the text change". Re-baking an
     unchanged page produces a byte-identical file, which is the normal case and
     must not read as failure. */
  const slot = new RegExp('<!--baked:' + mount + '-->[^]*?<!--/baked:' + mount + '-->');
  if (!slot.test(src)) {
    console.error(`prerender: ${name} has no <!--baked:${mount}--> pair.`);
    failed = 1;
    continue;
  }

  /* Function replacement, not a string: the markup is full of $ sequences that
     String.replace would otherwise read as $&, $1, $' and silently mangle. */
  writeFileSync(here(name), src.replace(slot,
    () => `<!--baked:${mount}-->${html}<!--/baked:${mount}-->`));
  console.log(`   prerender: ${name} -> ${(html.length / 1024).toFixed(1)} KB baked into #${mount}`);
}

process.exit(failed);
