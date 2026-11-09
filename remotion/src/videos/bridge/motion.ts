import { gsap } from "gsap";

/** Reusable scalar channel for frame-derived motion. Each sampler owns its target. */
export function motionTrack(
  initial: number,
  build: (timeline: gsap.core.Timeline, pose: { value: number }) => void,
): (seconds: number) => number {
  const pose = { value: initial };
  const timeline = gsap.timeline({ paused: true, defaults: { lazy: false } });
  build(timeline, pose);
  const duration = timeline.totalDuration();

  return (seconds) => {
    timeline.totalTime(Math.max(0, Math.min(seconds, duration)), true);
    return pose.value;
  };
}
