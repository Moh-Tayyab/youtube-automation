import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { HookScene } from "./scenes/HookScene";
import { Myth1Scene } from "./scenes/Myth1Scene";
import { Myth2Scene } from "./scenes/Myth2Scene";
import { Myth3Scene } from "./scenes/Myth3Scene";
import { Myth4Scene } from "./scenes/Myth4Scene";
import { CTAScene } from "./scenes/CTAScene";

const FPS = 30;

const SCENE_DURATIONS = {
  hook: 2 * FPS,
  myth1: 10 * FPS,
  myth2: 10 * FPS,
  myth3: 10 * FPS,
  myth4: 10 * FPS,
  cta: 8 * FPS,
};

const TOTAL_DURATION =
  SCENE_DURATIONS.hook +
  SCENE_DURATIONS.myth1 +
  SCENE_DURATIONS.myth2 +
  SCENE_DURATIONS.myth3 +
  SCENE_DURATIONS.myth4 +
  SCENE_DURATIONS.cta;

const AUDIO_OFFSET = 15;

export const BrainMythsVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Scene sequences with overlap for transitions */}
      <Sequence from={0} durationInFrames={SCENE_DURATIONS.hook}>
        <HookScene />
      </Sequence>

      <Sequence from={SCENE_DURATIONS.hook - 10} durationInFrames={SCENE_DURATIONS.myth1 + 10}>
        <Myth1Scene />
      </Sequence>

      <Sequence
        from={SCENE_DURATIONS.hook + SCENE_DURATIONS.myth1 - 10}
        durationInFrames={SCENE_DURATIONS.myth2 + 10}
      >
        <Myth2Scene />
      </Sequence>

      <Sequence
        from={
          SCENE_DURATIONS.hook +
          SCENE_DURATIONS.myth1 +
          SCENE_DURATIONS.myth2 -
          10
        }
        durationInFrames={SCENE_DURATIONS.myth3 + 10}
      >
        <Myth3Scene />
      </Sequence>

      <Sequence
        from={
          SCENE_DURATIONS.hook +
          SCENE_DURATIONS.myth1 +
          SCENE_DURATIONS.myth2 +
          SCENE_DURATIONS.myth3 -
          10
        }
        durationInFrames={SCENE_DURATIONS.myth4 + 10}
      >
        <Myth4Scene />
      </Sequence>

      <Sequence
        from={
          SCENE_DURATIONS.hook +
          SCENE_DURATIONS.myth1 +
          SCENE_DURATIONS.myth2 +
          SCENE_DURATIONS.myth3 +
          SCENE_DURATIONS.myth4 -
          10
        }
        durationInFrames={SCENE_DURATIONS.cta}
      >
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};