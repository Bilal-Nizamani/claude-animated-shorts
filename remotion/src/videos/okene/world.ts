// The three places of the Okene short as one three.js scene (pure function of shot id + frame):
//   seabed - the capsized tug lying upside down on the sea floor, light shafts, marine snow
//   cabin  - the air pocket: a cramped steel room, black water, two mattresses, Harrison sitting on them
//   sea    - the surface: overcast swell, the tug, her crew, the capsize
// Everything shares the bridge short's rendering contracts: two-tone world materials (shade.ts), camera-facing lit cards
// for characters (cast.ts Pool/Actor/Fx + cardshade.ts), world ink only on solid geometry (NOINK for cards and sky).
import * as THREE from "three";
import { LIGHTS, SKY, SEA_COLORS, CLOUD_OVERCAST, Place } from "./lights";
import { TONE, CHAR, twoTone, untone } from "../bridge/shade";
import { NOINK } from "../bridge/ink";
import { Pool, Actor, Fx } from "../bridge/cast";
import { Pen, bodyFront, fxSplash, fxPuff, Outfit, Expr, FrontOpts } from "../bridge/toon";
import { ctex, cloudHD } from "../bridge/paint";
import {
  FPS, SHOTS, CX, SX, T_WITHOUT, T_TANK, T_ROLL0, T_SPLASH, CREW, V3, camAt, rollAt, sinkAt, seaH, swellAt, smooth, clamp01, LEAD,
} from "./story";

// ---------------- materials ----------------
const M = (c: string | THREE.Texture, o: THREE.MeshLambertMaterialParameters = {}, lift = 1) =>
  twoTone(new THREE.MeshLambertMaterial(typeof c === "string" ? { color: c, ...o } : { map: c, ...o }), lift);
const hex = (c: string) => new THREE.Color(c);

// ---------------- painted textures (cached by ctex) ----------------
const sandTex = () => ctex("okSand", 1024, 1024, (g, r) => {
  g.fillStyle = "#a89f86"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 90; i++) { // soft blotches
    g.fillStyle = r() < 0.5 ? "rgba(255,250,225,0.07)" : "rgba(60,55,40,0.08)";
    g.beginPath(); g.ellipse(r() * 1024, r() * 1024, 40 + r() * 120, 20 + r() * 60, r() * 3, 0, Math.PI * 2); g.fill();
  }
  for (let y = 10; y < 1024; y += 22) { // wave ripples, seamless (whole periods across the tile)
    const k = 2 + Math.floor(r() * 3), ph = r() * 6.28, amp = 4 + r() * 5;
    g.beginPath();
    for (let x = 0; x <= 1024; x += 8) { const yy = y + amp * Math.sin((x / 1024) * Math.PI * 2 * k + ph); if (x) g.lineTo(x, yy); else g.moveTo(x, yy); }
    g.strokeStyle = r() < 0.5 ? "rgba(255,252,230,0.16)" : "rgba(70,60,40,0.18)"; g.lineWidth = 2 + r() * 2.5; g.stroke();
  }
  for (let i = 0; i < 1400; i++) { g.fillStyle = r() < 0.5 ? "rgba(255,255,240,0.18)" : "rgba(50,45,30,0.2)"; g.fillRect(r() * 1024, r() * 1024, 2, 2); }
});
const steelTex = () => ctex("okSteel", 512, 512, (g, r) => {
  g.fillStyle = "#6c8285"; g.fillRect(0, 0, 512, 512);
  for (let py = 0; py < 4; py++) for (let px = 0; px < 4; px++) {
    const v = (r() - 0.5) * 0.16;
    g.fillStyle = v > 0 ? `rgba(255,255,255,${v})` : `rgba(0,0,0,${-v})`; g.fillRect(px * 128, py * 128, 128, 128);
  }
  g.strokeStyle = "rgba(20,32,36,0.85)"; g.lineWidth = 4;
  for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 128, 0); g.lineTo(i * 128, 512); g.stroke(); g.beginPath(); g.moveTo(0, i * 128); g.lineTo(512, i * 128); g.stroke(); }
  g.fillStyle = "rgba(20,32,36,0.8)";
  for (let py = 0; py < 4; py++) for (let px = 0; px < 4; px++) for (const [dx, dy] of [[12, 12], [116, 12], [12, 116], [116, 116]]) {
    g.beginPath(); g.arc(px * 128 + dx, py * 128 + dy, 3.5, 0, 7); g.fill();
  }
  for (let i = 0; i < 26; i++) { // run-off stains from the seams
    const x = r() * 512, h = 40 + r() * 140, gr = g.createLinearGradient(0, 0, 0, h);
    gr.addColorStop(0, "rgba(40,28,20,0.22)"); gr.addColorStop(1, "rgba(40,28,20,0)");
    g.fillStyle = gr; g.fillRect(x, (Math.floor(r() * 4)) * 128 + 4, 5 + r() * 6, h);
  }
});
const mattressTex = () => ctex("okMattress", 256, 256, (g, r) => {
  for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? "#e7e2d4" : "#4a76a6"; g.fillRect(i * 32, 0, 32, 256); }
  g.strokeStyle = "rgba(30,30,40,0.35)"; g.lineWidth = 3;
  for (let y = 0; y < 256; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(256, y); g.stroke(); }
  for (let i = 0; i < 60; i++) { g.fillStyle = "rgba(40,50,60,0.12)"; g.beginPath(); g.ellipse(r() * 256, r() * 256, 4 + r() * 18, 3 + r() * 10, r() * 3, 0, 7); g.fill(); }
});
const shaftTex = () => ctex("okShaft", 128, 512, (g) => {
  const v = g.createLinearGradient(0, 0, 0, 512); v.addColorStop(0, "rgba(255,255,255,1)"); v.addColorStop(0.7, "rgba(255,255,255,0.35)"); v.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = v; g.fillRect(0, 0, 128, 512);
  g.globalCompositeOperation = "destination-in";
  const h = g.createLinearGradient(0, 0, 128, 0); h.addColorStop(0, "rgba(0,0,0,0)"); h.addColorStop(0.5, "rgba(0,0,0,1)"); h.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = h; g.fillRect(0, 0, 128, 512);
});
const rep = (t: THREE.Texture, x: number, y: number) => { const c = t.clone(); c.repeat.set(x, y); c.needsUpdate = true; return c; };

