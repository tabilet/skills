# 一个最小工程 Harness

这个仓库提供一套可以直接复制到项目里的轻量级工程协作框架。它由几个部分组成：

- `AGENTS.md`：智能体进入项目后的启动指南。
- `memory-bank/`：项目当前状态、边界和计划的事实来源。
- `evolution/`：项目方向变化的版本化记录。
- 执行 harness：用可重复运行的命令证明软件仍然正常工作。
- 模型评测 harness：用可重复评测衡量模型辅助工作是否变好。

这套结构的目的不是增加文档负担，而是让开发者和智能体共用同一份紧凑、明确、可执行的项目手册。

## 语言说明

这份中文文档面向中文开发者阅读。仓库里的 harness 示例文件，例如 `AGENTS.md`、`memory-bank/*`、`evolution/*` 和 `.codex/prompts/*`，默认仍使用英文，适合开发者用英文与智能体协作。

如果你希望用中文和智能体对话，需要自行把这些 harness 文件翻译成中文，并保持规则、状态标记、命令和路径的一致性。

## 仓库内容

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

Harness 参考：

- [执行 Harness](docs/EXECUTION_cn.md)
- [模型评测 Harness](docs/MODEL_EVAL_cn.md)

## 为新项目设置

### 手动设置

在新项目根目录执行：

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

然后按以下顺序填写复制过来的文件：

1. `memory-bank/product.md`：说明项目是什么、不是什么。
2. `memory-bank/architecture.md`：说明目录布局、数据流和边界。
3. `memory-bank/tech-stack.md`：说明命令、依赖和验证入口。
4. `memory-bank/milestone.md`：定义第一个里程碑。
5. `memory-bank/status.md`：列出第一批可执行状态行。
6. `evolution/prompt-v1.md`：记录初始方向。
7. `evolution/result-v1.md`：记录当前起点。
8. `AGENTS.md`：把占位符替换成项目自己的命令和规则。

保持 `README.md` 简洁，面向用户；长篇参考资料放到 `docs/`。

### 借助 AI 智能体

新项目可以先复制示例结构，再通过对话让智能体帮你填写内容。你需要先把产品、用户、边界、常用命令和第一个里程碑讲清楚。

注意：把这些文件复制到已有目录可能覆盖磁盘上的同名文件。请先备份，或者先提交当前工作。

在新项目根目录执行：

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

和智能体讨论清楚后，请它填写：

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

已有项目应先盘点，再改写：

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

然后：

1. 阅读根目录 README、智能体指南、docs、包级 README 和主要包注释。
2. 从本仓库复制 `AGENTS.md`、`memory-bank/` 和 `evolution/`。
3. 根据项目现状填写项目记忆库，不要凭空重塑项目方向。
4. 把稳定的长篇参考资料移入 `docs/`。
5. 把重复的 roadmap/status 内容整理到 `memory-bank/milestone.md` 和 `memory-bank/status.md`。
6. 把已知缺口保留在 `status.md`，不要藏起来。

### 借助 AI 智能体

已有项目可以让智能体先读现有文档和代码，再生成第一版项目记忆库。当项目已经有 README、docs、包注释、测试或 CI 文件时，这种方式通常效果更好。

注意：复制这些示例文件可能覆盖已有的 `AGENTS.md`、`memory-bank/` 或 `evolution/`。建议先提交、备份，或者先复制到临时目录，再让智能体合并。

在已有项目根目录执行：

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

然后让智能体先阅读项目，再写入这些协作文件：

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in memory-bank/status.md.
Do not invent product direction that is not supported by the existing project.
```

智能体应完成以下工作：

1. 盘点现有 markdown 和源码布局。
2. 识别命令、依赖、测试和验证入口。
3. 根据项目当前事实填写项目记忆库。
4. 把长篇参考资料移动或总结到 `docs/`。
5. 保持 `README.md` 简洁，面向用户。
6. 把未解决缺口作为待处理或被阻塞的状态行保留在 `memory-bank/status.md`。

## 使用项目记忆库

使用 Codex 或 Claude Code 这类智能体时，用户侧的操作可以很简单，例如：

```text
tackle next pending item in memory bank
```

智能体应在 `memory-bank/status.md` 中找到下一条可执行状态行，完成对应任务，运行必要验证，更新项目记忆库，并创建一个范围清晰的 git commit。如果这条状态行是某个里程碑的最后一个未完成项，智能体应在继续之前执行 `memory-bank/milestone.md` 中的里程碑评审。评审时还应判断 `evolution/` 是否需要新版本：只有当产品方向、架构边界、里程碑目标或公私契约发生实质变化时，才应新增版本。

底层的标准智能体流程是：

1. 阅读 `AGENTS.md`。
2. 按 `AGENTS.md` 指定的顺序阅读项目记忆库文件。
3. 只处理一个范围清晰的任务或状态行。
4. 如果范围、架构、工具、里程碑验收条件或状态发生变化，更新对应的项目记忆库文件。
5. 只有验证通过后，才把状态行标记为 `[+]`。
6. 把这一行对应的工作作为一个独立 commit 提交。
7. 如果某个里程碑完成，先执行 `memory-bank/milestone.md` 中的里程碑评审，再继续后续工作。
8. 检查 `evolution/`，只有评审确认存在真实的方向、边界、里程碑或契约变化时，才新增版本。

状态行使用这些标记：

| 标记 | 含义 |
|---|---|
| `[ ]` | 待处理 |
| `[+]` | 已完成 |
| `[~]` | 进行中 |
| `[!]` | 被阻塞 |
| `[X]` | 已取消 |

## 安装 API Harness

API harness 是账号级工具，因为它可以驱动任何采用这套项目记忆库结构的仓库。

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/.local/bin/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/.codex/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

只运行一条状态行：

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

循环运行多条状态行：

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

这个 harness 会把任务说明直接嵌入 API 提示词。它不调用 Codex CLI，运行时也不依赖外部提示词文件。仓库中保留提示词文件，是为了给开发者和智能体提供可复用参考。

## 这个 Harness 的定位

在普通项目工作中，`tackle-memory-bank-api-loop` 是一个执行 harness：它反复让智能体在真实仓库上工作，通过受控命令协议提供 shell 能力，并在每次运行之间检查 git 状态。

只有当你跨模型、提示词、通过率、评审发现、成本、延迟或回归情况进行打分时，它才成为模型评测 harness 的一部分。

继续阅读：

- [执行 Harness](docs/EXECUTION_cn.md)
- [模型评测 Harness](docs/MODEL_EVAL_cn.md)

## 维护规则

- 保持 `AGENTS.md` 简短。
- 保持项目 `README.md` 面向用户。
- 把长篇解释放进 `docs/`。
- 把当前事实放进 `memory-bank/`。
- 把历史方向快照放进 `evolution/`。
- 在描述代码或文档变更的同一个 commit 中更新项目记忆库。
- 只有真实方向变化时，才新增 evolution 版本。
- 合并有用内容后，删除重复文档。
