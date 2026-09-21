"""Disposable current Markdown projection. No project writes or task selection."""
from __future__ import annotations

import functools
import hashlib
import importlib.machinery
import importlib.util
import pathlib
import os
import json
import re
import sqlite3
import stat
import subprocess
import uuid

from tabilet_audit import AuditError, atomic, canonical_json, ensure_workspace, records, utc_now, pagination

MAX_BYTES = 4 * 1024 * 1024
STATUS = re.compile(r'status-([A-Z](?:0[1-9]|[1-9][0-9]))\.md$')
ARCHIVE = re.compile(r'archive-([A-Z](?:0[1-9]|[1-9][0-9]))\.md$')
EVOLUTION = re.compile(r'(prompt|result)-v([1-9][0-9]*)\.md$')
TABLES = ('index_documents','index_sections','index_milestones','index_tasks','index_relationships','index_search')


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
    parsed={table:[] for table in TABLES if table!='index_documents'}
    parsed['index_sections']=list(headings(text))
    parsed['index_search'].append(dict(line=1,kind=kind,milestone_id=None,state=None,text=text))
    for section in parsed['index_sections']:
        parsed['index_search'].append(dict(line=section['line'],kind='section',milestone_id=None,state=None,text=section['text']))
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
        all_rows=p.table_rows(status)
        for row in rows:
            headers=next((r['cells'] for r in reversed(all_rows) if r['line']<row['line'] and r['cells'][1].lower()=='state'),[])
            explicit=None
            for i,header in enumerate(headers):
                if header.lower() in ('id','task id') and i<len(row['cells']):explicit=row['cells'][i]
            parsed['index_tasks'].append(dict(sha256=digest,line=row['line']+offset,milestone_id=identity,
                label=row['item'],state=row['state'],notes=' | '.join(row['cells'][2:]),explicit_id=explicit))
            parsed['index_search'].append(dict(line=row['line']+offset,kind='task',milestone_id=identity,
                state=row['state'],text=' | '.join(row['cells'])))
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
    for table in TABLES:connection.execute(f'DELETE FROM {table} WHERE workspace_id=?',(workspace,))
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


def sync(connection, project_root, *, rebuild=False, force_literal=False):
    root=pathlib.Path(project_root).expanduser().resolve()
    # Layout/source discovery precedes registration and all index writes.
    layout_check(root)
    context=git_context(root)
    existing=connection.execute('SELECT workspace_id FROM workspaces WHERE project_root=?',(str(root),)).fetchone()
    workspace=existing[0] if existing else ensure_workspace(connection,root,branch=context['branch'])
    attempted=utc_now()
    try:
        paths=inventory(root)
        documents={};parsed={};stats={};diagnostics=[]
        previous={r['path']:r for r in records(connection,'SELECT * FROM index_documents WHERE workspace_id=?',(workspace,))}
        for path,kind in paths.items():
            text,digest,info=read_document(root,path)
            stats[path]=signature(info)
            documents[path]=dict(kind=kind,sha256=digest,mtime_ns=info.st_mtime_ns,size=info.st_size,text=text)
            old=previous.get(path)
            if old and old['sha256']!=digest and (kind=='history_status' or kind.startswith('evolution_') or (kind=='context_archive' and '**Coverage.** verified' in old['text'])):
                diagnostics.append(f'{path}: frozen source changed since indexed observation')
            if old and old['sha256']==digest and not rebuild:
                parts={}
                for table in TABLES[1:]:
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
    result['diagnostics']=json.loads(result.pop('diagnostics_json'))
    result['complete']=bool(result['complete'])
    result['source_freshness']='not_checked'
    return result


def workspace_id(connection, project_root):
    root=str(pathlib.Path(project_root).expanduser().resolve())
    row=connection.execute('SELECT workspace_id FROM workspaces WHERE project_root=?',(root,)).fetchone()
    if not row:raise AuditError('project has no indexed or audited workspace; use index sync')
    return row[0]


def search(connection, workspace, query, *, kind=None, milestone_id=None, state=None, limit=50, offset=0):
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


def show(connection, workspace, path):
    info=status(connection,workspace)
    rows=records(connection,'SELECT * FROM index_documents WHERE workspace_id=? AND path=?',(workspace,path)) if info.get('generation') else []
    if not rows:raise AuditError('document is not in the published index')
    return {'index':info,'document':rows[0],**{table.removeprefix('index_'):records(connection,f'SELECT * FROM {table} WHERE workspace_id=? AND path=?',(workspace,path)) for table in TABLES[1:-1]}}
