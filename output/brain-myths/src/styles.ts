export const colors = {
  bg: "#000000",
  textPrimary: "rgba(255,255,255,0.95)",
  textSecondary: "rgba(255,255,255,0.7)",
  textDim: "rgba(255,255,255,0.4)",
  teal: "#00D4FF",
  orange: "#FF6B35",
  pink: "#FF3366",
  blue: "#0066FF",
};

export const fonts = {
  display: "Bangers, sans-serif",
  body: "Inter, system-ui, sans-serif",
};

export const type = {
  hero: {
    fontSize: 96,
    fontWeight: 700,
    letterSpacing: "-0.04em",
    lineHeight: 1.05,
  },
  h1: {
    fontSize: 72,
    fontWeight: 700,
    letterSpacing: "-0.03em",
    lineHeight: 1.1,
  },
  h2: {
    fontSize: 56,
    fontWeight: 600,
    letterSpacing: "-0.025em",
    lineHeight: 1.2,
  },
  body: {
    fontSize: 32,
    fontWeight: 400,
    letterSpacing: "-0.01em",
    lineHeight: 1.4,
  },
  label: {
    fontSize: 18,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
  },
};

export const springs = {
  snappy: { stiffness: 400, damping: 30 },
  bouncy: { stiffness: 300, damping: 15 },
  smooth: { stiffness: 120, damping: 25 },
};