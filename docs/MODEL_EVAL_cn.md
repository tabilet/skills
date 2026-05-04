# Model Eval Harness

Model eval harness 是衡量模型辅助行为的一种可重复方式。当项目依赖 prompt、agent、classifier、retrieval、ranking、generation、code repair、summarization，或者任何模型质量很重要而普通软件测试不够覆盖的工作流时，它会很有用。

Execution harness 问的是：软件有没有正确运行？

Model eval harness 问的是：模型行为在代表性任务上变好了、变差了，还是保持不变？

## 示例

- 一组用户请求、期望答案和评分 rubric。
- 比较新旧 prompt 的 prompt regression suite。
- 衡量 accuracy、pass rate、refusal quality、latency 和 cost 的 baseline-vs-candidate 运行。
- 在 sandbox 中构建并测试生成 patch 的 code-repair eval。
- 衡量是否选中了正确文档的 retrieval eval。
- 列出 regression、improvement 和未解决 residual 的报告。

## 它放在哪里

- `memory-bank/product.md` 说明哪些模型辅助行为对产品重要。
- `memory-bank/architecture.md` 记录 prompt、dataset、grader 和 report 放在哪里。
- `memory-bank/tech-stack.md` 记录模型服务商、本地 runner、eval 命令、环境变量、成本控制和所需凭据。
- `memory-bank/milestone.md` 可以把 eval 分数或 regression review 作为 acceptance 的一部分。
- `evolution/` 记录重大的 prompt、model、architecture 或 benchmark 方向变化。

## 把 API Loop 变成 Eval

本仓库包含的 API loop 不会自动成为 model eval harness。只有当你运行受控对比并记录结果时，它才成为其中一部分。

有用的衡量项：

- model name；
- prompt version；
- dataset or todo set；
- pass/fail；
- number of loop iterations；
- test results；
- static analysis results；
- review findings；
- human acceptance；
- cost；
- latency；
- regressions introduced；
- residual failures。

## Promotion Rules

在提升一个新模型、prompt 或 agent workflow 之前，先定义：

- baseline model and prompt；
- candidate model and prompt；
- dataset or task set；
- primary metric；
- allowed regression budget；
- required deterministic checks；
- human review requirements；
- report location。

Promotion rule 应该足够明确，让 reviewer 能说清楚 candidate 为什么通过或失败。

## Reports

Eval report 应该列出：

- what was run；
- what changed；
- aggregate score；
- improved cases；
- regressed cases；
- flaky or inconclusive cases；
- cost and latency；
- unresolved residuals；
- promotion decision。

把 report 存在 eval harness 附近，或者放在文档化的 artifact 位置，并从 `evolution/` 链接重要方向变化。
