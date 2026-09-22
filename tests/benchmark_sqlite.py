#!/usr/bin/env python3
"""Disposable representative index benchmark; no project or network writes."""
import json
from pathlib import Path
import platform
import sqlite3
import statistics
import sys
import tempfile
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import tabilet_audit as audit
import tabilet_index as index
import tabilet_explorer as explorer


def main():
    with tempfile.TemporaryDirectory(prefix='tabilet-index-benchmark-') as temporary:
        root = Path(temporary) / 'project'
        bank = root / 'tabilet/memory-bank'
        bank.mkdir(parents=True)
        specifications = ['# Milestones\n']
        count = 0
        for lane in 'ABCDEFGHIJKLMNOPQ':
            for number in range(1, 9 if lane == 'A' else 8):
                identity = f'{lane}{number:02}'
                specifications.append(f'## {identity} - Delivery\n\n**Acceptance.** Verified feature.\n')
                rows = ['# Status\n\n| Item | State | Notes |\n|---|---|---|\n']
                for task in range(20):
                    rows.append(f'| {identity} task {task:02} | `[ ]` | authentication acceptance evidence |\n')
                (bank / f'status-{identity}.md').write_text(''.join(rows))
                count += 1
        (bank / 'milestone.md').write_text('\n'.join(specifications))
        docs = root / 'tabilet/docs'; history = docs / 'history'; evolution = root / 'tabilet/evolution'
        history.mkdir(parents=True); evolution.mkdir(parents=True)
        status = '# Status\n\n| Item | State | Notes |\n|---|---|---|\n| Retired work | `[+]` | verified |\n'
        retired = (
            '# Retired milestone R99\n\n**Milestone.** R99\n**Outcome.** completed\n'
            '**Retired.** 2026-09-22\n**Source status.** tabilet/memory-bank/status-R99.md\n'
            '**Source specification.** tabilet/memory-bank/milestone.md#r99-delivery\n'
            '**Evidence.** unversioned\n**Worktree.** unversioned\n**Review.** passed\n'
            '**Review iterations.** 1\n**Verification.** benchmark fixture\n'
            '**Consolidated into.** no current-truth change\n\n## Milestone specification\n\n'
            '`````markdown\n## R99 - Delivery\n\n**Acceptance.** Verified.\n`````\n\n'
            '## Status record\n\n`````markdown\n' + status + '`````\n'
        )
        (history/'status-R99.md').write_text(retired)
        (history/'index.md').write_text('# History\n\n| Milestone | Outcome | Retired | Record | Summary |\n|---|---|---|---|---|\n| R99 | completed | 2026-09-22 | [R99](status-R99.md) | Delivery |\n')
        (docs/'archive-A01.md').write_text('# Archive A01\n\n**Context.** Benchmark archive.\n**Baseline.** unversioned\n**Coverage.** verified\n')
        (evolution/'prompt-v1.md').write_text('# Prompt v1\n\nBenchmark direction request.\n')
        (evolution/'result-v1.md').write_text('# Result v1\n\nBenchmark direction result.\n')
        connection = audit.open_database(Path(temporary) / 'audit.db')
        try:
            start = time.perf_counter()
            state = index.sync(connection, root)
            initial = time.perf_counter() - start
            for run_number in range(250):
                parent = audit.start_run(connection, state['workspace_id'], 'goal' if run_number % 10 == 0 else 'next',
                                         run_id=f'run-{run_number:03}', capture_mode='relevant')
                if run_number % 10 == 0:
                    audit.capture_message(connection, parent, 'user', f'benchmark request {run_number}',
                                          capture_source='host', fidelity='exact', message_id=f'message-{run_number:03}')
                    child = audit.start_run(connection, state['workspace_id'], 'next', run_id=f'child-{run_number:03}', parent_run_id=parent)
                    audit.finish_run(connection, child, 'completed')
                audit.finish_run(connection, parent, 'completed')
            start = time.perf_counter()
            index.sync(connection, root)
            unchanged = time.perf_counter() - start
            elapsed = []
            for _ in range(100):
                start = time.perf_counter()
                found = index.search(connection, state['workspace_id'], 'authentication', kind='task', limit=50)
                elapsed.append(time.perf_counter() - start)
            assert len(found['results']) == 50
            fallback = index.sync(connection, root, force_literal=True)
            start = time.perf_counter()
            index.search(connection, state['workspace_id'], 'authentication', kind='task')
            literal = time.perf_counter() - start
            start = time.perf_counter()
            readiness = index.readiness(connection, state['workspace_id'], root)
            readiness_ms = (time.perf_counter() - start) * 1000
            assert readiness['source_freshness'] == 'current'
            assert len(readiness['ready']) == count * 20
            app = explorer.ExplorerApp(root, Path(temporary) / 'audit.db')
            start = time.perf_counter(); overview = app.overview(); overview_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter(); timeline = app.timeline({'limit':['50']}); timeline_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter(); detail = app.run('run-000'); detail_ms = (time.perf_counter() - start) * 1000
            start = time.perf_counter(); todo = app.todo({'limit': ['50']}); todo_ms = (time.perf_counter() - start) * 1000
            assert len(todo['ready']) == 50 and todo['totals']['ready'] == count * 20
            sizes = [len(explorer._json(value).encode()) for value in (overview, timeline, detail, todo)]
            print(json.dumps({
                'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
                'status_files': count, 'lanes': 17, 'tasks': count * 20,
                'initial_sync_ms': round(initial * 1000, 2),
                'unchanged_sync_ms': round(unchanged * 1000, 2),
                'search_mode': state['search_mode'], 'searches': len(elapsed),
                'search_median_ms': round(statistics.median(elapsed) * 1000, 2),
                'literal_search_ms': round(literal * 1000, 2),
                'readiness_ms': round(readiness_ms, 2),
                'recommendations': len(readiness['recommendations']),
                'fallback_mode': fallback['search_mode'],
                'retired_records': 1, 'archives': 1, 'evolution_documents': 2,
                'audit_parent_runs': 250, 'audit_child_runs': 25,
                'overview_ms': round(overview_ms, 2), 'timeline_page_ms': round(timeline_ms, 2),
                'run_detail_ms': round(detail_ms, 2), 'todo_page_ms': round(todo_ms, 2),
                'todo_page_entries': len(todo['ready']), 'todo_total_entries': todo['totals']['ready'],
                'timeline_page_entries': len(timeline['entries']),
                'peak_response_bytes': max(sizes),
            }, indent=2))
        finally:
            connection.close()


if __name__ == '__main__':
    main()
