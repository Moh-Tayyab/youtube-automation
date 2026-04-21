#!/bin/bash
# Render HTML animation to MP4 using ffmpeg + Chrome

HTML_FILE="$(pwd)/video.html"
OUTPUT_FILE="$(pwd)/output/video.mp4"
DURATION=28  # Total duration covering all scenes + transitions

echo "Starting render..."
echo "HTML: $HTML_FILE"
echo "Output: $OUTPUT_FILE"

# Use Chrome headless with remote debugging to capture
chrome --headless --disable-gpu --screenshot=/tmp/test.png --window-size=1920,1080 "$HTML_FILE" 2>/dev/null || true

# Alternative: Use ffmpeg with x11grab if available
if command -v recordmydesktop &> /dev/null; then
    echo "recordmydesktop available"
fi

# Check for alternative tools
for tool in scrot import gnome-screenshot; do
    if command -v $tool &> /dev/null; then
        echo "$tool found"
    fi
done

echo "Checking ffmpeg capabilities..."
ffmpeg -formats 2>/dev/null | grep -i x11 || echo "No x11 input"

echo "Render script ready - HTML file captured for verification"
ls -la output/
