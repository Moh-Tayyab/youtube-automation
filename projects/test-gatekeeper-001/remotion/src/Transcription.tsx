import { useCurrentFrame, interpolate } from "remotion";
import React from "react";
import { colors, fonts } from "./styles";

type Caption = { start: number; end: number; text: string };

export const Transcription: React.FC<{
  frame: number;
  fps: number;
  captions: Caption[];
}> = ({ frame, fps, captions }) => {
  const currentTime = frame / fps;
  const activeCaption = captions.find(
    (c) => currentTime >= c.start && currentTime <= c.end
  );

  if (!activeCaption) return null;

  const dur       = activeCaption.end - activeCaption.start;
  const fadeFrames = Math.min(8, Math.floor((dur * fps) / 4));
  const startF     = Math.floor(activeCaption.start * fps);
  const endF       = Math.floor(activeCaption.end * fps);

  const opacity = interpolate(
    frame,
    [startF, startF + fadeFrames, endF - fadeFrames, endF],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute", bottom: 40, left: 0, right: 320,
        display: "flex", justifyContent: "center", pointerEvents: "none", opacity,
      }}
    >
      <div style={{
        padding: "16px 40px", borderRadius: 12, background: colors.caption,
        backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,0.1)", maxWidth: 900,
      }}>
        <span style={{ fontSize: 24, fontWeight: 500, fontFamily: fonts.body, color: "#fff", letterSpacing: "-0.01em", lineHeight: 1.4, textAlign: "center", display: "block" }}>
          {activeCaption.text}
        </span>
      </div>
    </div>
  );
};
