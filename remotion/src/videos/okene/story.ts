// "The Cook Who Survived 3 Days Underwater" - 10 s test cut. Shots are timed to the aligned voice (words.json).
// Same camera grammar as the bridge short (STYLE_BIBLE / motion.md): continuous slow push-ins, symmetric smootherstep
// glides of 18-40 f, hard cuts on big reframes, impact kicks that flip sign every frame, no hand-held float.
//   shot 1  seabed wreck (hook, flash-forward)        "A man breathed at the bottom of the ocean ... three days,"
//   shot 2  the air pocket, close on Harrison          "without an air tank."
//   (4-frame white flash after the hook)
//   shot 3  the surface, the capsize                    "May 2013. A huge swell flips his tugboat upside down."
import { motionTrack } from "../bridge/motion";
import WORDS from "./words.json";

export const FPS = 30;
export type V3 = [number, number, number];
export type Place = "seabed" | "cabin" | "sea";

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };

// ---------------- words ----------------
type Word = { w: string; s: number; e: number };
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, "");
export const word = (text: string, nth = 0): Word => {
  const hits = (WORDS as Word[]).filter((x) => norm(x.w) === text);
  if (!hits[nth]) throw new Error(`words.json has no "${text}" #${nth}`);
  return hits[nth];
};
const LAST = (WORDS as Word[])[(WORDS as Word[]).length - 1];
const fr = (t: number) => Math.round(t * FPS);
/** reference reactions land 0-3 f before the word */
const LEAD = 2 / FPS;

export const T_BREATHED = word("breathed").s;
export const T_THREE = word("three").s;
export const T_WITHOUT = word("without").s;
export const T_TANK = word("tank").s;
export const T_TANK_END = word("tank").e;
export const T_MAY = word("may").s;
export const T_HUGE = word("huge").s;
export const T_FLIPS = word("flips").s;
export const T_UPSIDE = word("upside").s;

export const TOTAL = fr(LAST.e + 0.5);
/** cabin shot starts on "without"; the sea shot (and the flash that covers the cut) on "May" */
const A2 = fr(T_WITHOUT - LEAD);
const A3 = fr(T_MAY - LEAD);
export const FLASH_AT = A3;

export type ShotDef = { id: number; a: number; b: number; place: Place };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: A2, place: "seabed" },
  { id: 2, a: A2, b: A3, place: "cabin" },
  { id: 3, a: A3, b: TOTAL, place: "sea" },
];
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];

// ---------------- places in the world (three separate sets, far apart so they never overlap) ----------------
export const CX = 500; // cabin set origin (x)
export const SX = 1000; // sea set origin (x)

// ---------------- the capsize (shot 3) ----------------
/** seconds at which the tug starts to lean back, then rolls over; the deck hits the water ~0.95 s later */
export const T_ROLL0 = T_FLIPS - 0.36;
export const T_SPLASH = T_ROLL0 + 0.98;
/** roll angle about the tug's long axis (rad): small anticipation lean away, then over the top with weight, settle at pi */
const rollTrack = motionTrack(0, (tl, p) => {
  tl.to(p, { value: -0.12, duration: 0.3, ease: "power2.out" }, 0);
  tl.to(p, { value: Math.PI + 0.2, duration: 0.7, ease: "power3.in" }, 0.3);
  tl.to(p, { value: Math.PI - 0.03, duration: 0.28, ease: "power2.out" }, 1.0);
  tl.to(p, { value: Math.PI, duration: 0.4, ease: "sine.inOut" }, 1.28);
});
export const rollAt = (t: number) => rollTrack(t - T_ROLL0);
/** the swell that is coming (0 .. 1), then the slap after the boat has gone over */
export const swellAt = (t: number) => smooth((t - (T_ROLL0 - 2.2)) / 2.0);
/** how far the capsized hull sinks into the water afterwards (m) */
export const sinkAt = (t: number) => 0.55 * smooth((t - (T_ROLL0 + 1.0)) / 1.6);

export const waveH = (x: number, z: number, t: number) =>
  0.58 * Math.sin(0.33 * x + 0.5 * z - 0.95 * t) + 0.34 * Math.sin(-0.5 * x + 0.28 * z - 1.35 * t + 1.7) + 0.17 * Math.sin(1.1 * x + 0.7 * z - 2.2 * t + 0.4);
/** the big swell: a ridge along x that travels toward +z (toward the camera), lifting the far side first */
export const swellH = (x: number, z: number, t: number) => {
  const k = swellAt(t), zc = -22 + 21 * smooth((t - (T_ROLL0 - 2.2)) / 2.9), d = (z - zc) / 6.5;
  return 1.2 * k * Math.exp(-d * d) * (0.85 + 0.15 * Math.cos(0.18 * x));
};
export const seaH = (x: number, z: number, t: number) => waveH(x, z, t) + swellH(x, z, t);

