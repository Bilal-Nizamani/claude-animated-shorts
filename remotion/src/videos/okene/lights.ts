// Light and grade presets for the Okene short (serious tone: cold, dark, desaturated, one warm accent).
// Same field names as the bridge LightPreset so shade.ts / cardshade.ts can read them unchanged.
import type { LightPreset } from "../bridge/lights";
import type { GradeParams } from "../bridge/grade";

export type Place = "seabed" | "cabin" | "sea";

export const LIGHTS: Record<Place, LightPreset> = {
  // the wreck on the sea floor: a weak green-blue light from far above, everything else swallowed by teal fog
  seabed: {
    az: 20, el: 74,
    lit: [0.85, 1.08, 1.18], shade: [0.17, 0.21, 0.3], lift: [0.0, 0.035, 0.08], lambert: 0.4, sideK: 0.8, term: 0.22,
    charTint: [0.8, 1.0, 1.05], charShade: 0.82, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.7, 0.85, 1.0],
    blob: [0.4, 0.5, 0.6], actorShadow: false,
    top: "#0a3a4c", hor: "#0c4a5e", skyCurve: [0, 0.5, 0.6], fog: "#0a3f52", fogNear: 3, fogFar: 52, sunDisc: "#000000",
    sunCol: "#a8f0ff", sunI: 2.4, sky: "#3a8aa0", ground: "#0a2a38", hemiI: 0.4, bias: -0.0004, normalBias: 0.02,
  },
  // the air pocket: a dim lamp from the upper left, cold walls, a cyan glow from a porthole behind
  cabin: {
    az: -55, el: 38,
    lit: [1.25, 1.1, 0.88], shade: [0.1, 0.17, 0.24], lift: [0.015, 0.04, 0.075], lambert: 0.4, sideK: 0.8, term: 0.2,
    charTint: [1.0, 0.92, 0.82], charShade: 0.8, charGrad: 0.1, bodyGrad: 0.26, sideTint: [0.68, 0.8, 1.0],
    blob: [0.4, 0.5, 0.6], actorShadow: false,
    top: "#07222c", hor: "#07222c", skyCurve: [0, 0.5, 0.6], fog: "#06222c", fogNear: 3, fogFar: 16, sunDisc: "#000000",
    sunCol: "#ffd9a8", sunI: 2.4, sky: "#3a6a7a", ground: "#0a2a38", hemiI: 0.4, bias: -0.0004, normalBias: 0.02,
  },
  // the surface: flat overcast daylight (no golden hour, no sun disc)
  sea: {
    az: 60, el: 52,
    lit: [1.2, 1.24, 1.3], shade: [0.34, 0.4, 0.52], lift: [0.05, 0.065, 0.11], lambert: 0.35, sideK: 0.84, term: 0.2,
    charTint: [1.0, 0.97, 0.95], charShade: 0.86, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.9, 0.9, 0.97],
    blob: [0.62, 0.58, 0.58], actorShadow: false,
    top: "#5d7e9d", hor: "#c3d2dc", skyCurve: [0, 0.5, 0.6], fog: "#b2c3d0", fogNear: 70, fogFar: 640, sunDisc: "#000000",
    sunCol: "#f3f1ea", sunI: 2.6, sky: "#c9d8e6", ground: "#4a6a80", hemiI: 0.55, bias: -0.0006, normalBias: 0.05,
  },
};

/** sky gradient stops for the surface shot (on-screen targets, horizon -> zenith) */
export const SKY = { c: ["#c3d2dc", "#a3b8ca", "#7d98b2", "#5d7e9d", "#486a8a"], e: [0, 3, 9, 18, 40] };
export const SEA_COLORS = { trough: "#1c4a63", mid: "#34708f", crest: "#a9cad8", foam: "#f1f6f8", far: "#6f97ae" };
export const CLOUD_OVERCAST = { lit: "#e8eef2", mid: "#bccad5", shade: "#8b9bab" };

/** grade presets (7-knot curve, saturation per zone, split tone, vignette); strengths are set in Okene.tsx */
export const GRADES: Record<Place, GradeParams> = {
  seabed: { ky: [0, 0.085, 0.25, 0.56, 0.8, 0.93, 1], sat: [1.0, 0.92, 0.85], tintS: [0.018, -0.004], tintM: [0.004, -0.004], tintH: [-0.004, 0.004], vig: [0.3, 0.35] },
  cabin: { ky: [0, 0.08, 0.235, 0.54, 0.79, 0.925, 1], sat: [1.0, 0.95, 0.9], tintS: [0.02, -0.003], tintM: [0.004, 0.0], tintH: [-0.006, 0.01], vig: [0.34, 0.35] },
  sea: { ky: [0, 0.09, 0.26, 0.58, 0.82, 0.94, 1], sat: [1.0, 0.9, 0.85], tintS: [0.012, -0.002], tintM: [0.0, 0.0], tintH: [0.0, 0.0], vig: [0.18, 0.42] },
};
export const GRADE_AMOUNT: Record<Place, number> = { seabed: 1, cabin: 1, sea: 1 };
