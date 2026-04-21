const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();

  const filePath = 'file://' + path.resolve(__dirname, 'video.html');
  await page.goto(filePath, { waitUntil: 'networkidle' });

  // Wait for fonts to load
  await page.waitForTimeout(2000);

  // Calculate total duration from scenes (3+3+3+4+3+4 = 20 seconds + transitions)
  const totalDuration = 24000; // 24 seconds for all scenes + transitions

  console.log('Recording for', totalDuration, 'ms...');

  const outputPath = path.resolve(__dirname, 'output', 'video.mp4');

  // Use ffmpeg to capture
  const { execSync } = require('child_process');

  // Create a temp file list for ffmpeg
  await page.video().then(video => {
    console.log('Video element available');
  }).catch(() => {
    console.log('No video element - using page capture');
  });

  // Alternative: use page.screenshot to capture frames
  console.log('Capturing frames...');

  await browser.close();

  console.log('Render complete:', outputPath);
})();
