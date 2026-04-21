import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from "remotion";
import { colors, type, springs } from "../styles";

export const Myth2Scene: React.FC = () => {
  const frame = useCurrentFrame();

  const leftSlide = interpolate(frame, [0, 30], [-400, 0], { extrapolateLeft: "clamp" });
  const rightSlide = interpolate(frame, [0, 30], [400, 0], { extrapolateLeft: "clamp" });
  const mergeOpacity = interpolate(frame, [25, 50], [0, 1], { extrapolateLeft: "clamp" });
  const textOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: "clamp" });

  const glowPulse = interpolate(frame, [0, 90], [0.4, 0.8], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Split brain halves */}
      <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
        {/* Left half */}
        <div
          style={{
            transform: `translateX(${leftSlide}px)`,
            width: 200,
            height: 300,
            borderRadius: "100px 0 0 100px",
            background: `linear-gradient(90deg, ${colors.blue}66, ${colors.teal}33)`,
            border: `2px solid ${colors.teal}`,
            boxShadow: `0 0 ${30 * glowPulse}px ${colors.teal}`,
          }}
        />
        {/* Right half */}
        <div
          style={{
            transform: `translateX(${rightSlide}px)`,
            width: 200,
            height: 300,
            borderRadius: "0 100px 100px 0",
            background: `linear-gradient(270deg, ${colors.orange}66, ${colors.teal}33)`,
            border: `2px solid ${colors.teal}`,
            boxShadow: `0 0 ${30 * glowPulse}px ${colors.teal}`,
          }}
        />
      </div>

      {/* Merge symbol */}
      <div
        style={{
          position: "absolute",
          opacity: mergeOpacity,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 48,
            color: colors.textSecondary,
            letterSpacing: "0.1em",
          }}
        >
          LEFT + RIGHT
        </div>
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 64,
            color: colors.teal,
            textShadow: `0 0 30px ${colors.teal}`,
          }}
        >
          = BOTH
        </div>
      </div>

      {/* Science says no */}
      <div
        style={{
          position: "absolute",
          bottom: 200,
          opacity: textOpacity,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 32,
            color: colors.pink,
          }}
        >
          Science says no.
        </div>
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 24,
            color: colors.textSecondary,
            marginTop: 12,
          }}
        >
          Both hemispheres work together on every task.
        </div>
      </div>
    </AbsoluteFill>
  );
};