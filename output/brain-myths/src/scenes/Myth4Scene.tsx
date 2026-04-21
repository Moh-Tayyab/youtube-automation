import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from "remotion";
import { colors, type, springs } from "../styles";

export const Myth4Scene: React.FC = () => {
  const frame = useCurrentFrame();

  const neurons = Array.from({ length: 12 }, (_, i) => ({
    x: 150 + (i % 4) * 200,
    y: 200 + Math.floor(i / 4) * 180,
    connections: [(i + 1) % 12, (i + 4) % 12],
  }));

  const lineOpacity = interpolate(frame, [0, 30], [0, 0.6], { extrapolateLeft: "clamp" });
  const nodeAppear = neurons.map((_, i) =>
    interpolate(frame, [10 + i * 5, 25 + i * 5], [0, 1], { extrapolateLeft: "clamp" })
  );
  const textOpacity = interpolate(frame, [50, 70], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {/* Neural network visualization */}
      <svg width="700" height="500" style={{ position: "absolute" }}>
        {/* Connections */}
        {neurons.map((n, i) =>
          n.connections.map((c) => (
            <line
              key={`${i}-${c}`}
              x1={n.x}
              y1={n.y}
              x2={neurons[c].x}
              y2={neurons[c].y}
              stroke={colors.teal}
              strokeWidth="2"
              opacity={lineOpacity}
            />
          ))
        )}
        {/* Nodes */}
        {neurons.map((n, i) => (
          <circle
            key={i}
            cx={n.x}
            cy={n.y}
            r={20}
            fill={colors.teal}
            opacity={nodeAppear[i]}
            style={{
              filter: `drop-shadow(0 0 ${10 * nodeAppear[i]}px ${colors.teal})`,
            }}
          />
        ))}
      </svg>

      {/* Myth text */}
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
            fontFamily: "Bangers, sans-serif",
            fontSize: 48,
            color: colors.pink,
            textDecoration: "line-through",
          }}
        >
          &quot;Brain stops developing at 25&quot;
        </div>
        <div
          style={{
            fontFamily: "Bangers, sans-serif",
            fontSize: 64,
            color: colors.teal,
            marginTop: 20,
            textShadow: `0 0 30px ${colors.teal}`,
          }}
        >
          NEVER STOPS
        </div>
        <div
          style={{
            fontFamily: "Inter, sans-serif",
            fontSize: 24,
            color: colors.textSecondary,
            marginTop: 16,
          }}
        >
          Your brain rewires itself constantly.
        </div>
      </div>
    </AbsoluteFill>
  );
};