const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

async function capture() {
  console.log('Launching browser...');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const filePath = 'file://' + path.resolve(__dirname, 'index.html');
  await page.goto(filePath, { waitUntil: 'networkidle0' });
  console.log('Page loaded');

  // Scene durations in ms: 3+3+3+4+3+4 = 20s, add transition time
  const scenes = [
    { name: 'Scene 1', duration: 3000 },
    { name: 'Scene 2', duration: 3500 },
    { name: 'Scene 3', duration: 3500 },
    { name: 'Scene 4', duration: 4500 },
    { name: 'Scene 5', duration: 3500 },
    { name: 'Scene 6', duration: 5000 }
  ];

  const framesDir = '/tmp/frames';
  execSync(`mkdir -p ${framesDir} && rm -f ${framesDir}/*.png`);

  let frameIndex = 0;
  const fps = 30;
  let currentTime = 0;

  console.log('Capturing frames...');

  for (const scene of scenes) {
    console.log(`Capturing ${scene.name} for ${scene.duration}ms`);

    // Capture frames during this scene
    const sceneFrameCount = Math.ceil(scene.duration / 1000 * fps);

    for (let i = 0; i < sceneFrameCount; i++) {
      const timestamp = currentTime + (i / fps) * 1000;

      // Seek to time
      await page.evaluate((t) => {
        if (window.__hf && window.__hf.seek) {
          window.__hf.seek(t);
        }
      }, timestamp);

      // Wait for render
      await new Promise(r => setTimeout(r, 20));

      // Capture
      const framePath = `${framesDir}/frame_${String(frameIndex).padStart(5, '0')}.png`;
      await page.screenshot({ path: framePath, type: 'png', omitBackground: false });
      frameIndex++;
    }

    currentTime += scene.duration;
  }

  await browser.close();
  console.log(`${frameIndex} frames captured`);

  // Encode video
  const outputPath = path.resolve(__dirname, 'output', 'video.mp4');
  console.log('Encoding video...');

  try {
    execSync(`ffmpeg -y -framerate ${fps} -i ${framesDir}/frame_%05d.png -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p ${outputPath}`);
    console.log('Video saved:', outputPath);
    const stats = fs.statSync(outputPath);
    console.log(`Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  } catch (e) {
    console.error('Encoding failed:', e.message);
  }
}

capture().catch(console.error);
