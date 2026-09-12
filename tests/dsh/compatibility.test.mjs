import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { cp, lstat, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { Context } from '@deepseek-ai/cordis';
import SkillRegistry, { renderSkillContent } from '@deepseek-ai/dsh-skill';
import * as filesystem from '@deepseek-ai/dsh-skill-filesystem';
import * as skillTool from '@deepseek-ai/dsh-tool-skill';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../..');
const names = ['archive', 'goal', 'init', 'next', 'reconcile', 'upgrade'].map(s => `memory-bank-${s}`);
const guide = await readFile(join(repo, 'docs/DSH.md'), 'utf8');
const commands = Object.fromEntries(['install', 'update', 'remove'].map(action => {
  const match = guide.match(new RegExp(`<!-- dsh-${action} -->\n\x60\x60\x60bash\n([\\s\\S]*?)\n\x60\x60\x60`));
  assert.ok(match, `missing documented ${action} command`);
  return [action, match[1]];
}));

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'memory-bank-dsh-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const project = join(root, 'project');
  const dshHome = join(root, 'dsh');
  const agentsHome = join(root, 'agents');
  for (const dir of [project, dshHome, agentsHome]) await mkdir(dir);
  // Deliberately no inherited environment, credentials, personal roots, or remotes.
  const env = {
    PATH: process.env.PATH,
    DSH_HOME: dshHome,
    DSH_AGENTS_HOME: agentsHome,
    DSH_TELEMETRY_DISABLED: '1',
    DEEPSEEK_BASE_URL: 'http://127.0.0.1:9',
    MEMORY_BANK_CHECKOUT: repo,
    NO_COLOR: '1',
  };
  const run = (action, extra = {}) => spawnSync('bash', ['-c', commands[action]], {
    cwd: project, env: { ...env, ...extra }, encoding: 'utf8', timeout: 15_000,
  });
  return { root, project, dshHome, agentsHome, env, run };
}

function success(result) {
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stdout + result.stderr);
}

async function registry(t, f, config = {}) {
  const ctx = new Context();
  const service = await ctx.plugin(SkillRegistry);
  const provider = await ctx.plugin(filesystem, {
    dshHome: f.dshHome, agentsHome: f.agentsHome,
    bundledSkillDir: join(f.root, 'absent-bundled'), watch: false, ...config,
  });
  t.after(async () => { await provider.dispose(); await service.dispose(); });
  return ctx.skills;
}

async function tree(path) {
  const entries = {};
  for (const entry of await readdir(path, { withFileTypes: true })) {
    const full = join(path, entry.name);
    assert.ok(!entry.isSymbolicLink(), `unexpected symlink ${full}`);
    entries[entry.name] = entry.isDirectory() ? await tree(full) : (await readFile(full)).toString('base64');
  }
  return entries;
}

test('locked runtime and every installed DSH component are rc.1', async () => {
  assert.equal(process.versions.node.split('.')[0], '24');
  const lock = JSON.parse(await readFile(join(here, 'package-lock.json'), 'utf8'));
  let count = 0;
  for (const [path, info] of Object.entries(lock.packages)) {
    if (!/^@deepseek-ai\/dsh(?:-|$)/.test(path.split('node_modules/').at(-1))) continue;
    assert.equal(info.version, '0.1.5-rc.1', path);
    const actual = JSON.parse(await readFile(join(here, path, 'package.json'), 'utf8'));
    assert.equal(actual.version, info.version, path);
    count++;
  }
  assert.ok(count > 5);
  assert.equal(execFileSync(process.execPath, [join(here, 'node_modules/@deepseek-ai/dsh/lib/bin.js'), '--version'],
    { encoding: 'utf8' }).trim(), '0.1.5-rc.1');
});

