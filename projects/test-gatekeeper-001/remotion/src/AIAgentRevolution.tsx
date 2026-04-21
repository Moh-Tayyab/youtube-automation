import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Img,
  Audio,
  staticFile,
} from "remotion";
import React from "react";
import { colors, fonts, type } from "./styles";
import { Transcription } from "./Transcription";

const SCENES = [
  { id: "intro",      start: 0,    end: 4.0,  title: "The AI Agent Revolution Is Here", subtitle: null,     stat: null },
  { id: "adoption",  start: 4.94, end: 17.2, title: "72%",                              subtitle: "of enterprises now use or test AI agents", stat: "Up from 11% last year" },
  { id: "market",     start: 17.2, end: 23.3, title: "$47B",                              subtitle: "projected market size by 2030",           stat: "$5T in global commerce by 2028" },
  { id: "infra",      start: 23.3, end: 32.1, title: "32%",                               subtitle: "controlled by Microsoft & AWS",             stat: "345M Microsoft 365 seats ready" },
  { id: "healthcare",start: 32.1, end: 37.7, title: "900%",                               subtitle: "ROI on front desk automation",              stat: "20-40% cost reduction in hospitals" },
  { id: "growth",     start: 37.7, end: 42.8, title: "7 Months",                          subtitle: "capabilities double every",                 stat: "From 30min to multi-month tasks" },
  { id: "investment",start: 42.8, end: 55.6, title: "84%",                                subtitle: "increasing AI agent investments this year", stat: "40% of Global 2000 roles by 2028" },
  { id: "finale",    start: 55.6, end: 57.1, title: "The Future Is Now",                  subtitle: null, stat: null },
];

const CAPTIONS = [
  { start: 0,    end: 3.84,  text: "The AI agent revolution is here." },
  { start: 4.94, end: 17.2,  text: "72% of enterprises now use or test AI agents, up from just 11% last year." },
  { start: 17.2, end: 23.3, text: "The market hits $47 billion by 2030." },
  { start: 23.3, end: 32.1,  text: "Microsoft and AWS control a third of the infrastructure." },
  { start: 32.1, end: 37.7, text: "Healthcare sees 900% ROI." },
  { start: 37.7, end: 42.8, text: "Capabilities double every seven months." },
  { start: 42.8, end: 55.6, text: "84% of organizations are increasing investments this year." },
  { start: 55.6, end: 57.1, text: "It's now." },
];

// ── Animated Background ──────────────────────────────────────────────────────
const AnimatedBackground: React.FC<{ frame: number }> = ({ frame }) => {
  const pulse = interpolate(frame, [0, 150, 300], [0.3, 0.5, 0.3]);
  const moveX = interpolate(frame % 300, [0, 300], [0, 30]);
  const moveX2 = interpolate(frame % 300, [0, 300], [0, -20]);

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, #050508 0%, #0a0a18 50%, #050510 100%)" }} />
      <div style={{
        position: "absolute", top: `${10 + Math.sin(frame * 0.01) * 5}%`, left: `${20 + Math.cos(frame * 0.008) * 10}%`,
        width: 600, height: 600, borderRadius: "50%",
        background: `radial-gradient(circle, rgba(230,57,70,${(pulse * 0.15).toFixed(3)}) 0%, transparent 70%)`,
        transform: `translate(${moveX}px, 0)`,
      }} />
      <div style={{
        position: "absolute", bottom: `${15 + Math.sin(frame * 0.012 + 1) * 8}%`, right: `${10 + Math.cos(frame * 0.009 + 2) * 8}%`,
        width: 500, height: 500, borderRadius: "50%",
        background: `radial-gradient(circle, rgba(42,157,143,${(pulse * 0.12).toFixed(3)}) 0%, transparent 70%)`,
        transform: `translate(${moveX2}px, 0)`,
      }} />
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
      }} />
    </div>
  );
};

