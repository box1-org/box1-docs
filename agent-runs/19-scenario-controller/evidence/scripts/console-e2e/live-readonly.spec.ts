// Read-only live check of Demo control on the cluster: sign in, read /demo. Clicks nothing but the login.
import { expect, test } from '@playwright/test';
const SHOTS = '/private/tmp/claude-501/-Users-mike-Documents-ChatGPT-box1/ef05c591-4bf3-4f8d-9761-3715c9f2aabb/scratchpad/run19-work/console-shots';
test('live /demo shows the controller catalog for a signed-in operator', async ({ page }) => {
  const csp: string[] = [];
  page.on('console', (m) => { if (m.type() === 'error' && /Content-Security-Policy|CSP/i.test(m.text())) csp.push(m.text()); });
  await page.goto('https://operations-console-dev.apps.ocp.box1.org/demo');
  await page.locator('#username').fill(process.env.LIVE_USER!);
  await page.locator('#password').fill(process.env.LIVE_PASS!);
  await page.locator('#kc-login').click();
  await page.waitForURL((u) => u.host === 'operations-console-dev.apps.ocp.box1.org');
  await expect(page.getByRole('heading', { name: 'Demo control' })).toBeVisible();
  await page.waitForTimeout(3000);
  const me = await (await page.request.get('/api/v1/me')).json();
  console.log('me:', JSON.stringify({ roles: me.roles, scenarioRoles: me.scenarioRoles, environment: me.environment }));
  const cat = await (await page.request.get('/api/v1/scenarios')).json();
  console.log('catalog:', cat.items.length, 'items;', JSON.stringify(cat.sources));
  console.log('titles:', cat.items.map((s: { title: string; availability: string }) => `${s.title} [${s.availability}]`).join(' | '));
  const runs = await (await page.request.get('/api/v1/scenario-runs')).json();
  console.log('runs:', runs.items.length, JSON.stringify(runs.sources.map((s: { status: string }) => s.status)));
  for (const r of runs.items) console.log('run:', JSON.stringify({ id: r.scenarioRunId, scenario: r.scenario, status: r.status, detail: r.detail, actor: r.actor, startedAt: r.startedAt, reset: r.resetResult, resetDetail: r.resetDetail }));
  const audit = await (await page.request.get('/api/v1/scenario-audit')).json();
  for (const a of audit.items.slice(0, 15)) console.log('audit:', JSON.stringify({ seq: a.seq, at: a.occurredAt, action: a.action, outcome: a.outcome, actor: a.actor, detail: a.detail }));
  await page.screenshot({ path: `${SHOTS}/live-demo.png`, fullPage: true });
  console.log('start buttons visible:', await page.locator('[data-testid^="start-"]').count(), 'csp errors:', csp.length);
});
