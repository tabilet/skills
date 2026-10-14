"""Offline approval-alert fixtures: no Cloudflare account or live mail."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/memory-bank-goal/scripts/email_notify.py"
spec = importlib.util.spec_from_file_location("email_notify_test", SCRIPT)
notifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notifier)
BOUNDED_DELIVER = notifier.deliver_bounded


class EmailNotificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.config = self.root / "config/tabilet/email.json"
        self.config.parent.mkdir(parents=True)
        self.profile = {
            "account_id": "a" * 32, "from": "alerts@example.test",
            "allowed_recipients": ["owner@example.test", "second@example.test"],
            "token_env": "CLOUDFLARE_EMAIL_TEST_TOKEN",
        }
        self.write_profile()
        self.token = "fixture-credential-never-a-real-token"
        self.env = {
            "XDG_CONFIG_HOME": str(self.root / "config"),
            "XDG_STATE_HOME": str(self.root / "state"),
            "CLOUDFLARE_EMAIL_TEST_TOKEN": self.token,
        }
        patcher = mock.patch.dict(os.environ, self.env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Provider and reservation fixtures run in-process. Supervisor fixtures
        # below exercise the real isolated worker with offline fake programs.
        patcher = mock.patch.object(notifier, "deliver_bounded",
                                    side_effect=lambda *args: notifier.deliver(*args))
        patcher.start()
        self.addCleanup(patcher.stop)
        # Any accidental unmocked network access fails this suite.
        patcher = mock.patch.object(notifier.urllib.request.OpenerDirector, "open",
                                    side_effect=AssertionError("live network forbidden"))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.event = {
            "event": "approval_required", "run_id": "run-1",
            "request_id": hashlib.sha256(b"exact proposal").hexdigest(),
            "project": "fixture", "milestone": "M01/T01",
            "reason": "Producer publication scope requires approval.",
            "session_id": "session-1",
        }

    def write_profile(self):
        self.config.write_text(json.dumps(self.profile), encoding="utf-8")
        self.config.chmod(0o600)

    def response(self, **groups):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = json.dumps({"success": True, "result": groups}).encode()
        opener = mock.Mock()
        opener.open.return_value = response
        return mock.patch.object(notifier.urllib.request, "build_opener", return_value=opener), opener, response

    def send(self, event=None, recipient="owner@example.test"):
        return notifier.send(event or self.event, recipient, self.project)

    def test_readiness_is_local_and_creates_no_state(self):
        original = self.config.read_bytes()
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            result = notifier.main(["check", "--to", "owner@example.test", "--project-root", str(self.project)])
        self.assertEqual(0, result)
        self.assertEqual({"status": "ready", "network_checked": False}, json.loads(output.getvalue()))
        self.assertFalse((self.root / "state").exists())
        self.assertEqual(original, self.config.read_bytes())

    def test_bad_addresses_and_unpermitted_recipient_never_send(self):
        for value in ("", "owner", "Name <owner@example.test>", "a@example.test,b@example.test",
                      "owner@example.test\r\nBcc: evil@example.test", "x@localhost", "x@bad..test"):
            with self.subTest(address=value), self.assertRaises(notifier.NotificationError):
                notifier.address(value)
        with self.assertRaisesRegex(notifier.NotificationError, "not permitted"):
            self.send(recipient="unapproved@example.test")
        self.assertFalse((self.root / "state").exists())

    def test_missing_private_configuration_and_token_report_no_secrets(self):
        self.config.unlink()
        with self.assertRaisesRegex(notifier.NotificationError, "configuration"):
            self.send()
        self.write_profile()
        with mock.patch.dict(os.environ, {"CLOUDFLARE_EMAIL_TEST_TOKEN": ""}):
            with self.assertRaisesRegex(notifier.NotificationError, "token is missing"):
                self.send()
        if os.name == "posix":
            self.config.chmod(0o644)
            with self.assertRaisesRegex(notifier.NotificationError, "private"):
                self.send()
        self.assertFalse((self.root / "state").exists())

    def test_configuration_and_state_cannot_live_in_project(self):
        for key in ("XDG_CONFIG_HOME", "XDG_STATE_HOME"):
            with self.subTest(path=key), mock.patch.dict(os.environ, {key: str(self.project)}):
                with self.assertRaisesRegex(notifier.NotificationError, "outside the project"):
                    self.send()
        if hasattr(os, "symlink"):
            linked = self.root / "linked"
            try:
                linked.symlink_to(self.project, target_is_directory=True)
            except OSError:
                return
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(linked)}):
                with self.assertRaisesRegex(notifier.NotificationError, "outside the project"):
                    self.send()

    def test_structured_alert_excludes_attachments_and_redacts_sender_secret(self):
        event = {**self.event, "reason": "Needs approval; password: fixture-only " + self.token}
        patcher, opener, _response = self.response(queued=["owner@example.test"])
        with patcher:
            self.assertEqual({"status": "sent", "delivery": "queued"}, self.send(event))
        request = opener.open.call_args.args[0]
        self.assertEqual("https://api.cloudflare.com/client/v4/accounts/" + "a" * 32 + "/email/sending/send", request.full_url)
        self.assertEqual("Bearer " + self.token, request.get_header("Authorization"))
        self.assertEqual(notifier.TIMEOUT, opener.open.call_args.kwargs["timeout"])
        payload = json.loads(request.data)
        self.assertEqual({"to", "from", "subject", "text"}, set(payload))
        self.assertEqual(self.profile["from"], payload["from"])
        self.assertIn("M01/T01", payload["subject"])
        self.assertIn("session-1", payload["text"])
        self.assertNotIn(self.token, payload["text"])
        self.assertNotIn("password: fixture-only", payload["text"])
        for record in (self.root / "state").rglob("*.json"):
            self.assertNotIn(self.token, record.read_text())
            self.assertNotIn("password", record.read_text())
            if os.name == "posix":
                self.assertEqual(0o600, record.stat().st_mode & 0o777)

    def test_scope_changes_new_runs_and_recipient_changes_use_distinct_attempts(self):
        patcher, opener, _response = self.response(queued=["owner@example.test", "second@example.test"])
        with patcher:
            self.send()
            self.assertEqual({"status": "duplicate", "delivery": "queued"}, self.send())
            self.send({**self.event, "request_id": hashlib.sha256(b"changed scope").hexdigest()})
            self.send({**self.event, "run_id": "run-2"})
            self.send(recipient="second@example.test")
        self.assertEqual(4, opener.open.call_count)
        self.assertEqual(4, len(list((self.root / "state").rglob("*.json"))))

    def test_unknown_delivery_and_crash_reservations_never_replay(self):
        with mock.patch.object(notifier, "deliver", side_effect=notifier.NotificationError("uncertain", "unknown")) as deliver:
            with self.assertRaises(notifier.NotificationError):
                self.send()
            with self.assertRaisesRegex(notifier.NotificationError, "already attempted"):
                self.send()
            self.assertEqual(1, deliver.call_count)
        event = {**self.event, "run_id": "crash-run"}
        with mock.patch.object(notifier, "deliver", side_effect=KeyboardInterrupt) as deliver:
            with self.assertRaises(KeyboardInterrupt):
                self.send(event)
            with self.assertRaisesRegex(notifier.NotificationError, "already attempted"):
                self.send(event)
            self.assertEqual(1, deliver.call_count)

    def test_known_failure_stays_failed_without_retry(self):
        with mock.patch.object(notifier, "deliver", side_effect=notifier.NotificationError("fixture rejection")) as deliver:
            with self.assertRaises(notifier.NotificationError):
                self.send()
            with self.assertRaisesRegex(notifier.NotificationError, "already attempted and failed") as caught:
                self.send()
            self.assertEqual("failed", caught.exception.outcome)
            self.assertEqual(1, deliver.call_count)

    def test_success_after_post_with_failed_checkpoint_does_not_replay(self):
        with mock.patch.object(notifier, "deliver", return_value="accepted") as deliver:
            with mock.patch.object(notifier, "write_record", side_effect=OSError("fixture write failure")):
                with self.assertRaises(OSError):
                    self.send()
            with self.assertRaisesRegex(notifier.NotificationError, "already attempted"):
                self.send()
            self.assertEqual(1, deliver.call_count)

    def test_concurrent_duplicate_requests_dispatch_at_most_once(self):
        def attempt():
            try:
                return self.send()
            except notifier.NotificationError:
                return {"status": "suppressed"}
        with mock.patch.object(notifier, "deliver", return_value="accepted") as deliver:
            with ThreadPoolExecutor(max_workers=2) as workers:
                results = list(workers.map(lambda _i: attempt(), range(2)))
            self.assertEqual(1, deliver.call_count)
        self.assertEqual(1, sum(item["status"] == "sent" for item in results))

    def test_failed_suppressed_and_malformed_provider_responses(self):
        cases = (
            ({"success": False, "errors": [{"message": self.token}]}, "failed"),
            ({"success": True, "result": {"delivered": [], "queued": [], "permanent_bounces": ["owner@example.test"]}}, "failed"),
            ({"success": True, "result": {"suppressed_recipients": ["owner@example.test"]}}, "failed"),
            ({"success": True, "result": {"queued": "owner@example.test"}}, "unknown"),
            ({"success": True, "result": {}}, "unknown"),
        )
        for body, outcome in cases:
            with self.subTest(body=body):
                patcher, _opener, response = self.response()
                response.read.return_value = json.dumps(body).encode()
                with patcher, self.assertRaises(notifier.NotificationError) as caught:
                    notifier.deliver(self.profile, self.token, {"to": "owner@example.test"})
                self.assertEqual(outcome, caught.exception.outcome)
                self.assertNotIn(self.token, str(caught.exception))

    def test_provider_auth_throttle_server_errors_timeout_and_redirect(self):
        for status, expected in ((401, "failed"), (403, "failed"), (429, "failed"), (503, "unknown"), (302, "failed")):
            with self.subTest(status=status):
                patcher, opener, _response = self.response()
                opener.open.side_effect = urllib.error.HTTPError("https://fixture.invalid", status, self.token, {}, None)
                with patcher, self.assertRaises(notifier.NotificationError) as caught:
                    notifier.deliver(self.profile, self.token, {"to": "owner@example.test"})
                self.assertEqual(expected, caught.exception.outcome)
                self.assertNotIn(self.token, str(caught.exception))
        patcher, opener, _response = self.response()
        opener.open.side_effect = TimeoutError(self.token)
        with patcher, self.assertRaises(notifier.NotificationError) as caught:
            notifier.deliver(self.profile, self.token, {"to": "owner@example.test"})
        self.assertEqual("unknown", caught.exception.outcome)
        self.assertNotIn(self.token, str(caught.exception))
        self.assertIsNone(notifier.NoRedirect().redirect_request(None, None, 302, "", {}, "https://foreign.invalid"))

    def test_invalid_events_never_reserve_or_dispatch(self):
        invalid = [None, [], {}, {**self.event, "event": "completed"},
                   {**self.event, "html": "extra content"}, {**self.event, "request_id": "short"},
                   {**self.event, "reason": "x" * 501}, {**self.event, "reason": "multiline\nvalue"},
                   {**self.event, "reason": chr(0xD800)}]
        for event in invalid:
            with self.subTest(event=event), self.assertRaises(notifier.NotificationError):
                notifier.send(event, "owner@example.test", self.project)
        self.assertFalse((self.root / "state").exists())

    def test_bounded_cli_input_and_safe_errors(self):
        for content in ("not json", "x" * (notifier.MAX_INPUT + 1)):
            output = io.StringIO()
            with mock.patch("sys.stdin", io.StringIO(content)), mock.patch("sys.stdout", output):
                result = notifier.main(["send", "--to", "owner@example.test", "--project-root", str(self.project)])
            self.assertEqual(2, result)
            self.assertEqual("unavailable", json.loads(output.getvalue())["status"])
            self.assertNotIn(self.token, output.getvalue())
        self.assertFalse((self.root / "state").exists())

    def test_utf8_bytes_ignore_terminal_decoder_and_are_bounded(self):
        for raw in (b'\xff', json.dumps({**self.event, "reason": "\u597d" * 500}, ensure_ascii=False).encode("utf-8")
                    + b' ' * notifier.MAX_INPUT):
            output = io.StringIO()
            stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="ascii", errors="strict")
            with stdin, mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", output):
                result = notifier.main(["send", "--to", "owner@example.test", "--project-root", str(self.project)])
            self.assertEqual(2, result)
            self.assertEqual("unavailable", json.loads(output.getvalue())["status"])
        raw = json.dumps({**self.event, "reason": "\u9700\u8981\u6279\u51c6"}, ensure_ascii=False).encode("utf-8")
        output = io.StringIO()
        patcher, _, _ = self.response(queued=["owner@example.test"])
        with io.TextIOWrapper(io.BytesIO(raw), encoding="ascii", errors="strict") as stdin:
            with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", output), patcher:
                self.assertEqual(0, notifier.main(["send", "--to", "owner@example.test", "--project-root", str(self.project)]))
        self.assertEqual("sent", json.loads(output.getvalue())["status"])

    def test_unicode_controls_cannot_spoof_alert_lines(self):
        controls = ("\x00", "\x7f", "\x85", "\x9f", "\u2028", "\u2029", "\u202e", "\u2066", "\u200f", "\u061c")
        for field in ("run_id", "project", "milestone", "reason", "session_id"):
            for char in controls:
                with self.subTest(field=field, char=hex(ord(char))), self.assertRaises(notifier.NotificationError):
                    self.send({**self.event, field: "approval" + char + "forged line"})
        self.assertFalse((self.root / "state").exists())
        self.assertEqual("\u6279\u51c6 \U0001f44d", notifier.validate_event({**self.event, "reason": "\u6279\u51c6 \U0001f44d"})["reason"])

    def test_xdg_defaults_are_absolute_and_home_is_lazy(self):
        for values in ({}, {"XDG_CONFIG_HOME": "", "XDG_STATE_HOME": ""},
                       {"XDG_CONFIG_HOME": "relative", "XDG_STATE_HOME": "relative"}):
            with self.subTest(values=values), mock.patch.dict(os.environ, values, clear=True), mock.patch.object(Path, "home", return_value=self.root):
                self.assertEqual((self.root / ".config/tabilet/email.json",
                                  self.root / ".local/state/tabilet/email-notifications"), notifier.account_paths())
        with mock.patch.object(Path, "home", side_effect=RuntimeError("home failure")):
            self.assertEqual((self.config, self.root / "state/tabilet/email-notifications"), notifier.account_paths())
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": ""}):
                output = io.StringIO()
                with mock.patch("sys.stdout", output):
                    self.assertEqual(2, notifier.main(["check", "--to", "owner@example.test", "--project-root", str(self.project)]))
                self.assertEqual("unavailable", json.loads(output.getvalue())["status"])
        with mock.patch.object(Path, "resolve", side_effect=RuntimeError("symlink loop")):
            with self.assertRaisesRegex(notifier.NotificationError, "path could not be resolved"):
                notifier.load_profile("owner@example.test", self.project)
        self.assertFalse((self.root / "state").exists())

    def test_protocol_failures_are_json_unknown_and_never_replay(self):
        for index, failure in enumerate((http.client.IncompleteRead(b"private partial"), http.client.BadStatusLine(self.token))):
            event = {**self.event, "run_id": "protocol-" + str(index)}
            patcher, opener, response = self.response()
            if isinstance(failure, http.client.IncompleteRead):
                response.read.side_effect = failure
            else:
                opener.open.side_effect = failure
            for _ in range(2):
                output = io.StringIO()
                with patcher, mock.patch("sys.stdin", io.StringIO(json.dumps(event))), mock.patch("sys.stdout", output):
                    self.assertEqual(2, notifier.main(["send", "--to", "owner@example.test", "--project-root", str(self.project)]))
                result = json.loads(output.getvalue())
                self.assertEqual(("unavailable", "unknown"), (result["status"], result["delivery"]))
                self.assertNotIn(self.token, output.getvalue())
                self.assertNotIn("private partial", output.getvalue())
            self.assertEqual(1, opener.open.call_count)

    def test_json_recursion_errors_have_context_specific_safe_outcomes(self):
        # Older supported decoders can raise before schema validation. Force
        # that boundary failure without relying on this interpreter's depth.
        with mock.patch.object(notifier.json, "loads", side_effect=RecursionError):
            with self.assertRaises(notifier.NotificationError) as caught:
                notifier.load_profile("owner@example.test", self.project)
            self.assertEqual("failed", caught.exception.outcome)
            with mock.patch("sys.stdin", io.StringIO("[]")), self.assertRaises(notifier.NotificationError):
                notifier.read_json_input(notifier.MAX_INPUT)
            patcher, _, _ = self.response()
            with patcher, self.assertRaises(notifier.NotificationError) as caught:
                notifier.deliver(self.profile, self.token, {"to": "owner@example.test"})
            self.assertEqual("unknown", caught.exception.outcome)
        with mock.patch.object(notifier, "deliver_bounded", return_value="queued"):
            self.send()
        original_loads = json.loads
        def nested_record(raw):
            if '"outcome"' in raw:
                raise RecursionError
            return original_loads(raw)
        with mock.patch.object(notifier.json, "loads", side_effect=nested_record):
            with self.assertRaises(notifier.NotificationError) as caught:
                self.send()
            self.assertEqual("unknown", caught.exception.outcome)

    def test_address_matching_preserves_local_case_and_normalizes_domains(self):
        with self.assertRaisesRegex(notifier.NotificationError, "not permitted"):
            self.send(recipient="Owner@example.test")
        patcher, _, _ = self.response(queued=["owner@EXAMPLE.TEST"])
        with patcher:
            self.assertEqual("queued", self.send(recipient="owner@EXAMPLE.TEST")["delivery"])
        patcher, _, _ = self.response(queued=["Owner@example.test"])
        with patcher, self.assertRaises(notifier.NotificationError) as caught:
            notifier.deliver(self.profile, self.token, {"to": "owner@example.test"})
        self.assertEqual("unknown", caught.exception.outcome)

    def test_supervisor_uses_isolated_private_pipes_and_handles_worker_results(self):
        fixture = self.root / "worker.py"
        for code, response, expected in ((0, {"delivery": "queued"}, "queued"),
                                          (2, {"delivery": "failed"}, "failed"),
                                          (1, {"delivery": "accepted"}, "unknown"),
                                          (0, {"delivery": "unknown"}, "unknown"),
                                          (0, {"invalid": self.token}, "unknown")):
            fixture.write_text("import json,sys\nassert sys.flags.isolated\n"
                               "job=json.load(sys.stdin)\nassert set(job)=={'profile','token','payload'}\n"
                               "print(" + repr(json.dumps(response)) + ")\nraise SystemExit(" + str(code) + ")\n")
            with self.subTest(code=code, response=response), mock.patch.object(notifier, "__file__", str(fixture)), mock.patch.object(notifier.subprocess, "Popen", wraps=subprocess.Popen) as popen:
                if expected == "queued":
                    self.assertEqual("queued", BOUNDED_DELIVER(self.profile, self.token, {"to": "owner@example.test"}))
                else:
                    with self.assertRaises(notifier.NotificationError) as caught:
                        BOUNDED_DELIVER(self.profile, self.token, {"to": "owner@example.test"})
                    self.assertEqual(expected, caught.exception.outcome)
                    self.assertNotIn(self.token, str(caught.exception))
                self.assertNotIn(self.token, repr(popen.call_args))
                self.assertEqual([sys.executable, "-I", str(fixture), "--delivery-worker"], popen.call_args.args[0])

    def test_total_deadline_reaps_slow_worker_and_retains_reservation(self):
        fixture = self.root / "slow-worker.py"
        fixture.write_text("import json,sys,time\njson.load(sys.stdin)\n"
                           "for _ in range(100):\n time.sleep(.01)\n"
                           "print('{\"delivery\":\"queued\"}')\n")
        workers = []
        real_popen = subprocess.Popen
        def capture(*args, **kwargs):
            worker = real_popen(*args, **kwargs)
            workers.append(worker)
            return worker
        start = time.monotonic()
        with mock.patch.object(notifier, "__file__", str(fixture)), mock.patch.object(notifier, "TIMEOUT", .1), mock.patch.object(notifier.subprocess, "Popen", side_effect=capture), mock.patch.object(notifier, "deliver_bounded", side_effect=BOUNDED_DELIVER):
            with self.assertRaisesRegex(notifier.NotificationError, "deadline") as caught:
                self.send()
            self.assertEqual("unknown", caught.exception.outcome)
            with self.assertRaisesRegex(notifier.NotificationError, "already attempted"):
                self.send()
        self.assertLess(time.monotonic() - start, 1)
        self.assertEqual(1, len(workers))
        self.assertIsNotNone(workers[0].poll())
        records = list((self.root / "state").rglob("*.json"))
        self.assertEqual({"outcome": "unknown"}, json.loads(records[0].read_text()))

    def test_worker_converts_protocol_and_decoding_errors_without_provider_text(self):
        raw = json.dumps({"profile": self.profile, "token": self.token, "payload": {"to": "owner@example.test"}})
        for error in (http.client.IncompleteRead(self.token.encode()), http.client.BadStatusLine(self.token)):
            output = io.StringIO()
            with mock.patch("sys.stdin", io.StringIO(raw)), mock.patch("sys.stdout", output), mock.patch.object(notifier, "deliver", side_effect=error):
                self.assertEqual(2, notifier.main(["--delivery-worker"]))
            self.assertEqual({"delivery": "unknown"}, json.loads(output.getvalue()))
        output = io.StringIO()
        with io.TextIOWrapper(io.BytesIO(b'\xff'), encoding="utf-8") as stdin:
            with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", output):
                self.assertEqual(2, notifier.main(["--delivery-worker"]))
        self.assertEqual({"delivery": "unknown"}, json.loads(output.getvalue()))

    def test_copied_skill_runs_without_source_checkout(self):
        copied = self.root / "installed-email.py"
        copied.write_bytes(SCRIPT.read_bytes())
        # A project-controlled module must not execute inside a credentialed sender.
        (self.project / "json.py").write_text("raise RuntimeError('project shadow executed')\n")
        result = subprocess.run([sys.executable, "-I", str(copied), "check", "--to", "owner@example.test",
                                 "--project-root", str(self.project)],
                                env={**self.env, "PYTHONPATH": str(self.project)}, cwd=self.project,
                                capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("ready", json.loads(result.stdout)["status"])
        self.assertFalse((self.root / "state").exists())


if __name__ == "__main__":
    unittest.main()
