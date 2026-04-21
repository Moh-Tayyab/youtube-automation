import { registerRoot } from "remotion";
import React from "react";
import { Composition } from "remotion";
import { AIAgentRevolution } from "./AIAgentRevolution";

const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AIAgentRevolution"
      component={AIAgentRevolution}
      durationInFrames={1713}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};

registerRoot(RemotionRoot);
