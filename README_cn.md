# 一个最小工程 Harness

这个仓库提供一套可以直接复制到项目里的轻量级工程协作框架。它由几个部分组成：

- `AGENTS.md`：智能体进入项目后的启动指南。
- `memory-bank/`：项目当前状态、边界和计划的事实来源。
- `evolution/`：项目方向变化的版本化记录。
- 执行 harness：用可重复运行的命令证明软件仍然正常工作。
- 模型评测 harness：用可重复评测衡量模型辅助工作是否变好。

这套结构的目的不是增加文档负担，而是让开发者和智能体共用同一份紧凑、明确、可执行的项目手册。

其他语言版本: [🇬🇧 English](README.md) · [🇯🇵 日本語](README_ja.md) · [🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## 语言说明

这份中文文档面向中文开发者阅读。仓库里的 harness 示例文件，例如 `AGENTS.md`、`memory-bank/*`、`evolution/*` 和 `harness/prompts/*`，默认仍使用英文，适合开发者用英文与智能体协作。

如果你希望用中文和智能体对话，需要自行把这些 harness 文件翻译成中文，并保持规则、状态标记、命令和路径的一致性。

## 快速开始

**使用项目记忆库只需要 `git`，别无其他。** 项目记忆库就是普通的 markdown，因此日常工作流——让 Codex、Claude Code 这类智能体去处理下一条待办——完全不需要任何运行时。

**Python 3 只用于可选的 API harness**，也就是[安装 API Harness](#安装-api-harness)一节介绍的无人值守循环。它只使用标准库，无需 `pip` 安装任何东西。如果你本来就用某个智能体来驱动项目记忆库，完全可以跳过它。

下面“为已有项目设置”一节在做初始盘点时还会用到 [ripgrep](https://github.com/BurntSushi/ripgrep)（`rg`）。

先克隆本仓库一次。下面所有 `cp` 命令中的 `/path/to/skills` 都指向你的这份克隆：

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

克隆本身不需要运行任何东西。你只是从里面往外复制文件：把 `template/` 复制到项目里，把 `harness/` 复制到你的主目录。

## 仓库内容

项目级示例文件：

- [template/AGENTS.md](template/AGENTS.md)
- [template/GOAL.md](template/GOAL.md)——多里程碑执行协议
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

用户账号级示例文件：

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

Harness 参考：

- [执行 Harness](docs/EXECUTION_cn.md)
- [模型评测 Harness](docs/MODEL_EVAL_cn.md)

## 为新项目设置

### 手动设置

在新项目根目录执行：

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

然后按以下顺序填写复制过来的文件：

1. `memory-bank/product.md`：说明项目是什么、不是什么。
2. `memory-bank/architecture.md`：说明目录布局、数据流和边界。
3. `memory-bank/tech-stack.md`：说明命令、依赖和验证入口。
4. `memory-bank/milestone.md`：定义第一个里程碑。
5. `memory-bank/status-M01.md`：列出第一批可执行状态行。参见下文“填写后的状态文件长什么样”——标记两侧的反引号很关键。
6. `evolution/prompt-v1.md`：记录初始方向。
7. `evolution/result-v1.md`：记录当前起点。
8. `AGENTS.md`：把占位符替换成项目自己的命令和规则。

保持 `README.md` 简洁，面向用户；长篇参考资料放到 `docs/`。

### 接入你的智能体

`AGENTS.md` 是由 Agentic AI Foundation 维护的[开放跨厂商标准](https://agents.md)。绝大多数编码智能体无需任何配置就会读取它，包括 Codex, Cursor, Gemini CLI, GitHub Copilot, Devin, Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, Amp 等。

`template/` 中不包含任何特定厂商的文件。如果你的智能体读取的是别的文件名，请用一行把它桥接到 `AGENTS.md`，而不是维护一份迟早会走样的副本：

| 智能体 | 桥接方式 |
|---|---|
| 上述列表中的任意一个 | 无需处理 |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`，或建一个内容为 `@AGENTS.md` 的 `CLAUDE.md` |
| 其他读取自有文件的工具 | 同样用符号链接或 import 指向 `AGENTS.md` |

在 Windows 上创建符号链接需要管理员权限或开发者模式，因此建议改用 import 形式。

### 借助 AI 智能体

新项目可以先复制示例结构，再通过对话让智能体帮你填写内容。你需要先把产品、用户、边界、常用命令和第一个里程碑讲清楚。

注意：把这些文件复制到已有目录可能覆盖磁盘上的同名文件。请先备份，或者先提交当前工作。

在新项目根目录执行：

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

和智能体讨论清楚后，请它填写：

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status-M01.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

示例提示词：

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the status
ID lanes in memory-bank/milestone.md, and make memory-bank/status-M01.md contain
the first actionable milestone rows.
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
2. 从本仓库复制 `template/`。
3. 根据项目现状填写项目记忆库，不要凭空重塑项目方向。
4. 把稳定的长篇参考资料移入 `docs/`。
5. 把重复的 roadmap/status 内容整理到 `memory-bank/milestone.md` 和 `memory-bank/status-<LANE><NN>.md`。
6. 把已知缺口保留在 `status-<LANE><NN>.md`，不要藏起来。

### 借助 AI 智能体

已有项目可以让智能体先读现有文档和代码，再生成第一版项目记忆库。当项目已经有 README、docs、包注释、测试或 CI 文件时，这种方式通常效果更好。

注意：复制这些示例文件可能覆盖已有的 `AGENTS.md`、`memory-bank/` 或 `evolution/`。建议先提交、备份，或者先复制到临时目录，再让智能体合并。

在已有项目根目录执行：

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

然后让智能体先阅读项目，再写入这些协作文件：

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
memory-bank/status-<LANE><NN>.md file.
Do not invent product direction that is not supported by the existing project.
```

智能体应完成以下工作：

1. 盘点现有 markdown 和源码布局。
2. 识别命令、依赖、测试和验证入口。
3. 根据项目当前事实填写项目记忆库。
4. 把长篇参考资料移动或总结到 `docs/`。
5. 保持 `README.md` 简洁，面向用户。
6. 把未解决缺口作为待处理或被阻塞的状态行保留在 `memory-bank/status-<LANE><NN>.md`。

## 使用项目记忆库

围绕项目记忆库执行工作有三种方式，而且都是可选的——项目记忆库本身就是普通 markdown，单独用也成立：

| 执行方式 | 范围 | 需要 |
|---|---|---|
| 直接对智能体提出请求 | 一次一条状态行，你在回路里 | 无 |
| [API harness](#安装-api-harness) | 每次运行一条状态行，无人值守 | Python 3 |
| [目标循环](#按顺序执行多个里程碑) | 按顺序执行多个里程碑 | 一个 `/goal` 命令 |

使用 Codex 或 Claude Code 这类智能体时，用户侧的操作可以很简单，例如：

```text
tackle next pending item in memory bank
```

智能体应在 `memory-bank/status-<LANE><NN>.md` 中找到下一条可执行状态行，完成对应任务，运行必要验证，更新项目记忆库，并创建一个范围清晰的 git commit。如果这条状态行是某个里程碑的最后一个未完成项，智能体应在继续之前执行 `memory-bank/milestone.md` 中的里程碑评审。评审时还应判断 `evolution/` 是否需要新版本：只有当产品方向、架构边界、里程碑目标或公私契约发生实质变化时，才应新增版本。

底层的标准智能体流程是：

1. 阅读 `AGENTS.md`。
2. 按 `AGENTS.md` 指定的顺序阅读项目记忆库文件。
3. 只处理一个范围清晰的任务或状态行。
4. 如果范围、架构、工具、里程碑验收条件或状态发生变化，更新对应的项目记忆库文件。
5. 只有验证通过后，才把状态行标记为 `[+]`。
6. 把这一行对应的工作作为一个独立 commit 提交。
7. 如果某个里程碑完成，先执行 `memory-bank/milestone.md` 中的里程碑评审，再继续后续工作。
8. 检查 `evolution/`，只有评审确认存在真实的方向、边界、里程碑或契约变化时，才新增版本。

### 状态 ID 线

状态文件命名为 `memory-bank/status-<LANE><NN>.md`。字母表示这条状态线所属的领域，数字使用两位零填充：会计相关的里程碑写成 `status-A01.md`、`status-A02.md`，购物相关的写成 `status-S01.md`。无法归入某个领域的工作使用默认字母 `M`。每个字母最多 99 个文件；写满后请启用新的字母，不要扩展到三位数字。`memory-bank/milestone.md` 记录每个字母的含义，并保证状态 ID 不被重复使用。

状态行使用这些标记：

| 标记 | 含义 |
|---|---|
| `[ ]` | 待处理 |
| `[+]` | 已完成 |
| `[~]` | 进行中 |
| `[!]` | 被阻塞 |
| `[X]` | 已取消 |

### 按顺序执行多个里程碑

上面的流程一次推进一条状态行。如果要按既定顺序走完多个里程碑，[GOAL.md](template/GOAL.md) 是可选的一种协议：它在每个里程碑开始前核对依赖，在某个里程碑收尾后核对其下游里程碑，并在缺少决策或授权时停下来而不是猜测。

它是被调用的，不是常驻的。Codex 和 Claude Code 都提供 `/goal` 命令——Claude Code 的版本会跨多轮持续工作，直到目标条件达成——请求里写明文件和顺序：

```text
/goal
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

`COMMIT_POLICY` 很关键，而且目标循环是对常规规则的一次有意例外。在这次运行期间，它就是全部的 commit 规则：`AGENTS.md` 里可以写“每条状态行就是一个 commit 单元”，但 `COMMIT_POLICY: none`——也就是该协议的默认值——意味着完全不产生 commit，这是正确行为，而不是冲突。想要照常按行提交时，就写 `task`。优先级依次是请求、`GOAL.md`、`AGENTS.md`，而且只针对 commit，只在这次运行之内。

结尾的 `?` 表示条件里程碑：当其触发条件不存在时跳过，而不是取消。

`GOAL.md` 不包含任何项目专有路径、状态线字母或命令。它从 `AGENTS.md` 和项目记忆库中读取这些内容，因此同一份文件可以原样用于任何复制了它的项目。

没有任何地方要求你使用它。`/goal` 是你的智能体提供的命令，不属于这套 harness——你可以带上自己的协议，或者干脆不用，项目记忆库的行为完全一样。之所以提供 `GOAL.md`，只是因为这类协议写起来比较琐碎，而不是因为这里的任何东西依赖它。如果你有自己的协议，把提到 `GOAL.md` 的两处——`AGENTS.md` 和 `memory-bank/milestone.md`——指向它，或者直接删掉。

### 填写后的状态文件长什么样

模板里都是占位符。以一个小型购物服务为例，填写后的 `memory-bank/status-S01.md` 是这样：

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**每个标记两侧的反引号是必需的。** harness 匹配的是 `` `[ ]` ``，而不是 `[ ]`。写成 `| Item | [ ] | Notes |` 的状态行会被静默忽略：harness 会报告“No actionable memory-bank rows remain”并正常退出，就好像工作已经做完了一样。

项目记忆库的其余文件同样是把占位符替换掉。`memory-bank/product.md` 一开始是 `[project-name] is [one or two sentences describing the project]`，填写后变成：

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```


## 安装 API Harness

本节是可选的。上面的内容不依赖它——harness 只是多提供一个无人值守循环，用 API 驱动智能体，省去你手动输入。如果 Codex、Claude Code 或别的智能体已经在替你做这件事，可以跳过。

API harness 是账号级工具，因为它可以驱动任何采用这套项目记忆库结构的仓库。 它只需要 Python 3。

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

下面的命令直接以名字调用 `tackle-memory-bank-api-loop`，这要求 `~/.local/bin` 在你的 `PATH` 中。如果 `command -v tackle-memory-bank-api-loop` 没有任何输出，请把这一行加进你的 shell 配置文件：

```bash
export PATH="$HOME/.local/bin:$PATH"
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

改用 Anthropic（Claude），而不是兼容 OpenAI 的接口：

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

这个 harness 会把任务说明直接嵌入 API 提示词。它不调用 Codex CLI，运行时也不依赖外部提示词文件。仓库中保留提示词文件，是为了给开发者和智能体提供可复用参考。

### 第一次运行

一次运行会先打印仓库、提供方、模型和 API 端点，然后开始处理一条状态行：

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

harness 会有意提前停止，退出码说明原因。`3` 到 `7` 是正常的停止条件，而不是故障——例如 `4` 表示运行前工作区不干净，`6` 表示智能体结束时没有提交。`11` 表示没有找到任何 `status-<LANE><NN>.md` 文件，通常说明项目记忆库还没有填写。完整对照表见[执行 Harness](docs/EXECUTION_cn.md#退出码)。

## 这个 Harness 的定位

在普通项目工作中，`tackle-memory-bank-api-loop` 是一个执行 harness：它反复让智能体在真实仓库上工作，通过受控命令协议提供 shell 能力，并在每次运行之间检查 git 状态。

它会发现全部 `memory-bank/status-<LANE><NN>.md` 文件，报告每条状态线还有多少可执行行和被阻塞行，并让智能体按照状态线含义和里程碑优先级挑选下一行。某条状态线上的被阻塞行不会影响其他状态线；只有当仅剩被阻塞行时，循环才会停下来交由人工处理。

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