// ---------------- the tug (one model, used upside down on the sea floor and afloat) ----------------
// local frame: x forward (bow +x), y up from the keel, z to starboard; keel y = 0, deck y = 2.4, ~14 m long, ~4.6 m beam
const makeTug = () => {
  const g = new THREE.Group(), housing = new THREE.Group();
  const red = M("#d8503a"), black = M("#1c1c22"), white = M("#e8e6de"), grey = M("#5d6469"), yellow = M("#dcae2c"), glass = M("#1d3c4b"), steel = M("#7d8488");
  const plan = new THREE.Shape();
  [[-6.5, -2.3], [4.4, -2.3], [6.2, -1.6], [7.4, -0.5], [7.4, 0.5], [6.2, 1.6], [4.4, 2.3], [-6.5, 2.3]].forEach(([x, y], i) => (i ? plan.lineTo(x, y) : plan.moveTo(x, y)));
  const extrude = (depth: number, sx = 1, sz = 1) => { const e = new THREE.ExtrudeGeometry(plan, { depth, bevelEnabled: false }); e.rotateX(-Math.PI / 2); e.scale(sx, 1, sz); return e; };
  const add = (geo: THREE.BufferGeometry, mat: THREE.Material, x = 0, y = 0, z = 0, to: THREE.Object3D = g) => {
    const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; to.add(m); return m;
  };
  add(extrude(2.4), red); // hull
  add(extrude(0.55, 1.012, 1.016), black, 0, 0, 0); // boot-top band
  add(extrude(0.12, 0.985, 0.985), grey, 0, 2.4, 0); // deck slab
  const box = (w: number, h: number, d: number, mat: THREE.Material, x: number, y: number, z: number, to: THREE.Object3D = g) => add(new THREE.BoxGeometry(w, h, d), mat, x, y + h / 2, z, to);
  box(4.8, 2.1, 3.3, white, -2.8, 2.5, 0, housing); // deckhouse
  box(3.0, 1.5, 3.0, white, -3.7, 4.6, 0, housing); // wheelhouse
  box(3.5, 0.14, 3.5, grey, -3.7, 6.1, 0, housing); // roof
  box(0.06, 0.62, 2.5, glass, -2.17, 5.0, 0); box(2.0, 0.56, 0.06, glass, -3.7, 5.0, 1.52); box(2.0, 0.56, 0.06, glass, -3.7, 5.0, -1.52);
  const funnel = add(new THREE.CylinderGeometry(0.62, 0.7, 2.4, 14), yellow, -5.1, 4.6 + 1.2, 0);
  add(new THREE.CylinderGeometry(0.64, 0.64, 0.5, 14), black, -5.1, 4.6 + 2.15, 0);
  box(0.12, 2.4, 0.12, grey, -3.2, 6.2, 0); // mast
  box(0.08, 0.08, 1.4, grey, -3.2, 8.0, 0);
  const drum = add(new THREE.CylinderGeometry(0.55, 0.55, 2.4, 12), steel, 1.9, 2.52 + 0.55, 0); drum.rotation.x = Math.PI / 2; // towing winch
  for (const z of [-2.18, 2.18]) box(11.0, 0.8, 0.09, red, -1.0, 2.46, z); // bulwarks
  box(0.09, 0.8, 4.4, red, -6.42, 2.46, 0);
  for (const z of [-1.3, 1.3]) add(new THREE.CylinderGeometry(0.13, 0.17, 0.5, 8), black, 4.8, 2.72, z); // bollards
  g.add(housing); void funnel;
  return { group: g, housing };
};

