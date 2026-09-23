#!/usr/bin/env python3
"""Optional audit and Markdown lookup CLI; install this file as tabilet-audit."""
from __future__ import annotations

import argparse
import contextlib
import os
import pathlib
import sqlite3
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tabilet_audit as audit
import tabilet_index as index

TOOLKIT_INTERFACE = 1


def check_toolkit(include_explorer=False):
    modules = {'tabilet_audit': audit, 'tabilet_index': index}
    versions = {name: getattr(module, 'TOOLKIT_INTERFACE', None) for name, module in modules.items()}
    if include_explorer:
        try:
            from tabilet_explorer import TOOLKIT_INTERFACE as explorer_interface
        except ImportError as exc:
            raise audit.AuditError('incomplete explorer toolkit; reinstall the toolkit files together') from exc
        versions['tabilet_explorer'] = explorer_interface
    if any(value != TOOLKIT_INTERFACE for value in versions.values()):
        raise audit.AuditError(f'incompatible toolkit modules: expected interface {TOOLKIT_INTERFACE}, got {versions}; reinstall the toolkit files together')


def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-db',default=os.environ.get('TABILET_AUDIT_DB') or str(audit.default_database_path()),help='External database; only write commands create or migrate it.')
    parser.add_argument('--event',help='Compatibility alias for audit event with inline JSON.')
    groups=parser.add_subparsers(dest='group')
    audits=groups.add_parser('audit').add_subparsers(dest='action',required=True)
    begin=audits.add_parser('begin')
    begin.add_argument('project');begin.add_argument('operation',choices=sorted(audit.OPERATIONS))
    begin.add_argument('--run-id');begin.add_argument('--parent-run-id')
    begin.add_argument('--capture',choices=['metadata','relevant'],default=os.environ.get('TABILET_AUDIT_CAPTURE','metadata'))
    begin.add_argument('--provenance',default=None,help='JSON provenance file, or - for stdin')
    for name in ('event','message'):
        command=audits.add_parser(name)
        command.add_argument('--input',default='-',help='JSON file, or - for stdin; never interpreted as instructions.')
    coverage=audits.add_parser('coverage')
    coverage.add_argument('--input',default='-',help='JSON file, or - for stdin; never interpreted as instructions.')
    purge=audits.add_parser('purge-message')
    purge.add_argument('message_id');purge.add_argument('--reason',required=True);purge.add_argument('--confirm',required=True)
    finish=audits.add_parser('finish');finish.add_argument('run_id');finish.add_argument('result',choices=sorted(audit.RUN_RESULTS))
    finish.add_argument('--completed-at')
    for name in ('runs','events'):
        command=audits.add_parser(name)
        command.add_argument('--project');command.add_argument('--workspace-id')
        command.add_argument('--operation',choices=sorted(audit.OPERATIONS))
        command.add_argument('--milestone',dest='milestone_id');command.add_argument('--task')
        command.add_argument('--instruction-set',dest='instruction_set');command.add_argument('--instruction-set-version',dest='instruction_set_version')
        command.add_argument('--host');command.add_argument('--model');command.add_argument('--capture-method',dest='capture_method',choices=sorted(audit.PROVENANCE_CAPTURE_METHODS))
        command.add_argument('--coverage',choices=sorted(audit.COVERAGE_STATES));command.add_argument('--purged',action='store_true')
        command.add_argument('--since');command.add_argument('--until')
        command.add_argument('--limit',type=int,default=100);command.add_argument('--offset',type=int,default=0)
        if name=='events':command.add_argument('--run-id')
    export=audits.add_parser('export');export.add_argument('--project');export.add_argument('--workspace-id')
    export.add_argument('--include-content',action='store_true',help='Include selected messages and legacy snapshot bytes; may contain private material.')
    indexes=groups.add_parser('index').add_subparsers(dest='action',required=True)
    for name in ('sync','status','search','show'):
        command=indexes.add_parser(name);command.add_argument('project')
        if name=='sync':
            command.add_argument('--rebuild',action='store_true');command.add_argument('--literal',action='store_true',help='Use literal-text search even if FTS5 is available.')
        if name=='search':
            command.add_argument('query',nargs='?',default='');command.add_argument('--kind')
            command.add_argument('--milestone',dest='milestone_id');command.add_argument('--state',choices=sorted(audit.STATES))
            command.add_argument('--limit',type=int,default=50);command.add_argument('--offset',type=int,default=0)
        if name=='show':command.add_argument('path')
    for name in ('backup','restore'):
        command=groups.add_parser(name);command.add_argument('destination')
        if name=='restore':command.add_argument('--snapshot-id',help='Recover one legacy snapshot instead of the whole database.')
    explorer=groups.add_parser('explorer', help='serve the local Tabilet Explorer')
    explorer.add_argument('project')
    explorer.add_argument('--host', default='127.0.0.1')
    explorer.add_argument('--port', type=int, default=8000)
    explorer.add_argument('--database', dest='explorer_database', help='external database (defaults to --audit-db)')
    args=parser.parse_args(argv)
    if args.event is not None:
        if args.group:parser.error('--event cannot be combined with a command group')
        args.group='audit';args.action='event';args.input='-'
    if not args.group:parser.error('a command group is required')
    if getattr(args,'capture','metadata') not in ('metadata','relevant'):
        parser.error('TABILET_AUDIT_CAPTURE must be metadata or relevant')
    if getattr(args,'project',None) and getattr(args,'workspace_id',None):
        parser.error('choose --project or --workspace-id')
    return args


