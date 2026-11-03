"""The API runner retries transport failures and still exits with its documented codes.

Each case is a local socket server that misbehaves in one way. No network is used."""
import contextlib
import io
import json
import socket
import threading
import unittest
from unittest import mock

import test_harness as h

runner = h.harness

OK_BODY = json.dumps({"content": [{"type": "text", "text": "hi"}], "usage": {}}).encode()
OK = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\n\r\n%s" % (len(OK_BODY), OK_BODY)
FAILURES = {
    "closed before any response": b"",
    "truncated body": b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\nContent-Type: application/json\r\n\r\n{\"a\"",
    "malformed status line": b"NOT-HTTP\r\n\r\n",
    "overloaded": b"HTTP/1.1 529 Overloaded\r\nContent-Length: 2\r\n\r\n{}",
}


@contextlib.contextmanager
def server(replies):
    """Answer successive connections with the given raw replies, then close each one."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(8)
    seen = []

    def run():
        for reply in replies:
            try:
                conn, _ = sock.accept()
            except OSError:
                return
            conn.recv(65536)
            seen.append(reply)
            if reply:
                conn.sendall(reply)
            conn.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{sock.getsockname()[1]}", seen
    finally:
        sock.close()
        thread.join(timeout=2)


def post(url, retries):
    with mock.patch.object(runner.time, "sleep"), contextlib.redirect_stderr(io.StringIO()):
        return runner._post_json(url + "/v1/messages", {}, {}, "Anthropic API", timeout=5, max_retries=retries)


class TransportFailureTests(unittest.TestCase):
    def test_each_failure_is_retried_and_a_later_success_is_returned(self):
        for name, reply in FAILURES.items():
            with self.subTest(name), server([reply, OK]) as (url, seen):
                self.assertEqual(post(url, retries=1)["content"][0]["text"], "hi")
                self.assertEqual(len(seen), 2)

    def test_exhausted_retries_exit_with_the_documented_code_not_a_traceback(self):
        for name, reply in FAILURES.items():
            expected = 20 if name == "overloaded" else 21
            with self.subTest(name), server([reply, reply]) as (url, _):
                with self.assertRaises(SystemExit) as caught:
                    post(url, retries=1)
                self.assertEqual(caught.exception.code, expected)

    def test_a_permanent_http_error_is_not_retried(self):
        bad = b"HTTP/1.1 400 Bad Request\r\nContent-Length: 2\r\n\r\n{}"
        with server([bad, OK]) as (url, seen):
            with self.assertRaises(SystemExit) as caught:
                post(url, retries=2)
            self.assertEqual((caught.exception.code, len(seen)), (20, 1))

    def test_backoff_grows_with_jitter_and_is_capped(self):
        with mock.patch.object(runner.random, "uniform", return_value=0.5):
            self.assertEqual([runner._backoff(a) for a in range(6)], [2.5, 4.5, 8.5, 16.5, 30.0, 30.0])

    def test_default_timeout_allows_a_long_non_streaming_reply(self):
        with mock.patch.dict(runner.os.environ, {}, clear=True):
            self.assertEqual(runner.parse_args(["."]).api_timeout, 600)


if __name__ == "__main__":
    unittest.main()
