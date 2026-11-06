// Headless Firefox (Playwright) checks of the asset-service console: real Keycloak login, axe-core scan,
// keyboard-only arm/confirm/start/stop-all, honest "unknown" state, and screenshots. Local only; no Chrome.
import fs from 'node:fs';
import path from 'node:path';
import { firefox } from 'playwright';

const here = path.dirname(new URL(import.meta.url).pathname);
const out = path.join(here, 'shots');
fs.mkdirSync(out, { recursive: true });
const creds = JSON.parse(fs.readFileSync(path.join(here, '..', 'keycloak', 'local-test-users.json'), 'utf8'));
const axeSource = fs.readFileSync(path.join(here, 'node_modules', 'axe-core', 'axe.min.js'), 'utf8');
const BASE = 'http://localhost:18080';
const results = [];
const record = (label, ok, detail = '') => { results.push({ label, ok, detail }); console.log(ok ? 'PASS' : 'FAIL', label, detail); };

async function axe(page, label) {
  await page.addScriptTag({ content: axeSource });
  const report = await page.evaluate(async () => window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } }));
  const summary = report.violations.map((v) => `${v.id}(${v.impact}) x${v.nodes.length}: ${v.nodes.slice(0, 2).map((n) => n.target.join(' ')).join(', ')}`);
  record(`axe WCAG 2.1 AA: ${label}`, report.violations.length === 0, summary.join(' | ') || `${report.passes.length} rules passed`);
  return report;
}

async function focusedOutline(page) {
  return page.evaluate(() => {
    const el = document.activeElement;
    const style = getComputedStyle(el);
    return { id: el.id || el.tagName, outline: `${style.outlineStyle} ${style.outlineWidth}` };
  });
}

async function tabTo(page, id, key = 'Tab', max = 80) {
  for (let i = 0; i < max; i++) {
    if (await page.evaluate((target) => document.activeElement?.id === target, id)) { return i; }
    await page.keyboard.press(key);
  }
  throw new Error(`could not reach #${id} with ${key}`);
}