def submission(args):
    text=args.event if args.event is not None else sys.stdin.read() if args.input=='-' else pathlib.Path(args.input).read_text(encoding='utf-8')
    result=audit.strict_json_loads(text)
    if not isinstance(result,dict):raise audit.AuditError('submission must be a JSON object')
    return result


def provenance_submission(args):
    if not args.provenance:
        return None
    text=sys.stdin.read() if args.provenance=='-' else pathlib.Path(args.provenance).read_text(encoding='utf-8')
    result=audit.strict_json_loads(text)
    if not isinstance(result,dict):raise audit.AuditError('provenance must be a JSON object')
    return result


def refresh(connection, root):
    try:return index.sync(connection,root)
    except (audit.AuditError,sqlite3.Error,OSError) as exc:
        print(f'Index gap: {exc}',file=sys.stderr)
        return {'complete':False,'error':str(exc)}


@audit.atomic
def begin_run(connection, root, args):
    provenance = provenance_submission(args)
    if args.run_id:
        existing = audit.records(connection, """
            SELECT r.run_id,r.workspace_id,r.operation,r.capture_mode,r.parent_run_id,
                   r.started_at,w.project_root
            FROM runs r JOIN workspaces w USING(workspace_id)
            WHERE r.run_id=?
        """, (args.run_id,))
        if existing:
            row = existing[0]
            if (pathlib.Path(row['project_root']).resolve() != root.resolve()
                    or row['operation'] != args.operation
                    or row['capture_mode'] != args.capture
                    or row['parent_run_id'] != args.parent_run_id):
                raise audit.AuditConflict('run ID reused with a different payload')
            if provenance is not None:
                audit.record_provenance(connection, row['run_id'], provenance)
            return {'run_id': row['run_id'], 'workspace_id': row['workspace_id'], 'started_at': row['started_at']}
    context=index.git_context(root)
    workspace=audit.ensure_workspace(connection,root,branch=context['branch'])
    dirty=index.subprocess.run(['git','status','--porcelain'],cwd=root,capture_output=True,text=True) if context['git_head'] else None
    run_id=audit.start_run(connection,workspace,args.operation,run_id=args.run_id,capture_mode=args.capture,
        parent_run_id=args.parent_run_id,git_head=context['git_head'],worktree_state='unversioned' if dirty is None else 'dirty' if dirty.stdout else 'clean')
    started=connection.execute('SELECT started_at FROM runs WHERE run_id=?',(run_id,)).fetchone()[0]
    audit.append_event(connection,{'schema':'tabilet.audit.event/v1','event_id':run_id+':started','run_id':run_id,
        'workspace_id':workspace,'operation':args.operation,'event_type':'run_started','recorded_at':started,
        'occurred_at':started,'subject':{},'details':{'schema':'tabilet.audit.details/v1','branch':context['branch']}})
    if provenance is not None:
        audit.record_provenance(connection, run_id, provenance)
    return {'run_id':run_id,'workspace_id':workspace,'started_at':started}


@audit.atomic
def submit_event(connection, event):
    event=dict(event)
    event.setdefault('event_id',str(uuid.uuid4()))
    prior=connection.execute('SELECT payload_json FROM events WHERE event_id=?',(event['event_id'],)).fetchone()
    timestamp=audit.strict_json_loads(prior[0])['recorded_at'] if prior else audit.utc_now()
    event.setdefault('recorded_at',timestamp)
    event.setdefault('occurred_at',None)
    details=event.get('details',{})
    if not isinstance(details,dict):raise audit.AuditError('event details must be an object')
    if details.get('capture_source') not in audit.CAPTURE_SOURCES or details.get('fidelity') not in audit.FIDELITIES:
        raise audit.AuditError('host events require details.capture_source and details.fidelity')
    sequence=audit.append_event(connection,event)
    return {'event_id':event['event_id'],'sequence':sequence,'recorded_at':event['recorded_at']}


