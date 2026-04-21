import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, Easing } from "remotion";
import { colors, type, springs } from "../styles";

export const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();

  const scale = spring({
    frame,
    fps: 30,
    from: 0.5,
    to: 1,
    config: springs.bouncy,
  });

  const pulse = interpolate(frame, [0, 30, 60], [1, 1.1, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.sin),
  });

  const textOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: "clamp" });
  const ctaOpacity = interpolate(frame, [40, 60], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Brain icon pulse */}
      <div
        style={{
          transform: `scale(${scale * pulse})`,
          opacity: textOpacity,
        }}
      >
        <svg width="160" height="160" viewBox="0 0 120 120">
          <ellipse cx="60" cy="60" rx="45" ry="40" fill="none" stroke={colors.teal} strokeWidth="4" />
          <path d="M30 50 Q60 30 90 50" fill="none" stroke={colors.teal} strokeWidth="3" />
          <path d="M35 70 Q60 50 85 70" fill="none" stroke={colors.teal} strokeWidth="3" />
        </svg>
      </div>

      {/* Main message */}
      <div
        style={{
          position: "absolute",
          opacity: textOpacity,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 36,
            color: colors.textSecondary,
          }}
        >
          Your brain is more capable
        </div>
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 36,
            color: colors.textSecondary,
          }}
        >
          than you think.
        </div>
      </div>

      {/* CTA */}
      <div
        style={{
          position: "absolute",
          bottom: 180,
          opacity: ctaOpacity,
        }}
      >
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 72,
            color: colors.pink,
            textShadow: `0 0 30px ${colors.pink}`,
            letterSpacing: "0.05em",
          }}
        >
          FOLLOW FOR MORE
        </div>
      </div>
    </AbsoluteFill>
  );
};