const browser = await firefox.launch({ headless: true });
let crashed = null;
try {
  // bypassCSP only lets the harness inject axe-core; the page's own CSP is checked separately below.
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', colorScheme: 'dark', bypassCSP: true });
  const page = await context.newPage();
  await page.goto(`${BASE}/console/`);
  await page.fill('#username', 'operator');
  await page.fill('#password', creds.operator);
  await page.click('#kc-login');
  await page.waitForURL(`${BASE}/console/**`);
  await page.waitForFunction(() => document.getElementById('confirmed').textContent.startsWith('confirmed'));
  await page.waitForTimeout(4500);
  record('console served after Keycloak login', true, page.url());
  await page.screenshot({ path: path.join(out, '01-idle.png'), fullPage: true });
  await axe(page, 'idle, 1440 px');

  // Keyboard only: choose chaos, arm, type the namespace, start.
  await page.keyboard.press('Tab');
  const skip = await focusedOutline(page);
  record('first Tab reaches the skip link with a visible focus ring', skip.outline.startsWith('solid'), JSON.stringify(skip));
  await page.evaluate(() => document.body.focus());
  await tabTo(page, 'sites');
  await page.keyboard.press('Shift+Tab');
  await page.keyboard.press('ArrowDown');
  const kind = await page.evaluate(() => document.querySelector('input[name="kind"]:checked').value);
  record('arrow keys select the chaos run kind', kind === 'CHAOS', kind);
  await tabTo(page, 'duration');
  await page.keyboard.press('Control+a');
  await page.keyboard.type('120');
  await tabTo(page, 'arm');
  const armFocus = await focusedOutline(page);
  record('Arm button reachable and focus visible', armFocus.outline.startsWith('solid'), JSON.stringify(armFocus));
  await page.keyboard.press('Enter');
  await page.waitForSelector('#confirm-armed:not([hidden])');
  const focusAfterArm = await page.evaluate(() => document.activeElement.id);
  record('arming moves focus to the namespace confirmation', focusAfterArm === 'confirm-ns', focusAfterArm);
  record('Start stays disabled until the namespace is typed', await page.isDisabled('#start'));
  const namespace = await page.textContent('#confirm-ns-name');
  await page.keyboard.type(namespace);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(out, '02-armed-confirm.png'), fullPage: true });
  await tabTo(page, 'start');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.querySelectorAll('#open-runs tr td').length > 3 && document.querySelector('#open-runs').textContent.includes('RUNNING'), null, { timeout: 15000 });
  await page.waitForTimeout(9000);
  await page.screenshot({ path: path.join(out, '03-running-chaos.png'), fullPage: true });
  await axe(page, 'chaos run in progress, 1440 px');

  // Stop all, by keyboard, through the confirmation dialog.
  await tabTo(page, 'stop-all', 'Shift+Tab', 120);
  await page.keyboard.press('Enter');
  await page.waitForSelector('dialog[open]');
  await page.screenshot({ path: path.join(out, '04-stop-all-dialog.png') });
  const dialogFocus = await page.evaluate(() => document.activeElement.id);
  record('stop-all dialog takes focus', ['stop-confirm', 'stop-cancel', 'stop-dialog'].includes(dialogFocus), dialogFocus);
  await tabTo(page, 'stop-confirm', 'Tab', 6);
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.querySelector('#open-runs').textContent.includes('No armed or running runs'), null, { timeout: 10000 });
  record('keyboard stop-all ended the run', true);
  await page.waitForTimeout(5500);
  await page.screenshot({ path: path.join(out, '05-after-stop-all.png'), fullPage: true });

  // Honest state: when the service stops answering, the page says unknown rather than showing stale values.
  await page.route('**/api/v1/control/state', (route) => route.abort());
  await page.waitForFunction(() => document.getElementById('confirmed').textContent.startsWith('UNKNOWN'), null, { timeout: 25000 });
  const readout = await page.textContent('#r-admitted');
  record('page shows UNKNOWN when the backend cannot confirm state', readout === 'unknown', `admitted readout: ${readout}`);
  await page.screenshot({ path: path.join(out, '06-unknown-state.png'), fullPage: true });
  await page.unroute('**/api/v1/control/state');

  // Mobile width.
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce', bypassCSP: true, storageState: await context.storageState() });
  const small = await mobile.newPage();
  await small.goto(`${BASE}/console/`);
  await small.waitForFunction(() => document.getElementById('confirmed').textContent.startsWith('confirmed'));
  await small.screenshot({ path: path.join(out, '07-mobile-390.png'), fullPage: true });
  await axe(small, 'idle, 390 px');
  const overflow = await small.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  record('no horizontal page overflow at 390 px', overflow <= 1, `${overflow}px`);

  // Static checks: no external resources, no animation.
  const external = await page.evaluate(() => [...document.querySelectorAll('script[src],link[href],img[src]')]
    .map((e) => e.src || e.href).filter((u) => !u.startsWith(location.origin)));
  record('page loads nothing from outside this service', external.length === 0, JSON.stringify(external));

  // The real CSP, as a browser without bypass sees it: the page must still work under it.
  const strict = await browser.newContext({ viewport: { width: 1440, height: 1000 }, storageState: await context.storageState() });
  const strictPage = await strict.newPage();
  const violations = [];
  strictPage.on('console', (m) => { if (/Content-Security-Policy|Content Security Policy/i.test(m.text())) { violations.push(m.text()); } });
  await strictPage.goto(`${BASE}/console/`);
  await strictPage.waitForFunction(() => document.getElementById('confirmed').textContent.startsWith('confirmed'));
  const markLoaded = await strictPage.evaluate(() => document.querySelector('.brand-mark').naturalWidth);
  record('page works under its own CSP (state confirmed, no CSP violations)', violations.length === 0, JSON.stringify(violations).slice(0, 200));
  record('brand mark loads', markLoaded === 400, `naturalWidth ${markLoaded}`);
} catch (error) {
  crashed = error;
  record('check script completed', false, String(error).slice(0, 300));
} finally {
  await browser.close();
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(results, null, 2));
  console.log('failures:', results.filter((r) => !r.ok).length);
  if (crashed) { process.exitCode = 1; }
}