test('actual loader discovers all six complete bundles, policies, and resources', async t => {
  const f = await fixture(t);
  success(f.run('install'));
  const skills = await registry(t, f);
  const catalog = await skills.list({ cwd: f.project });
  assert.deepEqual(catalog.map(s => s.name), names);
  for (const name of names) {
    const skill = await skills.get(name, { cwd: f.project });
    const source = await readFile(join(repo, 'skills', name, 'SKILL.md'), 'utf8');
    const body = source.replace(/^---\n[\s\S]*?\n---\n/, '').trim();
    assert.equal(skill.content, body);
    assert.equal(skill.description, source.match(/^description: (.+)$/m)[1]);
    assert.equal(skill.source, 'user-dsh');
    assert.deepEqual(skill.invocation, { modelInvocable: true, userInvocable: true });
    assert.deepEqual(skill.resourceBase, { kind: 'directory', path: join(f.dshHome, 'skills', name) });
    const rendered = renderSkillContent(skill);
    assert.ok(rendered.includes(body));
    assert.ok(rendered.includes(skill.resourceBase.path));
    for (const [, resource] of body.matchAll(/\]\((references\/[^)]+)\)/g)) {
      assert.deepEqual(await readFile(join(skill.resourceBase.path, resource)),
        await readFile(join(repo, 'skills', name, resource)));
    }
    assert.deepEqual(await tree(skill.resourceBase.path), await tree(join(repo, 'skills', name)));
  }
  assert.deepEqual(await readFile(join(f.dshHome, 'skills/memory-bank-init/GOAL.md')),
    await readFile(join(repo, 'GOAL.md')));
  assert.deepEqual(await tree(join(f.dshHome, 'skills/memory-bank-upgrade/assets/template')),
    await tree(join(repo, 'template')));
});

test('updating a five-bundle installation adds upgrade and preserves all old bundles in backup', async t => {
  const f = await fixture(t); success(f.run('install'));
  await rm(join(f.dshHome, 'skills/memory-bank-upgrade'), { recursive: true });
  await writeFile(join(f.dshHome, 'skills/memory-bank-init/local-note.md'), 'keep this');
  const old = await tree(join(f.dshHome, 'skills'));
  const result = f.run('update'); success(result);
  const backup = result.stdout.trim().replace('Bundle backup: ', '');
  assert.deepEqual(await tree(backup), old);
  const catalog = await (await registry(t, f)).list({ cwd: f.project });
  assert.deepEqual(catalog.map(s => s.name), names);
});

test('DSH slash injection keeps explicit request text separate from the complete body', async t => {
  const f = await fixture(t);
  success(f.run('install'));
  const skills = await registry(t, f);
  const handlers = [];
  let tool;
  // Only the consumer's event/tool boundaries are fixtures; provider, registry,
  // body renderer, slash parser, and loader implementation are DSH's real code.
  skillTool.apply({ skills, tools: { register(value) { tool = value; } },
    on(event, handler) { if (event === 'agent/pre-step') handlers.push(handler); } });
  const request = '/memory-bank-goal M02 -> M03. COMMIT_POLICY: none. EXTERNAL_MUTATIONS: none.';
  const messages = [{ role: 'user', source: { kind: 'user' },
    content: [{ type: 'text', text: request }] }];
  const agent = { session: { header: { cwd: f.project } } };
  const signal = new AbortController().signal;
  const result = await handlers[0]({ agent, messages, signal }, async () => ({ kind: 'continue', messages }));
  assert.equal(result.messages.length, 2);
  assert.equal(result.messages[0].content[0].text, request);
  assert.equal(result.messages[1].source.name, 'memory-bank-goal');
  const loaded = await tool.execute({ name: 'memory-bank-goal' }, { agent, signal });
  assert.equal(result.messages[1].content[0].text, renderSkillContent(loaded));
  assert.ok(!loaded.content.includes('$ARGUMENTS'));
});

