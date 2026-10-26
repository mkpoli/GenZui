/** Validate the offline specimen, font loading and raster parity. Run through devrun. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { createServer } from 'node:http';
import { chromium, firefox } from 'playwright-core';
const out = path.resolve(import.meta.dirname, '../build/tangut-sans');
const stem = 'GenZuiSansTangut-Regular';
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const hashes = Object.fromEntries(['ttf', 'woff2'].map(ext => [ext + '_sha256', hash(path.join(out, stem + '.' + ext))]));
const screenshots = path.join(out, 'screenshots');
fs.mkdirSync(screenshots, { recursive: true });
const server = createServer(async (request, response) => {
  try {
    const name = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname).replace(/^\//, '') || 'index.html';
    const file = path.resolve(out, name);
    if (!file.startsWith(out + path.sep)) throw new Error('Outside specimen');
    const data = await fs.promises.readFile(file);
    const mime = { '.html': 'text/html; charset=utf-8', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.css': 'text/css', '.json': 'application/json' }[path.extname(file)] || 'application/octet-stream';
    response.writeHead(200, { 'Content-Type': mime }); response.end(data);
  } catch { response.writeHead(404); response.end('Not found'); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const url = `http://127.0.0.1:${server.address().port}/`;
const results = [];
try {
  for (const engine of [chromium, firefox]) {
    const executablePath = process.env[engine.name().toUpperCase() + '_EXECUTABLE_PATH'];
    const browser = await engine.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
    try {
      const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 2, colorScheme: 'light' });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      await page.evaluate(async () => {
        const faces = await Promise.all([document.fonts.load('76px Tangut', '𗟕𘢌'), document.fonts.load('76px Reference', '𗟕𘢌')]);
        if (!faces.every(group => group.length === 1 && group[0].status === 'loaded')) throw new Error('Specimen font is missing');
        await document.fonts.ready;
      });
      assert.equal(await page.title(), 'GenZui Sans Tangut');
      const baseline = await page.evaluate(() => {
        const ctx = document.createElement('canvas').getContext('2d');
        return ['Tangut', 'Reference'].map(family => {
          ctx.font = `100px ${family}`;
          const m = ctx.measureText('𗟕');
          return [m.fontBoundingBoxAscent, m.fontBoundingBoxDescent];
        });
      });
      assert.deepEqual(baseline[0], baseline[1], 'Comparison fonts have different baselines');
      const exampleLabel = await page.locator('[data-group=complex]').innerText();
      assert(Number(exampleLabel.match(/\d+/)[0]) >= 100, 'The proof needs a broad example set');
      assert.equal(await page.locator('#rows').evaluate(e => getComputedStyle(e).display), 'grid');
      const firstCard = await page.locator('.row').nth(0).boundingBox();
      const secondCard = await page.locator('.row').nth(1).boundingBox();
      assert(firstCard.y === secondCard.y && secondCard.x > firstCard.x, 'Grid does not show multiple characters per row');
      if (engine === chromium) await page.locator('#comparison').screenshot({ path: path.join(screenshots, 'comparison-grid-light.png') });
      await page.locator('#grid').uncheck();

      const raster = await page.evaluate(async stem => {
        for (const ext of ['ttf', 'woff2']) {
          const face = new FontFace('Test' + ext, `url(${stem}.${ext})`);
          await face.load(); document.fonts.add(face);
          if (face.status !== 'loaded') throw new Error('Font failed to load');
        }
        const canvas = document.createElement('canvas'); canvas.width = 900; canvas.height = 180;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        const pixels = (family, text, size) => {
          ctx.clearRect(0, 0, 900, 180); ctx.font = `${size}px ${family}`; ctx.fillText(text, 10, 140);
          return ctx.getImageData(0, 0, 900, 180).data;
        };
        let cases = 0;
        for (const text of ['𗀀𗐃𗟕𗷖𘴅', '𘠀𘠁𘠂𘢌𘢻', '𗎬𗲶𗻫𘁺']) for (const size of [24, 48, 96, 128]) {
          const a = pixels('Testttf', text, size), b = pixels('Testwoff2', text, size);
          if (!a.some(value => value)) throw new Error('Empty raster');
          if (!a.every((value, i) => value === b[i])) throw new Error('TTF/WOFF2 raster mismatch');
          cases++;
        }
        return cases;
      }, stem);
      await page.locator('#search').fill('U+1888C');
      assert.equal(await page.locator('.row').count(), 1);
      assert.equal(await page.locator('.row').getAttribute('data-codepoint'), '1888C');
      await page.locator('#search').fill('𗟕');
      assert.equal(await page.locator('.row').getAttribute('data-codepoint'), '177D5');
      await page.locator('#size').fill('96');
      assert.equal(await page.locator('.result').evaluate(e => getComputedStyle(e).fontSize), '96px');
      await page.locator('#compare').uncheck();
      assert.equal(await page.locator('.row .source').isVisible(), false);
      await page.locator('#compare').check();
      await page.locator('#overlay').check();
      assert.deepEqual(await page.locator('.row .source').boundingBox(), await page.locator('.row .result').boundingBox());
      await page.locator('#overlay').uncheck();
      await page.locator('#guides').check();
      assert.equal(await page.locator('.row .result').evaluate(e => getComputedStyle(e, '::after').borderTopStyle), 'dashed');
      await page.locator('#guides').uncheck();
      await page.locator('[data-group=dense]').click();
      assert.equal(await page.locator('.row').count(), 48);

      await page.locator('[data-group=components]').click();
      assert.equal(await page.locator('.row').count(), 48);
      assert.match(await page.locator('#position').innerText(), /768$/);
      await page.locator('#next').click();
      assert.equal(await page.locator('.row').first().getAttribute('data-codepoint'), '18830');
      await page.locator('[data-group=all]').click();
      assert.match(await page.locator('#position').innerText(), /6,914$/);
      await page.locator('#search').fill('U+10FFFF');
      assert.equal(await page.locator('.row').count(), 0);
      assert.match(await page.locator('.empty').innerText(), /No matching/);
      await page.locator('textarea').fill('𗀀𗟕𘢌');
      await page.locator('#search').fill(String.fromCodePoint(0x16FE0, 0x17000, 0x17002, 0x17017, 0x177D5, 0x17DD6, 0x188BB, 0x18943, 0x18A46));
      if (engine === chromium) {
        for (const theme of ['light', 'dark']) {
          await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
          await page.locator('#comparison').screenshot({ path: path.join(screenshots, `comparison-${theme}.png`) });
          // Crop each column from the same live comparison, retaining labels and code points.
          for (const side of ['before', 'after']) {
            const style = await page.addStyleTag({ content: side === 'before'
              ? '.head>span:last-child,.row>.result{display:none}.head,.row{grid-template-columns:115px 1fr}'
              : '.head>.source,.row>.source{display:none}.head,.row{grid-template-columns:115px 1fr}' });
            await page.locator('#comparison').screenshot({ path: path.join(screenshots, `${side}-${theme}.png`) });
            await style.evaluate(e => e.remove());
          }
          await page.screenshot({ path: path.join(screenshots, `specimen-${theme}.png`), fullPage: true });
        }
      }
      await page.evaluate(() => document.documentElement.dataset.theme = 'light');
      await page.locator('#theme').click();
      assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark');
      await page.setViewportSize({ width: 390, height: 844 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      if (engine === chromium) await page.screenshot({ path: path.join(screenshots, 'mobile-dark.png'), fullPage: true });

      await page.goto(pathToFileURL(path.join(out, 'index.html')).href);
      const offline = await page.evaluate(async () => {
        const faces = await Promise.all(['Tangut', 'Reference'].map(f => document.fonts.load(`76px ${f}`, '𗟕')));
        return faces.every(group => group.length === 1 && group[0].status === 'loaded');
      });
      assert(offline, 'Offline specimen fonts failed to load');
      assert.deepEqual(errors, []);
      results.push({ engine: engine.name(), version: browser.version(), raster_cases: raster, specimen_controls: true, shared_baseline: true, offline_fonts: true, mobile_layout: true, status: 'passed' });
      console.log(engine.name() + ': passed');
    } finally { await browser.close(); }
  }
  fs.writeFileSync(path.join(out, 'browser-checks.json'), JSON.stringify({ status: 'passed', family: 'GenZui Sans Tangut', ...hashes, specimen_sha256: hash(path.join(out, 'index.html')), checker_sha256: hash(import.meta.filename), browsers: results }, null, 2) + '\n');
} finally { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
