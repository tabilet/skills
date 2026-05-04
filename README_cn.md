# 一个最小工程 Harness

这个仓库是一个可以直接复制使用的起点，用来搭建一个轻量级的项目运行体系。它围绕以下几个部分组织：

- `AGENTS.md`：agent 的启动指南。
- `memory-bank/`：项目当前事实来源。
- `evolution/`：项目方向变化的版本化历史。
- execution harness：用可重复命令证明软件仍然正常工作。
- model eval harness：用可重复评测衡量模型辅助行为。

目标不是增加文档数量。目标是让人和 agent 共用同一份简洁的操作手册，并把这份手册连接到可执行的 harness。

## 这个仓库里有什么

项目级示例文件：

- [AGENTS.md](AGENTS.md)
- [memory-bank/product.md](memory-bank/product.md)
- [memory-bank/architecture.md](memory-bank/architecture.md)
- [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
- [memory-bank/milestone.md](memory-bank/milestone.md)
- [memory-bank/status.md](memory-bank/status.md)
- [evolution/prompt-v1.md](evolution/prompt-v1.md)
- [evolution/result-v1.md](evolution/result-v1.md)

用户账号级示例文件：

- [.local/bin/tackle-memory-bank-api-loop](.local/bin/tackle-memory-bank-api-loop)
- [.codex/prompts/tackle-next-memory-bank-todo.md](.codex/prompts/tackle-next-memory-bank-todo.md)

Harness 参考文档：

- [Execution Harness](docs/EXECUTION_cn.md)
- [Model Eval Harness](docs/MODEL_EVAL_cn.md)

## 为新项目设置

### 手动设置

在新项目根目录下执行：

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

然后按这个顺序编辑复制过来的文件：

1. `memory-bank/product.md`：定义项目是什么，以及不是什么。
2. `memory-bank/architecture.md`：定义布局、数据流和边界。
3. `memory-bank/tech-stack.md`：定义命令、依赖和 harness。
4. `memory-bank/milestone.md`：定义第一个 milestone。
5. `memory-bank/status.md`：定义第一批可执行任务行。
6. `evolution/prompt-v1.md`：记录初始方向。
7. `evolution/result-v1.md`：记录当前起始状态。
8. `AGENTS.md`：用项目自己的命令和规则替换占位符。

保持 `README.md` 简洁，面向用户。长篇参考资料放进 `docs/`。

### 借助 AI Agent

对于新项目，你可以先把示例文件作为初始结构复制进去，然后在描述清楚产品之后，请 AI agent 帮你填写。

警告：把这些文件复制到已有项目里可能覆盖磁盘上已有文件。请先备份，或者先提交当前工作。

在新项目根目录下执行：

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

然后和 agent 充分讨论，直到产品、用户、边界、命令和第一个 milestone 都清楚为止。请它填写：

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

示例提示词：

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, and make
memory-bank/status.md contain the first actionable milestone rows.
```

## 为已有项目设置

### 手动设置

对于已有项目，先读再写：

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

然后：

1. 阅读根目录 README、agent 指南、docs、包级 README，以及主要包注释。
2. 从这个仓库复制 `AGENTS.md`、`memory-bank/` 和 `evolution/`。
3. 根据项目已经表达出来的内容填写 memory bank，不要凭空重写项目方向。
4. 把稳定的长篇参考资料移到 `docs/`。
5. 把重复的 roadmap/status 内容转换到 `memory-bank/milestone.md` 和 `memory-bank/status.md`。
6. 把已知缺口保留在 `status.md` 里，不要隐藏。

### 借助 AI Agent

对于已有项目，agent 可以帮助盘点项目并生成第一版 memory bank。项目里已经有有用的 README、docs、包注释、测试或 CI 文件时，这种方式效果最好。

警告：把这些示例文件复制到已有项目里可能覆盖已有的 `AGENTS.md`、`memory-bank/` 或 `evolution/`。请先提交、备份，或者把示例复制到临时目录，再让 agent 合并。

在已有项目根目录下执行：

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

然后要求 agent 先读项目，再写文件：

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in memory-bank/status.md.
Do not invent product direction that is not supported by the existing project.
```

Agent 应该：

1. 盘点已有 markdown 和源码布局。
2. 识别命令、依赖、测试和 harness。
3. 根据当前项目事实填写 memory bank。
4. 把长篇参考资料移动或总结到 `docs/`。
5. 保持 `README.md` 简洁，面向用户。
6. 把未解决缺口作为 pending 或 blocked 行保留在 `memory-bank/status.md`。

## 使用 Memory Bank

使用 Codex 或 Claude Code 这类 agent 时，用户侧的工作流可以简单到只输入：

```text
tackle next pending item in memory bank
```

Agent 应该找到 `memory-bank/status.md` 中下一条可执行行，完成任务，运行必要验证，更新 memory bank，并创建一个有明确范围的 git commit。如果这一行是某个 milestone 的最后一个未完成项，agent 应该在继续之前运行 `memory-bank/milestone.md` 中的 milestone review。在 review 中，它也应该判断 `evolution/` 是否需要新版本，因为产品方向、架构边界、milestone 目标或公私契约方向发生了实质变化。

底层实际发生的正常 agent 工作流是：

1. 阅读 `AGENTS.md`。
2. 按 `AGENTS.md` 中列出的顺序阅读 memory bank 文件。
3. 只处理一个有明确范围的任务或 status 行。
4. 如果 scope、architecture、tools、milestone acceptance 或 status 发生变化，更新对应的 memory-bank 文件。
5. 只有验证通过后，才把一行标记为 `[+]`。
6. 把这一行作为一个有明确范围的 commit 提交。
7. 如果一个 milestone 完成，先运行 `memory-bank/milestone.md` 中的 milestone review，再继续。
8. 检查 `evolution/`，只有 review 发现真实的方向、边界、milestone 或契约变化时，才添加新版本。

Status 行使用这些标记：

| Symbol | Meaning |
|---|---|
| `[ ]` | Pending |
| `[+]` | Completed |
| `[~]` | In progress |
| `[!]` | Blocked |
| `[X]` | Cancelled |

## 安装 API Harness

API harness 是账号级工具，因为它可以驱动任何符合这个 memory-bank 结构的项目。

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/.local/bin/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/.codex/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

运行一行：

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

运行循环：

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

使用兼容 OpenAI API 的服务商：

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.5 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

使用本地兼容 OpenAI API 的服务：

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

这个 harness 会把任务说明嵌入 API prompt。它不调用 Codex CLI，也不在运行时依赖外部 prompt 文件。这里包含 prompt 文件，是为了作为人和 agent 可复用的参考。

## 这个 Harness 是什么

对于普通项目工作，`tackle-memory-bank-api-loop` 是一个 execution harness：它反复让 agent 在仓库上工作，通过受控命令协议给它 shell 访问，并在每次运行之间检查 git 状态。

只有当你跨模型、prompt、通过率、review 发现、成本、延迟或回归情况打分时，它才成为 model eval harness 的一部分。

继续阅读：

- [Execution Harness](docs/EXECUTION_cn.md)
- [Model Eval Harness](docs/MODEL_EVAL_cn.md)

## 维护规则

- 保持 `AGENTS.md` 简短。
- 保持项目 `README.md` 面向用户。
- 把长篇解释放进 `docs/`。
- 把当前事实放进 `memory-bank/`。
- 把历史方向快照放进 `evolution/`。
- 在描述代码或文档变更的同一个 commit 中更新 memory。
- 只有真实方向变化时，才添加新的 evolution 版本。
- 有用内容合并后，删除重复文档。
