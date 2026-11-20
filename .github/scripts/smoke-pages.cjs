const assert = require('node:assert/strict');
const { once } = require('node:events');
const { readFile } = require('node:fs/promises');
const { createServer } = require('node:http');
const { chromium } = require('playwright');

async function main() {
  const [directory, executablePath] = process.argv.slice(2);
  const routes = new Map([
    ['/redraft/', ['text/html', await readFile(`${directory}/index.html`)]],
    ['/redraft/site.css', ['text/css', await readFile(`${directory}/site.css`)]],
  ]);
  const server = createServer((request, response) => {
    const route = routes.get(request.url);
    if (!route) return response.writeHead(404).end();
    const [type, body] = route;
    response.writeHead(200, { 'Content-Type': `${type}; charset=utf-8` }).end(body);
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');

  let browser;
  try {
    browser = await chromium.launch({ executablePath });
    for (const width of [320, 390, 1280]) {
      const page = await browser.newPage({
        viewport: { width, height: 844 },
        isMobile: width < 400,
        hasTouch: width < 400,
      });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const stylesheet = page.waitForResponse(response => response.url().endsWith('/redraft/site.css'));
      const response = await page.goto(`http://127.0.0.1:${server.address().port}/redraft/`);
      assert.equal(response.status(), 200);
      assert.equal((await stylesheet).status(), 200);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const links = await page.getByRole('link').all();
      assert.equal(links.length, 6);
      for (const link of links) {
        assert.ok(await link.isVisible());
        assert.ok((await link.boundingBox()).height >= 44);
        await page.keyboard.press('Tab');
        assert.ok(await link.evaluate(element => element === document.activeElement));
      }
      assert.deepEqual(errors, []);
      console.log(`${width}px: stylesheet loaded, six 44px keyboard-accessible links, no horizontal overflow`);
      await page.close();
    }
  } finally {
    await browser?.close();
    server.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
