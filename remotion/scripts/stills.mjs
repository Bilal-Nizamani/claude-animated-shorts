// usage: node scripts/stills.mjs <outPrefix> <frame,frame,...> [scale]   (bundles once, ONE browser reused for every frame, jpeg)
// env: REMOTION_TMP = temp folder for the bundle; GL = angle | swangle (default swangle); POST = JSON for inputProps.post; COMP = composition id
import fs from "node:fs";
if (process.env.REMOTION_TMP) { fs.mkdirSync(process.env.REMOTION_TMP, { recursive: true }); process.env.TEMP = process.env.TMP = process.env.REMOTION_TMP; }
import { bundle } from "@remotion/bundler";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [prefix, frames, scale = "0.5"] = process.argv.slice(2);
const chromiumOptions = { gl: process.env.GL || "swangle" };
const inputProps = process.env.POST ? { post: JSON.parse(process.env.POST) } : {};
const t00 = Date.now(), lap = (m) => console.log(`[${((Date.now() - t00) / 1000).toFixed(0)}s] ${m}`);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
lap("bundled");
const puppeteerInstance = await openBrowser("chrome", { chromiumOptions, browserExecutable: process.env.CHROME || undefined });
lap("browser open");
const id = process.env.COMP || "OkeneShort";
const composition = await selectComposition({ serveUrl, id, chromiumOptions, inputProps, puppeteerInstance, timeoutInMilliseconds: 240000 });
lap(`composition ${composition.width}x${composition.height}, ${composition.durationInFrames} frames`);
const onBrowserLog = (l) => { if (!process.env.VERBOSE && /Clock/.test(l.text)) return; console.log(`[${l.type}]`, l.text.slice(0, 700)); };
fs.mkdirSync(path.dirname(prefix), { recursive: true });
for (const f of frames.split(",").map(Number)) {
  const t0 = Date.now();
  await renderStill({ composition, serveUrl, frame: f, output: `${prefix}${f}.jpg`, imageFormat: "jpeg", jpegQuality: 88, scale: Number(scale),
    chromiumOptions, inputProps, puppeteerInstance, timeoutInMilliseconds: 240000, onBrowserLog });
  console.log("still", f, ((Date.now() - t0) / 1000).toFixed(1) + "s");
}
await puppeteerInstance.close({ silent: true });
lap("done");
