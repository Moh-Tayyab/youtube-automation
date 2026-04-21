const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

(async () => {
  console.log('Starting capture...');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--use-gl=angle',
      '--enable-webgl'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const filePath = 'file://' + path.resolve(__dirname, 'index.html');
  await page.goto(filePath, { waitUntil: 'networkidle0' });
  console.log('Page loaded');

  const fps = 30;
  const duration = 24; // Total duration in seconds
  const totalFrames = fps * duration;

  const framesDir = '/tmp/frames';
  execSync(`mkdir -p ${framesDir} && rm -f ${framesDir}/*.png`);

  console.log(`Capturing ${totalFrames} frames at ${fps}fps...`);

  // Pre-generate all frame timestamps
  const timestamps = [];
  for (let i = 0; i < totalFrames; i++) {
    timestamps.push((i / fps) * 1000);
  }

  // Process in batches for speed
  const batchSize = 10;
  for (let batch = 0; batch < timestamps.length; batch += batchSize) {
    const batchTimestamps = timestamps.slice(batch, batch + batchSize);

    for (const timestamp of batchTimestamps) {
      const frameIndex = Math.round(timestamp / 1000 * fps);

      // Seek animation
      await page.evaluate((t) => {
        if (window.__hf && window.__hf.seek) {
          window.__hf.seek(t);
        }
      }, timestamp);

      // Small delay for render
      await new Promise(r => setTimeout(r, 30));

      // Capture frame
      const framePath = `${framesDir}/frame_${String(frameIndex).padStart(5, '0')}.png`;
      await page.screenshot({ path: framePath, type: 'png' });
    }

    console.log(`Progress: ${Math.min(batch + batchSize, totalFrames)}/${totalFrames} frames`);
  }

  await browser.close();
  console.log('Frames captured. Encoding video...');

  // Encode video from frames
  const outputPath = path.resolve(__dirname, 'output', 'video.mp4');
  execSync(`ffmpeg -y -framerate ${fps} -i ${framesDir}/frame_%05d.png -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p ${outputPath} 2>&1`);

  console.log('Video saved to:', outputPath);

  const stats = execSync(`ls -lh ${outputPath}`).toString();
  console.log(stats);
})();
