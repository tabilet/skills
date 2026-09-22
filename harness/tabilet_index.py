"""Disposable current Markdown projection. No project writes or task selection."""
from __future__ import annotations

import functools
import hashlib
import importlib.machinery
import importlib.util
import contextlib
import pathlib
import os
import re
import sqlite3
import stat
import subprocess
import uuid

from tabilet_audit import AuditError, atomic, canonical_json, ensure_workspace, records, strict_json_loads, utc_now, pagination

MAX_BYTES = 4 * 1024 * 1024
STATUS = re.compile(r'status-([A-Z](?:0[1-9]|[1-9][0-9]))\.md$')
ARCHIVE = re.compile(r'archive-([A-Z](?:0[1-9]|[1-9][0-9]))\.md$')
EVOLUTION = re.compile(r'(prompt|result)-v([1-9][0-9]*)\.md$')
TABLES = ('index_documents','index_sections','index_milestones','index_tasks','index_relationships','index_search')
EXPLORER_TABLES = ('index_milestone_projection','index_task_dependencies')
DERIVED_TABLES = TABLES + EXPLORER_TABLES


@functools.lru_cache(maxsize=1)
def parser():
    """Use the shipped runner's pure parsers without invoking its main loop."""
    path = pathlib.Path(__file__).with_name('tackle-memory-bank-api-loop')
    loader = importlib.machinery.SourceFileLoader('_tabilet_markdown_parser', str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def layout_check(root):
    legacy = ('GOAL.md','memory-bank','evolution','docs/history')
    if any((root/name).exists() or (root/name).is_symlink() for name in legacy) or list((root/'docs').glob('archive-[A-Z][0-9][0-9].md')):
        raise AuditError('v1.5.0 or mixed layout: preview and apply migrate-v1.5-to-v2.py PROJECT first')


def no_symlinks(root, path):
    if not path.is_relative_to(root):
        raise AuditError('source escapes project root')
    for item in (path, *path.parents):
        if item == root:
            break
        if item.is_symlink():
            raise AuditError(f'symlink source rejected: {item.relative_to(root)}')


def inventory(root):
    layout_check(root)
    found = {}
    fixed = {
        'tabilet/GOAL.md':'goal_protocol',
        **{f'tabilet/memory-bank/{name}.md':name for name in ('product','architecture','tech-stack','lessons','milestone')},
        'tabilet/docs/history/index.md':'history_index',
        'tabilet/docs/history/knowledge.md':'knowledge_history',
    }
    for name,kind in fixed.items():
        path=root/name
        no_symlinks(root,path)
        if path.exists():found[name]=kind
    for directory,pattern,validator,kind in (
        ('tabilet/memory-bank','status-*.md',STATUS,'active_status'),
        ('tabilet/docs/history','status-*.md',STATUS,'history_status'),
        ('tabilet/docs','archive-*.md',ARCHIVE,'context_archive'),
        ('tabilet/evolution','*.md',EVOLUTION,'evolution'),
    ):
        base=root/directory
        no_symlinks(root,base)
        for path in sorted(base.glob(pattern)):
            no_symlinks(root,path)
            match=validator.fullmatch(path.name)
            if not match:
                if kind=='evolution' and not path.name.startswith(('prompt-v','result-v')):continue
                raise AuditError(f'invalid declared filename: {path.relative_to(root)}')
            found[str(path.relative_to(root))]=('evolution_'+match[1]) if kind=='evolution' else kind
    if not found:
        raise AuditError('no declared v2 Markdown sources found')
    return dict(sorted(found.items()))


def signature(info):
    return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns


def read_document(root, relative):
    path=root/relative
    no_symlinks(root,path)
    before=path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_BYTES:
        raise AuditError(f'not a bounded regular Markdown file: {relative}')
    descriptor=os.open(path,os.O_RDONLY | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_NONBLOCK',0))
    with os.fdopen(descriptor,'rb') as source:
        opened=os.fstat(source.fileno())
        if not stat.S_ISREG(opened.st_mode) or signature(opened)!=signature(before):
            raise AuditError(f'source changed before read: {relative}')
        data=source.read(MAX_BYTES+1)
    after=path.stat()
    no_symlinks(root,path)
    if len(data)>MAX_BYTES or signature(before)!=signature(after):
        raise AuditError(f'source changed during read: {relative}')
    return data.decode('utf-8'),hashlib.sha256(data).hexdigest(),after


def git_context(root):
    def git(*args):
        try:
            proc=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True,timeout=10)
            return proc.stdout.strip() if proc.returncode==0 else None
        except (OSError,subprocess.TimeoutExpired):return None
    return {'git_head':git('rev-parse','HEAD'),'branch':git('symbolic-ref','--short','-q','HEAD')}


def headings(text):
    lines=text.splitlines()
    found=[]
    used={}
    for line,value in parser().unfenced_lines(text):
        match=re.match(r'^(#{1,6})\s+(.+?)\s*#*$',value)
        if not match:continue
        title=match[2]
        explicit=re.search(r'\{#([^}]+)\}',title)
        anchor=explicit[1] if explicit else re.sub(r'[^\w -]','',title.lower()).replace(' ','-')
        occurrence=used.get(anchor,0);used[anchor]=occurrence+1
        if occurrence:anchor+=f'-{occurrence}'
        found.append((line,len(match[1]),title,anchor))
    for i,(line,level,title,anchor) in enumerate(found):
        end=next((r[0]-1 for r in found[i+1:] if r[1]<=level),len(lines))
        yield {'line':line,'end_line':end,'heading':title,'anchor':anchor,'text':'\n'.join(lines[line-1:end])}


def parse_document(path,kind,text,digest):
    p=parser()
    parsed={table:[] for table in DERIVED_TABLES if table!='index_documents'}
    parsed['index_sections']=list(headings(text))
    parsed['index_search'].append(dict(line=1,kind=kind,milestone_id=None,state=None,text=text))
    for section in parsed['index_sections']:
        match = re.match(r'([A-Z](?:0[1-9]|[1-9][0-9]))(?:\s|$)', section['heading'])
        parsed['index_search'].append(dict(line=section['line'],kind='section',milestone_id=match[1] if match else None,state=None,text=section['text']))
    identity=None
    status=text
    offset=0
    specification_offset=0
    if kind in ('active_status','history_status'):
        identity=STATUS.fullmatch(pathlib.Path(path).name)[1]
        meta={}
        specification=None
        if kind=='history_status':
            record=p.retired_record(text,pathlib.Path(path).name)
            meta=record['metadata'];status=record['status'];specification=record['specification']
            envelope = dict((value, line) for line, value in p.unfenced_lines(text)
                            if value in ('## Status record', '## Milestone specification'))
            source_lines = text.splitlines(keepends=True)
            def body_offset(heading):
                start = envelope[heading]
                return next(n + 1 for n in range(start, len(source_lines))
                            if re.fullmatch(r'(?:`{3,}|~{3,})markdown', source_lines[n].strip()))
            offset = body_offset('## Status record')
            specification_offset = body_offset('## Milestone specification')
        problems=p.status_marker_problems(status)
        rows=p.status_rows(status)
        if problems or not rows:raise AuditError(f'{path}: invalid task table: {problems or "no rows"}')
        parsed['index_milestones'].append(dict(milestone_id=identity,lifecycle='retired' if meta else 'active',
            line=1,specification=specification,outcome=meta.get('Outcome'),review=meta.get('Review')))
        parsed['index_milestone_projection'].append(dict(
            milestone_id=identity, display_order=None, summary=None,
            acceptance_text=specification, review_evidence=meta.get('Review'),
            closure_state=meta.get('Outcome'), source_line=1, source_sha256=digest,
        ))
        all_rows=p.table_rows(status)
        for row in rows:
            headers=[]
            row_index=next((i for i,item in enumerate(all_rows) if item['line']==row['line']), None)
            if row_index is not None:
                table_start=row_index
                while (table_start > 0
                       and all_rows[table_start - 1]['line'] == all_rows[table_start]['line'] - 1):
                    table_start -= 1
                if table_start + 1 <= row_index:
                    header=all_rows[table_start]
                    separator=all_rows[table_start + 1]
                else:
                    header=separator=None
                if (header and separator
                        and separator['line'] == header['line'] + 1
                        and all(re.fullmatch(r':?-+:?', cell) for cell in separator['cells'])):
                    headers=header['cells']
            explicit=None
            for i,header in enumerate(headers):
                if header.lower() in ('id','task id') and i<len(row['cells']):explicit=row['cells'][i]
            parsed['index_tasks'].append(dict(sha256=digest,line=row['line']+offset,milestone_id=identity,
                label=row['item'],state=row['state'],notes=' | '.join(row['cells'][2:]),explicit_id=explicit))
            parsed['index_search'].append(dict(line=row['line']+offset,kind='task',milestone_id=identity,
                state=row['state'],text=' | '.join(row['cells'])))
            # Explicit task IDs are scoped by their milestone. Keep that scope
            # in the disposable dependency key so two milestones may both use
            # conventional IDs such as T01 without colliding in SQLite.
            task_key=f'{identity}/{explicit}' if explicit else f'{path}#{row["line"]+offset}'
            notes=' | '.join(row['cells'][2:])
            for target,reason in task_dependencies(notes):
                target_milestone, target_id = dependency_target(target)
                parsed['index_task_dependencies'].append(dict(
                    source_key=task_key, source_sha256=digest, source_line=row['line']+offset,
                    milestone_id=identity, target_key=target,
                    target_milestone_id=target_milestone, target_explicit_id=target_id,
                    relationship='depends_on', reason=reason,
                ))
    if kind == 'milestone':
        order=0
        for section in parsed['index_sections']:
            match=re.match(r'([A-Z](?:0[1-9]|[1-9][0-9]))(?:\s|$)',section['heading'])
            if not match:continue
            order += 1
            body=section['text'].splitlines()[1:]
            summary=next((line.strip() for line in body if line.strip() and not line.lstrip().startswith('#')), None)
            acceptance=next((line.strip() for line in body if re.match(r'\*\*(?:Acceptance|Accept)\b',line,re.I)), None)
            parsed['index_milestone_projection'].append(dict(
                milestone_id=match[1], display_order=order, summary=summary,
                acceptance_text=acceptance, review_evidence=None, closure_state=None,
                source_line=section['line'], source_sha256=digest,
            ))
    relation_lines = list(p.unfenced_lines(text))
    if kind == 'history_status':
        relation_lines = [(n + specification_offset, value) for n, value in p.unfenced_lines(specification)]
        relation_lines += [(n + offset, value) for n, value in p.unfenced_lines(status)]
    current_identity=identity
    for line,value in relation_lines:
        section_id=re.match(r'## ([A-Z][0-9]{2})(?:\s|$)',value)
        if kind=='milestone' and section_id:current_identity=section_id[1]
        dependency=re.search(r'(?:\*\*)?(?:Dependencies|Depends on|Successor|Supersedes)[.:]*(?:\*\*)?\s*:?\s*(.+)',value,re.I)
        if dependency:
            relation='depends_on' if dependency[0].lower().startswith(('depend','**depend')) else 'supersedes' if 'supersedes' in dependency[0].lower() else 'successor'
            source=('milestone:'+current_identity) if current_identity else path
            if kind=='context_archive':source='archive:'+ARCHIVE.fullmatch(pathlib.Path(path).name)[1]
            for target in dict.fromkeys(re.findall(r'\b[A-Z](?:0[1-9]|[1-9][0-9])\b',dependency[1])):
                parsed['index_relationships'].append(dict(line=line,source=source,relation=relation,target=('archive:' if kind=='context_archive' else 'milestone:')+target))
    if kind.startswith('evolution_'):
        match=EVOLUTION.fullmatch(pathlib.Path(path).name)
        counterpart = 'result' if match[1] == 'prompt' else 'prompt'
        parsed['index_relationships'].append(dict(line=1,source=path,relation='evolution_pair',target=f'tabilet/evolution/{counterpart}-v{match[2]}.md'))
    return parsed


def dependency_target(value):
    """Return an explicit target ID without treating ordinary prose as a relation."""
    value=value.strip().strip('`[]()')
    match=re.fullmatch(r'([A-Z](?:0[1-9]|[1-9][0-9]))/([A-Za-z0-9][A-Za-z0-9_.:-]*)',value)
    if match:return match[1],match[2]
    return None,value


def task_dependencies(notes):
    """Read only labelled dependency clauses from a task row's notes."""
    found=[]
    for match in re.finditer(r'(?i)\b(?:depends on|dependency|blocked by)\s*:\s*([^|;]+)',notes):
        reason=match.group(0).split(':',1)[0].strip().lower()
        values=re.findall(r'\[?([A-Z](?:0[1-9]|[1-9][0-9])/[A-Za-z0-9][A-Za-z0-9_.:-]*|[A-Za-z][A-Za-z0-9_.:-]*)\]?',match.group(1))
        found.extend((value,reason) for value in dict.fromkeys(values))
    return found


def validate_projection(documents, parsed):
    """Cross-file identity/retirement checks; terminal states are never acceptance."""
    milestones={};diagnostics=[]
    specs={}
    p=parser()
    for path,doc in documents.items():
        if doc['kind']=='milestone':
            for section in parsed[path]['index_sections']:
                match=re.match(r'([A-Z](?:0[1-9]|[1-9][0-9]))(?:\s|$)',section['heading'])
                if match:
                    if match[1] in specs:raise AuditError(f'duplicate milestone specification: {match[1]}')
                    specs[match[1]]=section['text']
        for milestone in parsed[path]['index_milestones']:
            identity=milestone['milestone_id']
            if identity in milestones:raise AuditError(f'duplicate active/retired milestone: {identity}')
            milestones[identity]=milestone
    history=documents.get('tabilet/docs/history/index.md',{}).get('text','')
    history_rows={}
    for row in p.table_rows(history):
        identity=row['cells'][0]
        if re.fullmatch(r'[A-Z][0-9]{2}',identity):
            if identity in history_rows:raise AuditError(f'duplicate history index ID: {identity}')
            history_rows[identity]=row['cells']
    for identity,milestone in milestones.items():
        if milestone['lifecycle']=='active':
            if identity not in specs:raise AuditError(f'active status missing specification: {identity}')
            milestone['specification']=specs[identity]
        else:
            if identity in specs:raise AuditError(f'retired specification remains active: {identity}')
            cells=history_rows.get(identity,[])
            path=f'tabilet/docs/history/status-{identity}.md'
            meta=p.retired_record(documents[path]['text'],pathlib.Path(path).name)['metadata']
            if len(cells)!=5 or cells[1:3]!=[meta['Outcome'],meta['Retired']] or not re.fullmatch(r'\[[^\]]+\]\(status-'+identity+r'\.md\)',cells[3]):
                raise AuditError(f'missing or inconsistent history index entry: {identity}')
    # A current milestone specification is the maintained source for display
    # order, summary, and acceptance.  Status records still own task state and
    # retired envelopes still own closure evidence, so discard the duplicate
    # status-side projection when a specification exists.
    for path,parts in parsed.items():
        if path not in parsed or not isinstance(parts, dict):
            continue
        if path.endswith('/milestone.md'):
            continue
        parts['index_milestone_projection']=[
            row for row in parts['index_milestone_projection'] if row['milestone_id'] not in specs
        ]
    for path,parts in parsed.items():
        if path.endswith('/milestone.md'):
            continue
        for row in parts['index_milestone_projection']:
            row['closure_state']=row.get('closure_state') or milestones[row['milestone_id']].get('lifecycle')
    for identity in set(specs)|set(history_rows):
        if identity not in milestones:raise AuditError(f'milestone has no status record: {identity}')
    for path,doc in documents.items():
        if doc['kind'] == 'context_archive':
            fields = dict(re.findall(r'^\*\*(Context|Baseline|Coverage)\.\*\* (.+)$', doc['text'], re.M))
            baseline = fields.get('Baseline', '').strip('`')
            if (not fields.get('Context') or fields.get('Coverage') != 'verified'
                    or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64}|unversioned)', baseline)):
                diagnostics.append(f'{path}: archive provenance is incomplete or unverified; text lookup only')
    for path,parts in parsed.items():
        for relation in parts['index_relationships']:
            target=relation['target']
            exists=target in documents
            if target.startswith('milestone:'):exists=target[10:] in milestones
            if target.startswith('archive:'):exists=f'tabilet/docs/archive-{target[8:]}.md' in documents
            if not exists:diagnostics.append(f'{path}:{relation["line"]}: unresolved {relation["relation"]}: {target}')
    return diagnostics


