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
        connection = audit.open_database(Path(temporary) / 'audit.db')
        try:
            start = time.perf_counter()
            state = index.sync(connection, root)
            initial = time.perf_counter() - start
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
            print(json.dumps({
                'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
                'status_files': count, 'lanes': 17, 'tasks': count * 20,
                'initial_sync_ms': round(initial * 1000, 2),
                'unchanged_sync_ms': round(unchanged * 1000, 2),
                'search_mode': state['search_mode'], 'searches': len(elapsed),
                'search_median_ms': round(statistics.median(elapsed) * 1000, 2),
                'literal_search_ms': round(literal * 1000, 2),
                'fallback_mode': fallback['search_mode'],
            }, indent=2))
        finally:
            connection.close()


if __name__ == '__main__':
    main()
