#!/bin/bash
# Brain Myths Video Renderer
# Creates video using ffmpeg with text overlays

OUTPUT="/home/muhammad_tayyab/bootlogix/output/brain-myths"
FRAMES="$OUTPUT/frames"
FINAL="$OUTPUT/final_video.mp4"

mkdir -p "$FRAMES"

# Scene timing (in frames, 30fps)
FPS=30
HOOK_END=60        # 0-2s
MYTH1_END=360      # 2-12s
MYTH2_END=660      # 12-22s
MYTH3_END=960      # 22-32s
MYTH4_END=1260     # 32-42s
CTA_END=1500       # 42-50s

# Color palette
BG="black"
TEAL="0x00D4FF"
ORANGE="0xFF6B35"
PINK="0xFF3366"
WHITE="0xFFFFFF"

echo "Rendering Brain Myths video..."

# Helper function to create text frame
create_frame() {
    local output=$1
    local text=$2
    local font="Bangers"
    local fontsize=$3
    local color=$4
    local x=$5
    local y=$6

    ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
        "drawtext=text='$text':fontsize=$fontsize:fontcolor=$color:x=$x:y=$y:borderw=2:bordercolor=black:font=$font" \
        -frames:v 1 "$output" -y 2>/dev/null
}

# Generate frames for each scene
# Hook scene (0-2s): "YOU'VE BEEN LIED TO ABOUT YOUR BRAIN"
echo "Generating Hook frames..."
for i in $(seq 0 59); do
    frame=$(printf "%04d" $i)
    if [ $i -lt 10 ]; then
        # Slam in animation - scale from small to large
        scale=$(echo "scale=2; 0.5 + ($i * 0.05)" | bc)
        ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
            "drawtext=text='YOU\\'VE BEEN LIED TO':fontsize=72:fontcolor=$WHITE:x=(w-text_w)/2:y=(h-text_h)/2-80:font=Bangers,drawtext=text='ABOUT YOUR BRAIN.':fontsize=72:fontcolor=$TEAL:x=(w-text_w)/2:y=(h-text_h)/2+20:font=Bangers" \
            -frames:v 1 "$FRAMES/hook_$frame.png" -y 2>/dev/null
    else
        ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
            "drawtext=text='YOU\\'VE BEEN LIED TO':fontsize=72:fontcolor=$WHITE:x=(w-text_w)/2:y=(h-text_h)/2-80:font=Bangers,drawtext=text='ABOUT YOUR BRAIN.':fontsize=72:fontcolor=$TEAL:x=(w-text_w)/2:y=(h-text_h)/2+20:font=Bangers" \
            -frames:v 1 "$FRAMES/hook_$frame.png" -y 2>/dev/null
    fi
done

# Myth 1 scene (2-12s): "10%? FALSE" + brain facts
echo "Generating Myth 1 frames..."
for i in $(seq 60 359); do
    frame=$(printf "%04d" $i)
    t=$((i - 60))
    ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
        "drawtext=text='\"You only use 10% of your brain\"':fontsize=36:fontcolor=0x888888:x=100:y=300:font=Bangers,drawtext=text='FALSE':fontsize=96:fontcolor=$PINK:x=700:y=100:font=Bangers,drawtext=text='Your brain runs your entire body':fontsize=32:fontcolor=$TEAL:x=100:y=800:font=Bangers,drawtext=text='100%':fontsize=120:fontcolor=$WHITE:x=(w-text_w)/2:y=1000:font=Bangers" \
        -frames:v 1 "$FRAMES/myth1_$frame.png" -y 2>/dev/null
done

# Myth 2 scene (12-22s): Left + Right = Both
echo "Generating Myth 2 frames..."
for i in $(seq 360 659); do
    frame=$(printf "%04d" $i)
    ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
        "drawtext=text='LEFT':fontsize=64:fontcolor=0x0066FF:x=150:y=400:font=Bangers,drawtext=text='+':fontsize=64:fontcolor=$WHITE:x=500:y=400:font=Bangers,drawtext=text='RIGHT':fontsize=64:fontcolor=0xFF6B35:x=700:y=400:font=Bangers,drawtext=text='= BOTH':fontsize=80:fontcolor=$TEAL:x=(w-text_w)/2:y=600:font=Bangers,drawtext=text='Science says no. Both hemispheres work together.':fontsize=28:fontcolor=$WHITE:x=(w-text_w)/2:y=900:font=Bangers" \
        -frames:v 1 "$FRAMES/myth2_$frame.png" -y 2>/dev/null
done

# Myth 3 scene (22-32s): Ear -> Brain
echo "Generating Myth 3 frames..."
for i in $(seq 660 959); do
    frame=$(printf "%04d" $i)
    ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
        "drawtext=text='EAR':fontsize=48:fontcolor=0x888888:x=200:y=400:font=Bangers,drawtext=text='→':fontsize=64:fontcolor=$ORANGE:x=450:y=400:font=Bangers,drawtext=text='BRAIN':fontsize=48:fontcolor=$ORANGE:x=700:y=400:font=Bangers,drawtext=text='You hear with your brain. Ears are just microphones.':fontsize=28:fontcolor=$TEAL:x=(w-text_w)/2:y=800:font=Bangers" \
        -frames:v 1 "$FRAMES/myth3_$frame.png" -y 2>/dev/null
done

# Myth 4 scene (32-42s): Neural plasticity
echo "Generating Myth 4 frames..."
for i in $(seq 960 1259); do
    frame=$(printf "%04d" $i)
    ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
        "drawtext=text='\"Brain stops developing at 25\"':fontsize=40:fontcolor=0x888888:x=100:y=300:font=Bangers:strikethrough=1,drawtext=text='NEVER STOPS':fontsize=80:fontcolor=$TEAL:x=(w-text_w)/2:y=600:font=Bangers,drawtext=text='Your brain rewires itself constantly.':fontsize=28:fontcolor=$WHITE:x=(w-text_w)/2:y=900:font=Bangers" \
        -frames:v 1 "$FRAMES/myth4_$frame.png" -y 2>/dev/null
done

# CTA scene (42-50s): Follow for more
echo "Generating CTA frames..."
for i in $(seq 1260 1499); do
    frame=$(printf "%04d" $i)
    ffmpeg -f lavfi -i "color=c=$BG:s=1080x1920:d=0.033333" -vf \
        "drawtext=text='Your brain is more capable':fontsize=36:fontcolor=$WHITE:x=(w-text_w)/2:y=700:font=Bangers,drawtext=text='than you think.':fontsize=36:fontcolor=$WHITE:x=(w-text_w)/2:y=760:font=Bangers,drawtext=text='FOLLOW FOR MORE':fontsize=72:fontcolor=$PINK:x=(w-text_w)/2:y=1000:font=Bangers" \
        -frames:v 1 "$FRAMES/cta_$frame.png" -y 2>/dev/null
done

echo "Encoding video from frames..."
ffmpeg -framerate $FPS -i "$FRAMES/hook_%04d.png" \
    -i "$FRAMES/myth1_%04d.png" \
    -i "$FRAMES/myth2_%04d.png" \
    -i "$FRAMES/myth3_%04d.png" \
    -i "$FRAMES/myth4_%04d.png" \
    -i "$FRAMES/cta_%04d.png" \
    -filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v]concat=n=6:v=1:a=0[out]" \
    -map "[out]" \
    -c:v libx264 -preset fast -crf 18 \
    -pix_fmt yuv420p \
    "$FINAL" -y 2>/dev/null

echo "Done! Output: $FINAL"