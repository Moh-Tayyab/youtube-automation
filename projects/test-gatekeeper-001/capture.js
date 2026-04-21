const puppeteer = require('puppeteer');
const path = require('path');
const { execSync } = require('child_process');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--enable-webgl',
      '--use-gl=angle',
      '--window-size=1920,1080'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  const filePath = 'file://' + path.resolve(__dirname, 'index.html');
  console.log('Loading:', filePath);
  await page.goto(filePath, { waitUntil: 'networkidle0', timeout: 30000 });

  // Wait for animations to start
  await page.waitForTimeout(2000);

  // Calculate total duration: scenes 3+3+3+4+3+4 = 20s, add transitions = ~24s
  const totalDuration = 24000;
  const fps = 30;
  const totalFrames = (totalDuration / 1000) * fps;

  console.log(`Capturing ${totalFrames} frames at ${fps}fps...`);

  // Use ffmpeg to capture frames from browser
  const framesDir = '/tmp/frames';
  execSync(`mkdir -p ${framesDir} && rm -f ${framesDir}/*.png`);

  for (let i = 0; i < totalFrames; i++) {
    const timestamp = (i / fps) * 1000;

    // Seek to timestamp via page evaluation
    await page.evaluate((t) => {
      if (window.__hf && window.__hf.seek) {
        window.__hf.seek(t);
      }
    }, timestamp);

    // Small delay for render
    await new Promise(r => setTimeout(r, 20));

    // Capture frame
    await page.screenshot({
      path: `${framesDir}/frame_${String(i).padStart(5, '0')}.png`,
      type: 'png'
    });

    if (i % 30 === 0) {
      console.log(`Frame ${i}/${totalFrames}`);
    }
  }

  await browser.close();
  console.log('Frames captured. Encoding video...');

  // Encode video from frames
  const outputPath = path.resolve(__dirname, 'output', 'video.mp4');
  execSync(`ffmpeg -y -framerate ${fps} -i ${framesDir}/frame_%05d.png -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p ${outputPath}`);

  console.log('Video encoded:', outputPath);

  // Show stats
  const stats = execSync(`ls -lh ${outputPath} && ffprobe -v error -show_entries stream=width,height,duration -of default=noprint_wrappers=1 ${outputPath}`).toString();
  console.log(stats);
})();