def ensure_fts(connection):
    try:
        connection.execute('CREATE VIRTUAL TABLE IF NOT EXISTS index_fts USING fts5(text)')
        return True
    except sqlite3.OperationalError as exc:
        if 'no such module' not in str(exc).lower():raise
        return False


@atomic
def publish(connection, workspace, documents, parsed, generation, context, attempted, diagnostics, force_literal=False, *, root, paths, stats):
    if inventory(root)!=paths or git_context(root)!=context:
        raise AuditError("source inventory or Git context changed during refresh")
    for path,expected in stats.items():
        no_symlinks(root,root/path)
        if signature((root/path).stat())!=expected:
            raise AuditError(f"source changed during refresh: {path}")
    fts=ensure_fts(connection) if not force_literal else False
    old_fts=connection.execute("SELECT 1 FROM sqlite_master WHERE name='index_fts'").fetchone()
    if old_fts:
        connection.execute('DELETE FROM index_fts WHERE rowid IN (SELECT search_id FROM index_search WHERE workspace_id=?)',(workspace,))
    for table in DERIVED_TABLES:connection.execute(f'DELETE FROM {table} WHERE workspace_id=?',(workspace,))
    for path,doc in documents.items():
        connection.execute('INSERT INTO index_documents VALUES (?,?,?,?,?,?,?)',(workspace,path,doc['kind'],doc['sha256'],doc['mtime_ns'],doc['size'],doc['text']))
        for table,items in parsed[path].items():
            for item in items:
                values={'workspace_id':workspace,'path':path,**item}
                columns=','.join(values)
                cursor=connection.execute(f'INSERT INTO {table} ({columns}) VALUES ({",".join("?" for _ in values)})',tuple(values.values()))
                if table=='index_search' and fts:connection.execute('INSERT INTO index_fts(rowid,text) VALUES (?,?)',(cursor.lastrowid,item['text']))
    connection.execute('INSERT OR REPLACE INTO index_state VALUES (?,?,?,?,?,?,?,?,?)',
        (workspace,generation,utc_now(),context['git_head'],context['branch'],1,attempted,canonical_json(diagnostics),'fts5' if fts else 'literal'))
    # A v2 database may already contain index_documents but none of the SQL9
    # explorer projections. Record readiness only after this publish has filled
    # the complete derived projection.
    connection.execute(
        "INSERT OR REPLACE INTO schema_meta(key,value) VALUES (?, 'v2')",
        (f'index_projection:{workspace}',),
    )


