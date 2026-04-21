import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from "remotion";
import { colors, type, springs } from "../styles";

export const Myth3Scene: React.FC = () => {
  const frame = useCurrentFrame();

  const earX = interpolate(frame, [0, 40], [-200, 0], { extrapolateLeft: "clamp" });
  const brainX = interpolate(frame, [0, 40], [200, 0], { extrapolateLeft: "clamp" });
  const waveOpacity = interpolate(frame, [30, 35], [0, 1], { extrapolateLeft: "clamp" });
  const textOpacity = interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: "clamp" });
  const earScale = interpolate(frame, [0, 30], [0.8, 1], { extrapolateLeft: "clamp" });
  const brainScale = interpolate(frame, [0, 30], [0.8, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Icons row */}
      <div style={{ display: "flex", alignItems: "center", gap: 120 }}>
        {/* Ear icon */}
        <div
          style={{
            transform: `translateX(${earX}px) scale(${earScale})`,
          }}
        >
          <svg width="120" height="120" viewBox="0 0 120 120">
            <ellipse cx="60" cy="60" rx="40" ry="50" fill="none" stroke={colors.teal} strokeWidth="3" />
            <path d="M60 20 Q80 40 60 60 Q40 80 60 100" fill="none" stroke={colors.teal} strokeWidth="2" />
          </svg>
          <div
            style={{
              fontFamily: "Bangers, sans-serif",
              fontSize: 32,
              color: colors.textSecondary,
              textAlign: "center",
              marginTop: 8,
            }}
          >
            EAR
          </div>
        </div>

        {/* Arrow/wave */}
        <div style={{ opacity: waveOpacity }}>
          <svg width="100" height="40" viewBox="0 0 100 40">
            <path
              d="M0 20 Q25 0 50 20 Q75 40 100 20"
              fill="none"
              stroke={colors.orange}
              strokeWidth="4"
              strokeDasharray="10 5"
            />
          </svg>
        </div>

        {/* Brain icon */}
        <div
          style={{
            transform: `translateX(${brainX}px) scale(${brainScale})`,
          }}
        >
          <svg width="120" height="120" viewBox="0 0 120 120">
            <ellipse cx="60" cy="60" rx="45" ry="40" fill="none" stroke={colors.orange} strokeWidth="3" />
            <path d="M30 50 Q60 30 90 50" fill="none" stroke={colors.orange} strokeWidth="2" />
            <path d="M35 70 Q60 50 85 70" fill="none" stroke={colors.orange} strokeWidth="2" />
          </svg>
          <div
            style={{
              fontFamily: "Bangers, sans-serif",
              fontSize: 32,
              color: colors.orange,
              textAlign: "center",
              marginTop: 8,
            }}
          >
            BRAIN
          </div>
        </div>
      </div>

      {/* Myth text */}
      <div
        style={{
          position: "absolute",
          bottom: 220,
          opacity: textOpacity,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 48,
            color: colors.textSecondary,
            textDecoration: "line-through",
          }}
        >
          &quot;You hear with your ears&quot;
        </div>
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 28,
            color: colors.teal,
            marginTop: 20,
            lineHeight: 1.5,
          }}
        >
          Your ears are just microphones.
          <br />
          The real processing happens upstairs.
        </div>
      </div>
    </AbsoluteFill>
  );
};