// ---------------- the world ----------------
type Pose = { p: THREE.Vector3; q: THREE.Quaternion };
const _e = new THREE.Euler(), _qa = new THREE.Quaternion(), _qb = new THREE.Quaternion(), _ax = new THREE.Vector3(1, 0, 0);
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q8 = (v: number, n = 120) => Math.round(v * n) / n;
const PIVOT_Y = 1.3; // local height of the rotation centre (waterline is 0.85)
const tier = (d: number): [number, number, number] => d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : d < 34 ? [300, 500, 0.5] : [200, 340, 0.34];

const HARRISON: Outfit = { jacket: "#cfcabc", pants: "#2d3646", boots: "#3a2a22", skin: "#8b5a3c", hat: "hair", hair: "#17110e" };
const CREW_FITS: Outfit[] = [
  { jacket: "#e07a2a", pants: "#2d3646", boots: "#1c1c22", skin: "#7a4b32", hat: "cap", cap: "#d9d6cc" },
  { jacket: "#d9a53a", pants: "#3b3f52", boots: "#1c1c22", skin: "#936043", hat: "hair", hair: "#1a1410" },
  { jacket: "#e07a2a", pants: "#3b3f52", boots: "#1c1c22", skin: "#6e422b", hat: "hair", hair: "#120d0b", build: "stout" },
];

export class OkeneWorld {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private sun: THREE.DirectionalLight;
  private fog = new THREE.Fog("#000000", 3, 50);
  private sets: Record<Place, THREE.Group>;
  private sunCache = new Map<number, THREE.Vector3>();
  private frustum = new THREE.Frustum(); private m4 = new THREE.Matrix4(); private sph = new THREE.Sphere(); private v = new THREE.Vector3();
  // seabed
  private wreckLamp!: THREE.Mesh; private snow: THREE.Points; private snowBase: Float32Array; private shafts: THREE.Mesh[] = [];
  // cabin
  private pocketWater: THREE.Mesh; private mattresses: THREE.Group; private glow: THREE.Mesh;
  // sea
  private sea: THREE.Mesh; private seaGeo: THREE.BufferGeometry; private seaTug: THREE.Group; private seaSky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private tugBody: THREE.Group; private clouds: THREE.Mesh[] = [];

