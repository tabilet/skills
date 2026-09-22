import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

class FakeNode {
  constructor(tag = '') { this.tagName = tag; this.children = []; this.attributes = {}; this.hidden = false; this.dataset = {}; this.listeners = {}; this._text = ''; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.children.push(child); return child; }
  get firstChild() { return this.children[0] || null; }
  removeChild(child) { this.children.splice(this.children.indexOf(child), 1); }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  removeAttribute(key) { delete this.attributes[key]; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  focus() { globalThis.document.activeElement = this; this.focused = true; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((child) => child instanceof FakeNode ? child.textContent : String(child)).join(''); }
}

globalThis.Node = FakeNode;
const ids = new Map();
for (const id of ['todo-validation', 'todo-content', 'detail-panel', 'backdrop', 'detail-title', 'detail-content', 'close-detail', 'notice', 'diagnostics']) ids.set(id, new FakeNode('div'));
ids.get('detail-panel').hidden = true;
globalThis.document = {
  activeElement: null, hidden: false,
  createElement: (tag) => new FakeNode(tag),
  createTextNode: (value) => { const node = new FakeNode('#text'); node._text = String(value); return node; },
  getElementById: (id) => ids.get(id) || new FakeNode('div'),
  querySelectorAll: () => [],
  addEventListener: () => {},
};
const historyCalls = [];
globalThis.location = { href: 'http://localhost:8000/?view=todo', search: '?view=todo' };
globalThis.history = {
  pushState: (_state, _title, url) => historyCalls.push(['push', String(url)]),
  replaceState: (_state, _title, url) => historyCalls.push(['replace', String(url)]),
};
globalThis.window = { addEventListener: () => {}, setInterval: () => 1, getSelection: () => ({ removeAllRanges() {}, addRange() {} }) };
Object.defineProperty(globalThis, 'navigator', { value: { clipboard: { writeText: async () => {} } }, configurable: true });
globalThis.fetch = async () => ({ ok: true, json: async () => ({}) });

vm.runInThisContext(readFileSync(new URL('../harness/explorer/explorer.js', import.meta.url), 'utf8'));
const client = window.TabiletExplorerTest;

test('polling detects the first generation or activity value', () => {
  assert.equal(client.activityChanged(null, null, 'generation-1', null), true);
  assert.equal(client.activityChanged('generation-1', null, 'generation-1', null), false);
});

test('degraded to-do keeps review evidence and its action visible', () => {
  client.renderTodo({
    validated: true, recommendations_available: false,
    resume: [], ready: [], waiting: [], blocked: [],
    needs_review: [{ milestone_id: 'M01', reason: 'closure review required', source: { path: 'tabilet/memory-bank/milestone.md', line: 3 } }],
  });
  const rendered = ids.get('todo-content').textContent;
  assert.match(rendered, /Needs review/);
  assert.match(rendered, /closure review required/);
  assert.match(rendered, /Review/);
  assert.match(ids.get('todo-validation').textContent, /recommendations withheld/i);
  client.renderTodo({ validated: true, recommendations_available: false, resume: [], ready: [], waiting: [], needs_review: [], blocked: [{ label: 'Blocked task', reason: 'operator needed' }] });
  assert.match(ids.get('todo-content').textContent, /Investigate/);
  client.renderTodo({ validated: true, recommendations_available: false,
    totals: { blocked: 1, needs_review: 1 }, pagination: {},
    resume: [], ready: [], waiting: [], needs_review: [],
    blocked: [{ label: 'Blocked task', reason: 'review exists on another page' }] });
  assert.doesNotMatch(ids.get('todo-content').textContent, /Investigate/);
  client.renderTodo({ validated: true, recommendations_available: true, resume: [], waiting: [], blocked: [], needs_review: [], ready: [{ label: '<script>unsafe</script>', reason: 'plain text' }] });
  assert.match(ids.get('todo-content').textContent, /<script>unsafe<\/script>/);
});

test('timeline renders captured requests and grouped goal children', () => {
  const entry = client.timelineEntry({
    run_id: 'parent', operation: 'goal', started_at: '2026-01-01T00:00:00Z',
    request_summary: 'deliver the goal', capture_fidelity: 'exact', result_summary: 'completed',
    children: [{ run_id: 'child', operation: 'next', started_at: '2026-01-01T00:01:00Z', request_summary: 'do one task', capture_fidelity: 'summarized' }],
  });
  assert.match(entry.textContent, /deliver the goal/);
  assert.match(entry.textContent, /do one task/);
  assert.match(entry.textContent, /Capture: exact/);
});

test('filter state is written to a bookmarkable URL', () => {
  client.updateUrl({ operation: 'next', cursor: 'opaque' }, false);
  assert.match(historyCalls.at(-1)[1], /operation=next/);
  assert.match(historyCalls.at(-1)[1], /cursor=opaque/);
});

test('detail URLs have one selection and source lines open around the target', () => {
  const values = client.detailUrl('document', 'tabilet/memory-bank/status-M01.md', { line: 20 });
  assert.equal(values.run, null);
  assert.equal(values.search, null);
  assert.equal(values.document, 'tabilet/memory-bank/status-M01.md');
  const preview = client.sourcePreview(Array.from({ length: 30 }, (_, index) => `line ${index + 1}`).join('\n'), 20);
  assert.match(preview.textContent, /> 20 \| line 20/);
  assert.doesNotMatch(preview.textContent, /line 1\n/);
  assert.match(client.sourcePreview('one\ntwo', 20).textContent, /outside the current 2-line document/);
});

test('detail close restores focus and clipboard failure keeps selectable prompt', async () => {
  const trigger = new FakeNode('button'); document.activeElement = trigger;
  client.openPanel('Details', new FakeNode('p'));
  assert.equal(ids.get('close-detail').focused, true);
  client.openPanel('Paged details', new FakeNode('p'));
  client.closePanel(false);
  assert.equal(trigger.focused, true);

  globalThis.fetch = async () => ({ ok: true, json: async () => ({ prompt: 'review prompt', validation_note: 'validated' }) });
  navigator.clipboard.writeText = async () => { throw new Error('denied'); };
  await client.prepareFollowUp('review', { milestone_id: 'M01', source: { path: 'tabilet/memory-bank/milestone.md', line: 3 } });
  const find = (node, label) => node.children.find((child) => child instanceof FakeNode && child.textContent === label) || node.children.map((child) => child instanceof FakeNode ? find(child, label) : null).find(Boolean);
  const copy = find(ids.get('detail-content'), 'Copy prompt');
  assert.ok(copy); await copy.listeners.click();
  assert.match(ids.get('notice').textContent, /Select the prompt text/);
});
