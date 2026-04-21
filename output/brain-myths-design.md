# Brain Myths — DESIGN Phase Artifact

## Overview
- **Project:** Brain Myths viral Shorts
- **Duration:** ~50 seconds (6 scenes)
- **Style:** Punchy, energetic, bold text overlays on AI-generated footage

---

## Scene Breakdown

### Scene 1: Hook (0-2s)
| Field | Value |
|-------|-------|
| **Timing** | 0-2 seconds |
| **Script** | "You've been lied to about your brain." |
| **Visual** | Bold text slams onto screen — stark white on deep black |
| **Model** | Text overlay (Remotion) — no AI video generation needed |
| **Style** | High contrast, dramatic, punch-in animation |

---

### Scene 2: Myth 1 — 10% Brain (2-12s)
| Field | Value |
|-------|-------|
| **Timing** | 10 seconds |
| **Script** | "You only use 10% of your brain. Total myth. Your brain runs your entire body—all at once. 100% right now." |
| **AI Video Prompt** | `A realistic 3D brain model rotating in dark space, glowing neural pathways lighting up to show 100% activity, cinematic lighting, dark background, scientific visualization style` |
| **Model** | `google/veo-3-1-fast` (text-to-video) |
| **Overlay** | "10%? FALSE" text stamp |
| **Style** | Glowing synapses, dark atmospheric background |

---

### Scene 3: Myth 2 — Left/Right Brain (12-22s)
| Field | Value |
|-------|-------|
| **Timing** | 10 seconds |
| **Script** | "You're left-brained or right-brained. Science says no. Both hemispheres work together." |
| **AI Video Prompt** | `Two halves of a brain glowing and connecting with electric sparks, forming whole brain, split-screen transform, dark scientific background, 3D render` |
| **Model** | `google/veo-3-1-fast` |
| **Overlay** | "LEFT + RIGHT = BOTH" text |
| **Style** | Split-brain visual merging, electric connection animation |

---

### Scene 4: Myth 3 — Hearing vs Understanding (22-32s)
| Field | Value |
|-------|-------|
| **Timing** | 10 seconds |
| **Script** | "You hear with your ears? No—you hear with your brain. Ears are microphones. Real processing happens upstairs." |
| **AI Video Prompt** | `Human ear icon morphing into brain icon, sound waves traveling from ear to brain, then brain lighting up with understanding, minimalist scientific animation, dark background` |
| **Model** | `google/veo-3-1-fast` |
| **Overlay** | "EAR → BRAIN" with wave animation |
| **Style** | Minimalist icon animation, sound wave visualization |

---

### Scene 5: Myth 4 — Brain Development (32-42s)
| Field | Value |
|-------|-------|
| **Timing** | 10 seconds |
| **Script** | "Brain stops developing at 25? Wrong. It never stops learning. Rewires constantly." |
| **AI Video Prompt** | `Time-lapse of brain neurons forming new connections, neuroplasticity visualization, branching neural network growing and rewiring, warm scientific aesthetic` |
| **Model** | `google/veo-3-1-fast` |
| **Overlay** | "NEVER STOPS" + rewiring graphic |
| **Style** | Growth animation, neural plasticity visualization |

---

### Scene 6: CTA / Twist (42-50s)
| Field | Value |
|-------|-------|
| **Timing** | 8 seconds |
| **Script** | "Your brain is more capable than you think. Follow for more brain facts." |
| **Visual** | All previous brain visuals flash by rapidly (montage) |
| **Model** | Composite of all previous scenes |
| **Overlay** | "FOLLOW FOR MORE" + brain icon pulse |
| **Style** | Energetic recap, call-to-action slam |

---

## storyboard_json

