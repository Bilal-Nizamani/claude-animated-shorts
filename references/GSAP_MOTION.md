# Frame-driven GSAP motion

Install `gsap` in the Remotion project that hosts the template. Author motion against narration word timings and the shot's frame range. Put holds, contacts, cuts and transition boundaries on deliberate frames. Use the same cue for the pose, prop, effect and audio.

## Own the playhead and the pose

- Build each shot's timeline once for a stable set of targets and fps. Use a paused master and nest unpaused child timelines under it if needed. Build and attach the children synchronously so only the master can advance them.
- Initialize every target from a known pose. Use explicit starting values for channels with multiple writers or deferred `fromTo()` tweens, and set `immediateRender: false` on deferred `fromTo()` tweens. Keep one owner per channel and use separate rig pivots or pose fields for additive motion.
- Read `useCurrentFrame()` and `useVideoConfig().fps`. Inside a Remotion `Sequence`, the frame is already local. Seek with `timeline.totalTime(Math.max(0, Math.min(frame / fps, timeline.totalDuration())), true)`. For a story retime, seek from the explicit frame-derived story time. Use finite repeat counts when the shot contains cycles. [Remotion frame hook](https://www.remotion.dev/docs/use-current-frame) · [GSAP timeline seeking](https://gsap.com/docs/v3/GSAP/Timeline/totalTime()/)
- Keep playback, event callbacks, wall-clock time, delta accumulation, unseeded randomness and runtime `repeatRefresh` out of the render path. Derive visibility, effects and audio from frame ranges or cue tables. Apply the sampled pose synchronously before Three.js draws.
- Give each mounted shot or overlapping transition layer its own mutable rig and timeline. Dispose component-owned timelines with `kill()` during teardown. The bridge's module-level scalar tracks have private targets and return a copied number synchronously, so even its two crossfade layers can share those samplers.

## Coordinated shot pattern

Author reusable gesture builders against a passed timeline and stable targets. This example uses a neutral shoulder pivot, a latch hinge and a camera pose sampled at the same frame. Values are illustrative and assume a shot of at least 36 frames.

```ts
import { gsap } from "gsap";
import * as THREE from "three";

export function makeLatchShot(fps: number) {
  const shoulder = new THREE.Euler();
  const hinge = new THREE.Euler();
  const eye = new THREE.Vector3(3, 2, 6);
  const aim = new THREE.Vector3(0, 1.4, 0);
  const lens = { fov: 40, roll: 0 };
  const tl = gsap.timeline({ paused: true, defaults: { lazy: false } });
  const contactFrame = 18;
  tl.addLabel("reach", 6 / fps)
    .addLabel("contact", contactFrame / fps)
    .to(shoulder, {
      keyframes: [
        { z: 0.12, duration: 4 / fps, ease: "sine.inOut" },
        { z: -0.55, duration: 8 / fps, ease: "power2.out" },
      ],
    }, "reach")
    .to(hinge, { y: 0.7, duration: 7 / fps, ease: "power2.out" }, "contact")
    .to(shoulder, { z: -0.43, duration: 10 / fps, ease: "sine.out" }, "contact")
    .to(eye, { x: 2.6, z: 5.4, duration: 30 / fps, ease: "sine.inOut" }, 0)
    .to(aim, { y: 1.25, duration: 30 / fps, ease: "sine.inOut" }, 0)
    .to(lens, { fov: 38, roll: -0.03, duration: 30 / fps, ease: "sine.inOut" }, 0);

  return {
    contactFrame,
    apply(frame: number, camera: THREE.PerspectiveCamera, arm: THREE.Object3D, latch: THREE.Object3D) {
      tl.totalTime(Math.max(0, Math.min(frame / fps, tl.totalDuration())), true);
      arm.rotation.copy(shoulder);
      latch.rotation.copy(hinge);
      camera.position.copy(eye);
      camera.lookAt(aim);
      camera.rotateZ(lens.roll);
      camera.fov = lens.fov;
      camera.updateProjectionMatrix();
    },
    dispose: () => tl.kill(),
  };
}
```

Use `contactFrame` for the matching sound and effect. For canvas characters, pass numeric pose channels into the drawing function and include all quantized drawing inputs in the texture cache key. For a dissolve, seek an opacity track against the transition's local frame and let each layer sample its own shot pose. The bridge's `cast.ts` hammer cue and `story.ts` camera, collapse and dissolve tracks show both patterns in the existing render path.

## Motion and image checks

- Block the silhouettes, eye lines, contact poses and stable proportions first. Use anticipation before fast gestures, a clear contact, then weighted follow-through and a settle. Check that supporting feet stay planted while the body moves and that hands track their props.
- Ease camera position and aim together. Check the projected path at consecutive frames for speed jumps, aim flips, jitter and clipping. Review foreground clearance and focus during the entire move. Reserve impact shake for the cue that motivates it.
- For pixel-art sprites, use `NearestFilter` for magnification and minification, disable mipmaps on those textures, and use `image-rendering: pixelated` on DOM pixel-art layers. For screen-aligned art, use integer scaling and snap the final screen position to the intended output grid where practical. Keep world and camera motion continuous. Review perspective sprites and post effects at final output size, especially where blur or resampling can soften a silhouette. The painted bridge assets retain their existing filtering.
- Render frame zero, the last frame, both sides of cuts and contacts, and the midpoint of transitions. Compare each isolated still with the same frame from a continuous render under identical settings. Seek forward, backward and repeatedly in Studio. Verify matching poses, opacity, camera and effects. Review short clips at speed and frame by frame for sliding feet, stiff gestures, camera jitter, edge shimmer and dropped transition frames.
