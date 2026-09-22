import { test, expect } from '@playwright/test';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline';

const root = resolve(import.meta.dirname, '../..');
const host = join(root, 'harness/tabilet_audit_host.py');
let temporary, project, database, server, baseURL;

function cli(args, input) {
  const result = spawnSync('python3', ['-B', host, '--audit-db', database, ...args], { input, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
  return JSON.parse(result.stdout);
}

async function launch() {
  server = spawn('python3', ['-B', host, '--audit-db', database, 'explorer', project, '--port', '0'], { stdio: ['ignore', 'pipe', 'pipe'] });
  const lines = createInterface({ input: server.stdout });
  return await new Promise((resolveURL, reject) => {
    const timer = setTimeout(() => reject(new Error('explorer did not start')), 10000);
    lines.once('line', (line) => { clearTimeout(timer); resolveURL(line.replace('Tabilet Explorer: ', '')); });
    server.once('exit', (code) => { clearTimeout(timer); reject(new Error(`explorer exited ${code}`)); });
  });
}

test.beforeAll(async () => {
  temporary = mkdtempSync(join(tmpdir(), 'tabilet-browser-'));
  project = join(temporary, 'project'); database = join(temporary, 'state/audit.sqlite3');
  mkdirSync(join(project, 'tabilet/memory-bank'), { recursive: true });
  writeFileSync(join(project, 'AGENTS.md'), '# Browser fixture\n');
  writeFileSync(join(project, 'tabilet/memory-bank/milestone.md'), '# Milestones\n\n## M01 - Browser explorer\n\nBrowser milestone summary.\n\n**Acceptance.** Browser paths work.\n');
  writeFileSync(join(project, 'tabilet/memory-bank/status-M01.md'), '# Status\n\n| ID | State | Notes |\n|---|---|---|\n| TASK-A | `[ ]` | First task |\n| TASK-B | `[!]` | Waiting for operator |\n');
  cli(['index', 'sync', project]);
  const run = cli(['audit', 'begin', project, 'propose', '--run-id', 'browser-propose', '--capture', 'relevant']);
  cli(['audit', 'message'], JSON.stringify({ run_id: run.run_id, message_id: 'browser-request', role: 'user', text: 'Please prepare the browser milestone', capture_source: 'host', fidelity: 'exact' }));
  cli(['audit', 'message'], JSON.stringify({ run_id: run.run_id, message_id: 'browser-output', role: 'assistant', text: 'Prepared M01 and its tasks', capture_source: 'host', fidelity: 'exact' }));
  cli(['audit', 'event'], JSON.stringify({ schema: 'tabilet.audit.event/v1', event_id: 'browser-event', run_id: run.run_id, workspace_id: run.workspace_id, operation: 'propose', event_type: 'task_observed', subject: { milestone_id: 'M01', task_label: 'TASK-A', status_path: 'tabilet/memory-bank/status-M01.md' }, details: { schema: 'tabilet.audit.details/v1', capture_source: 'host', fidelity: 'summarized' } }));
  cli(['audit', 'finish', run.run_id, 'completed']);
  baseURL = await launch();
});

test.afterAll(() => {
  if (server && server.exitCode == null) server.kill('SIGTERM');
  if (temporary) rmSync(temporary, { recursive: true, force: true });
});

test('desktop workflow preserves filters, history, detail, and follow-up evidence', async ({ page }) => {
  await page.goto(baseURL);
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
  await expect(page.getByText('Browser milestone summary.')).toBeVisible();

  await page.getByRole('link', { name: 'Timeline' }).click();
  await expect(page.getByText('Please prepare the browser milestone')).toBeVisible();
  await page.locator('#timeline-operation').selectOption('propose');
  await expect(page).toHaveURL(/operation=propose/);
  await page.getByRole('button', { name: 'Open propose details' }).click();
  await expect(page.getByRole('heading', { name: /Recorded then — request/ })).toBeVisible();
  await expect(page.locator('#detail-panel').getByText('Prepared M01 and its tasks')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Current state' })).toBeVisible();
  await expect(page.getByText(/milestone M01/)).toBeVisible();
  await page.goBack();
  await expect(page.locator('#detail-panel')).toBeHidden();

  await page.getByRole('link', { name: 'To-do' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'To-do' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'TASK-A', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'TASK-B', exact: true })).toBeVisible();
  await page.getByRole('button', { name: /continue TASK-A/i }).click();
  await expect(page.getByText(/Preserve the project's approval and commit policies/)).toBeVisible();
  await page.getByRole('button', { name: 'Select prompt' }).click();
});

test('narrow layout remains navigable and visible polling observes a new run', async ({ page }) => {
  await page.setViewportSize({ width: 600, height: 900 });
  await page.goto(`${baseURL}?view=timeline`);
  await expect(page.getByRole('heading', { name: 'Timeline' })).toBeVisible();
  const run = cli(['audit', 'begin', project, 'next', '--run-id', 'browser-next', '--capture', 'relevant']);
  cli(['audit', 'message'], JSON.stringify({ run_id: run.run_id, message_id: 'browser-next-request', role: 'user', text: 'Polling discovered this run', capture_source: 'host', fidelity: 'exact' }));
  cli(['audit', 'finish', run.run_id, 'completed']);
  await expect(page.getByText('Polling discovered this run')).toBeVisible({ timeout: 8000 });
  await expect(page.locator('#detail-panel')).toHaveCSS('width', '600px');
});
