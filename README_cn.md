# 一个最小工程 Harness

编码智能体在项目能自我说明时表现更好——这是什么、做完了什么、接下来做什么。通常的做法是引入一整套系统：一个 CLI、一套脚手架、一组斜杠命令、一堆自动生成的产物。半年之后，你维护这套系统文件的精力不亚于维护自己的代码，项目活在它的约定里，而不是你的约定里。

这个仓库押的是相反的方向。五六个 markdown 文件，复制进你的项目，完全归你所有。没有 CLI 要安装，没有词汇表要学，没有任何强制项。哪天某个文件不再值得保留，删掉就是。

**最终得到的东西属于你。** 本仓库是一个供你往外复制的起点——把 `template/` 复制进你的项目，`harness/` 按需复制到你的主目录。之后你的项目既不依赖本仓库，也不与它保持任何关联。

三个可选的斜杠命令可以替你完成复制和填写——见[安装这三个命令](#安装这三个命令)。它们不改变上面的取舍：它们*生成*的文件此后完全归你所有，之后不会再更新它们，卸载它们也不会动你的项目分毫。

你的项目最终会长成这样：

```text
your-project/
├── AGENTS.md              智能体首先该读的文件
├── memory-bank/           当前为真的内容
│   ├── product.md         项目是什么、不是什么
│   ├── architecture.md    目录布局、数据流、边界
│   ├── tech-stack.md      命令、依赖、如何验证
│   ├── milestone.md       里程碑及其验收标准
│   └── status-M01.md      每个里程碑一个文件，每个任务一行
└── evolution/             方向变化的原因与时间
```

全文中的 **harness** 指的是一条可重复执行、用来证明某件事可用的命令——你的测试套件、一个 CI job、一个脚本。你的项目在 `tech-stack.md` 里定义自己的 harness。本仓库另外提供一个可选的 harness：一个通过 API 驱动智能体、无人值守地推进项目记忆库的循环。

其他语言版本: [🇬🇧 English](README.md) · [🇯🇵 日本語](README_ja.md) · [🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## 语言说明

这份中文文档面向中文开发者阅读。仓库里的 harness 示例文件，例如 `AGENTS.md`、`memory-bank/*`、`evolution/*` 和 `harness/prompts/*`，默认仍使用英文，适合开发者用英文与智能体协作。

如果你希望用中文和智能体对话，需要自行把这些 harness 文件翻译成中文，并保持规则、状态标记、命令和路径的一致性。

## 快速开始

**第一次接触？**[docs/TUTORIAL.md](docs/TUTORIAL.md) 用二十分钟把一个玩具项目从空目录带到第一次提交，其中的搭建工作由 `/memory-bank-init` 完成。README 的其余部分是参考资料——教程是贯穿它的引导路径。

**使用项目记忆库只需要 `git`，别无其他。** 项目记忆库就是普通的 markdown，因此日常工作流——让 Codex、Claude Code 这类智能体去处理下一条待办——完全不需要任何运行时。

**Python 3 只用于可选的 API harness**，也就是[安装 API Harness](#安装-api-harness)一节介绍的无人值守循环。它只使用标准库，无需 `pip` 安装任何东西。如果你本来就用某个智能体来驱动项目记忆库，完全可以跳过它。

下面“为已有项目设置”一节在做初始盘点时还会用到 [ripgrep](https://github.com/BurntSushi/ripgrep)（`rg`）。

先克隆本仓库一次。下面所有 `cp` 命令中的 `/path/to/skills` 都指向你的这份克隆：

**最快的方式完全不需要 clone。** 安装这三个命令，然后让 `/memory-bank-init` 向你提问并写出项目记忆库：

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

在你的项目里运行 `/memory-bank-init`——空项目或已有项目都可以——然后回答它的问题。Codex 的等价做法和「直接用文件」的选项见[安装这三个命令](#安装这三个命令)。

如果想手工处理这些文件，先把本仓库 clone 一次。下面所有 `cp` 命令中的 `/path/to/skills` 都指你的这份 clone：

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

三个斜杠命令，位于 [skills/](skills/)。Claude Code 和 Codex 读取同一种 `SKILL.md` 格式，因此每个命令只有一份源文件：

- [memory-bank-init](skills/memory-bank-init/SKILL.md)
- [memory-bank-next](skills/memory-bank-next/SKILL.md)
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md)

`.claude-plugin/` 存放清单文件，使上述命令可以作为 Claude Code 插件安装。`template/` 里没有任何特定厂商的文件。

Harness 参考：

- [执行 Harness](docs/EXECUTION_cn.md)
- [模型评测 Harness](docs/MODEL_EVAL_cn.md)

## 填写后的项目记忆库长什么样

模板里都是占位符。下面是同一套项目记忆库为一个小型购物服务填写后的样子，让你先看到终点，再看路线。

`memory-bank/product.md` 一开始是 `[project-name] is [one or two sentences describing the project]`，填写后变成：

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

`memory-bank/milestone.md` 决定了其余一切如何组织——它命名状态线，并说明每条覆盖什么：

```markdown
## Status ID Pattern

M01, M02, ...   Default lane: cross-cutting work, infrastructure, chores
S01, S02, ...   Storefront: cart, checkout, product pages
A01, A02, ...   Accounting: pricing, invoices, payment reconciliation

Lane meanings:

- `M`: anything that does not belong to a product domain.
- `S`: shopping surface. Owned by the storefront team.
- `A`: money. Changes here need a second reviewer.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| S01 | [status-S01.md](status-S01.md) | Cart and checkout. |
| A02 | [status-A02.md](status-A02.md) | Payment contract. |

## S01 - Cart And Checkout

**Goal.** A shopper can fill a cart and complete a purchase.

**Scope.**

- Cart CRUD behind `POST /cart`.
- Line-item and order-total pricing.
- Handoff to the payment provider.

**Acceptance.** `make test` passes, and a scripted end-to-end purchase
succeeds against the staging payment sandbox.
```

随后 `memory-bank/status-S01.md` 承载该里程碑的状态行：

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

## 为新项目设置

如果你安装了[这三个命令](#安装这三个命令)，`/memory-bank-init` 可以完成本节的全部工作：它向你提问，提出线与里程碑的方案，等你认可，然后写出已经填好的文件。下面两条路径是同样的工作，只是手工完成。

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

`/memory-bank-init` 同样适用于这种情况，而且比一句冷启动的提示词做得更好：它会读取仓库里已经写明的内容——README、测试、构建与 CI 文件——只就那些无法从中得知的决策向你提问，通常是非目标、边界，以及工作顺序。

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
| [`/memory-bank-next`](#安装这三个命令) | 同上，但携带完整指令而不是你的转述 | 这三个命令 |
| [API harness](#安装-api-harness) | 每次运行一条状态行，无人值守 | Python 3 |
| [目标循环](#按顺序执行多个里程碑) | 按顺序执行多个里程碑 | 一个 `/goal` 命令 |

使用 Codex 或 Claude Code 这类智能体时，用户侧的操作可以很简单，例如：

```text
tackle next pending item in memory bank
```

智能体应在 `memory-bank/status-<LANE><NN>.md` 中找到下一条可执行状态行，完成对应任务，运行必要验证，更新项目记忆库，并创建一个范围清晰的 git commit。如果这条状态行是某个里程碑的最后一个未完成项，智能体应在继续之前执行 `memory-bank/milestone.md` 中的里程碑评审。评审时还应判断 `evolution/` 是否需要新版本：只有当产品方向、架构边界、里程碑目标或公私契约发生实质变化时，才应新增版本。

在信任这一切之前，先给智能体一个可验证的对象。在 `memory-bank/tech-stack.md` 的 **Execution harnesses** 表里填上能证明你的项目可用的命令——`make test`、`npm test`、某个脚本，任何你本来就在跑的东西——以及通过它证明了什么。在那条命令通过之前，状态行不应变成 `[+]`。没有它，“验证通过后才标记完成”就没有指向，智能体只能自己决定什么算验证。

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

**如何选择状态线。** 一条状态线是长期存在的工作轨道，不是一个里程碑，也不是一个迭代。请按领域划分——变更属于产品的哪一部分——而不是按团队、优先级或日期，因为领域比这三者都活得久。先只用 `M`；当某个领域的工作量大到会淹没其他内容，或者需要自己的评审节奏时，再拆出一个字母。两三条状态线是常见的稳定状态，很多项目长期只用一条也没问题。

拆得太少很容易补救：新开一个字母，把新工作放进去。拆得太多则不然，因为状态文件一旦存在，ID 就不会被复用或改名——你后悔的那条线会永远留在目录里。拿不准时，就先放在 `M`。

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

它是被调用的，不是常驻的。无论你用哪个智能体，启动一次运行的请求都是同一段内容——写明文件、顺序和 commit 策略：

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

发送这段内容的方式各不相同，因为 `/goal` 在不同智能体里并不是同一个命令。请看你所用智能体对应的小节。

#### 如果你用 Claude Code

`/goal` 是内置命令，但它**不是**用来启动任务的。它设置的是一个停止条件——“Claude 在停下之前会检查的目标”——因此会话会跨多轮持续工作，而不是回复一次就结束。

所以需要两条消息。先把上面那段内容作为普通消息发出去，然后设置判断这次运行何时结束的条件：

```text
/goal every row in M01 and S01 is `[+]` and the required verification passes
```

`/goal active` 查看当前条件，`/goal clear` 提前结束。条件上限为 4000 个字符，需要受信任的工作区，并且当 hooks 被设置或策略禁用时不可用。

如果想让这段内容本身可复用，把它存成项目命令——但不要叫 `.claude/commands/goal.md`，因为这个名字被内置命令占用了。改名为 `.claude/commands/milestones.md`，用 `/milestones` 调用。

#### 如果你用 Codex

Codex 没有内置的 `/goal`。自定义提示词是 `~/.codex/prompts/` 下的 markdown 文件，按文件名调用，所以你可以自己创建这个命令，并让它把顺序作为参数接收。写入 `~/.codex/prompts/goal.md`：

```markdown
---
description: Execute an ordered set of milestones using GOAL.md.
argument-hint: M01 -> S01 -> A01?
---

Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS
COMMIT_POLICY: task
```

然后一条消息即可运行：

```text
/goal M01 -> S01 -> A01?
```

这与随包提供的 [tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md) 提示词是同一套机制，安装到同一个目录。

#### 其他智能体

把这段内容作为普通请求粘贴过去即可。协议只需要请求里写明文件名；没有任何东西依赖斜杠命令的存在。

`COMMIT_POLICY` 很关键，而且目标循环是对常规规则的一次有意例外。在这次运行期间，它就是全部的 commit 规则：`AGENTS.md` 里可以写“每条状态行就是一个 commit 单元”，但 `COMMIT_POLICY: none`——也就是该协议的默认值——意味着完全不产生 commit，这是正确行为，而不是冲突。想要照常按行提交时，就写 `task`。优先级依次是请求、`GOAL.md`、`AGENTS.md`，而且只针对 commit，只在这次运行之内。

结尾的 `?` 表示条件里程碑：当其触发条件不存在时跳过，而不是取消。

`GOAL.md` 不包含任何项目专有路径、状态线字母或命令。它从 `AGENTS.md` 和项目记忆库中读取这些内容，因此同一份文件可以原样用于任何复制了它的项目。

没有任何地方要求你使用它。`/goal` 是你的智能体提供的命令，不属于这套 harness——你可以带上自己的协议，或者干脆不用，项目记忆库的行为完全一样。之所以提供 `GOAL.md`，只是因为这类协议写起来比较琐碎，而不是因为这里的任何东西依赖它。如果你有自己的协议，把提到 `GOAL.md` 的两处——`AGENTS.md` 和 `memory-bank/milestone.md`——指向它，或者直接删掉。

## 安装这三个命令

同样是可选的。上面的一切都可以靠输入普通句子完成；这三个命令只是让那三个时刻可重复，并且携带完整指令，而不是你临时转述的版本。

| 命令 | 何时使用 |
|---|---|
| `/memory-bank-init` | 一次性：项目还没有 `memory-bank/` 时。它会向你提问、提出拆分方案，然后写入文件。 |
| `/memory-bank-next` | 日常：处理一行、验证、提交。 |
| `/memory-bank-goal` | 想按顺序执行多个里程碑时。 |

`/memory-bank-init` 带来的改变最大：它一次只问一个问题并附上推荐答案，凡是能从仓库里读到的都自己查而不问你，并且在你认可拆分方案之前不写任何文件。你不会看到任何方括号占位符——项目记忆库交付时就是填好的。（提问技巧改编自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `grilling` skill，MIT 许可。）

两种智能体读取的是同一种 `SKILL.md` 格式，因此每个命令只有一份源文件：

两种智能体读取的是同一种 `SKILL.md` 格式**以及同一份清单文件**，因此每个命令只有一份源文件，也只有一个版本需要安装。

**Claude Code：**

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

**Codex** 有自己的插件系统，并且会回退读取 `.claude-plugin/plugin.json`，所以同一个仓库就能用：

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

当插件名在你已配置的多个 marketplace 中不唯一时，Codex 要求带上 `@marketplace` 限定，因此值得记住 `memory-bank@tabilet` 这种写法。有新版本发布时，用 `codex plugin marketplace upgrade` 刷新快照。

**两者的调用方式不同。** Claude Code 把它们注册为斜杠命令——`/memory-bank-init`。Codex 把它们注册为按名称调用的 skill，所以不要加斜杠，直接说：*“use the memory-bank-init skill”*。普通英语句子在两者中都有效，而这本来就是项目记忆库所依赖的方式。

**两种智能体都可以改为把它们当作你自己的文件**，而不是受管理的插件：

```bash
mkdir -p ~/.codex/skills            # or ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.codex/skills 'skills-main/skills'
```

想固定版本，把 `refs/heads/main` 换成 `refs/tags/<版本号>`，并把 `skills-main` 改成 `skills-<版本号>`，与该 tarball 内的目录名保持一致。

这个 skill 特意没有命名为 `goal`：Claude Code 有内置的 `/goal` 用于设置停止条件，那是另一回事。两者可以配合使用，见「按顺序执行多个里程碑」一节。

### 如果你已经在用 `/grill-me`

[mattpocock/skills](https://github.com/mattpocock/skills) 的 `/grill-me` 和 `/grilling` 在它们打算停下的地方停下：*"Do not act on it until I confirm we have reached a shared understanding."*（在我确认我们达成共识之前，不要动手）。对一个通用的访谈技巧来说，停在那里是正确的，这也正是它能用在任何事情上的原因。

但会话一结束，那份共识也随之消失。磁盘上没有任何东西，明天的智能体接不上，也没有可以执行的对象。

`/memory-bank-init` 是同一套访谈方法，只不过指向一份会留存下来的产物——一次只问一个问题，每个问题都附带推荐答案，能查到的事实自己查而不问。请在**同一个会话里，紧接着 grill 之后**运行它：

```text
/grill-me            # explore the design; no files written
/memory-bank-init    # turn those decisions into a memory bank
```

它不会重复问你已经确定的事。「能查的事实自己查，决策才问你」同样适用于对话本身，而不只是仓库，所以刚做完 grill 之后的访谈会很短——大多只是确认一份线与里程碑的拆分方案。

| | `/grill-me` 之后 | `/memory-bank-init` 之后 |
|---|---|---|
| 决策存放在哪里 | 对话里 | `product.md`、`architecture.md`、`tech-stack.md` |
| 明天的智能体 | 从零开始 | 读 `AGENTS.md` 就知道 |
| 下一步做什么 | 你来决定 | 下一条 `` `[ ]` `` 状态行 |
| 怎么执行 | — | `/memory-bank-next`，或用 `/memory-bank-goal` 跑一组 |

两者是互补的，不是竞争关系。那些不产出项目的决策——架构上的争论、招聘计划、演讲提纲——继续用 `/grill-me`。当你 grill 的对象是一个下周还得知道自己是什么的代码库时，就该用 `/memory-bank-init`。

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