/** crew on the deck: deck-local position, they are thrown clear at the roll */
export const CREW: { local: V3; v: V3; fall: number }[] = [
  { local: [-0.6, 2.45, 1.0], v: [1.5, 5.2, 4.6], fall: 0 },
  { local: [1.1, 2.45, -0.9], v: [-0.8, 4.6, 5.8], fall: 0.05 },
  { local: [2.6, 2.45, 0.7], v: [0.6, 5.6, 3.4], fall: 0.1 },
];

// ---------------- camera ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => Shot };
const glide = motionTrack(0, (tl, p) => {
  tl.to(p, { value: 1, duration: 1, ease: (u: number) => u * u * u * (u * (6 * u - 15) + 10) }, 0);
});
const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 40, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
/** push-in factor since f0 (the subject grows ~rate per frame); `punch` raises it for the first n frames with 8 f soft edges */
const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) for (let i = 0; i < Math.min(x, n); i++) s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
  return Math.exp(-s);
};
const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k], look, ...rest });

// shot 1: the wreck on the sea floor. Low, wide, from the stern quarter; then closer and lower ("almost three days")
const S1a = (f: number) => dolly([-1.2, 3.0, 27], [-0.8, 3.7, 0], pushK(f, 0, 0.0022), { fov: 46 });
const S1b = (f: number) => dolly([-10.5, 2.5, 20], [-1.5, 3.9, 0], pushK(f, fr(T_THREE) - 8, 0.0026), { fov: 44, roll: 0.045 });
// shot 2: the air pocket, medium on Harrison; punch push on "air tank"
const FACE: V3 = [CX, 0.8, -0.45];
const S2a = (f: number) => dolly([CX + 0.4, 0.85, 4.5], [CX, 0.45, -0.45], pushK(f, A2, 0.0024), { fov: 46 });
const S2b = (f: number) => dolly([CX + 0.25, 0.8, 3.45], [CX, 0.7, -0.45], pushK(f, fr(T_TANK) - 6, 0.0028, 0.006, 28), { fov: 38, roll: -0.04 });
// shot 3: the surface, 3/4 from the bow side (portrait frame: the boat has to be seen nearly end-on to fit)
const TUG_MID: V3 = [SX - 0.5, 2.7, 0];
const S3a = (f: number) => dolly([SX + 27.5, 4.0, 12.8], TUG_MID, pushK(f, A3, 0.0022), { fov: 46 });
const S3b = (f: number) => dolly([SX + 19.5, 2.4, 8.8], [SX, 2.3, 0], pushK(f, fr(T_ROLL0) + 4, 0.003, 0.006, 30), { fov: 44, roll: -0.045 });

const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, s: S1a }, { f: fr(T_THREE) - 14, dur: 30, s: S1b }],
  2: [{ f: A2, s: S2a }, { f: fr(T_TANK) - 14, dur: 22, s: S2b }],
  3: [{ f: A3, s: S3a }, { f: fr(T_ROLL0) - 10, dur: 26, s: S3b }],
};

// impact kicks: image offset flips sign every frame, decays in 7 f
const KICKS: [number, number][] = [[T_SPLASH, 1.5], [T_ROLL0 + 0.32, 0.5]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f), a = kickAt(f / FPS);
  if (!a || id !== 3) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens (depth of field): cInf px at 1080x1920 for things at infinity; wide shots stay sharp ----------------
export type Dof = { f: number; dur?: number; cInf: number; focus?: (f: number) => V3 };
export const DOF: Dof[] = [
  { f: 0, cInf: 0 },
  { f: fr(T_THREE) - 14, dur: 30, cInf: 7 }, // closer on the hull: soft far fog
  { f: A2, cInf: 13, focus: () => FACE }, // air pocket MS: Harrison's eyes sharp, the steel walls soft
  { f: A3, cInf: 0 }, // surface wide
  { f: fr(T_ROLL0) - 10, dur: 26, cInf: 6 },
];
export const dofAt = (f: number) => {
  let i = 0; while (i + 1 < DOF.length && f >= DOF[i + 1].f) i++;
  const d = DOF[i], p = DOF[Math.max(0, i - 1)];
  const k = d.dur ? Math.min(1, (f - d.f) / d.dur) : 1;
  return { cInf: p.cInf + (d.cInf - p.cInf) * k, focus: d.focus };
};
export { LEAD };
