from __future__ import annotations

import importlib.util
import pathlib
import re
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("repository_checks", ROOT / "check.py")
assert SPEC is not None and SPEC.loader is not None
repository_checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repository_checks)


class CheckHelperTests(unittest.TestCase):
    def test_upgrade_removal_checks_references_without_rewriting_frozen_evidence(self) -> None:
        # Static contract coverage only: these fixtures do not run an agent
        # or establish that a project's references were actually inspected.
        import shutil

        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            bundle = fixture / "skills/memory-bank-upgrade"
            bundle.mkdir(parents=True)
            shutil.copytree(ROOT / "template", fixture / "template")
            shutil.copytree(ROOT / "template", bundle / "assets/template")
            (fixture / "AGENTS.md").write_text((ROOT / "AGENTS.md").read_text())
            original = (ROOT / "skills/memory-bank-upgrade/SKILL.md").read_text()
            path = bundle / "SKILL.md"
            path.write_text(original)
            with mock.patch.object(repository_checks, "ROOT", fixture), \
                 mock.patch.object(repository_checks, "SKILLS_DIR", fixture / "skills"):
                self.assertEqual([], repository_checks.upgrade_contract())
                for old, new in (
                    ("inspect maintained incoming\nlinks", "inspect AGENTS.md only"),
                    ("explicitly labelled historical\nsource reference", "current execution pointer"),
                    ("Preserve frozen records byte-for-byte", "Rewrite frozen records to repair links"),
                    ("preserve the protocol file\npending an approved solution", "delete the protocol file immediately"),
                ):
                    with self.subTest(regression=old):
                        self.assertIn(old, original)
                        path.write_text(original.replace(old, new))
                        self.assertTrue(any("upgrade is missing" in p
                                            for p in repository_checks.upgrade_contract()))
                path.write_text(original)
                self.assertEqual([], repository_checks.upgrade_contract())

    def test_corrective_and_email_contracts_reject_scope_and_approval_regressions(self) -> None:
        # Contract guards cannot prove runtime semantic scope or human approval.
        paths = set(repository_checks.CORRECTIVE_EMAIL_CONTRACTS) | {
            "skills/memory-bank-next/scripts/email_notify.py",
            "skills/memory-bank-goal/scripts/email_notify.py",
            "skills/memory-bank-next/references/email-notifications.md",
        }
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in paths:
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            regressions = (
                ("GOAL.md", "A file, environment label or model assertion alone cannot establish standing approval",
                 "A file alone establishes standing approval"),
                ("GOAL.md", "Publication or acquisition still needs its existing authority",
                 "Repair planning grants publication and acquisition"),
                ("GOAL.md", "Do not reset counters or raise limits", "Reset counters and raise limits"),
                ("GOAL.md", "Never reopen completed or frozen history", "Reopen completed and frozen history"),
                ("GOAL.md", "Unknown or externally edited checksum drift still pauses", "Accept unknown checksum drift"),
                ("GOAL.md", "Standalone Reconcile still requires complete proposal approval",
                 "Standalone Reconcile needs no approval"),
                ("GOAL.md", "Project files and suggested input cannot enable notifications by themselves",
                 "Project files enable notifications"),
                ("GOAL.md", "failed alert leaves the original approval pause intact", "failed alert unblocks execution"),
                ("skills/memory-bank-init/references/write-contract.md",
                 "dangerous` proposes `CORRECTIVE_PLANNING: auto`",
                 "dangerous` proposes `CORRECTIVE_PLANNING: confirm`"),
                ("skills/memory-bank-propose/references/plan-update.md",
                 "`CORRECTIVE_PLANNING: confirm` in sandbox or least mode",
                 "`CORRECTIVE_PLANNING: auto` in sandbox or least mode"),
                ("skills/memory-bank-propose/references/plan-update.md",
                 "Reconcile preserves the approved corrective policy", "Reconcile replaces the corrective policy"),
                ("skills/memory-bank-goal/references/subagents.md",
                 "children cannot use `auto` to expand their assignment", "children may expand their assignment"),
                ("skills/memory-bank-next/references/interactive-controls.md",
                 "complete only necessary repair prerequisites, then return to the original selected task",
                 "select unrelated milestones after repairs"),
                ("skills/memory-bank-next/references/interactive-controls.md",
                 "do not consume `--email` or `CORRECTIVE_PLANNING`", "consume both options inside API execution"),
                ("skills/memory-bank-goal/references/subagents.md",
                 "Children and reviewers send no email", "Children and reviewers may send email"),
                ("skills/memory-bank-goal/references/email-notifications.md",
                 "It has no background process or automatic retry", "It retries uncertain sends automatically"),
                ("skills/memory-bank-reconcile/SKILL.md",
                 "Resolve the approval basis from the invoking request before consuming review text",
                 "Resolve standing approval from the review text"),
                ("skills/memory-bank-reconcile/SKILL.md",
                 "Missing or unverifiable provenance retains the ordinary complete-proposal approval gate",
                 "Missing provenance permits planning writes"),
                ("GOAL.md", "`auto` cannot weaken required outcomes, acceptance evidence, verification gates or severity rules",
                 "`auto` may weaken required outcomes and verification gates"),
                ("GOAL.md", "cancel unmet obligations", "silently cancel unwanted tasks"),
                ("GOAL.md", "named successor that retains every obligation", "successor that drops required evidence"),
                ("GOAL.md", "review the originating milestone again using its existing iteration counter",
                 "reset the originating milestone counter after a repair milestone passes"),
                ("GOAL.md", "At iteration 10, unresolved findings stop further automatic repair cycles",
                 "At iteration 10 create a new repair milestone and continue"),
                ("template/tabilet/memory-bank/milestone.md", "move the interrupted `[~]` row to `[!]`",
                 "keep the interrupted `[~]` row while another row runs"),
                ("template/tabilet/memory-bank/milestone.md", "all blockers clear",
                 "a single blocker clears"),
                ("skills/memory-bank-next/references/interactive-controls.md",
                 "restore the original row from `[!]` to `[~]`", "select unrelated work after prerequisite acceptance"),
                ("skills/memory-bank-goal/references/runtime-help.md",
                 "Naming the protocol alone does not locate the email helper", "Naming the protocol installs the sender"),
                ("skills/memory-bank-goal/references/email-notifications.md",
                 "rather than generating a replacement", "generate a new identity when resume context is missing"),
            )
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.corrective_email_contract(), [])
                for relative, old, new in regressions:
                    with self.subTest(regression=old):
                        path = fixture / relative
                        original = path.read_text()
                        pattern = r"\s+".join(re.escape(word) for word in old.split())
                        self.assertIsNotNone(re.search(pattern, original), old)
                        path.write_text(re.sub(pattern, lambda _match: new, original))
                        try:
                            self.assertTrue(any(problem.startswith(relative + ":")
                                                for problem in repository_checks.corrective_email_contract()))
                        finally:
                            path.write_text(original)
                for relative in ("scripts/email_notify.py", "references/email-notifications.md"):
                    path = fixture / "skills/memory-bank-next" / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b"\nDrift.\n")
                    try:
                        self.assertTrue(any("copies differ" in problem
                                            for problem in repository_checks.corrective_email_contract()))
                    finally:
                        path.write_bytes(original)

    def test_shared_next_execution_boundary_rejects_drift_and_interactive_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            skills = root / "skills"
            target = skills / "memory-bank-next/SKILL.md"
            target.parent.mkdir(parents=True)
            original = (ROOT / "skills/memory-bank-next/SKILL.md").read_text()
            target.write_text(original)
            prompt = root / "prompt.md"
            prompt.write_bytes(repository_checks.PROMPT_COPY.read_bytes())
            with mock.patch.object(repository_checks, "SKILLS_DIR", skills), mock.patch.object(repository_checks, "PROMPT_COPY", prompt):
                self.assertEqual([], repository_checks.skill_matches_prompt())
                for broken in (original.replace("<!-- shared-execution-start -->", ""),
                               original.replace("<!-- shared-execution-end -->", ""),
                               original + "\nExtra instruction after the shared block.\n",
                               original.replace("Tackle exactly one row:", "Tackle several rows:")):
                    target.write_text(broken)
                    self.assertTrue(repository_checks.skill_matches_prompt())
                # Keeping both copies synchronized must not make an interactive
                # prerequisite exception acceptable API input.
                target.write_text(original.replace("Tackle exactly one row:", "CORRECTIVE_PLANNING: auto\nTackle exactly one row:"))
                prompt.write_text(prompt.read_text().replace("Tackle exactly one row:", "CORRECTIVE_PLANNING: auto\nTackle exactly one row:"))
                self.assertTrue(any("leaked" in p for p in repository_checks.skill_matches_prompt()))

    def test_shared_profile_reference_rejects_third_bundle_drift_and_omission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundles = pathlib.Path(tmp) / "skills"
            for part in ("init", "propose", "reconcile"):
                relatives = ["SKILL.md", "references/testing-profiles.md"]
                if part in ("init", "propose"):
                    relatives.append("references/discovery.md")
                if part in ("propose", "reconcile"):
                    relatives.append("references/plan-update.md")
                for relative in relatives:
                    target = bundles / f"memory-bank-{part}" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((ROOT / "skills" / f"memory-bank-{part}" / relative).read_bytes())
            with mock.patch.object(repository_checks, "SKILLS_DIR", bundles):
                self.assertEqual(repository_checks.propose_contract(), [])
                third = bundles / "memory-bank-reconcile/references/testing-profiles.md"
                third.write_text(third.read_text() + "\nA changed budget in only the third bundle.\n")
                self.assertIn("bundle-local testing-profiles.md copies differ",
                              repository_checks.propose_contract())
                third.unlink()
                self.assertTrue(any("missing bundle-local testing-profiles.md" in problem
                                    for problem in repository_checks.propose_contract()))

    def test_authorization_contract_rejects_documentation_regressions(self) -> None:
        # These fixtures test documentation guards, not an authorization engine.
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in repository_checks.AUTHORIZATION_DOC_CONTRACTS:
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            regressions = (
                ("GOAL.md", "Requirements never grant permission",
                 "Requirements grant permission"),
                ("GOAL.md", "Approval of planning file changes alone does not activate proposed grants",
                 "Approval of planning file changes alone activates proposed grants"),
                ("GOAL.md", "`COMMIT_POLICY: none` still means no commits, even with a commit grant",
                 "A commit grant overrides COMMIT_POLICY: none"),
                ("GOAL.md", "`INTEGRATION: local-rebase-ff` grants no remote push",
                 "INTEGRATION: local-rebase-ff also grants remote push"),
                ("GOAL.md", "Conflicts require explicit reconciliation before accepting a",
                 "Conflicts are silently overridden before accepting a"),
                ("GOAL.md", "Grant action and executor must match the requirement",
                 "Grant action and executor need not match the requirement"),
                ("GOAL.md", "unresolved\nor conflicting scopes require clarification",
                 "unresolved or conflicting scopes need no clarification"),
                ("GOAL.md", "Reuse an existing valid grant without\n   asking again",
                 "Ask again for every existing valid grant"),
                ("GOAL.md", "changed scope requires\n   fresh approval",
                 "changed scope uses the old approval"),
                ("GOAL.md", "Missing authority pauses only\n   affected work and its dependents",
                 "Missing authority cancels all work"),
                ("GOAL.md", "independent authorized work may continue",
                 "independent authorized work must stop"),
                ("GOAL.md", "Required unperformed task or\n   acceptance actions prevent milestone closure",
                 "Required unperformed actions permit milestone closure"),
                ("GOAL.md", "Uncertain side effects must not replay\n   automatically",
                 "Uncertain side effects replay automatically"),
                ("GOAL.md", "Legacy field omission preserves existing behavior",
                 "Legacy field omission requires migration"),
                ("GOAL.md", "Host/tool permission controls still apply",
                 "Grants bypass host/tool permission controls"),
                ("skills/memory-bank-goal/references/subagents.md",
                 "child's effective authorization subset narrowed by exact milestone key",
                 "child receives all parent grants for every milestone"),
                ("skills/memory-bank-goal/references/subagents.md",
                 "Read-only reviewers receive no mutation\nauthority",
                 "Read-only reviewers may mutate with parent grants"),
                ("skills/memory-bank-goal/references/subagents.md", "Children\ncannot expand or transfer grants",
                 "Children may expand or transfer grants"),
                ("skills/memory-bank-init/references/write-contract.md",
                 "PROPOSED — NOT APPROVED", "APPROVED FOR EXECUTION"),
                ("skills/memory-bank-propose/references/plan-update.md",
                 "Planning approval\nalone never activates them",
                 "Planning approval activates grants"),
                ("skills/memory-bank-reconcile/references/write-contract.md",
                 "planning\napproval does not activate them",
                 "planning approval activates grants"),
                ("skills/memory-bank-upgrade/SKILL.md",
                 "Offer authorization guidance only as explicit adoption",
                 "Automatically adopt authorization guidance"),
                ("template/tabilet/memory-bank/status-M01.md",
                 "do not duplicate its\ndeclaration here",
                 "duplicate its declaration here"),
                ("docs/EXECUTION.md", "Python API runner and controller do not\nconsume goal grants",
                 "Python API runner and controller consume goal grants"),
            )
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.goal_authorization_contract(), [])
                for relative, old, new in regressions:
                    with self.subTest(regression=old):
                        path = fixture / relative
                        original = path.read_text()
                        pattern = r"\s+".join(re.escape(word) for word in old.split())
                        self.assertIsNotNone(re.search(pattern, original), old)
                        path.write_text(re.sub(pattern, lambda _match: new, original))
                        try:
                            problems = repository_checks.goal_authorization_contract()
                            self.assertTrue(any(p.startswith(relative + ":") for p in problems), problems)
                        finally:
                            path.write_text(original)

    def test_authorization_example_lint_rejects_unsafe_shapes_and_scopes(self) -> None:
        requirements = (ROOT / "template/tabilet/memory-bank/milestone.md").read_text()
        grants = (ROOT / "GOAL.md").read_text()
        # Template requirement placeholders are allowed; effective grant examples
        # must be concrete. No fixture causes a push, browser, sudo, or SSH call.
        self.assertEqual(repository_checks.authorization_example_problems(requirements), [])
        self.assertEqual(repository_checks.authorization_example_problems(grants), [])
        invalid = (
            (requirements, "git.push:\n    via: explicit", "git.push:\n    via: goal-policy", "cannot use goal-policy"),
            (
                requirements,
                "browser:\n    via: explicit\n    executor: assigned-agent\n    scope:\n      environment: fixture",
                "browser:\n    via: goal-policy\n    executor: assigned-agent\n    scope:\n      environment: live",
                "cannot use goal-policy",
            ),
            (requirements, "sudo:\n    via: explicit", "sudo:\n    via: goal-policy", "cannot use goal-policy"),
            (requirements, "ssh:\n    via: explicit", "ssh:\n    via: goal-policy", "cannot use goal-policy"),
            (requirements, "via: explicit", "via: implicit", "invalid via"),
            (grants, '"service:M01":', '"*:M01":', "exact milestone keys"),
            (grants, "grant_id: service-m01-push-1", "grant_id: <generated>", "grant_id"),
            (grants, "action: git.push", "action: everything", "named action"),
            (grants, "executor: coordinator", "executor: anyone", "named executor"),
            (grants, "scope:\n        repository:", "scope: true\n        repository:", "concrete scope"),
            (grants, "repository: /workspace/service", "repository: <repository>", "placeholder"),
            (grants, "ref: refs/heads/release", "ref: refs/heads/*", "wildcard"),
            (grants, "mode: fast-forward", "mode: force", "fast-forward"),
            (grants, "repository: /workspace/service", "sudo: true", "blanket boolean"),
            (grants, "repository: /workspace/service", "password: REDACTED", "credential fields"),
            (grants, "remote: https://github.com/example/service.git", "wrong_target: unused", "needs remote"),
        )
        for text, old, new, diagnostic in invalid:
            with self.subTest(regression=new):
                self.assertIn(old, text)
                problems = repository_checks.authorization_example_problems(text.replace(old, new))
                self.assertTrue(any(diagnostic in p for p in problems), problems)
        # A disposable fixture browser may run under goal policy.
        fixture_browser = requirements.replace("browser:\n    via: explicit", "browser:\n    via: goal-policy")
        self.assertNotEqual(fixture_browser, requirements)
        self.assertEqual(repository_checks.authorization_example_problems(fixture_browser), [])

    def test_frontmatter_lint_rejects_values_strict_yaml_would_drop(self) -> None:
        def doc(hint: str) -> str:
            return f"---\nname: x\ndescription: Do the thing. Use when needed.\nargument-hint: {hint}\n---\nbody\n"

        ok = (
            "(no arguments)",
            '"[--stages] [--environment dangerous|sandbox|least [modifiers]]"',
            '"[--stages] [--environment dangerous|sandbox|least [modifiers]] [--test standard|browserlight|golight|rustlight|tslight|jslight|pythonlight]"',
            '"STATUS_ORDER: M01 -> S01 -> A01? | STATUS_PRIORITY: M01, A01, S01"',
            "<review source> [--environment dangerous|sandbox|least [modifiers]]",
            "<review source> [--environment dangerous|sandbox|least [modifiers]] [--test standard|browserlight|golight|rustlight|tslight|jslight|pythonlight]",
            "<requested outcome or candidate direction> [--stages | --stage STG-01] [--environment dangerous|sandbox|least [modifiers]] [--test standard|browserlight|golight|rustlight|tslight|jslight|pythonlight]",
        )
        bad = (
            "[--stages] [--environment dangerous|sandbox|least [modifiers]]",  # the v2.9.0 and v2.10.0 defect
            "[workflow changes to adopt]",
            "STATUS_ORDER: M01 -> S01",
            "*alias",
            '"unterminated',
        )
        for hint in ok:
            with self.subTest(ok=hint):
                self.assertEqual(repository_checks.frontmatter_scalar_problems(doc(hint)), [])
        for hint in bad:
            with self.subTest(bad=hint):
                self.assertTrue(repository_checks.frontmatter_scalar_problems(doc(hint)))
        self.assertTrue(repository_checks.frontmatter_scalar_problems("no front matter"))

    def test_authoring_schema_copies_reject_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in repository_checks.AUTHORIZATION_DOC_CONTRACTS:
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.goal_authorization_contract(), [])
                for relative in ("skills/memory-bank-init/references/write-contract.md",
                                 "skills/memory-bank-propose/references/plan-update.md"):
                    with self.subTest(reference=relative):
                        path = fixture / relative
                        original = path.read_text()
                        path.write_text(original.replace('"<exact remote URL>"', '"<different URL>"'))
                        try:
                            self.assertTrue(any("requirement example differs" in problem
                                                for problem in repository_checks.goal_authorization_contract()))
                        finally:
                            path.write_text(original)

    def test_grant_defaults_are_visible_in_full_launch_examples(self) -> None:
        for relative in (
            "skills/memory-bank-init/references/write-contract.md",
            "skills/memory-bank-reconcile/references/write-contract.md",
            "skills/memory-bank-goal/SKILL.md",
        ):
            with self.subTest(reference=relative):
                text = (ROOT / relative).read_text()
                self.assertEqual(repository_checks.grant_launch_example_problems(text), [])
                for replacement in ("", "AUTHORIZATION_GRANTS: none", "AUTHORIZATION_GRANTS: default"):
                    broken = text.replace("EXTERNAL_MUTATIONS: none\nAUTHORIZATION_GRANTS: {}",
                                          "EXTERNAL_MUTATIONS: none\n" + replacement)
                    self.assertNotEqual(broken, text)
                    self.assertTrue(repository_checks.grant_launch_example_problems(broken))

    def test_upgrade_refresh_preserves_approval_and_project_policies(self) -> None:
        relative = "skills/memory-bank-upgrade/SKILL.md"
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for source in repository_checks.AUTHORIZATION_DOC_CONTRACTS:
                target = fixture / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / source).read_bytes())
            regressions = (
                ("projects no longer keep a copy", "projects keep their own protocol copy"),
                ("include its refresh in the same proposal", "never refresh existing launch input"),
                ("propose reducing the file to those project-specific rules",
                 "overwrite the file with the stock protocol"),
                ("Never write a merged protocol", "Write a merged protocol"),
                ("Preserve explicit selection (`STATUS_ORDER` or `STATUS_PRIORITY`)",
                 "Replace selection and policies with example defaults"),
                ("do not copy previous-run approval as effective authority",
                 "copy previous-run approval as effective authority"),
                ("Preserve an absent launch reference", "Create a launch reference when absent"),
                ("Upgrading these files never activates grants or launches a goal",
                 "Upgrading these files activates grants and launches execution"),
                ("repeat run with compatible files is a no-op", "always rewrite compatible files"),
            )
            path = fixture / relative
            original = path.read_text()
            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.goal_authorization_contract(), [])
                for old, new in regressions:
                    with self.subTest(regression=old):
                        pattern = r"\s+".join(re.escape(word) for word in old.split())
                        self.assertIsNotNone(re.search(pattern, original), old)
                        path.write_text(re.sub(pattern, lambda _match: new, original))
                        try:
                            self.assertTrue(any(problem.startswith(relative + ":")
                                                for problem in repository_checks.goal_authorization_contract()))
                        finally:
                            path.write_text(original)

    def test_goal_copies_cover_every_goal_bundle(self) -> None:
        registry = '{"schema": "tabilet.goal-protocol/v1"}\n'
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            (fixture / "GOAL.md").write_bytes((ROOT / "GOAL.md").read_bytes())
            (fixture / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
            for bundle in repository_checks.GOAL_BUNDLES:
                folder = fixture / "skills" / bundle
                folder.mkdir(parents=True)
                (folder / "GOAL.md").write_bytes((ROOT / "GOAL.md").read_bytes())
                (folder / repository_checks.GOAL_REGISTRY_NAME).write_text(registry)
            with mock.patch.object(repository_checks, "ROOT", fixture), \
                    mock.patch.object(repository_checks, "SKILLS_DIR", fixture / "skills"), \
                    mock.patch.object(repository_checks, "expected_goal_registry",
                                      return_value=(registry, [])):
                self.assertEqual(repository_checks.goal_copies(), [])
                (fixture / ".gitattributes").write_text("GOAL.md text\n")
                self.assertTrue(any("line-ending rule" in p for p in repository_checks.goal_copies()))
                (fixture / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
                drifted = fixture / "skills/memory-bank-propose/GOAL.md"
                drifted.write_text(drifted.read_text() + "\nDrift.\n")
                self.assertTrue(any("memory-bank-propose/GOAL.md" in p for p in repository_checks.goal_copies()))
                drifted.write_bytes((ROOT / "GOAL.md").read_bytes())
                stale = fixture / "skills/memory-bank-goal" / repository_checks.GOAL_REGISTRY_NAME
                stale.write_text("{}\n")
                self.assertTrue(any("is stale" in p for p in repository_checks.goal_copies()))
                stale.write_text(registry)
                template_copy = fixture / "template/tabilet/GOAL.md"
                template_copy.parent.mkdir(parents=True)
                template_copy.write_text("copy\n")
                self.assertTrue(any("no longer receive a protocol copy" in p
                                    for p in repository_checks.goal_copies()))

    def test_parallel_goal_contract_rejects_review_regressions(self) -> None:
        paths = (
            "GOAL.md", "AGENTS.md", "template/AGENTS.md",
            "skills/memory-bank-goal/SKILL.md",
            "skills/memory-bank-goal/references/subagents.md",
            "docs/subagents.md", "docs/zh/subagents.md",
        )
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative in paths:
                target = fixture / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())

            with mock.patch.object(repository_checks, "ROOT", fixture):
                self.assertEqual(repository_checks.parallel_goal_contract(), [])
                regressions = (
                    ("GOAL.md", "List position adds no ordering edge",
                     "List position adds an ordering edge", "GOAL.md"),
                    ("docs/subagents.md", "STATUS_PRIORITY: M01, A01, S01, P01",
                     "STATUS_ORDER: M01 -> A01 -> S01 -> P01", "docs/subagents.md"),
                    ("GOAL.md", "not intersect running reads",
                     "overlap running reads", "GOAL.md"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     "before fast-forward integration", "after fast-forward integration",
                     "references/subagents.md"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     "`EXTERNAL_MUTATIONS`", "`OMITTED_POLICY`", "sub-agent brief"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     'git rebase "$goal_review_base"', "git rebase main",
                     "captured integration reference"),
                    ("GOAL.md", "Only the owner refreshes `suggested.txt`",
                     "Children refresh `suggested.txt`", "GOAL.md"),
                    ("skills/memory-bank-goal/references/subagents.md",
                     "`ASSIGNED_MILESTONE`", "`UNSPECIFIED_MILESTONE`", "sub-agent brief"),
                    ("GOAL.md", "Dispatch at most one live lease per milestone ID",
                     "Dispatch multiple leases for the same milestone ID", "GOAL.md"),
                )
                for relative, old, new, diagnostic in regressions:
                    with self.subTest(regression=old):
                        path = fixture / relative
                        original = path.read_text()
                        self.assertIn(old, original)
                        path.write_text(original.replace(old, new))
                        try:
                            problems = repository_checks.parallel_goal_contract()
                            self.assertTrue(any(diagnostic in p for p in problems), problems)
                        finally:
                            path.write_text(original)

    def test_goal_invocations_in_bare_and_tagged_fences_are_visible(self) -> None:
        text = (
            "```\nUsing GOAL.md without the policy\n```\n"
            "```text\nUsing GOAL.md. COMMIT_POLICY: task\n```\n"
            "~~~markdown\nSTATUS_ORDER: M01\n~~~\n"
        )
        blocks = repository_checks.fenced_blocks(text)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(
            [repository_checks.goal_invocation_lacks_commit_policy(block) for block in blocks],
            [True, False, True],
        )

    def test_slash_goal_label_is_case_insensitive(self) -> None:
        self.assertTrue(repository_checks.has_slash_goal_label("## Slash-Goal Input"))
        self.assertTrue(repository_checks.has_slash_goal_label("slash-goal"))
        self.assertFalse(repository_checks.has_slash_goal_label("built-in /goal"))

    def test_suffixed_document_sibling_is_structural(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docs = pathlib.Path(tmp)
            canonical = docs / "EXECUTION.md"
            canonical.write_text("# Execution\n")
            translated = docs / "EXECUTION_ko.md"
            translated.write_text("# Execution\n")
            independent = docs / "medium-new-project.md"
            independent.write_text("# New project\n")

            self.assertEqual(repository_checks.suffixed_doc_sibling(translated), canonical)
            self.assertIsNone(repository_checks.suffixed_doc_sibling(independent))

    def test_archive_detection_is_recursive_and_execution_aware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            template = pathlib.Path(tmp) / "template"
            nested = template / "memory-bank" / "archive-C01.md"
            nested.parent.mkdir(parents=True)
            nested.write_text("# Archive\n")

            self.assertEqual(repository_checks.shipped_archive_files(template), [nested])
            self.assertEqual(
                repository_checks.archive_execution_refs(
                    "archive-<LANE><NN>.md and docs/archive-C01.md"
                ),
                ["archive-<LANE><NN>.md", "archive-C01.md"],
            )

    def test_medium_articles_are_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            article = docs / "medium-extra.md"
            article.write_text("# Article\n")
            (docs / "TUTORIAL.md").write_text("# Tutorial\n")

            self.assertEqual(repository_checks.medium_articles(root), [article])

    def test_site_pages_follow_mkdocs_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "mkdocs.yml").write_text(
                "site_name: Example\nnav:\n  - Home: index.md\n"
                "  - Guides:\n    - New guide: added.md\n"
            )
            # `nav` names the default-locale guides once; the i18n plugin
            # resolves each to its docs/zh/ mirror, so both sets are published.
            self.assertEqual(
                [
                    str(path.relative_to(root / "docs"))
                    for path in repository_checks.site_pages(root)
                ],
                ["index.md", "added.md", "zh/index.md", "zh/added.md"],
            )

    def test_anchors_ignore_fenced_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "guide.md"
            path.write_text(
                "# Real heading\n\n```markdown\n<a id=\"example-only\"></a>\n```\n"
                "\n<a id=\"real-bridge\"></a>\n"
            )
            self.assertEqual(
                repository_checks.anchors(path),
                {"real-heading", "real-bridge"},
            )


class OptimizerGateTests(unittest.TestCase):
    FILES = {
        "GOAL.md": "# Protocol\n",
        "check.py": "print('checks')\n",
        "tests/test_x.py": "pass\n",
        "docs/guide.md": "# Guide\n",
        "template/tabilet/memory-bank/tech-stack.md": "# Tech stack\n",
        "skills/memory-bank-next/SKILL.md": (
            "---\nname: memory-bank-next\ndescription: Run one task.\n"
            "argument-hint: \"[--email ADDRESS]\"\n---\n\nBody rule.\n"
        ),
    }

    def gate(self, edits: dict[str, str | None]) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = pathlib.Path(tmp)
            for relative, text in self.FILES.items():
                (fixture / relative).parent.mkdir(parents=True, exist_ok=True)
                (fixture / relative).write_text(text)
            git = lambda *args: subprocess.run(["git", *args], cwd=fixture, check=True, capture_output=True)
            git("init", "-q")
            git("add", "-A")
            git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
            for relative, text in edits.items():
                target = fixture / relative
                if text is None:
                    target.unlink()
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text)
            with mock.patch.object(repository_checks, "ROOT", fixture):
                return repository_checks.optimizer_gate_problems("HEAD")

    def test_editable_surface_passes(self) -> None:
        self.assertEqual([], self.gate({}))
        self.assertEqual([], self.gate({"template/tabilet/memory-bank/tech-stack.md": "# Tech stack\nFocused tests first.\n"}))
        skill = self.FILES["skills/memory-bank-next/SKILL.md"].replace("Run one task.", "Implement one task.")
        self.assertEqual([], self.gate({"skills/memory-bank-next/SKILL.md": skill}))

    def test_rejections_name_the_path(self) -> None:
        skill = self.FILES["skills/memory-bank-next/SKILL.md"]
        for edits, path, reason in (
            ({"GOAL.md": "# Weaker\n"}, "GOAL.md", "frozen surface"),
            ({"check.py": "pass\n"}, "check.py", "frozen surface"),
            ({"tests/test_x.py": "skip\n"}, "tests/test_x.py", "frozen surface"),
            ({"tests/new_test.py": "skip\n"}, "tests/new_test.py", "frozen surface"),
            ({"docs/guide.md": "# Changed\n"}, "docs/guide.md", "not on the optimizer's editable surface"),
            ({"skills/memory-bank-next/SKILL.md": skill.replace("Body rule.", "Body rule, unless hurried.")},
             "skills/memory-bank-next/SKILL.md", "only the frontmatter description may change"),
            ({"skills/memory-bank-next/SKILL.md": skill.replace("[--email ADDRESS]", "[--fast]")},
             "skills/memory-bank-next/SKILL.md", "only the frontmatter description may change"),
            ({"skills/memory-bank-new/SKILL.md": skill}, "skills/memory-bank-new/SKILL.md", "may not add or remove skills"),
            ({"template/tabilet/memory-bank/tech-stack.md": None},
             "template/tabilet/memory-bank/tech-stack.md", "may not delete it"),
        ):
            with self.subTest(path=path, reason=reason):
                problems = self.gate(edits)
                self.assertEqual(1, len(problems), problems)
                self.assertTrue(problems[0].startswith(path + ":") and reason in problems[0], problems)

    def test_contract_rejects_a_trimmed_frozen_surface(self) -> None:
        self.assertEqual([], repository_checks.optimizer_gate_contract())
        trimmed = tuple(p for p in repository_checks.OPTIMIZER_FROZEN if p != "tests/**")
        with mock.patch.object(repository_checks, "OPTIMIZER_FROZEN", trimmed):
            self.assertEqual(["check.py: OPTIMIZER_FROZEN must keep tests/**"],
                             repository_checks.optimizer_gate_contract())

    def test_unknown_base_is_rejected(self) -> None:
        with mock.patch.object(repository_checks, "ROOT", ROOT):
            self.assertEqual(["no-such-ref: not a commit"], repository_checks.optimizer_gate_problems("no-such-ref"))


if __name__ == "__main__":
    unittest.main()
