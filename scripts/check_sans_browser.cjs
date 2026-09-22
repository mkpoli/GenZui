/* Validate the offline specimens and TTF/WOFF2 rasterization in both engines. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');
const { chromium, firefox } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'build/sans');
const url = process.env.SANS_SPECIMEN_URL || pathToFileURL(path.join(out, 'index.html')).href;
const fontData = Object.fromEntries(['ttf', 'woff2'].map(ext => [ext,
  fs.readFileSync(path.join(out, 'GenZuiSans-Regular.' + ext)).toString('base64')]));
const hashes = Object.fromEntries(['ttf', 'woff2'].map(ext => [ext + '_sha256',
  crypto.createHash('sha256').update(fs.readFileSync(path.join(out, 'GenZuiSans-Regular.' + ext))).digest('hex')]));

(async () => {
  const results = [];
  for (const engine of [chromium, firefox]) {
    const browser = await engine.launch({ headless: true });
    try {
      const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await page.evaluate(async () => {
        await document.fonts.load('44px GenZui', '𛀁𛄣𛄧𛄨𛅨');
        await document.fonts.ready;
      });
      assert.equal(await page.title(), 'GenZui Sans — 源萃ゴシック');
      const raster = await page.evaluate(async data => {
        const desktop = new FontFace('Desktop', `url(data:font/ttf;base64,${data.ttf})`);
        const web = new FontFace('Web', `url(data:font/woff2;base64,${data.woff2})`);
        await Promise.all([desktop.load(), web.load()]);
        document.fonts.add(desktop); document.fonts.add(web);
        const samples = ['日本語かなカナ', '𛀁𛀂𛀆𛀋𛀗𛂒𛄍', '𛄣𛄤𛄥𛄦𛄧𛄨𛅨',
          '𛄟\u3099𛀆\u309a', 'チウ\u0305 チゥ\u0323 チア𚿰', '卄𝍲𝍳𝍴𝍵𝍶⿼⿽⿾⿿㇯'];
        function pixels(family, text, size) {
          const canvas = document.createElement('canvas');
          canvas.width = 1200; canvas.height = 160;
          const context = canvas.getContext('2d');
          context.font = `${size}px ${family}`;
          context.fillText(text, 20, 110);
          return context.getImageData(0, 0, 1200, 160).data;
        }
        let cases = 0;
        for (const text of samples) for (const size of [24, 48, 72]) {
          const a = pixels('Desktop', text, size), b = pixels('Web', text, size);
          if (!a.some(value => value)) throw new Error('Empty font rendering');
          if (!a.every((value, i) => value === b[i])) throw new Error('TTF/WOFF2 raster mismatch: ' + text);
          cases++;
        }
        return { cases, ttf: desktop.status, woff2: web.status };
      }, fontData);
      assert.equal(raster.ttf, 'loaded'); assert.equal(raster.woff2, 'loaded');
      await page.locator('#size').fill('60');
      assert.equal(await page.locator('#sample').evaluate(e => getComputedStyle(e).fontSize), '60px');
      await page.locator('#direction').click();
      assert.equal(await page.locator('#sample').evaluate(e => getComputedStyle(e).writingMode), 'vertical-rl');
      await page.locator('#direction').click();
      await page.screenshot({ path: path.join(out, engine.name() + '-specimen.png') });
      await page.setViewportSize({ width: 390, height: 844 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert.deepEqual(errors, []);
      results.push({ engine: engine.name(), version: browser.version(), raster_cases: raster.cases,
        horizontal_vertical_controls: true, mobile_layout: true, status: 'passed' });
      console.log(engine.name() + ': passed');
    } finally {
      await browser.close();
    }
  }
  fs.writeFileSync(path.join(out, 'browser-checks.json'), JSON.stringify({ status: 'passed',
    family: 'GenZui Sans', ...hashes, browsers: results }, null, 2) + '\n');
})().catch(error => { console.error(error.message); process.exitCode = 1; });