def sync(connection, project_root, *, rebuild=False, force_literal=False):
    root=pathlib.Path(project_root).expanduser().resolve()
    context=git_context(root)
    existing=connection.execute('SELECT workspace_id FROM workspaces WHERE project_root=?',(str(root),)).fetchone()
    # A new legacy project must fail before registering a workspace. Existing
    # workspaces record the failed refresh while retaining their last generation.
    if not existing:
        layout_check(root)
    workspace=existing[0] if existing else ensure_workspace(connection,root,branch=context['branch'])
    attempted=utc_now()
    try:
        layout_check(root)
        paths=inventory(root)
        documents={};parsed={};stats={};diagnostics=[]
        previous={r['path']:r for r in records(connection,'SELECT * FROM index_documents WHERE workspace_id=?',(workspace,))}
        projection = connection.execute(
            "SELECT value FROM schema_meta WHERE key=?",
            (f'index_projection:{workspace}',),
        ).fetchone()
        projection_ready = projection == ('v2',)
        for path,kind in paths.items():
            text,digest,info=read_document(root,path)
            stats[path]=signature(info)
            documents[path]=dict(kind=kind,sha256=digest,mtime_ns=info.st_mtime_ns,size=info.st_size,text=text)
            old=previous.get(path)
            if old and old['sha256']!=digest and (kind=='history_status' or kind.startswith('evolution_') or (kind=='context_archive' and '**Coverage.** verified' in old['text'])):
                diagnostics.append(f'{path}: frozen source changed since indexed observation')
            if old and old['sha256']==digest and not rebuild and projection_ready:
                parts={}
                for table in DERIVED_TABLES[1:]:
                    parts[table]=[{k:v for k,v in row.items() if k not in ('workspace_id','path','search_id')} for row in records(connection,f'SELECT * FROM {table} WHERE workspace_id=? AND path=?',(workspace,path))]
                parsed[path]=parts
            else:parsed[path]=parse_document(path,kind,text,digest)
        diagnostics.extend(validate_projection(documents,parsed))
        generation=str(uuid.uuid4())
        publish(connection,workspace,documents,parsed,generation,context,attempted,diagnostics,force_literal,root=root,paths=paths,stats=stats)
        return status(connection,workspace)
    except (OSError,ValueError,sqlite3.Error) as exc:
        with connection:
            connection.execute('INSERT INTO index_state(workspace_id,complete,last_attempt,diagnostics_json) VALUES (?,0,?,?) ON CONFLICT(workspace_id) DO UPDATE SET complete=0,last_attempt=excluded.last_attempt,diagnostics_json=excluded.diagnostics_json',
                (workspace,attempted,canonical_json([str(exc)])))
        raise AuditError(f'index refresh failed; previous generation retained: {exc}') from exc


