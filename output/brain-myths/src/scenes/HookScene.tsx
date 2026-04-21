import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from "remotion";
import { colors, type, springs } from "../styles";

export const HookScene: React.FC = () => {
  const frame = useCurrentFrame();

  const scale = spring({
    frame,
    fps: 30,
    from: 0.5,
    to: 1,
    config: springs.bouncy,
  });

  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: type.h1.fontSize,
            fontWeight: 800,
            color: colors.textPrimary,
            letterSpacing: "-0.03em",
            textShadow: `0 0 40px ${colors.teal}, 0 0 80px ${colors.teal}`,
          }}
        >
          YOU&apos;VE BEEN LIED TO
        </div>
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: type.h2.fontSize,
            fontWeight: 600,
            color: colors.teal,
            letterSpacing: "-0.02em",
            marginTop: 16,
            textShadow: `0 0 30px ${colors.teal}`,
          }}
        >
          ABOUT YOUR BRAIN.
        </div>
      </div>
    </AbsoluteFill>
  );
};