// Run 19 local end-to-end: the operations console's Demo page against the REAL scenario controller, order,
// inventory and fulfillment services, ERP harness and Keycloak (stack.sh up; console-client.sh; stack.sh console).
// Firefox only. Test users' password is read from the run's scratch WORK directory, never printed.
import { expect, test, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const WORK = '/private/tmp/claude-501/-Users-mike-Documents-ChatGPT-box1/ef05c591-4bf3-4f8d-9761-3715c9f2aabb/scratchpad/run19-work';
const SHOTS = process.env.SHOTS_DIR || `${WORK}/console-shots`;
const password = () => readFileSync(`${WORK}/user-password`, 'utf8').trim();

/** Every CSP violation or uncaught page error fails the test (as in the console's own e2e). */
function watch(page: Page) {
  const errors: string[] = [];
  page.on('console', (m) => { if (m.type() === 'error' && /Content-Security-Policy|CSP/i.test(m.text())) errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));
  return errors;
}

async function signIn(page: Page, user: string) {
  await page.goto('/demo');
  await page.locator('#username').fill(user);
  await page.locator('#password').fill(password());
  await page.locator('#kc-login').click();
  await page.waitForURL((u) => u.port === '39085');
  await expect(page.locator('.topbar .user')).toContainText(user);
  await expect(page.getByRole('heading', { name: 'Demo control' })).toBeVisible();
}

test('an operator seeds, runs The Trouble with Tribbles to VERIFIED, and finds it in the audit under their name', async ({ page }) => {
  const errors = watch(page);
  await signIn(page, 'operator');
  const cards = page.locator('li.scenario');
  await expect(cards).toHaveCount(10);
  await expect(page.locator('li.scenario[data-availability="AVAILABLE"]')).toHaveCount(5);
  await expect(page.locator('li.scenario[data-scenario="inventory-contention"] h3')).toHaveText('The Trouble with Tribbles');
  await expect(page.locator('li.scenario[data-scenario="red-alert"] [data-testid="not-yet-possible"]')).toBeVisible();
  await expect(page.getByTestId('needs-scenario-role')).toHaveCount(0);

  await page.getByTestId('seed').click();
  await expect(page.getByTestId('seeded')).toContainText('Fixtures seeded');
  await page.screenshot({ path: `${SHOTS}/01-operator-catalog.png`, fullPage: true });

  await page.getByTestId('start-inventory-contention').click();
  await expect(page.getByTestId('confirm-start')).toContainText('The Trouble with Tribbles');
  await page.getByTestId('confirm-start-button').click();
  await expect(page.getByTestId('active-run')).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/02-active-run.png`, fullPage: true });

  // The run ends (verified and reset) and leaves the active panel; the newest row is this run.
  await expect(page.getByTestId('active-run')).toHaveCount(0, { timeout: 120_000 });
  const newest = page.locator('[data-testid="runs"] tbody tr').first();
  await expect(newest).toContainText('The Trouble with Tribbles');
  await expect(newest.locator('[data-run-status]')).toHaveAttribute('data-run-status', 'VERIFIED');
  await expect(newest).toContainText('operator');
  await page.screenshot({ path: `${SHOTS}/03-verified.png`, fullPage: true });

  await page.locator('summary', { hasText: 'Audit trail' }).click();
  const audit = page.getByTestId('audit');
  await expect(audit).toContainText('START');
  await expect(audit).toContainText('operator');
  expect(errors).toEqual([]);
});

test('a guided step the controller cannot observe is confirmed from the console and recorded', async ({ page }) => {
  // erp-crash-after-commit asks the operator to confirm crash-armed before it places its order. Confirming without
  // arming the crash is allowed by the controller (it is the person's attestation); the run then cannot observe the
  // crash, so this test stops the run after the confirmation is recorded, and checks the reset.
  const errors = watch(page);
  await signIn(page, 'operator');
  await page.getByTestId('start-erp-crash-after-commit').click();
  await page.getByTestId('confirm-start-button').click();
  const step = page.getByTestId('operator-step');
  await expect(step).toContainText('arm the one-shot crash', { timeout: 30_000 });
  await page.screenshot({ path: `${SHOTS}/04-operator-step.png`, fullPage: true });
  await page.getByTestId('confirm-step').click();
  // Once confirmed, the run moves on (it places its order, then waits for crash-observed): the armed step is gone.
  await expect(page.getByTestId('active-run')).not.toContainText('arm the one-shot crash', { timeout: 30_000 });
  await page.getByTestId('stop').click();
  await expect(page.getByTestId('active-run')).toHaveCount(0, { timeout: 60_000 });
  const newest = page.locator('[data-testid="runs"] tbody tr').first();
  await expect(newest.locator('[data-run-status]')).toHaveAttribute('data-run-status', 'STOPPED');
  await page.locator('summary', { hasText: 'Audit trail' }).click();
  await expect(page.getByTestId('audit')).toContainText('CONFIRM');
  expect(errors).toEqual([]);
});

test('a viewer sees the catalog and runs but no actions', async ({ page }) => {
  const errors = watch(page);
  await signIn(page, 'viewer');
  await expect(page.locator('li.scenario')).toHaveCount(10);
  await expect(page.getByTestId('seed')).toHaveCount(0);
  await expect(page.locator('[data-testid^="start-"]')).toHaveCount(0);
  await expect(page.locator('[data-testid="runs"] tbody tr').first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/05-viewer.png`, fullPage: true });
  expect(errors).toEqual([]);
});

test('a console operator without a scenario role is told so, and the controller itself refuses a forced start', async ({ page }) => {
  const errors = watch(page);
  await signIn(page, 'norole');
  await expect(page.getByTestId('needs-scenario-role')).toBeVisible();
  await expect(page.locator('[data-testid^="start-"]')).toHaveCount(0);
  // The catalog read itself is refused by the controller: the page says why instead of showing an empty list.
  await expect(page.getByTestId('sources-banner').first()).toContainText('scenario-viewer or scenario-operator');
  await page.screenshot({ path: `${SHOTS}/06-norole.png`, fullPage: true });
  // Bypass the page: the console passes the call on, and the controller refuses it for this person.
  const r = await page.request.post('/api/v1/scenarios/inventory-contention/start', {
    headers: { 'X-Box1-Console': '1', 'Content-Type': 'application/json' }, data: {},
  });
  expect(r.status()).toBe(403);
  expect((await r.json()).code).toBe('SCENARIO_ROLE_REQUIRED');
  expect(errors).toEqual([]);
});