def dispatch(args):
    action=getattr(args,'action',None)
    if args.group == 'explorer':
        from tabilet_explorer import serve
        return serve(args.project, args.explorer_database or args.audit_db, args.host, args.port)
    project=getattr(args,'project',None)
    root=pathlib.Path(project).expanduser().resolve() if project else None
    write=(args.group=='audit' and action in ('begin','event','message','coverage','purge-message','finish')) or (args.group=='index' and action=='sync')
    if root and write:
        if not root.is_dir():raise audit.AuditError('project must be an existing directory')
        if args.group == 'index' and action == 'sync':
            try:
                index.layout_check(root)
            except (OSError, ValueError) as exc:
                database = pathlib.Path(args.audit_db).expanduser()
                registered = False
                if database.is_file():
                    with contextlib.closing(audit.open_readonly_database(database)) as readonly:
                        registered = bool(readonly.execute(
                            'SELECT 1 FROM workspaces WHERE project_root=?', (str(root),)
                        ).fetchone())
                if not registered:
                    raise exc
        else:
            index.layout_check(root)
    if write and action in ('event','message','coverage','purge-message','finish') and not pathlib.Path(args.audit_db).expanduser().exists():
        raise audit.AuditError('no audit database; start with audit begin PROJECT OPERATION')
    connection=audit.open_database(args.audit_db,project_roots=[root] if root else []) if write else audit.open_readonly_database(args.audit_db)
    with contextlib.closing(connection):
        if args.group=='backup':
            audit.backup_database(connection,args.destination)
            return {'backup':str(pathlib.Path(args.destination).absolute())}
        if args.group=='restore':
            if args.snapshot_id:audit.restore_snapshot(connection,args.snapshot_id,args.destination)
            else:audit.backup_database(connection,args.destination)
            return {'restored':str(pathlib.Path(args.destination).absolute())}
        if args.group=='index':
            if action=='sync':return index.sync(connection,root,rebuild=args.rebuild,force_literal=args.literal)
            workspace=index.workspace_id(connection,root)
            if action=='status':return index.status(connection,workspace)
            if action=='show':return index.show(connection,workspace,args.path)
            return index.search(connection,workspace,args.query,kind=args.kind,milestone_id=args.milestone_id,state=args.state,limit=args.limit,offset=args.offset)
        if action=='begin':return begin_run(connection,root,args)
        if action=='event':return submit_event(connection,submission(args))
        if action=='message':return {'message_id':audit.capture_message(connection,**submission(args))}
        if action=='coverage':return audit.record_coverage(connection,submission(args))
        if action=='purge-message':
            tombstone=audit.purge_message(connection,args.message_id,args.reason,args.confirm)
            return {'tombstone':tombstone,'cleanup':audit.cleanup_purged_content(connection)}
        if action=='finish':
            audit.finish_run(connection,args.run_id,args.result,completed_at=args.completed_at)
            root=connection.execute('SELECT w.project_root FROM runs r JOIN workspaces w USING(workspace_id) WHERE r.run_id=?',(args.run_id,)).fetchone()[0]
            return {'run_id':args.run_id,'result':args.result,'index':refresh(connection,root)}
        workspace=index.workspace_id(connection,root) if root else getattr(args,'workspace_id',None)
        if action=='export':return audit.strict_json_loads(audit.export_json(connection,workspace_id=workspace,include_content=args.include_content))
        kwargs={key:getattr(args,key) for key in ('operation','milestone_id','task','since','until','limit','offset')}
        kwargs.update({key:getattr(args,key) for key in ('instruction_set','instruction_set_version','host','model','capture_method','coverage')})
        kwargs['purged']=True if getattr(args,'purged',False) else None
        kwargs['workspace_id']=workspace
        if action=='events':kwargs['run_id']=args.run_id
        results=(audit.query_runs if action=='runs' else audit.query_events)(connection,**kwargs)
        return {'limit':args.limit,'offset':args.offset,'results':results}


def main(argv=None):
    args=arguments(argv)
    try:
        check_toolkit(args.group == 'explorer')
        print(audit.canonical_json(dispatch(args)))
        return 0
    except (audit.AuditError,sqlite3.Error,OSError,ValueError,TypeError) as exc:
        print(f'tabilet-audit: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