def status(connection, workspace):
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='index_state'").fetchone():
        return {'workspace_id':workspace,'generation':None,'complete':False,'diagnostic':'index requires writer migration and explicit sync'}
    rows=records(connection,'SELECT * FROM index_state WHERE workspace_id=?',(workspace,))
    if not rows:return {'workspace_id':workspace,'generation':None,'complete':False}
    result=rows[0]
    result['diagnostics']=strict_json_loads(result.pop('diagnostics_json'))
    result['complete']=bool(result['complete'])
    result['source_freshness']='not_checked'
    return result


@contextlib.contextmanager
def read_snapshot(connection):
    """Keep index metadata and rows on one SQLite read snapshot."""
    owner = not connection.in_transaction
    if owner:
        connection.execute('BEGIN')
    try:
        yield
    finally:
        if owner:
            connection.rollback()


def _current_source_state(connection, workspace, root):
    """Compare the published inventory with live Markdown without writing."""
    if root is None:
        return 'not_checked', ['live project root is required for readiness']
    try:
        paths=inventory(root)
        indexed={row['path']:row['sha256'] for row in records(
            connection,'SELECT path,sha256 FROM index_documents WHERE workspace_id=?',(workspace,))}
        if set(paths) != set(indexed):
            return 'stale', ['declared Markdown inventory changed since refresh']
        for path in paths:
            _,digest,_=read_document(root,path)
            if digest != indexed[path]:
                return 'stale', [f'{path}: source changed since refresh']
    except (AuditError,OSError,UnicodeError) as exc:
        return 'unavailable', [f'live source validation failed: {exc}']
    return 'current', []


