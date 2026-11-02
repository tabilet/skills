"""Literal history, correction integrity, and the execution boundary."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
import test_harness as h
import tabilet_audit as audit
import tabilet_horizon as horizon
import tabilet_index as index
import tabilet_proposal as proposal
import tabilet_recovery as recovery

core = h.harness
FIXTURES = Path(__file__).parent / 'fixtures/retired-history'


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def entry(text, operations, identity='M01'):
    return dict(milestone_id=identity, record_path=f'tabilet/docs/history/status-{identity}.md',
                record_sha256=digest(text), corrections=operations)


def manifest(entries):
    return json.dumps(dict(schema=core.HISTORY_CORRECTIONS_SCHEMA, records=entries))


class HistoryCorrectionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        h.make_repo(self.root)
        self.text = h.retirement_text('| Task | `[+]` | verified |\n')

    def expansion(self):
        text = self.text.replace('**Evidence.** unversioned', '**Evidence.** abcdef0').replace(
            '**Worktree.** unversioned', '**Worktree.** clean')
        correction = entry(text, [dict(kind='expand-evidence-commit', recorded='abcdef0', resolved='abcdef0' + '1' * 33)])
        return text, correction

    def test_literal_m152_review_is_readable_but_missing_closure_blocks_readiness(self):
        name = 'status-M152.md'
        raw = (FIXTURES / (name + '.literal')).read_text()
        corrections = core.history_corrections((FIXTURES / 'correction-M152.json').read_text())
        record = core.historical_record(raw, name, corrections['tabilet/docs/history/' + name])
        self.assertEqual(record['metadata']['Review'], 'passed')
        self.assertEqual(record['metadata']['Review iterations'], '2')
        self.assertIn('missing historical closure evidence: Worktree', record['blockers'])
        self.assertIn('missing historical closure evidence: Consolidated into', record['blockers'])
        parsed = index.parse_document('tabilet/docs/history/' + name, 'history_status', raw, digest(raw), corrections)
        self.assertEqual(len(parsed['index_tasks']), len(core.status_rows(record['status'])))
        for task in parsed['index_tasks']:
            self.assertIn(task['label'], raw.splitlines()[task['line'] - 1])

    def test_literal_fixtures_lookup_discovery_dependencies_and_runner_share_evidence(self):
        corrections_text = (FIXTURES / 'corrections.json').read_text()
        corrections = core.history_corrections(corrections_text)
        history = self.root / 'tabilet/docs/history'
        history.mkdir(parents=True)
        (history / 'corrections.json').write_text(corrections_text)
        rows = []
        for identity in ('M99', 'M100', 'M153'):
            name = f'status-{identity}.md'
            raw = (FIXTURES / (name + '.literal')).read_bytes()
            (history / name).write_bytes(raw)
            record = core.historical_record(raw.decode(), name, corrections.get('tabilet/docs/history/' + name))
            self.assertEqual(record['blockers'], [])
            self.assertIn(record['status'], raw.decode())
            parsed = index.parse_document('tabilet/docs/history/' + name, 'history_status', raw.decode(), digest(raw.decode()), corrections)
            self.assertEqual(len(parsed['index_tasks']), len(core.status_rows(record['status'])))
            for task in parsed['index_tasks']:
                self.assertIn(task['label'], raw.decode().splitlines()[task['line'] - 1])
            rows.append(f"| {identity} | completed | {record['metadata']['Retired']} | [{identity}]({name}) | fixture |\n")
        (history / 'index.md').write_text('| Milestone | Outcome | Retired | Record | Summary |\n|---|---|---|---|---|\n' + ''.join(rows))
        # A dependency on a corrected retired record is accepted, while the
        # active row itself still needs ordinary execution authorization.
        bank = self.root / 'tabilet/memory-bank'
        (bank / 'milestone.md').write_text('# Milestones\n\n[History](../docs/history/index.md)\n\n## M01 - Delivery\n\n**Depends on.** M99\n')
        snapshot = core.row_snapshot(self.root)
        self.assertEqual(snapshot['history']['problems'], [])
        self.assertEqual(len(snapshot['history']['records']), 3)
        live = horizon._live_projection(core, self.root)
        self.assertIn('M99', live['milestones'])
        with audit.open_database(self.root / 'tabilet/audit.sqlite3') as connection:
            state = index.sync(connection, self.root)
            ready = index.readiness(connection, state['workspace_id'], self.root)
            self.assertEqual(len(ready['ready']), 1)
            # Manifest edits invalidate cached derived records even when their
            # frozen source bytes are unchanged; deletion cannot reuse them.
            (history / 'corrections.json').unlink()
            with self.assertRaises(audit.AuditError):
                index.sync(connection, self.root)
        for identity in ('M99', 'M100', 'M153'):
            self.assertEqual((history / f'status-{identity}.md').read_bytes(), (FIXTURES / f'status-{identity}.md.literal').read_bytes())

    def test_schema_rejects_duplicates_conflicts_authority_and_missing_evidence(self):
        text, correction = self.expansion()
        core.history_corrections(manifest([correction]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            core.history_corrections(manifest([correction, correction]))
        for operation in (
            dict(kind='execution-authority', approved=True),
            dict(kind='supply-metadata', field='Authorization', value='approved', evidence=[]),
            dict(kind='identify-specification', heading='## Approved', evidence=[]),
        ):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                core.history_corrections(manifest([entry(text, [operation])]))
        with self.assertRaisesRegex(ValueError, 'duplicate correction JSON key'):
            core.history_corrections('{"schema":"a","schema":"b","records":[]}')
        bad = copy.deepcopy(correction)
        bad['corrections'] *= 2
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            core.history_corrections(manifest([bad]))

    def test_metadata_corrections_cannot_derive_facts_from_unrelated_task_rows(self):
        for field, old, value in (
                ('Milestone', 'M01', 'M01'),
                ('Outcome', 'completed', 'completed'),
                ('Retired', '2026-09-12', '2026-09-12'),
                ('Source status', 'tabilet/memory-bank/status-M01.md', 'tabilet/memory-bank/status-M01.md'),
                ('Source specification', 'tabilet/memory-bank/milestone.md#m01-delivery', 'tabilet/memory-bank/milestone.md#wrong-owner'),
                ('Evidence', 'unversioned', 'a' * 40),
                ('Worktree', 'unversioned', 'clean'),
                ('Review iterations', '2', '2'),
                ('Review', 'passed', 'legacy'),
                ('Review limit', '10', '21'),
                ('Review limit approval', 'not recorded', 'owner approved'),
                ('Verification', 'tests passed; review found no blocking issues', 'Recorded results: tests passed'),
                ('Consolidated into', 'no current-truth change', 'no current-truth change')):
            with self.subTest(field=field):
                text = self.text.replace(f'**{field}.** {old}\n', '')
                if field == 'Evidence':
                    text = text.replace('**Worktree.** unversioned', '**Worktree.** clean')
                if field == 'Worktree':
                    text = text.replace('**Evidence.** unversioned', '**Evidence.** ' + 'a' * 40)
                quote = '| Task | `[+]` | verified |'
                line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
                correction = entry(text, [dict(kind='supply-metadata', field=field, value=value,
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                with self.assertRaisesRegex(ValueError, 'unsupported'):
                    core.historical_record(text, 'status-M01.md', correction)

    def test_recorded_legacy_review_counter_remains_supported(self):
        text = self.text.replace('**Review.** passed', '**Review.** legacy\n**Legacy closure.** Predates the gate')
        text = text.replace('**Review iterations.** 2\n', '').replace(
            '| Task |', 'Review iterations: not recorded\n\n| Task |')
        quote = 'Review iterations: not recorded'
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review iterations', value='not recorded',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata']['Review iterations'], 'not recorded')

    def test_extended_review_approval_must_be_affirmative_and_unconditional(self):
        negatives = (
            'The owner approved no review extension.',
            'The owner did not approve the review extension.',
            'The owner approved the review extension but later revoked it.',
            'The owner approved the review extension. The approval was later reversed.',
            'The owner approved the review extension, then changed the decision.',
            'The owner approved the review extension only if the operator agreed.',
            'The owner subsequently answered "yes" to continuing M01 beyond ten whole reviews. '
            'The owner later reversed that decision.',
            'The owner answered "yes" to continuing M01 beyond ten whole reviews if tests passed.',
            'The owner answered "yes" to continuing M99 beyond ten whole reviews.',
            'The owner approved the review extension to 22.',
            'The owner approved interactive launch ceiling 21.',
            'The owner approved the review extension; the decision was later changed.',
            'The owner approved the review extension. No P1/P2, but the approval was withdrawn.',
            'No P1/P2. The owner did not approve the review extension.',
            'The owner approved zero review extension.',
            'The owner approved the UI review.',
            'The owner asked if review should continue.',
            'The owner answered "yes\' to continuing M01 beyond ten whole reviews.',
            'The owner answered "yes" to continuing documentation. The guide says beyond ten whole reviews.',
        )
        for quote in negatives:
            with self.subTest(quote=quote):
                text = self.text.replace('**Review iterations.** 2', '**Review iterations.** 21\n**Review limit.** 21')
                text = text.replace('| Task |', '## Review\n\n' + quote + '\n\n| Task |')
                line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
                correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval',
                    value='owner approved review extension', evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                with self.assertRaisesRegex(ValueError, 'unsupported review limit approval'):
                    core.historical_record(text, 'status-M01.md', correction)
        positives = ('Whole-milestone review 10/10 FAIL. The owner subsequently answered "yes" to '
                     'continuing M01 beyond ten whole reviews, retaining the existing count and '
                     'using fresh Sol/xhigh reviews until it passes, then resuming the ordered goal.',
                     'The owner subsequently answered "yes" to continuing M01 beyond ten whole reviews.',
                     'The owner approved the review limit extension to 21.',
                     'The user authorized extension of the whole review limit to 21.',
                     'The owner approved the review extension. No P1/P2.')
        for quote in positives:
            with self.subTest(quote=quote):
                text = self.text.replace('**Review iterations.** 2', '**Review iterations.** 21\n**Review limit.** 21')
                text = text.replace('| Task |', '## Review\n\n' + quote + '\n\n| Task |')
                line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
                correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval',
                    value='owner approved review extension', evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['blockers'], [])

        literal = self.text.replace('**Review iterations.** 2', '**Review iterations.** 21\n'
            '**Review limit.** 21\n**Review limit approval.** No owner approved an extension')
        self.assertIn('recorded review limit approval is ambiguous or unsupported',
                      core.historical_record(literal, 'status-M01.md')['blockers'])
        reversed_literal = literal.replace('No owner approved an extension',
            'The owner approved the extension; the approval was later reversed')
        self.assertIn('recorded review limit approval is ambiguous or unsupported',
                      core.historical_record(reversed_literal, 'status-M01.md')['blockers'])
        for value in ('The owner approved the review extension; the decision was later changed',
                      'The owner approved the review extension to 22',
                      'The owner approved the review extension only if tests passed',
                      'The owner answered "yes" to continuing M99 beyond ten whole reviews'):
            with self.subTest(literal=value):
                self.assertIn('recorded review limit approval is ambiguous or unsupported',
                    core.historical_record(literal.replace('No owner approved an extension', value),
                                           'status-M01.md')['blockers'])
        self.assertEqual(core.historical_record(literal.replace('No owner approved an extension',
            'The owner approved the review extension to 21'), 'status-M01.md')['blockers'], [])
        thirty = literal.replace('**Review iterations.** 21', '**Review iterations.** 30').replace(
            '**Review limit.** 21', '**Review limit.** 30').replace('No owner approved an extension',
            'Owner approved interactive launch ceiling 30')
        self.assertEqual(core.historical_record(thirty, 'status-M01.md')['blockers'], [])
        for value in ('Owner did not approve interactive launch ceiling 30',
                      'Owner approved interactive launch ceiling 31',
                      'Owner approved interactive launch ceiling 30; the decision was changed'):
            with self.subTest(literal=value):
                self.assertIn('recorded review limit approval is ambiguous or unsupported',
                    core.historical_record(thirty.replace('Owner approved interactive launch ceiling 30', value),
                                           'status-M01.md')['blockers'])
        continued = literal.replace('No owner approved an extension',
            'The owner approved the review extension to 21.\nThe decision was later changed.')
        self.assertIn('recorded review limit approval is ambiguous or unsupported',
                      core.historical_record(continued, 'status-M01.md')['blockers'])
        later = literal.replace('No owner approved an extension', 'The owner approved the review extension to 21')
        later = later.replace('| Task |', '## Review\n\nLater, the approval was withdrawn.\n\n| Task |')
        self.assertIn('recorded review limit approval is ambiguous or unsupported',
                      core.historical_record(later, 'status-M01.md')['blockers'])

    def test_extension_citation_cannot_hide_source_context(self):
        quote = 'The owner approved the review extension.'
        for suffix in (' The decision was later changed.', '\nThe decision was later changed.',
                       '\n\nThe decision was later changed.', '\n\nLater, the approval was withdrawn.',
                       '\n\nSubsequently, the owner changed their mind.',
                       '\n\nThat permission was canceled.',
                       '\n\nThe refreshed approval was withdrawn and launch reference after the owner\'s M01 review continuation',
                       '; the decision was later changed.', '\nOnly if tests passed.'):
            with self.subTest(suffix=suffix):
                text = self.text.replace('**Review iterations.** 2',
                    '**Review iterations.** 21\n**Review limit.** 21')
                text = text.replace('| Task |', '## Review\n\n' + quote + suffix + '\n\n| Task |')
                line = next(n for n, actual in enumerate(text.splitlines(), 1) if quote in actual)
                correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval',
                    value='owner approved review extension',
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                with self.assertRaisesRegex(ValueError, 'unsupported review limit approval'):
                    core.historical_record(text, 'status-M01.md', correction)
        text = self.text.replace('**Review iterations.** 2',
            '**Review iterations.** 21\n**Review limit.** 21')
        text = text.replace('| Task |', '## Review\n\nOnly if tests passed.\n' + quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval',
            value='owner approved review extension',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unsupported review limit approval'):
            core.historical_record(text, 'status-M01.md', correction)
        prefixed = 'Whole-milestone review 10/10 FAIL. ' + quote
        text = text.replace(quote, prefixed)
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == prefixed)
        correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval',
            value='owner approved review extension',
            evidence=[dict(start_line=line, end_line=line, quote=prefixed)])])
        with self.assertRaisesRegex(ValueError, 'unsupported review limit approval'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_extension_correction_value_cannot_add_ambiguity(self):
        quote = 'The owner approved the review extension.'
        text = self.text.replace('**Review iterations.** 2',
            '**Review iterations.** 21\n**Review limit.** 21')
        text = text.replace('| Task |', '## Review\n\n' + quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        for value in ('owner approved review extension; the decision was later changed',
                      'owner approved review extension to 22',
                      f'Historical owner continuation recorded at frozen lines {line}-{line}; '
                      'ceiling 22 is a proposed interpretation for this closed record only.'):
            with self.subTest(value=value):
                correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval',
                    value=value, evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                with self.assertRaisesRegex(ValueError, 'unsupported review limit approval'):
                    core.historical_record(text, 'status-M01.md', correction)

    def test_recorded_zero_counter_for_rowless_withdrawal_remains_supported(self):
        quote = 'Review iterations: 0'
        text = h.retirement_text(quote + '\n', 'M01-01', Outcome='cancelled',
            Review='not applicable', Disposition='Owner withdrew the option')
        text = text.replace('status-M01-01.md', 'option-M01-01.md').replace('**Review iterations.** 2\n', '')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = dict(milestone_id='M01-01', record_path='tabilet/docs/history/option-M01-01.md',
            record_sha256=digest(text), corrections=[dict(kind='supply-metadata', field='Review iterations', value='0',
                evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        record = core.historical_record(text, 'option-M01-01.md', correction)
        self.assertEqual(record['metadata']['Review iterations'], '0')
        self.assertEqual(record['blockers'], [])

    def test_metadata_evidence_refuses_mismatched_index_and_negative_verification(self):
        content = '| M02 | completed | 2026-09-12 | [M02](status-M02.md) | Delivery |'
        text = self.text.replace('**Outcome.** completed\n', '')
        correction = entry(text, [dict(kind='supply-metadata', field='Outcome', value='completed', evidence=[dict(
            path='tabilet/docs/history/index.md', commit='a' * 40, content=content, sha256=digest(content),
            start_line=1, end_line=1, quote=content)])])
        with self.assertRaisesRegex(ValueError, 'unsupported Outcome'):
            core.historical_record(text, 'status-M01.md', correction)

        quote = 'Go tests passed but the full suite failed.'
        text = self.text.replace('**Verification.** tests passed; review found no blocking issues\n', '').replace(
            '| Task |', quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Verification', value='Recorded results: Go tests passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unsupported Verification'):
            core.historical_record(text, 'status-M01.md', correction)

        text = self.text.replace('**Verification.** tests passed; review found no blocking issues\n', '').replace(
            '| Task |', 'Go tests passed\nUnrelated claim\n\n| Task |')
        locations = {value: n for n, value in enumerate(text.splitlines(), 1) if value in ('Go tests passed', 'Unrelated claim')}
        correction = entry(text, [dict(kind='supply-metadata', field='Verification',
            value='Recorded results: Go tests passed; Unrelated claim', evidence=[
                dict(start_line=locations[q], end_line=locations[q], quote=q)
                for q in ('Go tests passed', 'Unrelated claim')])])
        with self.assertRaisesRegex(ValueError, 'unsupported Verification'):
            core.historical_record(text, 'status-M01.md', correction)

        quote = '| Task | `[+]` | worktree commit abcdef0 |'
        text = self.text.replace('**Evidence.** unversioned\n', '').replace(
            '**Worktree.** unversioned', '**Worktree.** clean').replace('| Task | `[+]` | verified |', quote)
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Evidence', value='abcdef0' + '1' * 33,
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unsupported Evidence'):
            core.historical_record(text, 'status-M01.md', correction)

        quote = '# Status M01'
        text = self.text.replace('**Source specification.** tabilet/memory-bank/milestone.md#m01-delivery\n', '').replace(
            '| Task |', quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Source specification',
            value='tabilet/memory-bank/milestone.md#wrong-owner',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unrecorded anchor'):
            core.historical_record(text, 'status-M01.md', correction)

        quote = 'Go tests are available.'
        text = self.text.replace('**Verification.** tests passed; review found no blocking issues\n', '').replace(
            '| Task |', quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Verification', value='Recorded results: ' + quote,
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unsupported Verification'):
            core.historical_record(text, 'status-M01.md', correction)

        quote = 'Task review 21 PASS.'
        text = self.text.replace('| Task |', '## Review\n\n' + quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review limit', value='21',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unsupported review limit'):
            core.historical_record(text, 'status-M01.md', correction)

        quote = 'The owner did not approve continuing the review.'
        text = self.text.replace('| Task |', '## Review\n\n' + quote + '\n\n| Task |')
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review limit approval', value='owner approved',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'unsupported review limit approval'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_metadata_corrections_accept_explicit_recorded_facts(self):
        commit = 'abcdef0' + '1' * 33
        for field, old, value, quote in (
                ('Outcome', 'completed', 'completed', '**Status.** complete'),
                ('Retired', '2026-09-12', '2026-09-12', 'Retired: 2026-09-12'),
                ('Evidence', 'unversioned', commit, 'Evidence: commit abcdef0'),
                ('Worktree', 'unversioned', 'clean', 'Worktree: clean'),
                ('Review iterations', '2', '2', 'Review gate iterations: 2'),
                ('Verification', 'tests passed; review found no blocking issues', 'Recorded results: Go tests passed', 'Go tests passed'),
                ('Consolidated into', 'no current-truth change', 'no current-truth change', 'Consolidated into: no current-truth change')):
            with self.subTest(field=field):
                text = self.text.replace(f'**{field}.** {old}\n', '').replace('| Task |', quote + '\n\n| Task |')
                if field == 'Evidence':
                    text = text.replace('**Worktree.** unversioned', '**Worktree.** clean')
                if field == 'Worktree':
                    text = text.replace('**Evidence.** unversioned', '**Evidence.** ' + 'a' * 40)
                line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
                correction = entry(text, [dict(kind='supply-metadata', field=field, value=value,
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata'][field], value)

    def test_hashes_and_ids_are_bound_to_the_literal_bytes(self):
        text, correction = self.expansion()
        parsed = core.historical_record(text, 'status-M01.md', correction)
        self.assertEqual(parsed['status'], '| Task | `[+]` | verified |\n')
        self.assertEqual(parsed['literal_metadata']['Evidence'], 'abcdef0')
        with self.assertRaisesRegex(ValueError, 'stale'):
            core.historical_record(text + '\n', 'status-M01.md', correction)
        with self.assertRaises(ValueError):
            core.historical_record(text, 'status-M02.md', correction)

    def test_missing_review_cannot_be_supplied_by_a_prospective_task(self):
        text = self.text.replace('**Review.** passed\n', '')
        quote = 'Run tests and perform deep code review.'
        text = text.replace('| verified |', '| ' + quote + ' |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if quote in value)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                                       evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

        for quote in ('Whole review 2/10 PASS with no P1/P2.', 'Review: passed'):
            for continuation in ('The review result was later invalidated.',
                                 'Later, the owner changed that decision.',
                                 'The pass is contingent on further verification.',
                                 'Task review 2/10 FAIL. The review result was later invalidated.'):
                with self.subTest(quote=quote, continuation=continuation):
                    text = self.text.replace('**Review.** passed\n', '').replace(
                        '| Task |', '## Review\n\n' + quote + '\n' + continuation + '\n\n| Task |')
                    line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
                    correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                        evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                    with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                        core.historical_record(text, 'status-M01.md', correction)
                    literal = text.replace('**Outcome.** completed', '**Outcome.** completed\n**Review.** passed')
                    self.assertIn('unrecognized continuation after recorded review pass',
                                  core.historical_record(literal, 'status-M01.md')['blockers'])

    def test_pass_continuation_is_consistent_across_source_locations(self):
        for location in ('literal_envelope', 'corrected_envelope', 'preamble', 'preamble_literal', 'review'):
            for continuation in ('The result was later invalidated.',
                                 'Later, the owner changed that decision.',
                                 'The pass is contingent on further verification.'):
                with self.subTest(location=location, continuation=continuation):
                    quote = '**Review.** passed' if location in {'literal_envelope', 'preamble_literal'} else 'Review: passed'
                    text = self.text.replace('**Review.** passed\n', '')
                    if location in {'literal_envelope', 'corrected_envelope'}:
                        text = text.replace('## Milestone specification',
                            quote + '\n' + continuation + '\n\n## Milestone specification')
                    elif location in {'preamble', 'preamble_literal'}:
                        text = text.replace('| Task |', quote + '\n' + continuation + '\n\n| Task |')
                    else:
                        text = text.replace('| Task |', '## Review\n\n' + quote + '\n' + continuation + '\n\n| Task |')
                    line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
                    if location == 'literal_envelope':
                        self.assertIn('unrecognized continuation after recorded review pass',
                                      core.historical_record(text, 'status-M01.md')['blockers'])
                    else:
                        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                            core.historical_record(text, 'status-M01.md', correction)

    def test_pass_formats_reject_same_and_following_line_qualifications(self):
        forms = ('Review: passed', 'Review passed', '**Review.** passed',
                 'Whole review 2/10 PASS with no P1/P2.')
        for location in ('envelope', 'preamble', 'review'):
            for quote in forms:
                for joiner in (' ', '\n', '\n\n'):
                    with self.subTest(location=location, quote=quote, joiner=repr(joiner)):
                        text = self.text.replace('**Review.** passed\n', '')
                        statement = quote + joiner + 'The result was later invalidated.'
                        if location == 'envelope':
                            text = text.replace('## Milestone specification', statement + '\n\n## Milestone specification')
                        elif location == 'preamble':
                            text = text.replace('| Task |', statement + '\n\n| Task |')
                        else:
                            text = text.replace('| Task |', '## Review\n\n' + statement + '\n\n| Task |')
                        line = next(n for n, value in enumerate(text.splitlines(), 1) if quote in value)
                        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                        with self.assertRaises(ValueError):
                            core.historical_record(text, 'status-M01.md', correction)

    def test_other_metadata_cannot_hide_review_result_conflicts(self):
        for location in ('envelope', 'preamble', 'preamble_colon', 'preamble_bold_colon', 'review', 'verification_section'):
            for claim in ('The review result was later invalidated.',
                          'The review was not accepted.', 'The result of the review was withdrawn.',
                          'The review passed, then was invalidated.', 'Not review passed.',
                          'The review completed, then was invalidated.',
                          'Review: passed, then invalidated.', 'Whole review 2/10 PASS, then invalidated.'):
                with self.subTest(location=location, claim=claim):
                    if location == 'envelope':
                        text = self.text.replace('**Verification.** tests passed; review found no blocking issues',
                                                 '**Verification.** ' + claim)
                    elif location == 'review':
                        text = self.text.replace('| Task |', '## Review\n\n**Verification.** '
                                                 + claim + '\n\n| Task |')
                    elif location == 'verification_section':
                        text = self.text.replace('| Task |', '## Verification attempts and authority\n\n**Verification.** '
                                                 + claim + '\n\n| Task |')
                    else:
                        label = {'preamble': '**Verification.**', 'preamble_colon': 'Verification:',
                                 'preamble_bold_colon': '**Verification:**'}[location]
                        text = self.text.replace('| Task |', label + ' ' + claim + '\n\n| Task |')
                    self.assertIn('ambiguous review-result claim in structured metadata',
                                  core.historical_record(text, 'status-M01.md')['blockers'])

    def test_recovered_status_retains_review_context_conflicts(self):
        status = ('## Review\n\nReview: passed\nThe result was later invalidated.\n\n'
                  '| Task | `[+]` | verified |\n')
        text = self.text.replace('| Task | `[+]` | verified |\n', status)
        operation = dict(kind='recover-document', document='status', content=status, sha256=digest(status),
            source=dict(commit='a' * 40, path='tabilet/memory-bank/status-M01.md', start_line=1,
                        end_line=len(status.splitlines()), source_sha256=digest(status)))
        result = core.historical_record(text, 'status-M01.md', entry(text, [operation]))
        self.assertIn('unrecognized continuation after recorded review pass', result['blockers'])

    def test_wrapped_structured_review_claims_are_not_hidden(self):
        for location in ('envelope', 'preamble', 'preamble_colon', 'preamble_bold_colon', 'review'):
            for indentation in ('', '  ', '  - ', '> '):
                with self.subTest(location=location, indentation=repr(indentation)):
                    wrapped = 'Tests passed.\n' + indentation + 'The review result was later invalidated.'
                    if location == 'envelope':
                        text = self.text.replace('**Verification.** tests passed; review found no blocking issues',
                                                 '**Verification.** ' + wrapped)
                    elif location == 'review':
                        text = self.text.replace('| Task |', '## Review\n\n**Verification.** '
                                                 + wrapped + '\n\n| Task |')
                    else:
                        label = {'preamble': '**Verification.**', 'preamble_colon': 'Verification:',
                                 'preamble_bold_colon': '**Verification:**'}[location]
                        text = self.text.replace('| Task |', label + ' ' + wrapped + '\n\n| Task |')
                    record = core.historical_record(text, 'status-M01.md')
                    self.assertIn('ambiguous review-result claim in structured metadata', record['blockers'])
                    if location != 'envelope':
                        self.assertIn(wrapped, record['status'])

    def test_wrapped_fields_do_not_join_across_fenced_or_code_blocks(self):
        for example in ('```text\nThe review result was later invalidated.\n```',
                        '    The review result was later invalidated.'):
            with self.subTest(example=example):
                text = self.text.replace('| Task |', '**Verification.** Tests passed.\n'
                                         + example + '\n\n| Task |')
                self.assertEqual(core.historical_record(text, 'status-M01.md')['blockers'], [])

    def test_empty_label_line_cannot_hide_wrapped_review_claim(self):
        for label in ('**Verification.**', '**Verification:**', 'Verification:'):
            for indentation in ('', '  ', '  - ', '> '):
                for heading in ('', '## Verification attempts and authority\n\n'):
                    with self.subTest(label=label, indentation=repr(indentation), heading=heading):
                        text = self.text.replace('| Task |', heading + label + '\n' + indentation
                            + 'The review result was later invalidated.\n\n| Task |')
                        self.assertIn('ambiguous review-result claim in structured metadata',
                                      core.historical_record(text, 'status-M01.md')['blockers'])

    def test_separate_authoritative_block_cannot_hide_review_result_reference(self):
        for prefix in ('', '- ', '> '):
            for location in ('preamble', 'review', 'verification_section'):
                for statement in ('The review result was later invalidated.',
                                  'The review\nresult was later invalidated.'):
                    with self.subTest(prefix=prefix, location=location, statement=statement):
                        heading = {'preamble': '', 'review': '## Review\n\n',
                                   'verification_section': '## Verification attempts and authority\n\n'}[location]
                        text = self.text.replace('| Task |', '**Verification.** Tests passed.\n\n'
                            + heading + prefix + statement + '\n\n| Task |')
                        self.assertIn('ambiguous recorded review-result reference',
                                      core.historical_record(text, 'status-M01.md')['blockers'])

    def test_nested_list_in_structured_paragraph_preserves_status_bytes(self):
        wrapped = ('**Verification.** Tests passed.\n  - Further details.\n'
                   '    - The review result was later invalidated.\n')
        text = self.text.replace('| Task |', wrapped + '\n| Task |')
        record = core.historical_record(text, 'status-M01.md')
        self.assertIn('ambiguous review-result claim in structured metadata', record['blockers'])
        self.assertIn(wrapped, record['status'])

    def test_wrapped_recovered_status_preserves_literal_source_and_offsets(self):
        status = ('**Verification.** Tests passed.\n'
                  '  - The review result was later invalidated.\n\n'
                  '| Task | `[+]` | verified |\n')
        text = self.text.replace('| Task | `[+]` | verified |\n', status)
        source = dict(commit='a' * 40, path='tabilet/memory-bank/status-M01.md', start_line=11,
                      end_line=10 + len(status.splitlines()), source_sha256=digest(status))
        operation = dict(kind='recover-document', document='status', content=status,
                         sha256=digest(status), source=source)
        record = core.historical_record(text, 'status-M01.md', entry(text, [operation]))
        self.assertIn('ambiguous review-result claim in structured metadata', record['blockers'])
        self.assertEqual(record['status'], status)
        self.assertEqual(record['sources']['status'], source)
        self.assertEqual(record['offsets']['status'], 10)

    def test_review_claims_in_all_other_structured_status_fields_block(self):
        for field in ('State', 'Verification', 'Consolidated into', 'Evidence', 'Worktree',
                      'Disposition', 'Marker correction', 'Custom notes'):
            for claim in ('The review result was later invalidated.',
                          'Review: passed, then invalidated.', 'Whole review 2/10 PASS, then invalidated.'):
                with self.subTest(field=field, claim=claim):
                    text = self.text.replace('| Task |', '**' + field + '.** ' + claim + '\n\n| Task |')
                    self.assertIn('ambiguous review-result claim in structured metadata',
                                  core.historical_record(text, 'status-M01.md')['blockers'])

    def test_named_review_result_fields_fail_closed(self):
        for name in ('Review result', 'Review verdict', 'Review outcome', 'Review decision'):
            for label in ('**' + name + '.**', '**' + name + ':**', name + ':'):
                for value in ('invalidated.', 'passed, then withdrawn.', 'unknown.'):
                    with self.subTest(label=label, value=value):
                        text = self.text.replace('| Task |', label + ' ' + value + '\n\n| Task |')
                        self.assertIn('ambiguous review-result claim in structured metadata',
                                      core.historical_record(text, 'status-M01.md')['blockers'])
        quote = '**Review result.** passed'
        text = self.text.replace('**Review.** passed\n', '').replace('| Task |', quote + '\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_external_citation_cannot_supply_review_acceptance(self):
        text = self.text.replace('**Review.** passed\n', '')
        quote = 'Review: passed'
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed', evidence=[dict(
            path='tabilet/docs/history/index.md', commit='a' * 40, content=quote, sha256=digest(quote),
            start_line=1, end_line=1, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_earlier_pending_state_requires_matching_later_review_counter(self):
        state = ('**State.** Tasks complete; R1-R3 verified, whole-milestone review pending. '
                 'Persisted review count 0/10.')
        text = self.text.replace('| Task |', state + '\n\n## Review\n\n'
            'Persisted iteration count: 2/10, passed.\n\n| Task |')
        self.assertEqual(core.historical_record(text, 'status-M01.md')['blockers'], [])
        stale = text.replace('Persisted iteration count: 2/10', 'Persisted iteration count: 1/10')
        self.assertIn('ambiguous review-result claim in structured metadata',
                      core.historical_record(stale, 'status-M01.md')['blockers'])
        for suffix in (', failed.', ', passed but later invalidated.'):
            bad_counter = text.replace('Persisted iteration count: 2/10, passed.',
                                       'Persisted iteration count: 2/10' + suffix)
            self.assertIn('ambiguous review-result claim in structured metadata',
                          core.historical_record(bad_counter, 'status-M01.md')['blockers'])
        later_state = self.text.replace('| Task |', '## Review\n\n'
            'Persisted iteration count: 2/10, passed.\n' + state + '\n\n| Task |')
        self.assertIn('ambiguous review-result claim in structured metadata',
                      core.historical_record(later_state, 'status-M01.md')['blockers'])

    def test_review_correction_requires_an_explicit_passed_result(self):
        for quote, accepted in (('review not passed', False),
                                ('review failed, but tests passed', False),
                                ('review performed', False),
                                ('Review: passed', True)):
            with self.subTest(quote=quote):
                text = self.text.replace('**Review.** passed\n', '').replace('| Task |', quote + '\n\n| Task |')
                line = next(n for n, value in enumerate(text.splitlines(), 1) if quote in value)
                correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                if accepted:
                    self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata']['Review'], 'passed')
                else:
                    with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                        core.historical_record(text, 'status-M01.md', correction)

        text = self.text.replace('**Review.** passed\n', '').replace('| Task |', 'Not Review: passed\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if 'Not Review: passed' in value)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote='Review: passed')])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_completed_retirement_row_explicitly_records_zero_review_defects(self):
        def inspect(row, *, heading='Tasks', iteration='2', evidence_quote=None):
            status = ('# Status M01 - Delivery\n\n**Milestone.** M01\n'
                      '**Review gate iterations.** ' + iteration + '\n\n## ' + heading +
                      '\n\n| Item | State | Notes |\n|---|---|---|\n' + row + '\n')
            text = h.retirement_text(status).replace('**Review.** passed\n', '')
            line = next(n for n, value in enumerate(text.splitlines(), 1) if value == row)
            correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                evidence=[dict(start_line=line, end_line=line, quote=evidence_quote or row)])])
            return core.historical_record(text, 'status-M01.md', correction)

        valid = ('| M01.5: Deep code review & milestone retirement | `[+]` | '
                 'Ran full verification suite (`check`); deep code review performed with '
                 '0 defects remaining; retired M01 to `tabilet/docs/history/status-M01.md`. |')
        self.assertEqual(inspect(valid)['metadata']['Review'], 'passed')
        for row, heading, iteration in (
            (valid.replace('performed with 0', 'will be performed with 0'), 'Tasks', '2'),
            (valid.replace('0 defects remaining;', '0 defects remaining if fixed;'), 'Tasks', '2'),
            (valid.replace('0 defects remaining;', '0 defects remaining; review later failed;'), 'Tasks', '2'),
            (valid.replace('`check`', '`check failed`'), 'Tasks', '2'),
            (valid.replace('`[+]`', '`[ ]`'), 'Tasks', '2'),
            (valid.replace('retired M01', 'retired M02'), 'Tasks', '2'),
            (valid, 'Example tasks', '2'),
        ):
            with self.subTest(row=row, heading=heading):
                with self.assertRaises(ValueError):
                    inspect(row, heading=heading, iteration=iteration)
        self.assertIn('retained review counter conflicts with retirement metadata',
                      inspect(valid, iteration='1')['blockers'])
        with self.assertRaises(ValueError):
            inspect(valid, evidence_quote='deep code review performed with 0 defects remaining')

        no_counter = ('# Status M01 - Delivery\n\n**Milestone.** M01\n\n## Tasks\n\n'
                      '| Item | State | Notes |\n|---|---|---|\n' + valid + '\n')
        text = h.retirement_text(no_counter).replace('**Review.** passed\n', '')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == valid)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=valid)])])
        with self.assertRaisesRegex(ValueError, 'recorded review counter'):
            core.historical_record(text, 'status-M01.md', correction)

        conflict = ('# Status M01 - Delivery\n\n**Milestone.** M01\n'
                    '**Review gate iterations.** 2\n\n## Tasks\n\n'
                    '| Item | State | Notes |\n|---|---|---|\n' + valid + '\n\n'
                    '## Review\n\nReview: failed\n')
        text = h.retirement_text(conflict).replace('**Review.** passed\n', '')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == valid)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=valid)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

        later = no_counter.replace('**Milestone.** M01\n',
            '**Milestone.** M01\n**Review gate iterations.** 2\n') + '\nIt was later withdrawn.\n'
        text = h.retirement_text(later).replace('**Review.** passed\n', '')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == valid)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=valid)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

        duplicate = valid.replace('M01.5:', 'M01.6:')
        text = h.retirement_text(no_counter.replace('**Milestone.** M01\n',
            '**Milestone.** M01\n**Review gate iterations.** 2\n').replace(valid, valid + '\n' + duplicate))
        text = text.replace('**Review.** passed\n', '')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == valid)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=valid)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_zero_defect_retirement_row_is_shared_by_lookup_and_dependencies(self):
        row = ('| M144.5: Deep code review & milestone retirement | `[+]` | '
               'Ran full verification suite (`check`); deep code review performed with '
               '0 defects remaining; retired M144 to `tabilet/docs/history/status-M144.md`. |')
        status = ('# Status M144 - Delivery\n\n**Milestone.** M144\n'
                  '**Review gate iterations.** 2\n\n## Tasks\n\n'
                  '| Item | State | Notes |\n|---|---|---|\n' + row + '\n')
        raw = h.retirement_text(status, milestone_id='M144').replace('**Review.** passed\n', '')
        number = next(n for n, value in enumerate(raw.splitlines(), 1) if value == row)
        correction = entry(raw, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=number, end_line=number, quote=row)])], identity='M144')
        history = self.root / 'tabilet/docs/history'
        history.mkdir(parents=True)
        (history / 'status-M144.md').write_text(raw)
        (history / 'corrections.json').write_text(manifest([correction]))
        (history / 'index.md').write_text('| Milestone | Outcome | Retired | Record | Summary |\n'
            '|---|---|---|---|---|\n| M144 | completed | 2026-09-12 | [M144](status-M144.md) | Fixture |\n')
        bank = self.root / 'tabilet/memory-bank'
        (bank / 'milestone.md').write_text('# Milestones\n\n[History](../docs/history/index.md)\n\n'
                                          '## M01 - Delivery\n\n**Depends on.** M144\n')
        snapshot = core.row_snapshot(self.root)
        self.assertEqual(snapshot['history']['problems'], [])
        self.assertIn('M144', horizon._live_projection(core, self.root)['milestones'])
        with audit.open_database(self.root / 'tabilet/audit.sqlite3') as connection:
            state = index.sync(connection, self.root)
            ready = index.readiness(connection, state['workspace_id'], self.root)
            self.assertEqual(len(ready['ready']), 1)
        record = snapshot['history']['records']['status-M144.md']
        self.assertEqual(record['blockers'], [])
        self.assertEqual(raw.splitlines()[number - 1], row)

    def test_unfinished_rows_and_inconsistent_counters_remain_blocking(self):
        text = self.text.replace('`[+]`', '`[ ]`')
        self.assertIn('retired status contains unfinished task rows', core.historical_record(text, 'status-M01.md')['blockers'])
        text = self.text.replace('| Task', 'Review gate iterations: 3\n\n| Task')
        self.assertIn('retained review counter conflicts with retirement metadata', core.historical_record(text, 'status-M01.md')['blockers'])

        text = self.text.replace('| Task', 'Review iterations: 2\nReview iterations: 3\n\n| Task')
        self.assertIn('retained review counter conflicts with retirement metadata', core.historical_record(text, 'status-M01.md')['blockers'])

        text = self.text.replace('| Task', '## Example\nReview iterations: 3\n\n## Tasks\n| Task')
        self.assertNotIn('retained review counter conflicts with retirement metadata', core.historical_record(text, 'status-M01.md')['blockers'])

        for state in ('pending', 'planned', 'not started', 'incomplete', 'failed'):
            with self.subTest(state=state):
                text = self.text.replace('| Task |', '**Status.** ' + state + '\n\n| Task |')
                self.assertIn('retained status conflicts with retirement outcome', core.historical_record(text, 'status-M01.md')['blockers'])

    def test_numbered_whole_review_requires_a_matching_unambiguous_pass(self):
        cases = [
            ('Whole review 2/10 PASS with no P1/P2.', True),
            ('Whole review 1/10 FAIL found an issue; fixes passed. Whole review 2/10 PASS with no P1/P2.', True),
            ('Whole review 1/10 PASS with no P1/P2.', False),
            ('Whole review 2/999 PASS with no P1/P2.', False),
            ('Task review 2/10 PASS with no P1/P2.', False),
            ('Whole review 2/10 PASS with no P1/P2. Review failed.', False),
            ('Run whole review 2/10 PASS with no P1/P2.', False),
            ('Whole review 2/10 PASS with no P1/P2 pending.', False),
        ]
        for quote, accepted in cases:
            with self.subTest(quote=quote):
                text = self.text.replace('**Review.** passed\n', '').replace('| Task |', '## Review\n\n' + quote + '\n\n| Task |')
                line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
                correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                if accepted:
                    self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata']['Review'], 'passed')
                else:
                    with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                        core.historical_record(text, 'status-M01.md', correction)

        quote = 'Whole review 2/10 PASS with no P1/P2.'
        text = self.text.replace('**Review.** passed\n', '').replace(
            '| Task |', '## Review\n\n' + quote + '\nWhole review 2/10 FAIL.\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_review_pass_citation_must_be_unfenced_status_or_envelope_evidence(self):
        for quote in ('Review: passed', 'Whole review 2/10 PASS with no P1/P2.'):
            for source in ('status_example', 'example_section', 'nested_example',
                           'nested_simulation', 'review_inside_simulation', 'specification'):
                with self.subTest(quote=quote, source=source):
                    text = self.text.replace('**Review.** passed\n', '')
                    if source == 'status_example':
                        text = text.replace('| Task |', '```text\n' + quote + '\n```\n\n| Task |')
                    elif source == 'example_section':
                        text = text.replace('| Task |', '## Example template\n\n' + quote + '\n\n| Task |')
                    elif source == 'nested_example':
                        text = text.replace('| Task |', '## Review\n\n### Example\n\n' + quote + '\n\n| Task |')
                    elif source == 'nested_simulation':
                        text = text.replace('| Task |', '## Review\n\n### Simulation\n\n' + quote + '\n\n| Task |')
                    elif source == 'review_inside_simulation':
                        text = text.replace('| Task |', '## Simulation\n\n### Review\n\n' + quote + '\n\n| Task |')
                    else:
                        text = text.replace('**Acceptance.** Feature works.',
                                            '**Acceptance.** Feature works.\n\n' + quote)
                    line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
                    correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                        evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                    with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                        core.historical_record(text, 'status-M01.md', correction)

        text = self.text.replace('**Review.** passed', 'Review: passed')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == 'Review: passed')
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote='Review: passed')])])
        self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata']['Review'], 'passed')

    def test_canonical_pass_refuses_conflicting_review_evidence(self):
        quote = 'Review: passed'
        for conflict in ('Whole review 2/10 FAIL.', 'Whole review 3/10 PASS.', 'Review: failed',
                         'Whole review failed.', 'Whole review: not passed.',
                         'Whole review was not passed.', 'Review: did not pass.', 'Review: in progress.',
                         'Review 2/10 FAILED.', 'Whole review 2/10 NOT PASSED.', 'Review 2/10 PENDING.',
                         'Whole review 2/10: FAIL.', 'Whole review 2/10 — FAIL.',
                         'Whole review 2/10 was FAILED.', 'Whole review 2/10: unknown.',
                         'Review: result unknown', '| Review | failed |'):
            with self.subTest(conflict=conflict):
                text = self.text.replace('**Review.** passed\n', '').replace(
                    '| Task |', '## Review\n\n' + quote + '\n' + conflict + '\n\n| Task |')
                line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
                correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
                    core.historical_record(text, 'status-M01.md', correction)
        text = self.text.replace('**Review.** passed', 'Review: passed\nReview: failed')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)
        text = self.text.replace('| Task |', '## Review\n\nWhole review 2/10 FAIL.\n\n| Task |')
        self.assertIn('conflicting whole review result', core.historical_record(text, 'status-M01.md')['blockers'])

    def test_examples_do_not_create_conflicting_review_results(self):
        quote = 'Whole review 2/10 PASS with no P1/P2.'
        text = self.text.replace('**Review.** passed\n', '').replace(
            '| Task |', '## Review\n\n' + quote + '\n\n### Example\n\nWhole review 2/10 FAIL.\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['blockers'], [])

        text = self.text.replace('**Review.** passed\n', '').replace(
            '| Task |', '## Review\n\n' + quote + '\nWhole-milestone review 2/10, passed.\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['blockers'], [])

        text = self.text.replace('**Review.** passed\n', '').replace(
            '| Task |', '## Review\n\n' + quote + '\nTask review 2/10 FAIL.\n\n| Task |')
        line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['blockers'], [])

    def test_review_section_and_source_binding_preserve_literal_evidence(self):
        quote = 'Whole review 2/10 PASS with no P1/P2.'
        for heading in ('## Review\n\n### Iteration 2', '## Milestone closure\n\n### Review'):
            with self.subTest(heading=heading):
                text = self.text.replace('**Review.** passed\n', '').replace('| Task |', heading + '\n\n' + quote + '\n\n| Task |')
                line = next(n for n, value in enumerate(text.splitlines(), 1) if value == quote)
                correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                    evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                self.assertEqual(core.historical_record(text, 'status-M01.md', correction)['metadata']['Review'], 'passed')

        # A quote from another embedded document is not the record's own
        # status evidence, even when the embedded content checksum is correct.
        text = self.text.replace('**Review.** passed\n', '')
        external = 'Review: passed'
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed', evidence=[dict(
            path='tabilet/docs/history/index.md', commit='a' * 40, content=external, sha256=digest(external),
            start_line=1, end_line=1, quote=external)])])
        with self.assertRaisesRegex(ValueError, 'cannot supply acceptance'):
            core.historical_record(text, 'status-M01.md', correction)

    def test_explicit_retained_status_identity_must_match_record(self):
        for prefix, row in (('# Status M02\n\n', '| Task |'),
                            ('# Status m02\n\n', '| Task |'),
                            ('**Milestone.** M02\n\n', '| Task |'),
                            ('', '| M02.1 — other task |'),
                            ('', '| m02.1 — other task |')):
            with self.subTest(prefix=prefix, row=row):
                text = self.text.replace('| Task |', prefix + row)
                with self.assertRaisesRegex(ValueError, 'status.*identity'):
                    core.historical_record(text, 'status-M01.md')

    def test_recovery_preserves_source_bytes_locations_and_refuses_modified_content(self):
        raw_status = '| Task | `[+]` | verified |\n'
        start = next(n for n, value in enumerate(self.text.splitlines(), 1) if value == raw_status.rstrip())
        operation = dict(kind='recover-document', document='status', content=raw_status, sha256=digest(raw_status),
                         source=dict(commit='a' * 40, path='tabilet/docs/history/status-M01.md', start_line=start,
                                     end_line=start, source_sha256=digest(self.text)))
        correction = entry(self.text, [operation])
        result = core.historical_record(self.text, 'status-M01.md', correction)
        self.assertEqual(result['status'], raw_status)
        self.assertEqual(result['offsets']['status'], start - 1)
        changed = copy.deepcopy(correction)
        changed['corrections'][0]['content'] = raw_status.replace('verified', 'changed')
        with self.assertRaisesRegex(ValueError, 'hash'):
            core.historical_record(self.text, 'status-M01.md', changed)

    def test_recovery_cannot_change_or_omit_retained_task_states(self):
        original = self.text.replace('`[+]`', '`[ ]`')
        changed = '| Task | `[+]` | verified |\n'
        correction = entry(original, [dict(kind='recover-document', document='status',
            content=changed, sha256=digest(changed), source=dict(commit='a' * 40,
                path='tabilet/memory-bank/status-M01.md', start_line=1, end_line=1,
                source_sha256='a' * 64))])
        with self.assertRaisesRegex(ValueError, 'cannot change or discard'):
            core.historical_record(original, 'status-M01.md', correction)

    def test_execution_and_closure_cannot_add_a_manifest_or_use_a_compatibility_retirement(self):
        h.retire_fixture(self.root)
        before = core.row_snapshot(self.root)
        (self.root / core.HISTORY_CORRECTIONS).write_text(manifest([]))
        after = core.row_snapshot(self.root)
        self.assertNotEqual(horizon.snapshot_digest(before), horizon.snapshot_digest(after))
        self.assertIn('history corrections changed during execution', core.validate_row_transition(before, after))
        self.assertIn('history corrections changed during closure', horizon._closure_integrity_problems(before, after))
        # Both approval snapshots and interrupted-run recovery retain JSON.
        paths, _ = proposal._workflow_snapshot(core, self.root)
        self.assertIn(core.HISTORY_CORRECTIONS, paths)
        self.assertTrue(recovery._workflow_path(core.HISTORY_CORRECTIONS, core))
        h.run('git', 'add', '-A', cwd=self.root)
        h.run('git', 'commit', '-qm', 'history', cwd=self.root)
        commit = h.run('git', 'rev-parse', 'HEAD', cwd=self.root).stdout.strip()
        recovered = recovery._snapshot_at(core, self.root, commit)
        self.assertEqual(after['history']['corrections_sha256'], recovered['history']['corrections_sha256'])

    def test_projects_without_corrections_preserve_the_previous_snapshot_digest(self):
        # Frozen output of the pre-manifest snapshot contract. Existing
        # approval receipts without a manifest must not become stale solely
        # because this optional capability was added.
        previous = '4d7243b53a74e0f8213f8b76c4d240c6e6eb29a524f34bbefa29e83dc6916339'
        self.assertEqual(horizon.snapshot_digest({}), previous)
        self.assertEqual(horizon.snapshot_digest({'history': {'corrections_sha256': None}}), previous)
        self.assertNotEqual(horizon.snapshot_digest({'history': {'corrections_sha256': 'a' * 64}}), previous)

    def test_new_retirement_with_historical_alias_is_rejected(self):
        before = core.row_snapshot(self.root)
        path = h.retire_fixture(self.root)
        path.write_text(path.read_text().replace('\n## Status record\n', '\n## Final status\n'))
        after = core.row_snapshot(self.root)
        self.assertTrue(any('strict contract' in message for message in core.validate_row_transition(before, after)))

    def test_successor_correction_resolves_dependencies_without_rewriting_evidence(self):
        text = h.retirement_text('| Old | `[-]` | superseded |\n| New | `[+]` | accepted |\n')
        number = next(n for n, line in enumerate(text.splitlines(), 1) if '| New |' in line)
        correction = entry(text, [dict(kind='historical-successor', item='Old', successor='New',
            evidence=[dict(start_line=number, end_line=number, quote='| New | `[+]` | accepted |')])])
        record = core.historical_record(text, 'status-M01.md', correction)
        self.assertNotIn('Accepted successor:', record['status'])
        rows = [dict(key=row['item'], task_id=row['item'], milestone_id='M01',
                     file='status-M01.md', label=row['item'], notes=' '.join(row['cells'][2:]))
                for row in core.status_rows(record['task_status'])]
        self.assertEqual(horizon._successor_for(None, rows[0], rows)['task_id'], 'New')

    def test_summary_code_pipes_are_historical_only(self):
        source = self.root / 'tabilet/memory-bank/status-M01.md'
        source.write_text(source.read_text().replace('`[ ]`', '`[+]`'))
        path = h.retire_fixture(self.root)
        index_path = path.parent / 'index.md'
        index_path.write_text(index_path.read_text().replace('| fixture |', '| `project.yaml|json` |'))
        # retire_fixture uses a different summary; replace the actual last cell.
        lines = index_path.read_text().splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith('| M01 |'):
                cells = core.table_rows(line)[0]['cells']
                lines[i] = '| ' + ' | '.join(cells[:4]) + ' | `project.yaml|json` |\n'
        index_path.write_text(''.join(lines))
        snapshot = core.history_snapshot(self.root)
        self.assertEqual(snapshot['problems'], [])
        self.assertEqual(snapshot['index_compatibility'], ['status-M01.md'])
        self.assertEqual(core.historical_index_cells(['M01', 'completed', 'date', 'record', 'extra', 'column']),
                         ['M01', 'completed', 'date', 'record', 'extra', 'column'])

    def test_manifest_symlinks_and_nonregular_files_are_rejected(self):
        path = self.root / core.HISTORY_CORRECTIONS
        path.parent.mkdir(parents=True)
        path.symlink_to(self.root / 'missing.json')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            core.read_history_corrections(self.root)
        path.unlink()
        path.mkdir()
        with self.assertRaisesRegex(ValueError, 'regular file'):
            core.read_history_corrections(self.root)

    def test_malformed_json_values_are_validation_errors(self):
        text, correction = self.expansion()
        for bad in (dict(kind=[]), dict(kind='supply-metadata', field=[], value='passed', evidence=[]),
                    dict(kind='resolve-evidence-set', commits=[{}], evidence=[])):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                core.history_corrections(manifest([entry(text, [bad])]))
        with self.assertRaisesRegex(ValueError, 'input limit'):
            core.history_corrections(' ' * (core.HISTORY_INPUT_LIMIT + 1))

    def test_indented_review_limit_approval_field_is_located(self):
        approval = 'The owner approved review extension to 12.'
        base = h.retirement_text('| Task | `[+]` | verified |\n', **{
            'Review limit': '12', 'Review iterations': '12', 'Review limit approval': approval})
        for indentation in ('', ' ', '   '):
            with self.subTest(indentation=repr(indentation)):
                text = base.replace('**Review limit approval.**', indentation + '**Review limit approval.**')
                record = core.historical_record(text, 'status-M01.md')
                self.assertEqual(record['literal_metadata']['Review limit approval'], approval)
                self.assertNotIn('recorded review limit approval is ambiguous or unsupported', record['blockers'])

    def test_status_identity_guard_ignores_unrelated_headings_and_malformed_ids(self):
        for prefix, row in (('# Q4 results\n\n', '| Task |'),
                            ('# V8 notes\n\n', '| Task |'),
                            ('# Q40 results\n\n', '| Task |'),
                            ('', '| M1.1 - legacy task |'),
                            ('', '| m01.1 - own task, lowercase |'),
                            ('# Status m01\n\n', '| Task |')):
            with self.subTest(prefix=prefix, row=row):
                text = self.text.replace('| Task |', prefix + row)
                self.assertEqual(core.historical_record(text, 'status-M01.md')['blockers'], [])

    def test_conflicting_retained_counter_is_found_in_bullets_tables_and_prose(self):
        for line in ('- Review gate iterations: 3', 'Notes - Review gate iterations: 3',
                     '| Review gate iterations: 3 | note |', '* **Review gate iterations.** 3'):
            with self.subTest(line=line):
                text = self.text.replace('| Task |', line + '\n\n| Task |')
                self.assertIn('retained review counter conflicts with retirement metadata',
                              core.historical_record(text, 'status-M01.md')['blockers'])
        for line in ('- Review gate iterations: 2', 'Prior closing-review iterations: 0',
                     'The earlier non-review iterations: 5 were unrelated.'):
            with self.subTest(benign=line):
                text = self.text.replace('| Task |', line + '\n\n| Task |')
                self.assertEqual(core.historical_record(text, 'status-M01.md')['blockers'], [])

    def test_trailing_nested_item_cannot_hide_a_review_claim(self):
        wrapped = ('**Verification.** Tests passed.\n  - Further details.\n'
                   '    - The review result was later invalidated.\n')
        for tail in ('', '\n| Other | `[+]` | verified |\n'):
            with self.subTest(tail=tail):
                text = h.retirement_text('| Task | `[+]` | verified |\n\n' + wrapped + tail)
                record = core.historical_record(text, 'status-M01.md')
                self.assertIn('ambiguous review-result claim in structured metadata', record['blockers'])

    def test_later_approval_reference_in_a_foreign_status_excerpt_is_found(self):
        status = 'Later, the owner revoked that approval.\n\n| Task | `[+]` | verified |\n'
        text = h.retirement_text(status, **{
            'Review limit': '12', 'Review iterations': '12',
            'Review limit approval': 'The owner approved review extension to 12.'})
        operation = dict(kind='recover-document', document='status', content=status, sha256=digest(status),
                         source=dict(commit='a' * 40, path='tabilet/memory-bank/status-M01.md',
                                     start_line=1, end_line=3, source_sha256=digest(status)))
        record = core.historical_record(text, 'status-M01.md', entry(text, [operation]))
        self.assertIn('recorded review limit approval is ambiguous or unsupported', record['blockers'])

    def test_a_fenced_block_does_not_end_the_review_pass_context(self):
        fences = {'backtick': '```text\nlog excerpt\n```\n', 'tilde': '~~~text\nlog excerpt\n~~~\n',
                  'two blocks': '```text\nlog\n```\n\n~~~text\nmore\n~~~\n'}
        for name, fence in fences.items():
            for reversal in ('The result was later invalidated.', 'The review was later withdrawn.'):
                with self.subTest(fence=name, reversal=reversal):
                    status = ('| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\n'
                              + fence + '\n' + reversal + '\n')
                    text = h.retirement_text(status).replace('**Review.** passed\n', '')
                    quote = 'Review: passed'
                    line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
                    correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
                        evidence=[dict(start_line=line, end_line=line, quote=quote)])])
                    with self.assertRaisesRegex(ValueError, 'conflicting recorded review result'):
                        core.historical_record(text, 'status-M01.md', correction)
                    # Without a correction the retained reversal is still a blocker.
                    uncorrected = core.historical_record(h.retirement_text(status), 'status-M01.md')
                    self.assertIn('unrecognized continuation after recorded review pass', uncorrected['blockers'])
        # A fence with nothing after it is not a continuation.
        status = '| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\n```text\nlog\n```\n'
        self.assertEqual(core.historical_record(h.retirement_text(status), 'status-M01.md')['blockers'], [])

    def test_ordinary_review_prose_in_a_strict_record_is_not_a_blocker(self):
        task = '| Task | `[+]` | verified |\n'
        benign = {
            'retirement progress after a pass': '**State.** Manifest verified; whole-milestone review passed 2/10. '
                                                'Normal retirement is in progress.\n\n' + task,
            'findings line after a pass': '## Review\n\nWhole review 2/10 PASS with no P1/P2.\n- Findings: none\n\n' + task,
            'iteration table after a pass': '## Review\n\nReview: passed\n| Iteration | State |\n|---|---|\n'
                                            '| 1 | FAIL |\n| 2 | PASS |\n\n' + task,
            'ordinary note after a pass': '## Review\n\nReview: passed\n\nLogs are in ignored scratch.\n\n' + task,
            'reference to a result': '## Review\n\nThe review outcome is recorded below.\n\nReview: passed\n\n' + task,
            'numbered reference': '**Verification.** Tests passed; see review 2/10 for details.\n\n' + task,
            'pass in the recorded iteration': '**Verification.** Whole-milestone review passed in iteration 2.\n\n' + task,
            'earlier iteration failure': '**Verification.** Review 1/10 FAIL, fixed; review 2/10 passed.\n\n' + task,
            'clause break after a counter': '**State.** Accepted after closing review 2/10; consolidation next.\n\n' + task,
            'another milestone cited': '**Dependency.** M17 accepted at abc1234, review 3/10, retired.\n\n' + task,
            'negated reopening': '**Verification.** Review passed 2/10; no retired review is reopened.\n\n' + task,
            'annotated review declaration': '**Review.** Passed in iteration 2/10; no open P1/P2 findings.\n\n' + task,
        }
        for name, status in benign.items():
            with self.subTest(name):
                record = core.historical_record(h.retirement_text(status), 'status-M01.md')
                self.assertEqual(record['blockers'], [])

    def test_reversed_conditional_or_inconsistent_review_prose_still_blocks(self):
        task = '| Task | `[+]` | verified |\n'
        adverse = {
            'later invalidated': '## Review\n\nReview: passed\n\nThe result was later invalidated.\n\n' + task,
            'pronoun withdrawn': '## Review\n\nReview: passed\n\nIt was later withdrawn.\n\n' + task,
            'conditional pass': '## Review\n\nReview: passed\n\nThe pass is contingent on further verification.\n\n' + task,
            'wrong iteration': '**Verification.** Whole-milestone review passed in iteration 3.\n\n' + task,
            'pass at an earlier iteration': '**Verification.** Review 1/10 passed.\n\n' + task,
            'final iteration failed': '**Verification.** Review 2/10 FAIL.\n\n' + task,
            'unknown verdict': '**Verification.** Whole review 2/10: unknown.\n\n' + task,
            'second claim hidden behind the first': '**Verification.** Review 1/10 FAIL; review 2/10 pending.\n\n' + task,
            'reversal after a structured pass': '**Verification.** Review passed in iteration 2. '
                                                'The result was later invalidated.\n\n' + task,
            'reversal in the same sentence': '**Verification.** The review passed, then was invalidated.\n\n' + task,
            'declaration with a qualification': '**Review.** Passed in iteration 2/10, later withdrawn.\n\n' + task,
        }
        for name, status in adverse.items():
            with self.subTest(name):
                record = core.historical_record(h.retirement_text(status), 'status-M01.md')
                self.assertTrue(record['blockers'], name)

    def test_adverse_review_wording_needs_a_subject_a_predicate_and_no_negation(self):
        adverse = core.adverse_review_wording
        for text in ('The review result was later invalidated.', 'Later, the owner changed that decision.',
                     'The pass is contingent on further verification.', 'It was later withdrawn.',
                     'The review was not accepted.', 'The result of the review was withdrawn.',
                     'Not review passed.', 'The review is pending further verification.'):
            with self.subTest(text):
                self.assertTrue(adverse(text, 2))
        for text in ('The review outcome is recorded below.', 'Findings: none', 'The tests were changed.',
                     'The review was not invalidated.', 'No failures were found in the review.',
                     'Review 1/10 FAIL, fixed.', 'Iteration 1 failed; iteration 2 passed.',
                     'The root must review the exact changed verification input.',
                     'A long paragraph mentions the review at the start and, many words later in an unrelated '
                     'clause about disk space, that a build was cancelled.'):
            with self.subTest(text):
                self.assertFalse(adverse(text, 2))

    def review_variants(self, where, payload):
        """The same retained text read uncorrected and with a correction supplying `Review: passed`."""
        task = '| Task | `[+]` | verified |\n'
        if where == 'after':
            status = task + '\n## Review\n\nReview: passed\n' + payload + '\n'
        else:
            status = payload + '\n\n' + task + '\n## Review\n\nReview: passed\n'
        uncorrected = core.historical_record(h.retirement_text(status), 'status-M01.md')['blockers']
        text = h.retirement_text(status).replace('**Review.** passed\n', '')
        quote = 'Review: passed'
        line = next(n for n, actual in enumerate(text.splitlines(), 1) if actual == quote)
        correction = entry(text, [dict(kind='supply-metadata', field='Review', value='passed',
            evidence=[dict(start_line=line, end_line=line, quote=quote)])])
        try:
            corrected = core.historical_record(text, 'status-M01.md', correction)['blockers']
        except ValueError as error:
            corrected = [str(error)]
        return uncorrected, corrected

    def test_adverse_review_prose_blocks_on_both_paths(self):
        payloads = (
            ('after', 'The review result was not invalidated but withdrawn.'),
            ('after', 'It is conditional on further verification.'),
            ('after', 'The review result; withdrawn.'),
            ('after', 'The result was later\nwithdrawn.'),
            ('after', 'The review result, after checking every item in the original document carefully, was withdrawn.'),
            ('after', 'Review 1/10 FAIL; iteration 2 failed.'),
            ('after', 'Review: passed provided that remaining checks succeed.'),
            ('after', '| Finding | Disposition |\n| Closure | The review result was invalidated. |'),
            ('after', '| Iteration | State |\n|---|---|\n| 1 | FAIL |\n| 2 | FAIL |'),
            ('after', 'Compared with M02, M01 whole review 2/999 PASS.'),
            ('field', '**State.** Review passed 2/10. Review passed 9/10.'),
            ('after', '```text\nx\n```\n\nIt was later withdrawn.'),
            ('after', '> The review was later rescinded.'),
        )
        for where, payload in payloads:
            with self.subTest(payload=payload):
                uncorrected, corrected = self.review_variants(where, payload)
                self.assertTrue(uncorrected, 'uncorrected record accepted ' + repr(payload))
                self.assertTrue(corrected, 'correction-backed record accepted ' + repr(payload))

    def test_every_subject_connector_and_predicate_combination_still_blocks(self):
        subjects = ('The review result', 'The pass', 'It', 'The result')
        connectors = (' was ', ' was later ', ' was, after checking every required acceptance condition again, ',
                      ' was not invalidated but ')
        predicates = ('invalidated', 'withdrawn', 'reversed', 'conditional on further verification',
                      'pending further verification', 'not accepted')
        for subject in subjects:
            for connector in connectors:
                for predicate in predicates:
                    payload = subject + connector + predicate + '.'
                    with self.subTest(payload=payload):
                        uncorrected, corrected = self.review_variants('after', payload)
                        self.assertTrue(uncorrected)
                        self.assertTrue(corrected)

    def test_a_correction_that_supplies_acceptance_keeps_the_conservative_rule(self):
        # Uncorrected, these are ordinary prose. When a correction supplies the
        # pass, an unrecognized continuation is not made safe by a vocabulary
        # miss, so the record is refused.
        for where, payload in (('after', 'Findings: none'), ('after', 'The review outcome is recorded below.'),
                               ('after', 'Logs are in ignored scratch.')):
            with self.subTest(payload=payload):
                uncorrected, corrected = self.review_variants(where, payload)
                self.assertEqual(uncorrected, [])
                self.assertTrue(corrected)

    def test_ordinary_english_next_to_a_review_pass_is_not_a_blocker(self):
        for where, payload in (
                ('field', '**State.** No changes were required after review passed.'),
                ('field', '**Verification.** Review passed 12/12 checks.'),
                ('field', '**State.** Complete; whole review 2/10 passed (no P1/P2); retired 2026-10-29.'),
                ('field', '**State.** M01.2 review 4 PASS; whole review 2/10 passed.'),
                ('field', '**Verification.** Review passed all 12/12 checks.'),
                ('field', '**State.** Review passed 2/10; retirement pending.'),
                ('after', 'The build was cancelled by the user and rerun.'),
                ('after', '| Iteration | State |\n|---|---|\n| 1 | FAIL |\n| 2 | PASS |')):
            with self.subTest(payload=payload):
                self.assertEqual(self.review_variants(where, payload)[0], [])

    def test_review_prose_must_be_a_complete_recognized_form(self):
        # A recognized form has no free-text tail, so a qualification cannot
        # ride inside it, and a later sentence that refers back to the review
        # is held to the same rule. A reversal word in an unrecognized clause
        # blocks on both paths, however far it is from the subject.
        for where, payload in (
                ('after', 'Review passed after testing and was subsequently voided.'),
                ('after', 'The review result is recorded in the log as voided.'),
                ('after', 'Review found no defects but was annulled.'),
                ('after', 'Review passed. Later it was annulled.'),
                ('after', 'See the review log for details, which was voided.')):
            with self.subTest(payload=payload):
                uncorrected, corrected = self.review_variants(where, payload)
                self.assertTrue(uncorrected)
                self.assertTrue(corrected)

    def test_unrecognized_review_wording_warns_on_a_literal_record(self):
        # Without a reversal word, unrecognized wording about the review is a
        # warning on a record that carries its own pass, and still a blocker
        # when a correction supplies the pass.
        for where, payload in (
                ('after', 'The review passed after the failed test was fixed.'),
                ('after', 'The review took two hours.'),
                ('field', '**State.** Review passed 2/10. The review result was later deemed moot.'),
                ('after', 'Review passed. Afterwards it was discussed with the owner.')):
            with self.subTest(payload=payload):
                uncorrected, corrected = self.review_variants(where, payload)
                self.assertEqual(uncorrected, [])
                self.assertTrue(corrected)
                status = (payload + '\n\n| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\n' if where == 'field'
                          else '| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\n' + payload + '\n')
                warnings = core.historical_record(h.retirement_text(status), 'status-M01.md')['warnings']
                self.assertEqual(len(warnings), 1)
                self.assertIn('unrecognized review wording', warnings[0])
        clean = core.historical_record(h.retirement_text(
            '| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\nThe review result is recorded below.\n'),
            'status-M01.md')
        self.assertEqual((clean['blockers'], clean['warnings']), ([], []))

    def literal_after_pass(self, payload):
        base = '| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\n'
        return core.historical_record(h.retirement_text(base + payload + '\n'), 'status-M01.md')

    def test_this_records_id_is_found_inside_punctuation(self):
        for payload in ("M02 confirmed M01's review 3/10 passed.", 'Project:M02 confirmed (M01) review 3/10 passed.',
                        'M02 confirmed review 3/10 passed for M01.'):
            with self.subTest(payload=payload):
                self.assertTrue(self.literal_after_pass(payload)['blockers'])
        self.assertEqual(self.literal_after_pass('M100 review 3/10 passed.')['blockers'], [])

    def test_only_a_task_table_ends_the_review_context(self):
        for payload in ('| Item | Notes |\n|---|---|\n| Closure | The review was voided |',
                        '| Task | Notes |\n|---|---|\n| Closure | The review was voided |',
                        '| Item | Notes |\n| Closure | The review was voided |',
                        '| The review was voided |\n|---|'):
            with self.subTest(payload=payload):
                self.assertTrue(self.literal_after_pass(payload)['blockers'])
        record = self.literal_after_pass('| Iteration | Result |\n|---|---|\n| 1 | FAIL |\n| 2 | PASS |')
        self.assertEqual((record['blockers'], record['warnings']), ([], []))

    def test_the_recorded_pass_stays_the_subject_of_its_continuation(self):
        for payload in ('Later it was annulled.', 'The review passed.\n\nLater it was voided.',
                        'Review passed. No errors remained. Later it was annulled.',
                        'No errors remained.\n\nAfterwards this result was set aside.'):
            with self.subTest(payload=payload):
                self.assertTrue(self.literal_after_pass(payload)['blockers'])
        record = self.literal_after_pass('No errors remained.\n\nLater it was discussed with the owner.')
        self.assertEqual(record['blockers'], [])
        self.assertTrue(record['warnings'])

    def test_every_reversal_word_is_judged_in_its_own_negation_scope(self):
        for payload in ('The review was not voided but annulled.', 'The review was never voided and was annulled.',
                        'The review was not reopened; it was revoked.'):
            with self.subTest(payload=payload):
                self.assertTrue(self.literal_after_pass(payload)['blockers'])
        self.assertEqual(self.literal_after_pass('The review was not voided or annulled.')['blockers'], [])

    def test_warning_excerpts_escape_control_characters(self):
        warnings = self.literal_after_pass('The review was deemed moot.\x1b[2J\u202e')['warnings']
        self.assertEqual(len(warnings), 1)
        self.assertNotRegex(warnings[0], '[\x00-\x1f\x7f\u202e]')
        self.assertIn('\\x1b[2J', warnings[0])

    def test_no_review_reversal_or_counter_conflict_passes_silently(self):
        # Property check over every place a pass can be continued or claimed:
        # a reversal in the vocabulary or a conflicting counter blocks on both
        # paths; other wording about the review at least warns on a literal
        # record; ordinary test prose does not block.
        task, review = '| Task | `[+]` | verified |\n', '\n## Review\n\nReview: passed\n'
        places = {
            'after': lambda p: task + review + p + '\n',
            'after a blank line': lambda p: task + review + '\n' + p + '\n',
            'after a neutral sentence': lambda p: task + review + 'No errors remained.\n\n' + p + '\n',
            'after a fence': lambda p: task + review + '```text\nexample\n```\n' + p + '\n',
            'after indented code': lambda p: task + review + '    example output\n' + p + '\n',
            'prose with an inline marker after a task row': lambda p: (task + review + '| Item | `[+]` | done |\n'
                                                                       + p + ' (recorded as | `[+]` |)\n'),
            'table after a task row': lambda p: (task + review + '| Item | `[+]` | done |\n| Verdict | Details |\n'
                                                 '|---|---|\n| Closure | ' + p + ' |\n'),
            'table body': lambda p: task + review + '| Item | Notes |\n|:---|---:|\n| Closure | ' + p + ' |\n',
            'table header': lambda p: task + review + '| ' + p + ' |\n|---|\n',
            'after the task table': lambda p: (task + review + '| Item | State | Notes |\n|---|---|---|\n'
                                               '| Closure | `[+]` | done |\n\n' + p + '\n'),
            'State field': lambda p: '**State.** Review passed 2/10. ' + p + '\n\n' + task + review,
            'Verification field': lambda p: '**Verification.** Review passed 2/10. ' + p + '\n\n' + task + review,
            'State field alone': lambda p: '**State.** ' + p + '\n\n' + task + review,
            'Result field alone': lambda p: '**Result.** ' + p + '\n\n' + task + review,
            'Closure field alone': lambda p: '**Closure.** ' + p + '\n\n' + task + review,
            'Disposition field alone': lambda p: '**Disposition.** ' + p + '\n\n' + task + review,
        }
        blocking = ('The review was voided.', 'Later this was annulled.', 'Later those were set aside.',
                    'After the release, following discussion, the verdict was subsequently voided.',
                    'Subsequently annulled.', 'The pass was revoked.', 'The review was not only voided.',
                    'The review was never voided and was annulled.', 'This has since been rejected.',
                    'Later, this, after discussion, was annulled.', 'Later the same was annulled.',
                    'Later the owner annulled this.', 'Later it was ann\u00adulled.',
                    'Pending.', 'Conditional on further checks.', 'No longer valid.', 'Later it was pending.',
                    'The review, after discussion, is now pending.', 'It is, after discussion, conditional.',
                    'M02 confirms review 3/10 passed for our milestone.', 'M02 says review 3/10 passed, unlike ours.',
                    'Whole-milestone review passed 3/10.', 'Passed 9/10.', "M02 confirmed M01's review 3/10 passed.",
                    'M02 confirmed \u041c01 review 3/10 passed.', 'M02 confirmed M\u200b01 review 3/10 passed.',
                    'Pending owner sign-off.', 'Rejected when reviewed.', 'Failed and reverted.',
                    'Rejected, then rewritten.', 'Voided; see notes.',
                    'Pending final checks by the designated owner.',
                    'Rejected until the owner finishes all mandatory checks.',
                    'No longer valid because the evidence was wrong.',
                    'Withdrawn until the owner finishes all mandatory checks.',
                    'M02 confirms review 3/10 passed for this project.',
                    'M02 confirms review 3/10 passed for this delivery.',
                    'Completed implementation; pending final checks by the designated owner.',
                    'Incomplete until the owner finishes all mandatory checks.',
                    'Pending final checks now.', 'Pending all required checks by the designated owner.')
        flagged = ('Later the review was deemed moot.', 'Later it was treated as never having happened.',
                   'Withheld.', 'Not granted.', 'Withheld; see notes.')
        # A correction-backed pass must also block these in a claim field with no positive sentence first.
        for field in ('State', 'Result'):
            for payload in ('Annulled.', 'The whole thing was set aside.', 'The result was voided.', 'Pending.'):
                with self.subTest(field=field, payload=payload):
                    self.assertTrue(self.review_variants('field', f'**{field}.** {payload}')[0])
                    self.assertTrue(self.review_variants('field', f'**{field}.** {payload}')[1])
        benign = ('Tests confirm that revoked tokens are rejected.', 'Revoked credentials are rejected by the broker.',
                  'Tests verify that the stale grant was revoked.', 'Cancellation at Git staging still produced a commit.',
                  'A wrong directory in the rewritten path fails it.',
                  'Tests verify that this path is cancelled cleanly.', 'The review result is recorded below.')
        # A State or Status value opening with Failed, Pending or Blocked is an
        # outcome statement; elsewhere an adverse word leading a noun phrase that
        # has its own predicate is not a verdict.
        benign_elsewhere = ('Failed preparation contexts retained.', 'Failed delivery permits a bounded explicit retry.',
                            'Rejection leaves the ledger and authorization receipts unchanged.')
        for place, build in places.items():
            if not place.startswith(('State', 'Status')):
                for payload in benign_elsewhere:
                    with self.subTest(place=place, payload=payload):
                        record = core.historical_record(h.retirement_text(build(payload)), 'status-M01.md')
                        self.assertEqual(record['blockers'], [])
            for payload in blocking + flagged + benign:
                if place.startswith('prose with') and payload in flagged:
                    continue  # the added words make an out-of-vocabulary verdict long narrative
                status = build(payload if '|' not in build('') else payload.replace('|', '/'))
                with self.subTest(place=place, payload=payload):
                    record = core.historical_record(h.retirement_text(status), 'status-M01.md')
                    if payload in benign:
                        self.assertEqual(record['blockers'], [])
                        continue
                    if payload in blocking:
                        self.assertTrue(record['blockers'])
                    else:
                        self.assertTrue(record['blockers'] or record['warnings'])
                    if payload not in benign:
                        self.assertTrue(self.review_variants('after', payload)[1])

    def test_an_explicit_verdict_field_is_never_silent(self):
        # Result, Review gate and Outcome exist to state the verdict: wording
        # outside the vocabulary there warns on a literal record and blocks a
        # correction-backed one, whatever its length.
        task, review = '| Task | `[+]` | verified |\n', '\n## Review\n\nReview: passed\n'
        for field in ('Result', 'Review gate', 'Outcome'):
            for value in ('Undone by the owner after the release went out.',
                          'Withheld until the owner returns from leave next week.',
                          'M02 declined the requested sign-off.'):
                with self.subTest(field=field, value=value):
                    record = core.historical_record(
                        h.retirement_text(f'**{field}.** {value}\n\n' + task + review), 'status-M01.md')
                    self.assertTrue(record['blockers'] or record['warnings'])
                    self.assertTrue(self.review_variants('field', f'**{field}.** {value}')[1])

    def test_a_formal_outcome_value_is_metadata_not_a_review_claim(self):
        task, review = '| Task | `[+]` | verified |\n', '\n## Review\n\nReview: passed\n'
        for value in ('completed', 'cancelled', 'superseded'):
            with self.subTest(value=value):
                record = core.historical_record(
                    h.retirement_text(f'**Outcome.** {value}\n\n' + task + review), 'status-M01.md')
                self.assertNotIn('ambiguous review-result claim in structured metadata', record['blockers'])
        for value in ('superseded, then voided.', 'Withdrawn since.', 'Superseded.'):
            with self.subTest(value=value):
                uncorrected, corrected = self.review_variants('field', f'**Outcome.** {value}')
                self.assertTrue(uncorrected)
                self.assertTrue(corrected)

    def test_task_rows_after_a_pass_are_checked_on_both_paths(self):
        for row in ('| Item | `[+]` | The review was voided |', '| Item | `[+]` | Whole-milestone review passed 3/10. |',
                    '| M01.3 | `[+]` | The milestone review was annulled |'):
            with self.subTest(row=row):
                uncorrected, corrected = self.review_variants('after', row)
                self.assertTrue(uncorrected)
                self.assertTrue(corrected)
        uncorrected, corrected = self.review_variants('after', '| Item | `[+]` | done |\nThe review was withdrawn.')
        self.assertTrue(uncorrected)
        self.assertTrue(corrected)
        for row in ('| Item | `[+]` | The milestone review is conditional on further checks. |',
                    '| Item | `[+]` | The milestone review was deemed moot. |'):
            with self.subTest(row=row):
                uncorrected, corrected = self.review_variants('after', row)
                self.assertTrue(corrected)
                record = core.historical_record(h.retirement_text(
                    '| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\n' + row + '\n'), 'status-M01.md')
                self.assertTrue(record['blockers'] or record['warnings'])
        self.assertTrue(self.review_variants('after', '| Item | `[+]` | The milestone review is conditional. |')[0])
        # Ordinary task notes and task-level review counters stay task evidence.
        for row in ('| Item | `[+]` | Tests revoke stale tokens |', '| Item | `[+]` | M01.2 review 4 fixed |'):
            with self.subTest(row=row):
                self.assertEqual(self.review_variants('after', row)[0], [])

    def test_review_warnings_reach_the_snapshot_and_index_without_blocking(self):
        history = self.root / 'tabilet/docs/history'
        history.mkdir(parents=True)
        text = h.retirement_text('| Task | `[+]` | verified |\n\n## Review\n\nReview: passed\nThe review took two hours.\n')
        (history / 'status-M01.md').write_text(text)
        (history / 'index.md').write_text('| Milestone | Outcome | Retired | Record | Summary |\n|---|---|---|---|---|\n'
                                          '| M01 | completed | 2026-09-12 | [M01](status-M01.md) | Delivery |\n')
        (self.root / 'tabilet/memory-bank/milestone.md').write_text('# Milestones\n\n[History](../docs/history/index.md)\n')
        (self.root / 'tabilet/memory-bank/status-M01.md').unlink(missing_ok=True)
        snapshot = core.row_snapshot(self.root)
        self.assertEqual(snapshot['history']['problems'], [])
        self.assertEqual(len(snapshot['history']['warnings']), 1)
        self.assertIn('tabilet/docs/history/status-M01.md: unrecognized review wording: "The review took two hours"',
                      snapshot['history']['warnings'][0])
        with audit.open_database(self.root / 'tabilet/audit.sqlite3') as connection:
            state = index.sync(connection, self.root)
            diagnostics = index.status(connection, state['workspace_id'])['diagnostics']
        self.assertTrue(any('warning: unrecognized review wording' in item for item in diagnostics), diagnostics)
        parsed = index.parse_document('tabilet/docs/history/status-M01.md', 'history_status', text, digest(text))
        self.assertNotIn('unverified', repr(parsed))

    def test_claim_fields_use_the_same_review_validator(self):
        for field in ('State', 'Status', 'Verification', 'Outcome', 'Result', 'Acceptance', 'Closure',
                      'Review gate', 'Disposition'):
            payload = f'**{field}.** Review passed 2/10. The review result was voided.'
            with self.subTest(payload=payload):
                self.assertTrue(self.review_variants('field', payload)[0])
        for payload in ('**State.** Accepted after closing review 2/10.', '**State.** Review 2/10 passed.',
                        '**State.** Review passed in iteration 2.', '**Verification.** Review passed 2/10.'):
            with self.subTest(payload=payload):
                self.assertEqual(self.review_variants('field', payload)[0], [])

    def test_counters_are_checked_before_mentions_and_table_verdicts(self):
        for where, payload in (
                ('after', 'Iteration 3 passed.'),
                ('after', 'Passed 9/10.'),
                ('after', '| Iteration | State |\n|---|---|\n| 2 | PASS; iteration 3 passed. |'),
                ('field', '**Verification.** Review passed 12/10.')):
            with self.subTest(payload=payload):
                self.assertTrue(self.review_variants(where, payload)[0])

    def test_only_a_bound_foreign_milestone_exempts_a_counter(self):
        for payload in ('**State.** Compared with M02, our review 3/10 passed.',
                        '**State.** Unlike M02, this review 3/10 passed.',
                        '**State.** M02 shipped first and then, after much work here, review 3/10 passed.'):
            with self.subTest(payload=payload):
                self.assertTrue(self.review_variants('field', payload)[0])
        for payload in ('**State.** M02 review 3/10 passed but ours was voided.',
                        '**State.** M02 review 3/10 passed; it was voided.'):
            with self.subTest(payload=payload):
                self.assertTrue(self.review_variants('field', payload)[0])
        for payload in ('**State.** Review 2/10 passed; M02 review 3/10 passed.',
                        '**State.** Review 2/10 passed; Other:M02 is accepted at abc1234 after whole review 3/10.'):
            with self.subTest(payload=payload):
                self.assertEqual(self.review_variants('field', payload)[0], [])

    def test_a_table_header_is_structure_not_a_verdict(self):
        header = '| Iteration | Result |\n|---|---|\n'
        self.assertEqual(self.review_variants('after', header + '| 1 | FAIL |\n| 2 | PASS |')[0], [])
        self.assertTrue(self.review_variants('after', header + '| 1 | FAIL |\n| 2 | FAIL |')[0])

    def test_adverse_wording_binds_negation_to_its_clause_and_the_subject_to_the_sentence(self):
        adverse = core.adverse_review_wording
        for text, context in (('The review result was not invalidated but withdrawn.', False),
                              ('It is conditional on further verification.', True),
                              ('The review result; withdrawn.', False),
                              ('The result was later\nwithdrawn.', False),
                              ('Review 1/10 FAIL; iteration 2 failed.', False),
                              ('Withdrawn.', True)):
            with self.subTest(text):
                self.assertTrue(adverse(text, 2, context))
        for text in ('The review passed after the failed test was fixed.', 'No changes were required after review passed.',
                     'Whole review 2/10 passed; retirement pending.', 'Tests failed in the build job.'):
            with self.subTest(text):
                self.assertFalse(adverse(text, 2))

    def test_tables_counters_and_grammar_cannot_hide_a_reversal(self):
        payloads = (
            ('after', '| Iteration | Result |\n| 1 | FAIL; the review result was withdrawn. |'),
            ('after', '| Iteration | Result |\n| 2 | PASS; the review result was withdrawn. |'),
            ('after', 'Review passed 9/10.'),
            ('field', '**State.** Review passed 2/10. Iteration 3 passed.'),
            ('field', '**State.** Review passed 2/10; passed 9/10.'),
            ('after', 'The review result was not invalidated and was withdrawn.'),
            ('after', 'After checking the release notes, the review result, after discussion with the entire '
                      'engineering team at the meeting yesterday, was withdrawn.'),
            ('after', 'Following further discussion yesterday it is conditional on final verification.'),
            # Outside the adverse vocabulary: the conservative fallback still blocks it.
            ('after', 'The review result was voided.'),
        )
        for where, payload in payloads:
            with self.subTest(payload=payload):
                uncorrected, corrected = self.review_variants(where, payload)
                self.assertTrue(uncorrected, 'uncorrected record accepted ' + repr(payload))
                self.assertTrue(corrected, 'correction-backed record accepted ' + repr(payload))

    def test_dates_repeat_counts_and_task_reviews_are_not_review_counters(self):
        for where, payload in (
                ('field', '**Verification.** make check passed 2026-09-29; review passed 2/10.'),
                ('field', '**Verification.** Race tests passed 20 times; review passed 2/10.'),
                ('field', '**State.** M01.2 review 4 PASS; whole review 2/10 passed.'),
                ('field', '**State.** Task-review 3 corrections applied; whole review 2/10 passed.'),
                ('field', '**State.** No changes were required after review 2/10 passed.'),
                ('field', '**State.** Iteration 1 failed; iteration 2 passed.'),
                ('after', 'No extra code change followed the review.')):
            with self.subTest(payload=payload):
                self.assertEqual(self.review_variants(where, payload)[0], [])


if __name__ == '__main__':
    unittest.main()
