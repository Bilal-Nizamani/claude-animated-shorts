// usage: node scripts/render.mjs <out.mp4> [scale=1.3333] [startFrame] [endFrame]
// One browser, MSAA scene + post chain as in the stills; video only (muted) - the mix is muxed in with ffmpeg afterwards.
// env: REMOTION_TMP, GL (default angle), CONC (default 1), CRF (default 16)
import fs from "node:fs";
if (process.env.REMOTION_TMP) { fs.mkdirSync(process.env.REMOTION_TMP, { recursive: true }); process.env.TEMP = process.env.TMP = process.env.REMOTION_TMP; }
import { bundle } from "@remotion/bundler";
import { openBrowser, renderMedia, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [out, scale = "4/3", f0, f1] = process.argv.slice(2);
const chromiumOptions = { gl: process.env.GL || "angle" };
const t00 = Date.now(), lap = (m) => console.log(`[${((Date.now() - t00) / 1000).toFixed(0)}s] ${m}`);
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
lap("bundled");
const puppeteerInstance = await openBrowser("chrome", { chromiumOptions });
const composition = await selectComposition({ serveUrl, id: "OkeneShort", chromiumOptions, puppeteerInstance, timeoutInMilliseconds: 240000 });
fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
let last = 0;
await renderMedia({
  composition, serveUrl, codec: "h264", crf: Number(process.env.CRF || 16), outputLocation: path.resolve(out), scale: scale === "4/3" ? 4 / 3 : Number(scale),
  chromiumOptions, puppeteerInstance, muted: true, concurrency: Number(process.env.CONC || 1), timeoutInMilliseconds: 240000, pixelFormat: "yuv420p",
  ...(f0 !== undefined ? { frameRange: [Number(f0), Number(f1 ?? f0)] } : {}),
  onProgress: ({ renderedFrames, encodedFrames }) => { if (renderedFrames - last >= 10 || renderedFrames === 1) { last = renderedFrames; lap(`rendered ${renderedFrames}, encoded ${encodedFrames}`); } },
});
await puppeteerInstance.close({ silent: true });
lap("done " + out);