def _readiness(connection, workspace, project_root=None):
    """Return explained, read-only task readiness for the explorer To-do view.

    This function never chooses an execution owner and never changes source or
    audit data.  It intentionally withholds recommendations when the current
    projection cannot be trusted.
    """
    info=status(connection,workspace)
    result={
        'workspace_id':workspace, 'index':info,
        'source_freshness':'not_checked', 'freshness_diagnostics':[],
        'resume':[], 'ready':[], 'waiting':[], 'blocked':[], 'needs_review':[],
        'recommendations':[],
    }
    if not info.get('generation'):
        result['needs_review'].append({'reason':info.get('diagnostic','index has no published generation')})
        return result
    required_tables = {'index_milestones', 'index_tasks', 'index_task_dependencies'}
    present_tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing_tables = sorted(required_tables - present_tables)
    if missing_tables:
        result['needs_review'].append({'reason':'index schema needs an explicit refresh after audit migration', 'missing_tables':missing_tables})
        return result
    freshness,problems=_current_source_state(connection,workspace,project_root)
    result['source_freshness']=freshness;result['freshness_diagnostics']=problems
    diagnostics=list(info.get('diagnostics') or [])+problems
    milestones={row['milestone_id']:row for row in records(
        connection,'SELECT * FROM index_milestones WHERE workspace_id=?',(workspace,))}
    tasks=records(connection,'SELECT * FROM index_tasks WHERE workspace_id=? ORDER BY path,line',(workspace,))
    active={key for key,value in milestones.items() if value['lifecycle']=='active'}
    tasks=[row for row in tasks if row['milestone_id'] in active]
    projection_exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='index_milestone_projection'").fetchone()
    projection_order = {row['milestone_id']: (row['display_order'] if row['display_order'] is not None else 2147483647)
                       for row in records(connection, 'SELECT milestone_id,display_order FROM index_milestone_projection WHERE workspace_id=?', (workspace,))} if projection_exists else {}
    tasks.sort(key=lambda row: (projection_order.get(row['milestone_id'], 2147483647), row['path'], row['line']))
    for row in tasks:
        row['task_key']=row.get('explicit_id') or f"{row['path']}#{row['line']}"
        row['dependency_key']=(f"{row['milestone_id']}/{row['explicit_id']}"
                               if row.get('explicit_id') else row['task_key'])
        row['source']={'path':row['path'],'line':row['line'],'sha256':row['sha256']}
        row['prerequisites']=[]
        row['dependents']=[]
    by_key={}
    by_dependency_key={}
    for row in tasks:
        by_key.setdefault(row['task_key'], []).append(row)
        by_dependency_key.setdefault(row['dependency_key'], []).append(row)
    dependency_rows=records(connection,'SELECT * FROM index_task_dependencies WHERE workspace_id=?',(workspace,))
    dependencies={}
    for dep in dependency_rows:
        dependencies.setdefault(dep['source_key'],[]).append(dep)

    def dependency_candidates(dep, source_row):
        if dep.get('target_milestone_id'):
            return [item for item in by_key.get(dep['target_explicit_id'], [])
                    if item['milestone_id'] == dep['target_milestone_id']]
        candidates = [item for item in by_key.get(dep['target_key'], [])
                      if item['milestone_id'] == source_row['milestone_id']]
        return candidates or by_key.get(dep['target_key'], [])

    for source_row in tasks:
        for dep in (item for item in dependencies.get(source_row['dependency_key'], [])
                    if item.get('milestone_id') == source_row['milestone_id']):
            candidates = dependency_candidates(dep, source_row)
            reference = {'task_key': dep['target_key'], 'milestone_id': dep.get('target_milestone_id'),
                         'relationship': dep['relationship'], 'reason': dep.get('reason'),
                         'resolved': len(candidates) == 1}
            if len(candidates) == 1:
                target = candidates[0]
                reference.update({'task_key': target['task_key'], 'milestone_id': target['milestone_id'],
                                  'label': target['label'], 'state': target['state'], 'source': target['source']})
                target['dependents'].append({'task_key': source_row['task_key'],
                                             'milestone_id': source_row['milestone_id'],
                                             'label': source_row['label'], 'state': source_row['state'],
                                             'source': source_row['source']})
            source_row['prerequisites'].append(reference)
    # Milestone-level dependencies are an explicit ordering constraint for all
    # tasks in the dependent milestone. Preserve the reason in the same
    # explained waiting bucket instead of treating display order as priority.
    milestone_dependencies=records(connection, "SELECT source, target, path, line FROM index_relationships WHERE workspace_id=? AND relation='depends_on' AND source LIKE 'milestone:%'", (workspace,))
    milestone_waiting={}
    milestone_review={}
    for relation in milestone_dependencies:
        source_id=relation['source'].removeprefix('milestone:')
        target_id=relation['target'].removeprefix('milestone:')
        if source_id not in active:
            continue
        if target_id not in milestones:
            diagnostics.append(f"{relation['path']}:{relation['line']}: unresolved milestone dependency: {relation['target']}")
            continue
        target = milestones[target_id]
        target_rows=records(connection, "SELECT state FROM index_tasks WHERE workspace_id=? AND milestone_id=?", (workspace,target_id))
        unfinished=any(row['state'] in {'pending','in_progress','blocked'} for row in target_rows)
        unsafe_terminal=any(row['state'] in {'cancelled','historical'} for row in target_rows)
        accepted = target['lifecycle'] == 'retired' and target.get('outcome') == 'completed'
        if not accepted:
            milestone_waiting.setdefault(source_id,[]).append(target_id)
            if not target_rows or unsafe_terminal or (not unfinished and target['lifecycle'] == 'active'):
                milestone_review.setdefault(source_id, []).append(target_id)
    in_progress=[row for row in tasks if row['state']=='in_progress']
    if len(in_progress)>1:
        result['needs_review'].append({'reason':'multiple in-progress tasks own the ledger',
                                       'tasks':[row['task_key'] for row in in_progress],
                                       'milestone_ids': sorted({row['milestone_id'] for row in in_progress})})
    elif in_progress:
        result['resume'].append({'task':in_progress[0],'reason':'resume the sole in-progress task'})
    for row in tasks:
        if row['state']=='blocked':
            result['blocked'].append({'task':row,'reason':row['notes'] or 'status row is explicitly blocked'})
    for milestone_id in active:
        milestone_tasks=[row for row in tasks if row['milestone_id']==milestone_id]
        if milestone_tasks and all(row['state'] in {'completed','cancelled','historical'} for row in milestone_tasks):
            milestone = milestones[milestone_id]
            result['needs_review'].append({'milestone_id':milestone_id,
                'source': {'path': milestone['path'], 'line': milestone['line']},
                'reason':'all task rows are terminal; milestone acceptance and closure review are still required'})
    for row in tasks:
        if row['state']!='pending':
            continue
        reasons=[]
        if in_progress:
            reasons.append('another task is already in progress')
        if row['milestone_id'] in milestone_waiting:
            reason = 'milestone dependency is unfinished: '
            if row['milestone_id'] in milestone_review:
                reason = 'milestone dependency requires review: '
            reasons.append(reason + ', '.join(sorted(milestone_waiting[row['milestone_id']])))
        for dep in (item for item in dependencies.get(row['dependency_key'], []) if item.get('milestone_id') == row['milestone_id']):
            candidates = dependency_candidates(dep, row)
            if len(candidates) != 1:
                reasons.append(f"unresolved dependency: {dep['target_key']}")
                continue
            target=candidates[0]
            if target['state'] in {'cancelled','historical'}:
                reasons.append(f"dependency requires review: {dep['target_key']}")
            elif target['state']!='completed':
                reasons.append(f"dependency is {target['state']}: {dep['target_key']}")
        if reasons:
            result['waiting'].append({'task':row,'reason':'; '.join(reasons)})
        else:
            result['ready'].append({'task':row,'reason':'pending row has no unsatisfied explicit dependency'})
    # Detect cycles in the explicit task graph. A cycle is review work, even if
    # another independent task could technically be selected.
    graph={}
    for source, items in dependencies.items():
        source_rows=by_dependency_key.get(source, [])
        for source_row in source_rows:
            node=(source_row['milestone_id'], source_row['task_key'])
            for dep in items:
                if dep.get('milestone_id') != source_row['milestone_id']:
                    continue
                targets=by_key.get(dep['target_key'], [])
                if dep.get('target_milestone_id'):
                    targets=[item for item in targets if item['milestone_id'] == dep['target_milestone_id']]
                else:
                    same_milestone=[item for item in targets if item['milestone_id'] == source_row['milestone_id']]
                    targets=same_milestone or targets
                if len(targets) != 1:
                    continue
                for target in targets:
                    graph.setdefault(node, set()).add((target['milestone_id'], target['task_key']))
    # Iterative DFS keeps readiness safe for projects whose dependency depth is
    # greater than Python's recursion limit.
    colors={}; cycles=[]
    for start in graph:
        if colors.get(start, 0):
            continue
        colors[start]=1
        trail=[start]
        positions={start:0}
        stack=[(start, iter(graph.get(start, ())))]
        while stack:
            node, targets = stack[-1]
            try:
                target=next(targets)
            except StopIteration:
                stack.pop(); colors[node]=2; positions.pop(node, None); trail.pop()
                continue
            color=colors.get(target, 0)
            if color == 0:
                colors[target]=1; positions[target]=len(trail); trail.append(target)
                stack.append((target, iter(graph.get(target, ()))))
            elif color == 1:
                cycle=trail[positions[target]:] + [target]
                cycles.append(' -> '.join(f'{mid}/{key}' for mid,key in cycle))
    if cycles:
        cycle_values = sorted(set(cycles))
        cycle_milestones = sorted({node[0] for node in graph if any(f'{node[0]}/' in cycle for cycle in cycle_values)})
        result['needs_review'].append({'reason':'dependency cycle requires review', 'cycles': cycle_values,
                                       'milestone_ids': cycle_milestones})
    if diagnostics or freshness!='current' or len(in_progress)>1 or result['needs_review']:
        if diagnostics:
            result['needs_review'].append({'reason':'projection or source diagnostics prevent safe ordering', 'diagnostics':diagnostics})
        result['recommendations']=[]
    else:
        result['recommendations']=result['resume'] or result['ready']
    return result