// ── Portrait Overlay ──────────────────────────────────────────────────────────
const PortraitOverlay: React.FC<{ frame: number }> = ({ frame }) => {
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateLeft: "clamp" });
  const scale   = interpolate(frame, [0, 40], [0.85, 1],   { extrapolateLeft: "clamp" });

  return (
    <div style={{
      position: "absolute", bottom: 90, right: 30, width: 260, height: 320,
      opacity, transform: `scale(${scale})`, borderRadius: 16, overflow: "hidden",
      border: "2px solid rgba(255,255,255,0.15)", boxShadow: "0 20px 60px rgba(0,0,0,0.7)",
    }}>
      <Img src={staticFile("images/portrait.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <div style={{
        position: "absolute", inset: -20,
        background: "radial-gradient(ellipse at center, rgba(230,57,70,0.18) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
    </div>
  );
};

// ── Intro Scene ───────────────────────────────────────────────────────────────
const SceneIntro: React.FC<{ globalFrame: number; sceneStart: number }> = ({ globalFrame, sceneStart }) => {
  const sceneFrame = globalFrame - sceneStart * 30;
  const enter      = interpolate(sceneFrame, [0, 30], [0, 1],    { extrapolateLeft: "clamp" });
  const scale      = interpolate(sceneFrame, [0, 40], [0.9, 1], { extrapolateLeft: "clamp" });
  const ls         = interpolate(sceneFrame, [0, 40], [0.3, -0.02], { extrapolateLeft: "clamp" });
  const lineScale  = interpolate(sceneFrame, [20, 55], [0, 1],  { extrapolateLeft: "clamp" });

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
      <h1 style={{ fontFamily: fonts.display, fontSize: type.hero.fontSize, fontWeight: 700, letterSpacing: `${ls}em`, lineHeight: 1.0, color: colors.textPrimary, margin: 0, opacity: enter, transform: `scale(${scale})`, textAlign: "center" }}>
        The Future
      </h1>
      <div style={{
        width: 120, height: 4, background: colors.accent, marginTop: 24, opacity: enter,
        transform: `scaleX(${lineScale})`, transformOrigin: "center",
      }} />
      <p style={{ fontFamily: fonts.mono, fontSize: type.h3.fontSize, fontWeight: 400, color: colors.textSecondary, marginTop: 24, opacity: enter }}>
        Is Already Here
      </p>
    </div>
  );
};

// ── Finale Scene ──────────────────────────────────────────────────────────────
const SceneFinale: React.FC<{ globalFrame: number; sceneStart: number }> = ({ globalFrame, sceneStart }) => {
  const sceneFrame = globalFrame - sceneStart * 30;
  const enter      = interpolate(sceneFrame, [0, 30], [0, 1],    { extrapolateLeft: "clamp" });
  const scale      = interpolate(sceneFrame, [0, 40], [0.8, 1], { extrapolateLeft: "clamp" });

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
      <h1 style={{ fontFamily: fonts.display, fontSize: type.h1.fontSize, fontWeight: 700, letterSpacing: "-0.04em", color: colors.textPrimary, margin: 0, opacity: enter, transform: `scale(${scale})`, textAlign: "center" }}>
        The Agents Are Here.
      </h1>
      <h1 style={{ fontFamily: fonts.display, fontSize: type.h1.fontSize, fontWeight: 700, letterSpacing: "-0.04em", color: colors.accent, margin: "16px 0 0 0", opacity: enter, transform: `scale(${scale})`, textAlign: "center" }}>
        The Question Is How Fast.
      </h1>
    </div>
  );
};

// ── Data Scene Card ───────────────────────────────────────────────────────────
const ACCENT_MAP: Record<string, string> = {
  adoption:  colors.accent,
  market:   colors.accent2,
  infra:    colors.accent3,
  healthcare: "#e63946",
  growth:   "#f4a261",
  investment: "#2a9d8f",
};

