// Usage: node render.js /abs/path/konspekt.html /abs/path/raw.pdf ["Footer title"]
// Optional env PW_CHANNEL (e.g. "msedge" or "chrome") to use an installed browser instead of Playwright's Chromium.
const { chromium } = require('playwright');
const footer = process.argv[4] || 'Урок 3 · Вебинар: нейропаспорт и ИИ-помощники';
(async () => {
  const b = await chromium.launch(process.env.PW_CHANNEL ? { channel: process.env.PW_CHANNEL } : {});
  const p = await b.newPage();
  await p.goto('file://' + process.argv[2], { waitUntil: 'networkidle' });
  await p.pdf({ path: process.argv[3], format: 'A4', printBackground: true, outline: true, tagged: true, displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font-family:Inter;font-size:7pt;color:#8a8d84;padding:0 15mm;display:flex;justify-content:space-between"><span>' + footer + '</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
    margin: { top: '16mm', bottom: '18mm', left: '15mm', right: '15mm' } });
  await b.close();
})();