def readiness(connection, workspace, project_root=None):
    with read_snapshot(connection):
        return _readiness(connection, workspace, project_root)


def workspace_id(connection, project_root):
    root=str(pathlib.Path(project_root).expanduser().resolve())
    row=connection.execute('SELECT workspace_id FROM workspaces WHERE project_root=?',(root,)).fetchone()
    if not row:raise AuditError('project has no indexed or audited workspace; use index sync')
    return row[0]


def _search(connection, workspace, query, *, kind=None, milestone_id=None, state=None, limit=50, offset=0):
    pagination(limit,offset)
    info=status(connection,workspace)
    if not info.get('generation'):return {'index':info,'results':[]}
    clauses=['s.workspace_id=?'];values=[workspace]
    for column,value in [('kind',kind),('milestone_id',milestone_id),('state',state)]:
        if value is not None:clauses.append(f's.{column}=?');values.append(value)
    fts=info.get('search_mode')=='fts5'
    if query:
        clauses.append('index_fts MATCH ?' if fts else 'instr(lower(s.text),lower(?))>0');values.append(query)
    join=' JOIN index_fts ON index_fts.rowid=s.search_id' if fts and query else ''
    order='bm25(index_fts),s.path,s.line' if join else 's.path,s.line'
    rows=records(connection,'SELECT s.*,d.sha256,substr(s.text,1,240) AS snippet FROM index_search s JOIN index_documents d ON d.workspace_id=s.workspace_id AND d.path=s.path'+join+' WHERE '+' AND '.join(clauses)+f' ORDER BY {order} LIMIT ? OFFSET ?',(*values,limit,offset))
    for row in rows:row.pop('text');row['refreshed_at']=info['refreshed_at']
    return {'index':info,'limit':limit,'offset':offset,'results':rows}


def search(connection, workspace, query, *, kind=None, milestone_id=None, state=None, limit=50, offset=0):
    with read_snapshot(connection):
        return _search(connection, workspace, query, kind=kind, milestone_id=milestone_id,
                       state=state, limit=limit, offset=offset)


def _show(connection, workspace, path):
    info=status(connection,workspace)
    rows=records(connection,'SELECT * FROM index_documents WHERE workspace_id=? AND path=?',(workspace,path)) if info.get('generation') else []
    if not rows:raise AuditError('document is not in the published index')
    return {'index':info,'document':rows[0],**{table.removeprefix('index_'):records(connection,f'SELECT * FROM {table} WHERE workspace_id=? AND path=?',(workspace,path)) for table in DERIVED_TABLES[1:] if table != 'index_search'}}


def show(connection, workspace, path):
    with read_snapshot(connection):
        return _show(connection, workspace, path)
