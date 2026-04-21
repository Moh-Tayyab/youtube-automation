const { chromium } = require('puppeteer');
const path = require('path');

(async () => {
  console.log('Starting capture...');

  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--use-gl=angle',
      '--enable-webgl'
    ]
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: '/tmp',
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();
  const filePath = 'file://' + path.resolve(__dirname, 'index.html');

  await page.goto(filePath, { waitUntil: 'networkidle' });
  console.log('Page loaded');

  // Wait for animation to complete (24 seconds for all scenes)
  console.log('Waiting for animation...');
  await page.waitForTimeout(26000);

  const video = await context.close();
  const videoPath = video.outputPath;

  if (videoPath) {
    console.log('Video recorded:', videoPath);
    // Move to output
    const outputPath = path.resolve(__dirname, 'output', 'video.mp4');
    require('fs').copyFileSync(videoPath, outputPath);
    console.log('Video saved to:', outputPath);
  } else {
    console.log('No video path returned');
  }

  await browser.close();
})();
