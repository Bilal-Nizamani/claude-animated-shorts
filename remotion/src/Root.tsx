import React from "react";
import { Composition } from "remotion";
import { OkeneShort, OKENE_FRAMES } from "./videos/okene/Okene";
import { FPS } from "./videos/okene/story";

export const Root: React.FC = () => (
  <Composition id="OkeneShort" component={OkeneShort} durationInFrames={OKENE_FRAMES} fps={FPS} width={1080} height={1920} />
);
