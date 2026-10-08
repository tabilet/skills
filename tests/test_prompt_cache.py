"""Prompt-cache request layout, provider markers, and normalized usage.

All checks use fake providers; none of them proves a real cache hit, which a
separately bounded live run measures.
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import sys
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tests"))
import test_harness as h  # noqa: E402

core = h.harness
horizon_path = ROOT / "harness" / "tabilet_horizon.py"
sys.path.insert(0, str(ROOT / "harness"))

OFFICIAL = "https://api.anthropic.com/v1"
LONG_SYSTEM = "S" * 1200


def anthropic_body(text='{"final":"done"}', **usage):
    return {
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 8, "output_tokens": 3, **usage},
    }


def marked(payload):
    """Every cache_control marker in a request, wherever it sits."""
    found = []
    system = payload.get("system")
    if isinstance(system, list):
        found += [block for block in system if "cache_control" in block]
    for message in payload["messages"]:
        if isinstance(message["content"], list):
            found += [block for block in message["content"] if "cache_control" in block]
    return found


class InitialMessageTests(unittest.TestCase):
    def build(self, repo, run, summary):
        return core.initial_user_message(pathlib.Path(repo), run, 5, summary, None)

    def test_stable_instructions_come_first_and_survive_a_new_run(self):
        lanes_a = [{"file": "status-M01.md", "actionable": 2, "in_progress": 0, "blocked": 0, "historical": 0}]
        lanes_b = [{"file": "status-M01.md", "actionable": 1, "in_progress": 1, "blocked": 0, "historical": 3}]
        first = self.build("/work/one", 1, lanes_a)
        second = self.build("/other/place", 4, lanes_b)
        self.assertGreater(first.cache_prefix, 0)
        self.assertEqual(first.cache_prefix, second.cache_prefix)
        self.assertEqual(first[: first.cache_prefix], second[: second.cache_prefix])
        self.assertIn(core.EMBEDDED_TASK, first[: first.cache_prefix])
        # Everything that changes between runs sits after the stable prefix.
        for volatile in ("/work/one", "Run: 1/5", "status-M01.md"):
            self.assertNotIn(volatile, first[: first.cache_prefix])
            self.assertIn(volatile, first[first.cache_prefix:])
        self.assertNotEqual(first, second)

    def test_prefixed_text_is_plain_text_on_the_wire(self):
        text = core.PrefixedText("abc def", 3)
        self.assertEqual(text, "abc def")
        self.assertEqual(json.dumps({"c": text}), json.dumps({"c": "abc def"}))


class PolicyTests(unittest.TestCase):
    def policy(self, provider, base, **env):
        return core.prompt_cache_policy(provider, base, env)

    def test_auto_marks_only_the_official_anthropic_host(self):
        self.assertEqual(self.policy("anthropic", OFFICIAL), {"ttl": "5m"})
        self.assertIsNone(self.policy("anthropic", "https://gateway.example/v1"))
        self.assertIsNone(self.policy("anthropic", "http://127.0.0.1:9/v1"))

    def test_on_and_off_override_the_host_check(self):
        self.assertEqual(
            self.policy("anthropic", "https://gateway.example/v1", LLM_PROMPT_CACHE="on"), {"ttl": "5m"}
        )
        self.assertIsNone(self.policy("anthropic", OFFICIAL, LLM_PROMPT_CACHE="off"))

    def test_one_hour_lifetime_is_opt_in(self):
        self.assertEqual(self.policy("anthropic", OFFICIAL, LLM_PROMPT_CACHE_TTL="1h"), {"ttl": "1h"})

    def test_openai_compatible_providers_never_get_markers(self):
        for base in ("https://api.openai.com/v1", "https://api.deepseek.com/v1"):
            self.assertIsNone(self.policy("openai", base))
            self.assertIsNone(self.policy("openai", base, LLM_PROMPT_CACHE="on"))

    def test_invalid_settings_are_rejected(self):
        with self.assertRaises(ValueError):
            self.policy("anthropic", OFFICIAL, LLM_PROMPT_CACHE="maybe")
        with self.assertRaises(ValueError):
            self.policy("anthropic", OFFICIAL, LLM_PROMPT_CACHE_TTL="2h")

    def test_invalid_setting_stops_with_exit_two(self):
        quiet = contextlib.redirect_stderr(io.StringIO())
        with quiet, mock.patch.dict("os.environ", {"LLM_PROMPT_CACHE": "maybe"}):
            with self.assertRaises(SystemExit) as stopped:
                core.call_anthropic("http://127.0.0.1:9/v1", "k", "m", [{"role": "user", "content": "u"}], None, 10, 1, 0)
        self.assertEqual(stopped.exception.code, 2)
        with quiet, mock.patch.dict("os.environ", {"LLM_PROMPT_CACHE_TTL": "9h"}), mock.patch.object(
            sys, "argv", [str(h.HARNESS), "--model", "m"]
        ):
            with self.assertRaises(SystemExit) as stopped:
                core.parse_args()
        self.assertEqual(stopped.exception.code, 2)


class AnthropicRequestTests(unittest.TestCase):
    def send(self, messages, base_env=None, **env):
        """Send one request to a fake gateway and return the captured payload."""
        with h.fake_api([(200, {}, anthropic_body())]) as (base, handler):
            with mock.patch.dict("os.environ", env):
                core.call_anthropic(base, "k", "claude", messages, None, 100, 2, 0)
        return handler.requests[0]

    def standalone_messages(self, run, history=()):
        user = core.initial_user_message(
            pathlib.Path(f"/repo/{run}"), run, 5,
            [{"file": "status-M01.md", "actionable": 3 - run, "in_progress": 0, "blocked": 0, "historical": 0}],
            None,
        )
        return [{"role": "system", "content": core.SYSTEM_PROMPT}, {"role": "user", "content": user}, *history]

    def test_unknown_endpoint_payload_is_unchanged_by_default(self):
        payload = self.send(self.standalone_messages(1))
        self.assertIsInstance(payload["system"], str)
        self.assertTrue(all(isinstance(m["content"], str) for m in payload["messages"]))
        self.assertNotIn("cache_control", json.dumps(payload))

    def test_explicit_opt_in_places_two_markers_around_the_stable_prefix(self):
        payload = self.send(self.standalone_messages(1), LLM_PROMPT_CACHE="on")
        markers = marked(payload)
        self.assertEqual([m["cache_control"] for m in markers], [{"type": "ephemeral"}] * 2)
        self.assertLessEqual(len(markers), 4)
        first = payload["messages"][0]["content"]
        self.assertEqual(len(first), 2)
        self.assertIn("cache_control", first[0])
        self.assertIn(core.EMBEDDED_TASK, first[0]["text"])
        # The text on the wire is exactly the original message, only split.
        original = self.standalone_messages(1)[1]["content"]
        self.assertEqual("".join(block["text"] for block in first), original)

    def test_one_hour_lifetime_reaches_both_markers(self):
        payload = self.send(
            self.standalone_messages(1), LLM_PROMPT_CACHE="on", LLM_PROMPT_CACHE_TTL="1h"
        )
        self.assertEqual({m["cache_control"]["ttl"] for m in marked(payload)}, {"1h"})

    def test_second_run_reuses_the_first_runs_prefix_bytes(self):
        one = self.send(self.standalone_messages(1), LLM_PROMPT_CACHE="on")
        two = self.send(self.standalone_messages(2), LLM_PROMPT_CACHE="on")
        self.assertEqual(one["system"], two["system"])
        self.assertEqual(one["messages"][0]["content"][0], two["messages"][0]["content"][0])
        self.assertNotEqual(one["messages"][0]["content"][1], two["messages"][0]["content"][1])

    def test_second_marker_follows_the_newest_message(self):
        history = [
            {"role": "assistant", "content": '{"tool":"run_shell","cmd":"ls"}'},
            {"role": "user", "content": "Command result:\nREADME.md"},
        ]
        payload = self.send(self.standalone_messages(1, history), LLM_PROMPT_CACHE="on")
        self.assertEqual(len(marked(payload)), 2)
        self.assertIn("cache_control", payload["messages"][0]["content"][0])
        self.assertNotIn("cache_control", payload["messages"][0]["content"][1])
        self.assertEqual(payload["messages"][1]["content"], '{"tool":"run_shell","cmd":"ls"}')
        last = payload["messages"][-1]["content"]
        self.assertEqual(last[-1]["text"], "Command result:\nREADME.md")
        self.assertIn("cache_control", last[-1])

    def test_short_system_prompt_gets_no_prefix_marker(self):
        messages = [
            {"role": "system", "content": core.SYSTEM_PROMPT},
            {"role": "user", "content": "Execute the selected row."},
        ]
        payload = self.send(messages, LLM_PROMPT_CACHE="on")
        self.assertIsInstance(payload["system"], str)
        self.assertEqual(len(marked(payload)), 1)

    def test_planning_system_prompt_splits_at_the_context_boundary(self):
        stable = LONG_SYSTEM * 3
        system = core.PrefixedText(stable + "\n\ncontext for this project", len(stable))
        payload = self.send(
            [{"role": "system", "content": system}, {"role": "user", "content": "request"}],
            LLM_PROMPT_CACHE="on",
        )
        self.assertEqual(payload["system"][0]["text"], stable)
        self.assertIn("cache_control", payload["system"][0])
        self.assertNotIn("cache_control", payload["system"][1])
        self.assertEqual("".join(b["text"] for b in payload["system"]), str(system))

    def test_unsplit_long_system_prompt_is_marked_whole(self):
        payload = self.send(
            [{"role": "system", "content": LONG_SYSTEM * 3}, {"role": "user", "content": "q"}],
            LLM_PROMPT_CACHE="on",
        )
        self.assertEqual(len(payload["system"]), 1)
        self.assertIn("cache_control", payload["system"][0])

    def test_caller_messages_are_not_modified(self):
        messages = self.standalone_messages(1)
        snapshot = json.dumps(messages)
        self.send(messages, LLM_PROMPT_CACHE="on")
        self.assertEqual(json.dumps(messages), snapshot)


class OpenAIRequestTests(unittest.TestCase):
    def test_payload_is_identical_with_and_without_prefix_metadata(self):
        user = core.initial_user_message(pathlib.Path("/r"), 1, 2, [], None)
        plain = [{"role": "system", "content": "s"}, {"role": "user", "content": str(user)}]
        tagged = [{"role": "system", "content": "s"}, {"role": "user", "content": user}]
        sent = []
        for messages in (plain, tagged):
            with h.fake_api([(200, {}, h.openai_response('{"final":"x"}'))]) as (base, handler):
                core.call_openai(base, "k", "m", messages, None, 10, 2, 0)
            sent.append(json.dumps(handler.requests[0], sort_keys=True))
        self.assertEqual(sent[0], sent[1])
        self.assertNotIn("cache", sent[0])

    def test_compatible_endpoint_never_receives_cache_fields(self):
        with h.fake_api([(200, {}, h.openai_response('{"final":"x"}'))]) as (base, handler):
            with mock.patch.dict("os.environ", {"LLM_PROMPT_CACHE": "on"}):
                core.call_openai(base, "k", "m", [{"role": "user", "content": "u"}], None, 10, 2, 0)
        self.assertEqual(set(handler.requests[0]), {"model", "messages", "max_tokens"})


class UsageTests(unittest.TestCase):
    def test_openai_nested_cached_tokens(self):
        usage = {"prompt_tokens": 2006, "completion_tokens": 300,
                 "prompt_tokens_details": {"cached_tokens": 1920}}
        self.assertEqual(
            core.normalize_usage("openai", usage),
            {"input_total": 2006, "cached_read": 1920, "cache_write": None, "output": 300},
        )

    def test_deepseek_hit_and_miss_counters(self):
        usage = {"prompt_cache_hit_tokens": 900, "prompt_cache_miss_tokens": 100, "completion_tokens": 7}
        self.assertEqual(
            core.normalize_usage("openai", usage),
            {"input_total": 1000, "cached_read": 900, "cache_write": None, "output": 7},
        )

    def test_claude_input_total_adds_cache_fields_back(self):
        usage = {"input_tokens": 40, "cache_creation_input_tokens": 1000,
                 "cache_read_input_tokens": 5000, "output_tokens": 12}
        self.assertEqual(
            core.normalize_usage("anthropic", usage),
            {"input_total": 6040, "cached_read": 5000, "cache_write": 1000, "output": 12},
        )

    def test_unreported_counts_are_unknown_not_zero(self):
        normalized = core.normalize_usage("openai", {"prompt_tokens": 10, "completion_tokens": 4})
        self.assertIsNone(normalized["cached_read"])
        self.assertEqual(
            core.format_usage(normalized), "input=10, cached=unknown, cache_write=unknown, output=4"
        )
        zero = core.normalize_usage("anthropic", {"input_tokens": 5, "cache_read_input_tokens": 0})
        self.assertEqual(zero["cached_read"], 0)

    def test_nothing_reported_prints_nothing(self):
        for usage in ({}, None, "x", {"prompt_tokens": True, "completion_tokens": -1}):
            self.assertEqual(core.format_usage(core.normalize_usage("openai", usage)), "")

    def test_totals_sum_known_values_and_keep_unreported_fields_unknown(self):
        totals = core.UsageTotals()
        totals.add({"input_total": 10, "cached_read": None, "cache_write": None, "output": 1})
        totals.add({"input_total": 5, "cached_read": 4, "cache_write": None, "output": 2})
        self.assertEqual(totals.turns, 2)
        self.assertEqual(
            core.format_usage(totals.values), "input=15, cached=4, cache_write=unknown, output=3"
        )

    def test_run_prints_per_turn_and_total_lines_without_sqlite(self):
        replies = [
            {"content": '{"tool":"run_shell","cmd":"true"}', "usage": {
                "prompt_tokens": 100, "completion_tokens": 5,
                "prompt_tokens_details": {"cached_tokens": 0}}},
            {"content": '{"final":"done"}', "usage": {
                "prompt_tokens": 140, "completion_tokens": 3,
                "prompt_tokens_details": {"cached_tokens": 128}}},
        ]
        args = types.SimpleNamespace(
            max_runs=1, max_turns=5, max_history_chars=1_000_000, provider="openai",
            api_base="http://unused", api_key="", model="m", temperature=None, max_tokens=10,
            api_timeout=2, max_retries=0, tool_timeout=5, max_tool_output=1000,
            allow_dangerous=False, tool_env={},
        )
        seen = []
        executor = lambda *_a: {"exit_code": 0, "stdout": "", "stderr": "", "truncated": False}
        with mock.patch.object(core, "call_llm", side_effect=replies):
            with mock.patch("builtins.print") as printed:
                core.one_agent_run(args, ROOT, 1, [], None, executor=executor, after_model_response=seen.append)
        lines = [call.args[0] for call in printed.call_args_list if call.args]
        self.assertIn("  LLM usage: input=100, cached=0, cache_write=unknown, output=5", lines)
        self.assertIn("  LLM usage: input=140, cached=128, cache_write=unknown, output=3", lines)
        self.assertIn("  LLM usage total (2 turns): input=240, cached=128, cache_write=unknown, output=8", lines)
        self.assertEqual([item["cached_read"] for item in seen], [0, 128])


class ReceiptTotalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.machinery
        import importlib.util
        loader = importlib.machinery.SourceFileLoader("horizon_cache_test", str(horizon_path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        cls.horizon = importlib.util.module_from_spec(spec)
        loader.exec_module(cls.horizon)

    def test_totals_stay_four_integers_however_many_turns_run(self):
        receipt = {"usage": {}}
        for _ in range(5000):
            self.horizon._add_token_usage(
                receipt, {"input_total": 900, "cached_read": 800, "cache_write": None, "output": 10}
            )
        tokens = receipt["usage"]["tokens"]
        self.assertEqual(tokens, {"input_total": 4_500_000, "cached_read": 4_000_000, "output": 50_000})
        self.assertLess(len(json.dumps(receipt)), 200)

    def test_nothing_reported_leaves_the_receipt_untouched(self):
        receipt = {"usage": {"rows_started": 1}}
        self.horizon._add_token_usage(
            receipt, {"input_total": None, "cached_read": None, "cache_write": None, "output": None}
        )
        self.assertEqual(receipt, {"usage": {"rows_started": 1}})
        self.assertEqual(self.horizon._token_summary(receipt), "")

    def test_progress_line_reports_unknown_for_unreported_fields(self):
        receipt = {"usage": {"tokens": {"input_total": 10, "output": 2}}}
        self.assertEqual(
            self.horizon._token_summary(receipt),
            "; tokens input=10 cached=unknown cache_write=unknown output=2",
        )


if __name__ == "__main__":
    unittest.main()