test('repeat install, backed-up update, and removal preserve unrelated content', async t => {
  const f = await fixture(t);
  await mkdir(join(f.dshHome, 'skills/unrelated'), { recursive: true });
  await writeFile(join(f.dshHome, 'skills/unrelated/notes.txt'), 'user content');
  await writeFile(join(f.dshHome, '.credentials.yaml'), 'unrelated credential sentinel');
  await mkdir(join(f.project, 'memory-bank'));
  await writeFile(join(f.project, 'memory-bank/lessons.md'), 'project memory');
  success(f.run('install'));
  const initial = await tree(join(f.dshHome, 'skills'));
  const initialStat = await lstat(join(f.dshHome, 'skills/memory-bank-init/SKILL.md'));
  success(f.run('install'));
  assert.deepEqual(await tree(join(f.dshHome, 'skills')), initial);
  assert.equal((await lstat(join(f.dshHome, 'skills/memory-bank-init/SKILL.md'))).mtimeMs, initialStat.mtimeMs);
  await writeFile(join(f.dshHome, 'skills/memory-bank-init/old-resource.md'), 'local addition');
  const changed = await tree(join(f.dshHome, 'skills/memory-bank-init'));
  assert.notEqual(f.run('install').status, 0);
  const updated = f.run('update'); success(updated);
  const backup = updated.stdout.trim().replace('Bundle backup: ', '');
  assert.deepEqual(await tree(join(backup, 'memory-bank-init')), changed);
  assert.deepEqual(await tree(join(f.dshHome, 'skills/memory-bank-init')),
    await tree(join(repo, 'skills/memory-bank-init')));
  success(f.run('remove'));
  success(f.run('remove'));
  assert.deepEqual(await tree(join(f.dshHome, 'skills')), { unrelated: initial.unrelated });
  assert.equal(await readFile(join(f.dshHome, '.credentials.yaml'), 'utf8'), 'unrelated credential sentinel');
  assert.equal(await readFile(join(f.project, 'memory-bank/lessons.md'), 'utf8'), 'project memory');
  assert.deepEqual(await (await registry(t, f)).list({ cwd: f.project }), []);
});

test('collision preflight and symlink rejection preserve every existing destination', async t => {
  const f = await fixture(t);
  const outside = join(f.root, 'outside'); await mkdir(outside);
  await writeFile(join(outside, 'SKILL.md'), 'user instructions');
  await mkdir(join(f.dshHome, 'skills'));
  await symlink(outside, join(f.dshHome, 'skills/memory-bank-goal'));
  for (const action of ['install', 'update', 'remove']) assert.notEqual(f.run(action).status, 0);
  assert.equal(await readFile(join(outside, 'SKILL.md'), 'utf8'), 'user instructions');
  assert.deepEqual(await readdir(join(f.dshHome, 'skills')), ['memory-bank-goal']);
});

test('interrupted update retains complete original bundles for recovery', async t => {
  const f = await fixture(t); success(f.run('install'));
  await writeFile(join(f.dshHome, 'skills/memory-bank-next/local-note.md'), 'keep this edit');
  const original = await tree(join(f.dshHome, 'skills'));
  const bin = join(f.root, 'bin'); await mkdir(bin);
  // Fail the copy phase after the documented move-to-backup phase.
  await writeFile(join(bin, 'cp'), '#!/bin/sh\nexit 17\n', { mode: 0o755 });
  const result = f.run('update', { PATH: `${bin}:${f.env.PATH}` });
  assert.equal(result.status, 17);
  const backup = result.stdout.trim().replace('Bundle backup: ', '');
  assert.deepEqual(await tree(backup), original);
  assert.deepEqual(await readdir(join(f.dshHome, 'skills')), []);
  // Restoring from the announced backup recovers user edits as well as bodies.
  await cp(backup, join(f.dshHome, 'skills'), { recursive: true });
  assert.deepEqual(await tree(join(f.dshHome, 'skills')), original);
});

test('update and removal refuse an unrelated bundle before moving any content', async t => {
  const f = await fixture(t); success(f.run('install'));
  const path = join(f.dshHome, 'skills/memory-bank-goal/SKILL.md');
  await writeFile(path, '---\nname: unrelated-command\n---\nUser-owned instructions.\n');
  const original = await tree(f.dshHome);
  for (const action of ['update', 'remove']) {
    assert.notEqual(f.run(action).status, 0);
    assert.deepEqual(await tree(f.dshHome), original);
  }
});

test('incomplete source bundles stop installation and update before any changes', async t => {
  const f = await fixture(t); success(f.run('install'));
  const candidate = join(f.root, 'candidate');
  await mkdir(candidate);
  await cp(join(repo, 'skills'), join(candidate, 'skills'), { recursive: true });
  const original = await tree(f.dshHome);
  for (const resource of ['memory-bank-init/GOAL.md', 'memory-bank-archive/references/write-contract.md',
    'memory-bank-goal/references/runtime-help.md',
    'memory-bank-upgrade/assets/template/memory-bank/milestone.md']) {
    const path = join(candidate, 'skills', resource);
    const content = await readFile(path);
    await rm(path);
    assert.notEqual(f.run('update', { MEMORY_BANK_CHECKOUT: candidate }).status, 0);
    assert.deepEqual(await tree(f.dshHome), original);
    const emptyRoot = join(f.root, 'fresh-skills');
    assert.notEqual(f.run('install', { MEMORY_BANK_CHECKOUT: candidate, DSH_SKILL_ROOT: emptyRoot }).status, 0);
    await assert.rejects(lstat(emptyRoot), { code: 'ENOENT' });
    await writeFile(path, content);
  }
});