  constructor() {
    const R = this.root;
    this.sun = new THREE.DirectionalLight("#ffffff", 2.4);
    this.sun.castShadow = true; this.sun.shadow.mapSize.set(2048, 2048);
    R.add(this.sun, this.sun.target);
    this.sets = { seabed: new THREE.Group(), cabin: new THREE.Group(), sea: new THREE.Group() };
    R.add(this.sets.seabed, this.sets.cabin, this.sets.sea);

    // ================= seabed =================
    {
      const S = this.sets.seabed;
      const floor = new THREE.Mesh(new THREE.PlaneGeometry(260, 260), M(rep(sandTex(), 34, 34)));
      floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; S.add(floor);
      const { group: tug } = makeTug();
      const holder = new THREE.Group(); holder.add(tug);
      // upside down, leaning, nose toward the camera side; the wheelhouse roof rests on the sand
      tug.rotation.x = 2.05; holder.rotation.y = 0.3; holder.rotation.z = 0.05; holder.updateMatrixWorld(true);
      const bb = new THREE.Box3().setFromObject(tug);
      holder.position.y -= bb.min.y + 0.5; holder.position.x = 0.5;
      S.add(holder);
      const rockM = M("#6e7a74"), rockM2 = M("#5a655f");
      for (let i = 0; i < 26; i++) {
        const a = hh(i) * 6.28, d = 9 + hh(i, 2) * 38, s = 0.4 + hh(i, 3) * 1.6;
        const rk = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), i % 2 ? rockM : rockM2);
        rk.scale.set(s * (1 + hh(i, 4)), s * 0.55, s * (1 + hh(i, 5))); rk.position.set(Math.cos(a) * d, 0.1 * s, Math.sin(a) * d);
        rk.rotation.y = hh(i, 6) * 3; rk.castShadow = rk.receiveShadow = true; S.add(rk);
      }
      const drumM = M("#8a3a2c");
      for (const [x, z, ry] of [[-7.5, 4.5, 0.4], [8.5, -5.5, 1.2], [-3.5, -9, 2.0]] as const) {
        const d = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.45, 0.9, 12), drumM);
        d.position.set(x, 0.3, z); d.rotation.set(1.3, ry, 0.4); d.castShadow = d.receiveShadow = true; S.add(d);
      }
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.12, 8, 20), M("#d7d2c4"));
      ring.position.set(-4.4, 0.3, 6.2); ring.rotation.set(1.2, 0.5, 0); ring.castShadow = ring.receiveShadow = true; S.add(ring);
      const lamp = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 10), new THREE.MeshBasicMaterial({ color: new THREE.Color(3.2, 1.7, 0.5), fog: false }));
      lamp.name = "wreckLamp"; tug.add(lamp); lamp.position.set(-2.1, 5.35, 0.9); this.wreckLamp = lamp;
      // light shafts from far above
      const shaftMat = new THREE.MeshBasicMaterial({ map: shaftTex(), color: new THREE.Color(0.32, 0.62, 0.7), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false });
      for (let i = 0; i < 7; i++) {
        const w = 3 + hh(i, 7) * 5, m = new THREE.Mesh(new THREE.PlaneGeometry(w, 44), shaftMat);
        m.position.set(-20 + hh(i, 8) * 40, 20, -16 + hh(i, 9) * 26); m.rotation.set(0, hh(i, 10) * 3, 0.16 + hh(i, 11) * 0.1);
        m.renderOrder = 4; this.shafts.push(m); S.add(m);
      }
      // marine snow
      const N = 520; this.snowBase = new Float32Array(N * 3);
      for (let i = 0; i < N; i++) this.snowBase.set([(hh(i, 1) - 0.5) * 46, hh(i, 2) * 16, (hh(i, 3) - 0.5) * 46], i * 3);
      const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(N * 3), 3));
      this.snow = new THREE.Points(sg, new THREE.PointsMaterial({ size: 0.075, sizeAttenuation: true, color: new THREE.Color(0.8, 1.1, 1.15), transparent: true, opacity: 0.75, depthWrite: false }));
      this.snow.frustumCulled = false; S.add(this.snow);
    }

    // ================= cabin (air pocket) =================
    {
      const S = this.sets.cabin; S.position.x = CX;
      const above = M(rep(steelTex(), 2, 1)), ceilM = M(rep(steelTex(), 2, 2)), below = M("#1d3a42"), frameM = M("#2c3c40"), pipeM = M("#8a8f86"), pipeM2 = M("#9a5a38");
      const X0 = -1.9, X1 = 1.9, Y0 = -1.25, Y1 = 1.38, Z0 = -1.5, Z1 = 4.6;
      const wall = (w: number, h: number, mat: THREE.Material, x: number, y: number, z: number, ry: number, rx = 0) => {
        const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); m.position.set(x, y, z); m.rotation.set(rx, ry, 0); m.receiveShadow = true; S.add(m); return m;
      };
      const hAbove = Y1, hBelow = -Y0;
      wall(X1 - X0, hAbove, above, 0, hAbove / 2, Z0, 0);           // back wall above water
      wall(X1 - X0, hBelow, below, 0, -hBelow / 2, Z0, 0);          // back wall below water
      wall(Z1 - Z0, hAbove, above, X0, hAbove / 2, (Z0 + Z1) / 2, Math.PI / 2);   // left wall
      wall(Z1 - Z0, hBelow, below, X0, -hBelow / 2, (Z0 + Z1) / 2, Math.PI / 2);
      wall(Z1 - Z0, hAbove, above, X1, hAbove / 2, (Z0 + Z1) / 2, -Math.PI / 2);  // right wall
      wall(Z1 - Z0, hBelow, below, X1, -hBelow / 2, (Z0 + Z1) / 2, -Math.PI / 2);
      wall(X1 - X0, Z1 - Z0, ceilM, 0, Y1, (Z0 + Z1) / 2, 0, Math.PI / 2);      // ceiling (faces down)
      wall(X1 - X0, Z1 - Z0, below, 0, Y0, (Z0 + Z1) / 2, 0, -Math.PI / 2);     // floor under the water
      // frames: vertical ribs + ceiling beams (they give the ink pass something to draw)
      const box = (w: number, h: number, d: number, mat: THREE.Material, x: number, y: number, z: number) => {
        const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; S.add(m); return m;
      };
      for (const z of [-0.9, 2.2]) { box(0.14, Y1 - Y0, 0.16, frameM, X0 + 0.07, (Y1 + Y0) / 2, z); box(0.14, Y1 - Y0, 0.16, frameM, X1 - 0.07, (Y1 + Y0) / 2, z); box(X1 - X0, 0.15, 0.16, frameM, 0, Y1 - 0.075, z); }
      for (const x of [-1.0, 0.0, 1.0]) box(0.14, Y1 - Y0, 0.16, frameM, x, (Y1 + Y0) / 2, Z0 + 0.08);
      for (const [y, m] of [[Y1 - 0.3, pipeM], [Y1 - 0.5, pipeM2]] as const) {
        const p = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, Z1 - Z0 - 0.2, 10), m);
        p.rotation.x = Math.PI / 2; p.position.set(X0 + 0.45 + (y === Y1 - 0.5 ? 0.25 : 0), y, (Z0 + Z1) / 2); p.castShadow = true; S.add(p);
      }
      const px = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, X1 - X0 - 0.3, 10), pipeM);
      px.rotation.z = Math.PI / 2; px.position.set(0, Y1 - 0.2, Z0 + 0.28); S.add(px);
      box(0.9, 0.55, 0.5, M("#4a5a58"), -1.15, -0.1, -1.1); // a half-sunk locker in the back corner
      // porthole in the back wall, glowing cold from the sea outside
      const ringM = M("#9aa09a");
      const tor = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.07, 10, 28), ringM); tor.position.set(1.0, 0.55, Z0 + 0.06); S.add(tor);
      this.glow = new THREE.Mesh(new THREE.CircleGeometry(0.3, 28), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.5, 2.1, 2.5), fog: false }));
      this.glow.position.set(1.0, 0.55, Z0 + 0.03); S.add(this.glow);
      const shaft = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 3.6), new THREE.MeshBasicMaterial({ map: shaftTex(), color: new THREE.Color(0.18, 0.55, 0.62), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false }));
      shaft.position.set(0.55, 0.15, 0.4); shaft.rotation.set(Math.PI / 2 - 0.1, 0, -0.3); shaft.renderOrder = 4; S.add(shaft);
      // black water
      const wg = new THREE.PlaneGeometry(X1 - X0 - 0.02, Z1 - Z0 - 0.02, 36, 36); wg.rotateX(-Math.PI / 2);
      this.pocketWater = new THREE.Mesh(wg, new THREE.MeshBasicMaterial({ vertexColors: true }));
      wg.setAttribute("color", new THREE.Float32BufferAttribute(new Float32Array(wg.attributes.position.count * 3), 3));
      this.pocketWater.position.set(0, 0, (Z0 + Z1) / 2); this.pocketWater.receiveShadow = true; S.add(this.pocketWater);
      // two mattresses afloat
      this.mattresses = new THREE.Group();
      const mt = M(mattressTex());
      for (const [y, rz, w, d] of [[0.03, 0.05, 1.9, 1.05], [0.17, -0.08, 1.7, 0.95]] as const) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(w, 0.15, d), mt); m.position.set(0, y, 0); m.rotation.y = rz; m.castShadow = m.receiveShadow = true; this.mattresses.add(m);
      }
      this.mattresses.position.set(0, 0, -0.45); S.add(this.mattresses);
    }

    // ================= sea =================
    {
      const S = this.sets.sea; S.position.x = SX;
      // polar grid, fine near the boat and coarse toward the horizon
      const RINGS = 96, SEG = 160, RMAX = 900, pos: number[] = [], idx: number[] = [];
      for (let k = 0; k <= RINGS; k++) for (let s = 0; s < SEG; s++) { const r = RMAX * (k / RINGS) ** 2.2, a = (s / SEG) * Math.PI * 2; pos.push(Math.cos(a) * r, 0, Math.sin(a) * r); }
      for (let k = 0; k < RINGS; k++) for (let s = 0; s < SEG; s++) {
        const a = k * SEG + s, b = k * SEG + ((s + 1) % SEG), c = (k + 1) * SEG + s, d = (k + 1) * SEG + ((s + 1) % SEG);
        idx.push(a, b, c, b, d, c);
      }
      this.seaGeo = new THREE.BufferGeometry();
      this.seaGeo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      this.seaGeo.setAttribute("color", new THREE.Float32BufferAttribute(new Float32Array(pos.length), 3));
      this.seaGeo.setIndex(idx);
      this.sea = new THREE.Mesh(this.seaGeo, M("#ffffff", { vertexColors: true }, 0.6));
      this.sea.receiveShadow = true; this.sea.frustumCulled = false; S.add(this.sea);
      const { group } = makeTug();
      this.tugBody = group; group.position.y = -PIVOT_Y;
      this.seaTug = new THREE.Group(); this.seaTug.add(group); S.add(this.seaTug);
      // sky dome
      this.skyMat = new THREE.ShaderMaterial({
        uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() }, c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() } },
        vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
        fragmentShader: `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
          void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
            vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
            c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`,
        side: THREE.BackSide, depthWrite: false, fog: false,
      });
      this.seaSky = new THREE.Mesh(new THREE.SphereGeometry(1100, 40, 20), this.skyMat);
      this.seaSky.renderOrder = -1; this.seaSky.frustumCulled = false; this.seaSky.layers.set(NOINK); S.add(this.seaSky);
      const maps = [0, 1, 2, 3].map((k) => cloudHD(k, CLOUD_OVERCAST));
      for (let i = 0; i < 9; i++) {
        const a = (i / 9) * Math.PI * 2 + 0.3, d = 640 + (i % 3) * 60, w = 190 + (i % 4) * 40;
        const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: maps[i % 4], color: new THREE.Color(1.0, 1.0, 1.0), transparent: true, depthWrite: false, fog: false }));
        m.position.set(Math.cos(a) * d, 110 + (i % 4) * 36, Math.sin(a) * d); m.scale.set(w, w / 2, 1); m.layers.set(NOINK); this.clouds.push(m); S.add(m);
      }
    }
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  /** camera-relative sun, frozen per shot (az from the shot's first camera forward, el above the horizon) */
  private shotSun(id: number, az: number, el: number) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1], c = camAt(id, s.a);
    const fx = c.look[0] - c.pos[0], fz = c.look[2] - c.pos[2], l = Math.hypot(fx, fz) || 1;
    const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el), nx = fx / l, nz = fz / l;
    const hx = nx * Math.cos(a) - nz * Math.sin(a), hz = nz * Math.cos(a) + nx * Math.sin(a);
    v = new THREE.Vector3(hx * Math.cos(e), Math.sin(e), hz * Math.cos(e)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  /** tug pose on the swell at time t (pivot position + orientation). Pure function of t. */
  private tugPose(t: number, out: Pose) {
    const x = 0, z = 0, h = seaH(x, z, t), d = 1.2;
    const sx = (seaH(x + d, z, t) - seaH(x - d, z, t)) / (2 * d), sz = (seaH(x, z + d, t) - seaH(x, z - d, t)) / (2 * d);
    const sink = sinkAt(t);
    out.p.set(x, h + (PIVOT_Y - 0.85) - sink, z);
    _e.set(0.8 * Math.atan(sz), 0, 0.7 * Math.atan(sx), "XYZ"); _qa.setFromEuler(_e);
    _qb.setFromAxisAngle(_ax, rollAt(t));
    out.q.copy(_qa).multiply(_qb);
    return out;
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], place = s.place, L = LIGHTS[place];
    // ---- camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.15; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = new THREE.Vector3(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    for (const k of Object.keys(this.sets) as Place[]) this.sets[k].visible = k === place;
    // ---- light rig ----
    const sunDir = this.shotSun(id, L.az, L.el);
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 6, 10, place === "sea" ? 60 : 45);
    this.sun.position.copy(focus).addScaledVector(sunDir, 160); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 10; sc.far = 340; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(0, 0, 0); TONE.uSat.value = 1;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    // ---- fog / background ----
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog;
    if (place === "sea") {
      scene.background = null;
      const su = this.skyMat.uniforms, stops = [L.fog, ...SKY.c.slice(1)];
      stops.forEach((h, i) => untone(h, su["c" + i].value));
      const e = SKY.e.map((d) => THREE.MathUtils.degToRad(d));
      su.e.value.set(e[1], e[2], e[3], e[4]);
      this.seaSky.position.copy(cam.position);
      for (const m of this.clouds) m.lookAt(cam.position.x, m.position.y, cam.position.z);
    } else scene.background = untone(L.fog, new THREE.Color());

    const reqs: { key: string; w: number; h: number; k: number; draw: (p: Pen) => void }[] = [];
    void reqs;
    const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
    const light2D = () => {
      const sx = sunDir.dot(right), sy = -sunDir.y;
      return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
    };
    type PlaceActor = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; size: [number, number, number]; scale?: number; roll?: number };
    const people: PlaceActor[] = [];
    type PlaceFx = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; soft?: boolean; rot?: number; flat?: boolean };
    const fxs: PlaceFx[] = [];
    const person = (name: string, o: Outfit, x: number, y: number, z: number, fo: FrontOpts, scale = 1) => {
      const d = cam.position.distanceTo(this.v.set(x, y + 1.0 * scale, z)) / scale, [w, h, k] = tier(d), light = light2D();
      const f2: FrontOpts = { ...fo, light, seed: 4 };
      const key = `F|${name}|${JSON.stringify(f2, (_k, v) => (typeof v === "number" ? q8(v) : v))}`;
      people.push({ key, x, y, z, size: [w, h, k], scale, draw: (p) => bodyFront(p, o, f2) });
    };
    const bubble = (x: number, y: number, z: number, size: number) => fxs.push({ key: "bubble", cw: 128, ch: 128, soft: true, x, y, z, w: size, h: size,
      draw: (p) => {
        const g = p.g; g.beginPath(); g.arc(64, 64, 50, 0, Math.PI * 2); g.fillStyle = "rgba(170,225,240,0.16)"; g.fill();
        g.lineWidth = 7; g.strokeStyle = "rgba(225,248,255,0.9)"; g.stroke();
        g.beginPath(); g.arc(64, 64, 33, Math.PI * 1.05, Math.PI * 1.55); g.lineWidth = 6; g.strokeStyle = "rgba(255,255,255,0.9)"; g.lineCap = "round"; g.stroke();
      } });

    // ======================= per place =======================
    if (place === "seabed") {
      (this.wreckLamp.material as THREE.MeshBasicMaterial).color.setRGB(3.0 + 0.8 * Math.sin(t * 5.3), 1.6 + 0.4 * Math.sin(t * 5.3), 0.45);
      // marine snow drifts down slowly and wraps in a 46 x 16 x 46 box around the tug
      const arr = this.snow.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < this.snowBase.length; i += 3) {
        const k = i / 3, drift = 0.1 + 0.08 * hh(k, 5);
        arr[i] = this.snowBase[i] + 0.35 * Math.sin(t * 0.4 + k);
        arr[i + 1] = (((this.snowBase[i + 1] - t * drift) % 16) + 16) % 16;
        arr[i + 2] = this.snowBase[i + 2] + 0.3 * Math.cos(t * 0.33 + k * 1.3);
      }
      this.snow.geometry.attributes.position.needsUpdate = true;
      this.shafts.forEach((m, i) => { m.quaternion.setFromEuler(new THREE.Euler(0, hh(i, 10) * 3 + 0.02 * Math.sin(t * 0.3 + i), 0.18 + hh(i, 11) * 0.1 + 0.02 * Math.sin(t * 0.25 + i))); });
      for (let i = 0; i < 9; i++) { // a thin stream of bubbles leaking from the hull
        const u = ((t * 0.18 + i / 9) % 1), x = 1.2 + 0.6 * Math.sin(u * 7 + i), z = 1.2 + 0.4 * Math.cos(u * 5 + i);
        bubble(x, 0.6 + u * 9, z, 0.18 + 0.2 * hh(i, 12));
      }
    } else if (place === "cabin") {
      const W = this.pocketWater.geometry as THREE.PlaneGeometry, pa = W.attributes.position.array as Float32Array, ca = W.attributes.color.array as Float32Array;
      const lo = hex("#0d3a47"), hi = hex("#2f8696"), col = new THREE.Color();
      for (let i = 0; i < pa.length; i += 3) {
        const x = pa[i], zl = pa[i + 2], wv = 0.018 * Math.sin(2.6 * x + 1.4 * zl - 1.6 * t) + 0.012 * Math.sin(-1.9 * x + 3.1 * zl - 2.3 * t + 1.1);
        pa[i + 1] = wv;
        const gl = Math.exp(-(((x - 1.0) / 0.9) ** 2 + ((zl + 0.4) / 1.6) ** 2)); col.copy(lo).lerp(hi, clamp01(0.35 + wv * 14 + 0.5 * gl)); ca[i] = col.r; ca[i + 1] = col.g; ca[i + 2] = col.b;
      }
      W.attributes.position.needsUpdate = true; W.attributes.color.needsUpdate = true; W.computeVertexNormals();
      const bob = 0.012 * Math.sin(t * 1.5), tilt = 0.01 * Math.sin(t * 0.9);
      this.mattresses.position.y = bob; this.mattresses.rotation.z = tilt;
      // Harrison sits on the mattresses, wedged under the ceiling. Expression follows the narration (lands 2 f early).
      const swap = T_TANK - LEAD - 0.12, blink = (() => {
        const k = f - Math.round(swap * FPS) + 1; if (k >= 0 && k < 4) return [0.5, 1, 1, 0.5][k];
        let st = Math.round(-40 * hh(3, 9)); for (let n = 0; st <= f && n < 60; n++) { const j = f - st; if (j >= 0 && j < 4) return [0.5, 1, 1, 0.5][j]; st += Math.round(26 + 58 * hh(3 * 31 + n, 13)); }
        return 0;
      })();
      const expr: Expr = t < swap ? "stern" : "nervous";
      const breathe = 0.7 * Math.sin(t * 2.1);
      person("harrison", HARRISON, CX + 0.0, 0.31 + bob, -0.45, { mode: "sit", expr, blink, tilt: q8(breathe * 0.6, 20), headTilt: q8(-1.5 + 0.8 * Math.sin(t * 0.7), 10), look: 0 });
      for (let i = 0; i < 6; i++) { // bubbles sipping out of the water by the wall + tiny dust
        const u = ((t * 0.22 + i / 6) % 1);
        bubble(CX - 1.2 + 0.25 * Math.sin(i * 2 + u * 3), 0.05 + u * 1.0, -1.1 + 0.2 * Math.cos(i), 0.07 + 0.05 * hh(i, 4));
      }
    } else {
      // ---- sea ----
      const pa = this.seaGeo.attributes.position.array as Float32Array, ca = this.seaGeo.attributes.color.array as Float32Array;
      const tr = hex(SEA_COLORS.trough), md = hex(SEA_COLORS.mid), cr = hex(SEA_COLORS.crest), fo = hex(SEA_COLORS.foam), fa = hex(SEA_COLORS.far), col = new THREE.Color();
      for (let i = 0; i < pa.length; i += 3) {
        const x = pa[i], z = pa[i + 2], r = Math.hypot(x, z), h = r > 260 ? 0.0 : seaH(x, z, t) * (1 - smooth((r - 120) / 140));
        pa[i + 1] = h;
        const hn = clamp01((h + 0.9) / 2.6);
        col.copy(tr).lerp(md, smooth(hn * 1.5)).lerp(cr, smooth((hn - 0.55) / 0.3) * 0.65).lerp(fo, smooth((hn - 0.9) / 0.1) * 0.5).lerp(fa, smooth((r - 70) / 380) * 0.8);
        ca[i] = col.r; ca[i + 1] = col.g; ca[i + 2] = col.b;
      }
      this.seaGeo.attributes.position.needsUpdate = true; this.seaGeo.attributes.color.needsUpdate = true; this.seaGeo.computeVertexNormals();
      const pose: Pose = { p: new THREE.Vector3(), q: new THREE.Quaternion() };
      this.tugPose(t, pose);
      this.seaTug.position.copy(pose.p); this.seaTug.quaternion.copy(pose.q);
      this.seaTug.updateMatrixWorld(true);
      const tugWorld = (tt: number, local: V3, out: THREE.Vector3) => {
        const p2: Pose = { p: new THREE.Vector3(), q: new THREE.Quaternion() }; this.tugPose(tt, p2);
        return out.set(local[0], local[1] - PIVOT_Y, local[2]).applyQuaternion(p2.q).add(p2.p);
      };
      // crew: standing on the deck, then thrown clear as she goes over
      CREW.forEach((cw, i) => {
        const tl = T_ROLL0 + 0.2 + cw.fall, o = CREW_FITS[i];
        if (t < tl) {
          const p = tugWorld(t, cw.local, new THREE.Vector3());
          const expr: Expr = t < T_ROLL0 - LEAD ? (i === 1 ? "neutral" : "stern") : "shock";
          person(`crew${i}`, o, SX + p.x, p.y, p.z, { mode: "stand", expr, blink: 0, tilt: q8(2.2 * Math.sin(t * 1.4 + i), 4) });
        } else {
          const p0 = tugWorld(tl, cw.local, new THREE.Vector3()), u = t - tl;
          const x = p0.x + cw.v[0] * u * 0.55, z = p0.z + cw.v[2] * u * 0.7, y = p0.y + cw.v[1] * u - 4.9 * u * u;
          const wl = seaH(x, z, t);
          if (y > wl - 0.15) person(`crew${i}`, o, SX + x, y, z, { mode: "fall", expr: "shock", blink: 0, tilt: q8(22 * Math.sin(u * 5 + i) * Math.max(0, 1 - u * 0.4), 4) });
          const tw = u - 2 * (cw.v[1]) / 9.8 * 0.92; // landing time (water at ~ the launch height)
          if (y <= wl + 0.3 && tw > -0.3) { /* in the water: a splash ring marks the entry (below) */ }
        }
      });
      // splash crown + spray where the deck slaps the water, and one for every body that lands
      const sp = (t - T_SPLASH) / 0.9;
      if (sp > 0 && sp < 1.2) {
        fxs.push({ key: "splashA", cw: 800, ch: 800, x: SX + 0.4, y: seaH(0.4, 2.6, t) + 1.9, z: 2.9, w: 6.8, h: 6.8, draw: (p) => fxSplash(p, clamp01(sp)) });
        fxs.push({ key: "splashB", cw: 800, ch: 800, x: SX - 3.6, y: seaH(-3.6, 2.4, t) + 1.2, z: 2.6, w: 4.2, h: 4.2, draw: (p) => fxSplash(p, clamp01((t - T_SPLASH - 0.14) / 0.8)) });
      }
      CREW.forEach((cw, i) => {
        const tl = T_ROLL0 + 0.2 + cw.fall, tLand = tl + 1.0 + 0.08 * i, k = (t - tLand) / 0.8;
        if (k > 0 && k < 1.1) {
          const p0 = tugWorld(tl, cw.local, new THREE.Vector3()), u = tLand - tl;
          const x = p0.x + cw.v[0] * u * 0.55, z = p0.z + cw.v[2] * u * 0.7;
          fxs.push({ key: `splashC${i}`, cw: 800, ch: 800, x: SX + x, y: seaH(x, z, t) + 0.9, z, w: 3.0, h: 3.0, draw: (p) => fxSplash(p, clamp01(k)) });
        }
      });
      void swellAt; void fxPuff;
    }

    // ---- publish cards ----
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0; const usedA: Actor[] = [];
    for (const p of people) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.0 * sc2, p.z), 3.2))) continue;
      const a = this.actor(ai++), [w, h, k] = p.size;
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true; a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(sc2, sc2, sc2); a.mesh.castShadow = false;
      usedA.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0; const usedF: Fx[] = [];
    for (const p of fxs) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const e = this.fx(fi++);
      e.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      e.use(!!p.soft); e.mesh.visible = true; e.mesh.position.set(p.x, p.y, p.z);
      e.mesh.quaternion.copy(cam.quaternion); e.mesh.rotateZ(p.rot ?? 0); e.mesh.scale.set(p.w, p.h, 1);
      usedF.push(e);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of usedA) a.bind();
    for (const e of usedF) e.bind();
    return focus;
  }
}
void T_WITHOUT;
