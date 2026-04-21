import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, Easing } from "remotion";
import { colors, type, springs } from "../styles";

export const Myth1Scene: React.FC = () => {
  const frame = useCurrentFrame();

  const stampScale = spring({
    frame,
    fps: 30,
    from: 2,
    to: 1,
    config: springs.bouncy,
  });

  const mythOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp" });
  const factOpacity = interpolate(frame, [25, 45], [0, 1], { extrapolateLeft: "clamp" });
  const stampOpacity = interpolate(frame, [40, 55], [0, 1], { extrapolateLeft: "clamp" });

  const glowPulse = interpolate(frame, [0, 60], [0.5, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Brain glow background */}
      <div
        style={{
          position: "absolute",
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${colors.teal}33 0%, transparent 70%)`,
          opacity: glowPulse,
        }}
      />

      {/* Myth text */}
      <div style={{ opacity: mythOpacity, textAlign: "center" }}>
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 64,
            color: colors.textSecondary,
            letterSpacing: "-0.02em",
          }}
        >
          &quot;You only use 10%
        </div>
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 64,
            color: colors.textSecondary,
            letterSpacing: "-0.02em",
          }}
        >
          of your brain&quot;
        </div>
      </div>

      {/* FALSE stamp */}
      <div
        style={{
          position: "absolute",
          top: 80,
          right: 100,
          transform: `scale(${stampScale}) rotate(-12deg)`,
          opacity: stampOpacity,
        }}
      >
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 72,
            color: colors.pink,
            fontWeight: 800,
            textShadow: `0 0 20px ${colors.pink}`,
            border: `4px solid ${colors.pink}`,
            padding: "12px 24px",
            borderRadius: 8,
          }}
        >
          FALSE
        </div>
      </div>

      {/* Fact text */}
      <div style={{ opacity: factOpacity, textAlign: "center", maxWidth: 800, marginTop: 60 }}>
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 36,
            color: colors.teal,
            lineHeight: 1.4,
          }}
        >
          Your brain runs your entire body — every breath, every heartbeat, every thought — all at once.
        </div>
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 80,
            color: colors.textPrimary,
            marginTop: 24,
            textShadow: `0 0 30px ${colors.teal}`,
          }}
        >
          100%
        </div>
      </div>
    </AbsoluteFill>
  );
};