test('duplicate roots obey DSH precedence and removal reveals lower-priority copies', async t => {
  const f = await fixture(t);
  const shared = join(f.agentsHome, 'skills');
  success(f.run('install', { DSH_SKILL_ROOT: shared }));
  success(f.run('install'));
  execFileSync('git', ['init', '-q'], { cwd: f.project, env: f.env });
  const custom = join(f.root, 'custom');
  const projectAgents = join(f.project, '.agents/skills');
  const projectDsh = join(f.project, '.dsh/skills');
  const nested = join(f.project, 'src'); await mkdir(nested);
  for (const root of [custom, projectAgents, projectDsh]) {
    await mkdir(root, { recursive: true });
    await cp(join(repo, 'skills/memory-bank-goal'), join(root, 'memory-bank-goal'), { recursive: true });
  }
  // Recreate the registry after each edit to model the documented fresh session.
  for (const [source, root] of [['project-dsh', projectDsh], ['project-agents', projectAgents],
    ['custom', custom], ['user-dsh', join(f.dshHome, 'skills')], ['user-agents', shared]]) {
    const skills = await registry(t, f, { customSkillDirs: [custom] });
    const skill = await skills.get('memory-bank-goal', { cwd: nested });
    assert.equal(skill.source, source);
    assert.equal(skill.resourceBase.path, join(root, 'memory-bank-goal'));
    await rm(join(root, 'memory-bank-goal'), { recursive: true });
  }
});

test('missing resource or changed body stays observable rather than fabricated', async t => {
  const f = await fixture(t); success(f.run('install'));
  const skills = await registry(t, f);
  const first = await skills.get('memory-bank-init', { cwd: f.project });
  const contract = join(first.resourceBase.path, 'references/write-contract.md');
  await rm(contract);
  const stillLoaded = await skills.get('memory-bank-init', { cwd: f.project });
  assert.equal(stillLoaded.content, first.content);
  await assert.rejects(readFile(contract), { code: 'ENOENT' });
  const path = join(first.resourceBase.path, 'SKILL.md');
  await writeFile(path, (await readFile(path, 'utf8')) + '\nUpdated body.\n');
  assert.ok((await skills.get('memory-bank-init', { cwd: f.project })).content.endsWith('Updated body.'));
});

test('Web and headless compose the actual filesystem skill loader without credentials', async t => {
  const f = await fixture(t);
  const cli = join(here, 'node_modules/@deepseek-ai/dsh/lib/bin.js');
  for (const profile of ['web', 'headless']) {
    const result = spawnSync(process.execPath, [cli, '--profile', profile, '--dump-config'], {
      cwd: f.project, env: f.env, encoding: 'utf8', timeout: 30_000, maxBuffer: 4_000_000,
    });
    success(result);
    for (const component of ['dsh-skill-filesystem', 'dsh-tool-skill', 'dsh-agent-instructions']) {
      assert.ok(result.stdout.includes(component), `${profile} missing ${component}`);
    }
  }
});

test('headless without a model credential fails without changing the project', async t => {
  const f = await fixture(t);
  success(f.run('install'));
  await writeFile(join(f.project, 'AGENTS.md'), 'Preserve this instruction. Do not create files without approval.\n');
  const before = await tree(f.project);
  const cli = join(here, 'node_modules/@deepseek-ai/dsh/lib/bin.js');
  const result = spawnSync(process.execPath, [cli, '--profile', 'headless',
    'Use memory-bank-init. Stop if a required answer or capability is unavailable.'], {
    cwd: f.project, env: f.env, encoding: 'utf8', timeout: 30_000, maxBuffer: 4_000_000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.match(result.stdout + result.stderr, /MISSING_CREDENTIAL/);
  assert.deepEqual(await tree(f.project), before);
});