```json
{
  "project": "brain-myths",
  "duration_seconds": 50,
  "scenes": [
    {
      "scene_id": 1,
      "start": 0,
      "end": 2,
      "type": "text_overlay",
      "script": "You've been lied to about your brain.",
      "visual_description": "Bold white text on black, slam-in animation",
      "ai_video_prompt": null,
      "overlay_text": "YOU'VE BEEN LIED TO.",
      "model": null,
      "style": "high_contrast_minimal"
    },
    {
      "scene_id": 2,
      "start": 2,
      "end": 12,
      "type": "ai_generated",
      "script": "You only use 10% of your brain. Total myth. 100% right now.",
      "visual_description": "3D brain glowing with full neural activity",
      "ai_video_prompt": "A realistic 3D brain model rotating in dark space, glowing neural pathways lighting up to show 100% activity, cinematic lighting, dark background, scientific visualization style",
      "overlay_text": "10%? FALSE",
      "model": "google/veo-3-1-fast"
    },
    {
      "scene_id": 3,
      "start": 12,
      "end": 22,
      "type": "ai_generated",
      "script": "Left-brained or right-brained? Science says both work together.",
      "visual_description": "Split brain halves merging with electric sparks",
      "ai_video_prompt": "Two halves of a brain glowing and connecting with electric sparks, forming whole brain, split-screen transform, dark scientific background, 3D render",
      "overlay_text": "LEFT + RIGHT = BOTH",
      "model": "google/veo-3-1-fast"
    },
    {
      "scene_id": 4,
      "start": 22,
      "end": 32,
      "type": "ai_generated",
      "script": "You hear with your brain. Ears are just microphones.",
      "visual_description": "Ear icon morphing into brain with sound waves",
      "ai_video_prompt": "Human ear icon morphing into brain icon, sound waves traveling from ear to brain, then brain lighting up with understanding, minimalist scientific animation, dark background",
      "overlay_text": "EAR → BRAIN",
      "model": "google/veo-3-1-fast"
    },
    {
      "scene_id": 5,
      "start": 32,
      "end": 42,
      "type": "ai_generated",
      "script": "Brain stops developing at 25? Wrong. Never stops learning.",
      "visual_description": "Neural network growing and rewiring",
      "ai_video_prompt": "Time-lapse of brain neurons forming new connections, neuroplasticity visualization, branching neural network growing and rewiring, warm scientific aesthetic",
      "overlay_text": "NEVER STOPS",
      "model": "google/veo-3-1-fast"
    },
    {
      "scene_id": 6,
      "start": 42,
      "end": 50,
      "type": "composite",
      "script": "Your brain is more capable. Follow for more brain facts.",
      "visual_description": "Rapid montage of all previous brain visuals",
      "ai_video_prompt": null,
      "overlay_text": "FOLLOW FOR MORE",
      "model": "remotion_composite",
      "style": "energetic_recap"
    }
  ]
}
```

---

## asset_list

| Asset | Type | Source | Status |
|-------|------|--------|--------|
| brain_rotate.mp4 | AI Generated | Veo 3.1 Fast | Pending |
| brain_split_merge.mp4 | AI Generated | Veo 3.1 Fast | Pending |
| ear_to_brain.mp4 | AI Generated | Veo 3.1 Fast | Pending |
| neural_growth.mp4 | AI Generated | Veo 3.1 Fast | Pending |
| narration.wav | Audio | ElevenLabs TTS | Pending |
| captions.ass | Subtitles | Maven-Edit pipeline | Pending |
| final_composite.mp4 | Output | Remotion | Pending |

---

## style_guide

### Visual Language
- **Background:** Deep black (#000000) — emphasizes brain glow
- **Primary color:** Electric blue (#00D4FF) — neural activity
- **Accent:** Hot pink (#FF3366) — myth "FALSE" stamps
- **Text:** White with glow effects

### Typography
- **Myth claims:** Bold sans-serif, uppercase, stamp effect
- **Debunk text:** Clean sans-serif, readable
- **CTA:** Large, centered, pulse animation

### Animation Philosophy
- Quick cuts (2-3 seconds per visual)
- Text slams in, doesn't fade
- Brain visuals have subtle organic movement
- Contrast between static text and moving backgrounds

### Overlay Style
- Myth statements: Red "FALSE" / "MYTH" stamp
- Facts: Blue/white with glow
- CTA: Pink accent with pulse

---

## scene_timing

| Scene | Start | End | Duration |
|-------|-------|-----|----------|
| Hook | 0s | 2s | 2s |
| Myth 1 | 2s | 12s | 10s |
| Myth 2 | 12s | 22s | 10s |
| Myth 3 | 22s | 32s | 10s |
| Myth 4 | 32s | 42s | 10s |
| CTA | 42s | 50s | 8s |

**Total: 50 seconds**

---

*Created by scriptwriter agent — video-pipeline team*
*Phase: DESIGN*
