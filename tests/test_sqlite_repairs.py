"""Regressions from the branch review: real storage and concurrency boundaries."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import tabilet_audit as a


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'state/audit.sqlite3'
        self.c = a.open_database(self.db)
        self.addCleanup(self.c.close)
        self.w = a.ensure_workspace(self.c, self.root / 'project')

    def event(self, run, identity):
        return dict(schema='tabilet.audit.event/v1',event_id=identity,run_id=run,workspace_id=self.w,
                    operation='next',event_type='task_observed',recorded_at=a.utc_now(),subject={},
                    details={'schema':'tabilet.audit.details/v1'})

    def test_foreign_and_corrupt_files_are_not_mutated(self):
        foreign = self.root / 'foreign.db'
        with sqlite3.connect(foreign) as c:
            c.execute('CREATE TABLE schema_meta(key TEXT,value TEXT)')
            c.execute("INSERT INTO schema_meta VALUES ('schema','other/v1')")
            c.execute('PRAGMA user_version=1')
        c.close()
        for data in [foreign.read_bytes(), b'not a database']:
            foreign.write_bytes(data)
            self.root.chmod(0o755)
            before = foreign.read_bytes()
            with self.assertRaises((a.AuditError, sqlite3.DatabaseError)):
                a.open_database(foreign)
            self.assertEqual(foreign.read_bytes(),before)
            self.assertEqual(self.root.stat().st_mode & 0o777,0o755)

    def test_external_paths_and_symlinks(self):
        project = self.root / 'project'
        project.mkdir()
        with self.assertRaises(a.AuditError):
            a.open_database(project / 'audit.db',project_roots=[project])
        self.assertFalse((project/'audit.db').exists())
        (self.root/'link').symlink_to(project,target_is_directory=True)
        with self.assertRaises(a.AuditError):
            a.open_database(self.root/'link/audit.db')
        with self.assertRaises(a.AuditError):
            a.ensure_workspace(self.c,self.root)

    def test_metadata_capture_and_exact_provenance(self):
        run=a.start_run(self.c,self.w,'next')
        with self.assertRaises(a.AuditError):
            a.capture_message(self.c,run,'user','private',capture_source='host',fidelity='exact')
        run=a.start_run(self.c,self.w,'next',capture_mode='relevant')
        kwargs=dict(capture_source='host',fidelity='exact',message_id='message')
        a.capture_message(self.c,run,'user','selected',**kwargs)
        a.capture_message(self.c,run,'user','selected',**kwargs)
        with self.assertRaises(a.AuditConflict):
            a.capture_message(self.c,run,'user','different',**kwargs)
        with self.assertRaises(a.AuditError):
            a.capture_message(self.c,run,'assistant','text',capture_source='agent',fidelity='exact')
        self.assertEqual(self.c.execute('SELECT COUNT(*) FROM captured_messages').fetchone()[0],1)

    def test_parent_identity_and_run_retry(self):
        parent=a.start_run(self.c,self.w,'goal')
        child=a.start_run(self.c,self.w,'next',run_id='child',parent_run_id=parent)
        self.assertEqual(a.start_run(self.c,self.w,'next',run_id='child',parent_run_id=parent),child)
        other=a.ensure_workspace(self.c,self.root/'other')
        with self.assertRaises(a.AuditError):
            a.start_run(self.c,other,'next',parent_run_id=parent)
        with self.assertRaises(a.AuditError):
            a.append_event(self.c,{**self.event(child,'bad'),'workspace_id':other})
        a.finish_run(self.c,child,'blocked')
        a.finish_run(self.c,child,'blocked')
        self.assertEqual(len(a.query_events(self.c,child)),1)

    def test_concurrent_sequence_allocation(self):
        run=a.start_run(self.c,self.w,'next')
        def submit(i):
            c=a.open_database(self.db)
            try:return a.append_event(c,self.event(run,str(i)))
            finally:c.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            sequences=list(pool.map(submit,range(24)))
        self.assertEqual(sorted(sequences),list(range(1,25)))
        blocker=sqlite3.connect(self.db)
        try:
            blocker.execute('BEGIN IMMEDIATE')
            self.c.execute('PRAGMA busy_timeout=1')
            with self.assertRaises(sqlite3.OperationalError):
                a.append_event(self.c,self.event(run,'locked'))
        finally:blocker.rollback();blocker.close()
        self.assertEqual(len(a.query_events(self.c,run)),24)

    def test_complete_export_pagination_and_safe_backup(self):
        for i in range(1002):
            a.start_run(self.c,self.w,'next',run_id=f'run{i}')
        payload=json.loads(a.export_json(self.c))
        self.assertEqual(len(payload['runs']),1002)
        self.assertEqual(len(a.query_runs(self.c,offset=1000)),2)
        target=self.root/'backup.db'
        a.backup_database(self.c,target)
        original=target.read_bytes()
        with self.assertRaises(FileExistsError):a.backup_database(self.c,target)
        self.assertEqual(target.read_bytes(),original)
        with self.assertRaises(a.AuditError):a.backup_database(self.c,self.root/'project/backup.db')
        restored=self.root/'restored.db'
        a.restore_database(target,restored)
        c=a.open_readonly_database(restored)
        try:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM runs').fetchone()[0],1002)
            with self.assertRaises(sqlite3.OperationalError):c.execute('DELETE FROM runs')
        finally:c.close()

    def test_legacy_migration_preserves_snapshot_bytes(self):
        legacy=self.root/'legacy.db'
        c=sqlite3.connect(legacy)
        c.executescript(a.SCHEMA_SQL)
        c.execute("INSERT INTO schema_meta VALUES ('schema','tabilet.audit/v1')")
        c.execute('PRAGMA user_version=1')
        w=a.ensure_workspace(c,self.root/'legacy-project')
        run=a.start_run(c,w,'next')
        data=b'frozen bytes\n'
        c.execute('INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?)',('snapshot',w,'history_status','tabilet/docs/history/status-M01.md',data,hashlib.sha256(data).hexdigest(),a.utc_now(),None,'unversioned',run,None))
        c.execute('INSERT INTO run_snapshots VALUES (?,?,?,?,?,?)',(run,'snapshot',a.utc_now(),'observed','tabilet/docs/history/status-M01.md',None))
        c.commit();c.close()
        c=a.open_database(legacy)
        try:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)
            self.assertEqual(c.execute('SELECT content FROM snapshots').fetchone()[0],data)
            self.assertEqual(len(json.loads(a.export_json(c))['snapshots']),1)
            a.restore_snapshot(c,'snapshot',self.root/'recovered.md')
            self.assertEqual((self.root/'recovered.md').read_bytes(),data)
            with self.assertRaises(a.AuditError):a.capture_snapshots(c,w,run,self.root)
        finally:c.close()

    def test_time_filter_accepts_legacy_precision_without_changing_evidence(self):
        first=a.start_run(self.c,self.w,'next',started_at='2026-09-21T12:00:00Z')
        second=a.start_run(self.c,self.w,'next',started_at='2026-09-21T12:00:00.000001Z')
        self.assertEqual([r['run_id'] for r in a.query_runs(self.c,since='2026-09-21T12:00:00Z')],[first,second])
        self.assertEqual([r['run_id'] for r in a.query_runs(self.c,until='2026-09-21T12:00:00Z')],[first])
        self.assertEqual([r['run_id'] for r in a.query_runs(self.c,since='2026-09-21T12:00:00.000001Z')],[second])

    def test_wal_symlinks_are_rejected_before_open(self):
        target=self.root/'target';target.write_text('preserve')
        fake=self.root/'fake.db'
        Path(str(fake)+'-wal').symlink_to(target)
        with self.assertRaises(a.AuditError):a.open_database(fake)
        self.assertFalse(fake.exists())
        self.assertEqual(target.read_text(),'preserve')

    def test_initial_creation_failure_removes_partial_database_and_retries(self):
        legacy = self.root / 'new.db'
        original = sqlite3.connect

        class Interrupted(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if sql.strip().startswith('CREATE TABLE IF NOT EXISTS index_sections'):
                    raise sqlite3.OperationalError('injected creation interruption')
                return super().execute(sql, *args, **kwargs)

        def connect(path, *args, **kwargs):
            if str(path) == str(legacy):
                kwargs['factory'] = Interrupted
            return original(path, *args, **kwargs)

        from unittest import mock
        with mock.patch.object(a.sqlite3, 'connect', side_effect=connect), self.assertRaises(sqlite3.OperationalError):
            a.open_database(legacy)
        self.assertFalse(legacy.exists())
        connection = a.open_database(legacy)
        self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 3)
        connection.close()

    def test_backup_rejects_existing_sqlite_sidecars(self):
        for suffix in ('-wal', '-shm', '-journal'):
            with self.subTest(suffix=suffix):
                destination = self.root / ('backup-' + suffix[1:] + '.db')
                sidecar = Path(str(destination) + suffix)
                sidecar.write_bytes(b'preserve')
                with self.assertRaises(FileExistsError):
                    a.backup_database(self.c, destination)
                self.assertEqual(sidecar.read_bytes(), b'preserve')

    def test_interrupted_schema_migration_rolls_back_and_retries(self):
        from unittest import mock
        legacy=self.root/'migration.db'
        c=sqlite3.connect(legacy)
        c.executescript(a.SCHEMA_SQL)
        c.execute("INSERT INTO schema_meta VALUES ('schema','tabilet.audit/v1')")
        c.execute('PRAGMA user_version=1')
        c.commit();c.close()
        original=sqlite3.connect
        class Interrupted(sqlite3.Connection):
            def execute(self,sql,*args,**kwargs):
                if sql.strip().startswith('CREATE TABLE IF NOT EXISTS index_sections'):
                    raise sqlite3.OperationalError('injected migration interruption')
                return super().execute(sql,*args,**kwargs)
        def connect(path,*args,**kwargs):
            if str(path)==str(legacy):kwargs['factory']=Interrupted
            return original(path,*args,**kwargs)
        with mock.patch.object(a.sqlite3,'connect',side_effect=connect),self.assertRaises(sqlite3.OperationalError):
            a.open_database(legacy)
        c=original(legacy)
        try:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertNotIn('index_state',a.schema_tables(c))
            self.assertEqual(c.execute("SELECT value FROM schema_meta WHERE key='schema'").fetchone()[0],'tabilet.audit/v1')
        finally:c.close()
        c=a.open_database(legacy)
        self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3)
        c.close()