const SceneCard: React.FC<{
  title: string; subtitle?: string | null; stat?: string;
  globalFrame: number; sceneStart: number; accentColor: string;
}> = ({ title, subtitle, stat, globalFrame, sceneStart, accentColor }) => {
  const sceneFrame = globalFrame - sceneStart * 30;
  const enter      = interpolate(sceneFrame, [0, 25], [0, 1],    { extrapolateLeft: "clamp" });
  const titleY     = interpolate(sceneFrame, [0, 30],  [40, 0], { extrapolateLeft: "clamp" });
  const subY       = interpolate(sceneFrame, [15, 45], [30, 0],  { extrapolateLeft: "clamp" });
  const statY      = interpolate(sceneFrame, [25, 55], [25, 0],  { extrapolateLeft: "clamp" });
  const glow       = interpolate(sceneFrame, [0, 20, 40], [0, 0.6, 0.3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "flex-start", padding: "0 80px" }}>
      <div style={{ position: "absolute", top: "50%", left: 80, width: 600, height: 300, transform: "translateY(-50%)",
        background: `radial-gradient(ellipse, ${accentColor}${Math.round(glow * 40).toString(16).padStart(2,"0")} 0%, transparent 70%)`,
        pointerEvents: "none",
      }} />
      <div style={{ fontFamily: fonts.mono, fontSize: 13, letterSpacing: "0.2em", textTransform: "uppercase" as const, color: accentColor, opacity: enter, marginBottom: 16 }}>
        AI AGENTS
      </div>
      <h1 style={{ fontFamily: fonts.display, fontSize: type.hero.fontSize, fontWeight: type.hero.fontWeight, letterSpacing: type.hero.letterSpacing, lineHeight: type.hero.lineHeight, color: colors.textPrimary, margin: 0, opacity: enter, transform: `translateY(${titleY}px)`, textShadow: `0 0 80px ${accentColor}40` }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{ fontFamily: fonts.body, fontSize: type.h3.fontSize, fontWeight: 400, color: colors.textSecondary, margin: "20px 0 0 0", opacity: enter, transform: `translateY(${subY}px)`, maxWidth: 700 }}>
          {subtitle}
        </p>
      )}
      {stat && (
        <div style={{ marginTop: 28, padding: "10px 20px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, opacity: enter, transform: `translateY(${statY}px)` }}>
          <span style={{ fontFamily: fonts.mono, fontSize: 15, color: colors.textDim, letterSpacing: "0.05em" }}>{stat}</span>
        </div>
      )}
    </div>
  );
};

// ── Root Composition ─────────────────────────────────────────────────────────
export const AIAgentRevolution: React.FC = () => {
  const frame = useCurrentFrame();
  const fps = 30;
  const totalDuration = 57.1;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <Audio src={staticFile("audio/voiceover.mp3")} />
      <AnimatedBackground frame={frame} />

      {SCENES.map((scene) => {
        const dur = (scene.end - scene.start) * fps;
        const sf  = scene.start * fps;

        if (scene.id === "intro") {
          return <Sequence key={scene.id} from={sf} durationInFrames={dur}><SceneIntro globalFrame={frame} sceneStart={scene.start} /></Sequence>;
        }
        if (scene.id === "finale") {
          return <Sequence key={scene.id} from={sf} durationInFrames={dur}><SceneFinale globalFrame={frame} sceneStart={scene.start} /></Sequence>;
        }
        return (
          <Sequence key={scene.id} from={sf} durationInFrames={dur}>
            <SceneCard title={scene.title} subtitle={scene.subtitle} stat={scene.stat}
              globalFrame={frame} sceneStart={scene.start}
              accentColor={ACCENT_MAP[scene.id] || colors.accent} />
          </Sequence>
        );
      })}

      <PortraitOverlay frame={frame} />
      <Transcription frame={frame} fps={fps} captions={CAPTIONS} />
    </AbsoluteFill>
  );
};
