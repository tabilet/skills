# 一个最小工程 Harness

项目能说清自己是什么、做完了什么、接下来做什么，编码智能体就能做得更好。本仓库提供的正是这样一小组纯文本文件，大多是 markdown。你把它们复制进项目，从那一刻起就完全归你所有。

这里的一切都是纯文本，所以你只需要 `git`。这些文件可以直接阅读、手工编辑、改名或删除，任何能读 markdown 的智能体都可以处理它们。可选的插件会替你生成这些文件，可选的 API runner 会无人值守地逐条推进，两者都留在项目之外。

`template/` 复制进项目，`harness/` 在你需要 API runner 时复制到主目录。文件到位之后就归项目所有，项目本身也不再和本仓库有任何牵连。半年之后，你要维护的仍然只有自己的代码。

复制和填写也可以交给三个可选 skill 完成，见[安装这三个命令](#安装这三个命令)。它们写下的文件从出现那一刻起就归你，并且会一直保持你留下的样子。

你的项目最终会长成这样：

```text
your-project/
├── AGENTS.md              智能体首先该读的文件
├── GOAL.md                可选的多里程碑协议
├── memory-bank/           当前为真的事实
│   ├── product.md         项目是什么、不是什么
│   ├── architecture.md    目录布局、数据流、边界
│   ├── tech-stack.md      命令、依赖、如何验证
│   ├── milestone.md       活跃里程碑和未编号的后续方向
│   ├── status-M01.md      每个活跃里程碑一个永久文件
│   └── suggested.txt      可选且可丢弃的活跃范围启动参考
└── evolution/             版本化的方向快照
    ├── prompt-v1.md       初始方向
    └── result-v1.md       由此产生的状态
```

*memory bank*（项目记忆库）这个说法由 [Cline](https://docs.cline.bot/best-practices/memory-bank) 推广开来。这里是同一想法的另一种实现，只用纯文件，不带运行时。

全文中的 **harness** 指一条可重复执行的命令，用来证明某件事确实能用，比如你的测试套件、一个 CI job 或一个脚本。项目在 `tech-stack.md` 里定义自己的 harness。本仓库另外提供一个可选的 harness，它通过 API 驱动智能体，无人值守地推进项目记忆库。

其他语言版本: [🇬🇧 English](README.md) · [🇯🇵 日本語](README_ja.md) · [🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## 语言说明

这份中文文档面向中文开发者。仓库里的 harness 示例文件默认仍是英文，例如 `AGENTS.md`、`memory-bank/*`、`evolution/*` 和 `harness/prompts/*`，适合用英文与智能体协作。

如果你希望用中文和智能体对话，需要自己把这些文件翻译过来，并保持规则、状态标记、命令和路径一致。

## 快速开始

**第一次接触？**[docs/TUTORIAL.md](docs/TUTORIAL.md) 用二十分钟把一个玩具项目从空目录带到第一次提交，其中的搭建工作由 `memory-bank-init` 完成。README 其余部分是参考资料，而教程是贯穿这些资料的一条引导路径。

使用项目记忆库只需要 `git`，别的都不需要。它本身就是普通 markdown，所以日常工作流也不需要运行时：你让 Codex、Claude Code 这类智能体去处理下一条待办，它直接编辑这些文件。

**Python 3 只用于可选的 API harness**，也就是[安装 API Harness](#安装-api-harness)一节介绍的无人值守循环。它只用标准库，不需要 `pip` 装任何东西。如果你本来就用某个智能体来驱动项目记忆库，可以完全跳过。

下面「为已有项目设置」一节做初始盘点时还会用到 [ripgrep](https://github.com/BurntSushi/ripgrep)（`rg`）。

最快的入手方式不需要 clone 任何东西。装上插件，让其中带命名空间的 `memory-bank-init` skill 向你提问，并替你写出项目记忆库：

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
/memory-bank:memory-bank-init
```

在 Claude Code 的项目里运行这些命令，空项目或已经有代码的项目都可以，然后回答问题。Codex 的等价做法和「直接用文件」的选项见[安装这三个命令](#安装这三个命令)。

想手工处理这些文件，就先把本仓库 clone 一次。下面所有 `cp` 命令里的 `/path/to/skills` 都指你这份 clone：

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

clone 本身不需要运行任何东西。你只是从里面往外复制文件：`template/` 复制到项目，`harness/` 复制到主目录。

## 仓库内容

项目级示例文件：

- [template/AGENTS.md](template/AGENTS.md)
- [template/GOAL.md](template/GOAL.md)，多里程碑执行协议
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

可选 API runner，以及仅供仓库参考的人类可读指令副本：

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

三个 skill 放在 [skills/](skills/)。Claude Code 和 Codex 读同一种 `SKILL.md` 格式，所以每个 skill 只有一份源文件：

- [memory-bank-init](skills/memory-bank-init/SKILL.md)
- [memory-bank-next](skills/memory-bank-next/SKILL.md)
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md)

`.claude-plugin/` 存放兼容清单，让同一个插件能装进 Claude Code 和 Codex。`template/` 里没有任何特定厂商的文件。

Harness 参考：

- [执行 Harness](docs/EXECUTION_cn.md)
- [模型评测 Harness](docs/MODEL_EVAL_cn.md)

## 填写后的项目记忆库长什么样

模板里都是占位符。下面是同一套项目记忆库为一个小型购物服务填写后的样子，先看到终点，再看路线。

`memory-bank/product.md` 一开始是 `[project-name] is [one or two sentences describing the project]`，填好之后变成：

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

`memory-bank/milestone.md` 决定其余一切如何组织。它给状态线命名，并说明每条覆盖什么：

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

随后 `memory-bank/status-S01.md` 承载这个里程碑的状态行：

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**每个标记两侧的反引号是必需的。** harness 匹配 `` `[ ]` ``，不匹配 `[ ]`。写成 `| Item | [ ] | Notes |` 的状态行会被静默忽略：harness 报告「No actionable memory-bank rows remain」然后正常退出，就好像工作已经做完了。

## 为新项目设置

如果你装了[这三个命令](#安装这三个命令)，`memory-bank-init` 可以完成本节的全部工作。它向你提问，提出线与里程碑的方案，等你认可，然后写出填好的文件。下面两条路径做的是同样的事，只是手工完成。

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
5. `memory-bank/status-M01.md`：列出第一批可执行状态行。参见上文「填写后的项目记忆库长什么样」，标记两侧的反引号很关键。
6. `evolution/prompt-v1.md`：记录初始方向。
7. `evolution/result-v1.md`：记录当前起点。
8. `AGENTS.md`：把占位符换成项目自己的命令和规则。

`README.md` 保持简洁、面向用户，长篇参考资料放进 `docs/`。

### 接入你的智能体

`AGENTS.md` 是由 Agentic AI Foundation 维护的[开放跨厂商标准](https://agents.md)。绝大多数编码智能体不用配置就会读它，包括 Codex, Cursor, Gemini CLI, GitHub Copilot, Devin, Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, Amp 等。

`template/` 里没有任何特定厂商的文件。如果你的智能体读别的文件名，用一行把它桥接到 `AGENTS.md`，不要维护一份迟早会走样的副本：

| 智能体 | 桥接方式 |
|---|---|
| 上述列表中的任意一个 | 无需处理 |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`，或建一个内容为 `@AGENTS.md` 的 `CLAUDE.md` |
| 其他读取自有文件的工具 | 同样用符号链接或 import 指向 `AGENTS.md` |

Windows 上建符号链接需要管理员权限或开发者模式，建议改用 import 形式。

### 借助 AI 智能体

新项目可以先复制示例结构，再通过对话让智能体帮你填内容。你需要先把产品、用户、边界、常用命令和第一个里程碑讲清楚。

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

`memory-bank-init` 同样适用，而且比一句冷启动的提示词做得更好。它会先读仓库里已经写明的内容，包括 README、测试、构建与 CI 文件、接口、schema、源码布局和基础设施，然后只询问证据无法决定的事项，并按项目实际情况展开相关分支，而不是让每个项目回答同一套问题。

### 手动设置

已有项目先盘点，再改写：

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

然后：

1. 阅读根目录 README、智能体指南、docs、包级 README 和主要包注释。
2. 从本仓库复制 `template/`。
3. 按项目现状填写项目记忆库，不要凭空重塑项目方向。
4. 把稳定的长篇参考资料移进 `docs/`。
5. 把重复的 roadmap 与 status 内容整理到 `memory-bank/milestone.md` 和 `memory-bank/status-<LANE><NN>.md`。
6. 把已知缺口保留在 `status-<LANE><NN>.md`，不要藏起来。

### 借助 AI 智能体

已有项目可以让智能体先读现有文档和代码，再生成第一版项目记忆库。项目已经有 README、docs、包注释、测试或 CI 文件时，这种方式通常效果更好。

注意：复制这些示例文件可能覆盖已有的 `AGENTS.md`、`memory-bank/` 或 `evolution/`。建议先提交、备份，或者先复制到临时目录，再让智能体合并。

在已有项目根目录执行：

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

然后让智能体先读项目，再写入这些协作文件：

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
3. 按项目当前事实填写项目记忆库。
4. 把长篇参考资料移动或总结到 `docs/`。
5. 保持 `README.md` 简洁、面向用户。
6. 把未解决缺口作为待处理或被阻塞的状态行留在 `memory-bank/status-<LANE><NN>.md`。

## 使用项目记忆库

围绕项目记忆库执行工作有四种方式，而且都是可选的，因为项目记忆库本身就是普通 markdown，单独用也成立：

| 执行方式 | 范围 | 需要 |
|---|---|---|
| 直接对智能体提出请求 | 一次一条状态行，你在回路里 | 无 |
| [`memory-bank-next`](#安装这三个命令) | 同上，但携带完整指令，不是你的转述 | 可选 skills |
| [API harness](#安装-api-harness) | 每次运行一条状态行，无人值守 | Python 3 |
| [目标循环](#按顺序执行多个里程碑) | 按顺序执行多个里程碑 | `GOAL.md` 与普通请求或可选 skill |

用 Codex 或 Claude Code 这类智能体时，用户侧的操作可以很简单，例如：

```text
tackle next pending item in memory bank
```

智能体应在 `memory-bank/status-<LANE><NN>.md` 里找到下一条可执行状态行，完成任务，运行必要验证，更新项目记忆库，并创建一个范围清晰的 git commit。如果这条状态行是某个里程碑的最后一个未完成项，智能体应先执行 `memory-bank/milestone.md` 里的里程碑评审，再继续。评审有改动时提交这些改动；没有改动时不要创建空的里程碑 commit。评审时还要判断 `evolution/` 是否需要新版本：只有产品方向、架构边界、里程碑目标或公私契约发生实质变化，才新增版本。

在信任这一切之前，先给智能体一个可验证的对象。请在 `memory-bank/tech-stack.md` 的 **Execution harnesses** 表里填上能证明项目可用的命令，比如 `make test`、`npm test` 或某个你本来就在跑的脚本，并写明这条命令通过之后能说明什么。在它通过之前，状态行不应该变成 `[+]`。缺了这一步，「验证通过才标记完成」就没有指向，智能体只能自己决定什么算验证。

底层的标准智能体流程是：

1. 阅读 `AGENTS.md`。
2. 按 `AGENTS.md` 指定的顺序阅读项目记忆库文件。
3. 只处理一个范围清晰的任务或状态行。
4. 如果范围、架构、工具、里程碑验收条件或状态发生变化，更新对应文件。
5. 只有验证通过，才把状态行标记为 `[+]`。
6. 把这一行对应的工作作为一个独立 commit 提交。
7. 如果某个里程碑完成，先执行 `memory-bank/milestone.md` 里的里程碑评审，再继续后续工作。
8. 检查 `evolution/`，只有评审确认存在真实的方向、边界、里程碑或契约变化，才新增版本。

### 状态 ID 线

状态文件命名为 `memory-bank/status-<LANE><NN>.md`。字母表示这条状态线所属的领域，数字用两位零填充：会计相关的里程碑写成 `status-A01.md`、`status-A02.md`，购物相关的写成 `status-S01.md`。归不进任何领域的工作用默认字母 `M`。每个字母最多 99 个文件，写满就启用新字母，不要扩展到三位数字。`memory-bank/milestone.md` 记录每个字母的含义，并保证状态 ID 不被重复使用。

里程碑文件还会记录活跃执行范围之外的**候选方向**。它们保持未编号，也没有状态文件；只有在晋升触发条件满足、重新核对工作并批准晋升方案后，才会获得永久 ID。这样不会过早冻结推测性的远期任务。

**如何选择状态线。** 一条状态线是长期存在的工作轨道，尺度接近一个产品领域，而不是一个里程碑或一次迭代。划分时请按领域，也就是看一次变更属于产品的哪一部分，因为领域比团队、优先级和日期都活得久。一开始只用 `M` 就够了。等某个领域的工作量大到会淹没其他内容，或者需要自己的评审节奏，再拆出一个字母。两三条状态线是常见的稳定状态，很多项目长期只用一条也没问题。

拆得太少很容易补救，新开一个字母，把新工作放进去就是了。拆得太多则是永久的：状态文件一旦存在，这个 ID 就会在项目的余生里一直用这个名字。拿不准的时候先放进 `M`。

状态行使用这些标记：

| 标记 | 含义 |
|---|---|
| `[ ]` | 待处理 |
| `[+]` | 已完成 |
| `[~]` | 进行中 |
| `[!]` | 被阻塞 |
| `[X]` | 已取消 |

### 按顺序执行多个里程碑

上面的流程一次推进一条状态行。要按既定顺序走完多个里程碑，[GOAL.md](template/GOAL.md) 是一种可选协议：每个里程碑开始前核对依赖，某个里程碑收尾后核对下游里程碑，缺少决策或授权就停下来，而不是猜。

它是被调用的，不是常驻的。无论你用哪个智能体，启动一次运行的请求都是同一段内容，其中写明了文件、顺序和 commit 策略：

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

如果 `memory-bank-init` 创建或批准了兼容的 `GOAL.md`，它还会把完整的建议请求写进
`memory-bank/suggested.txt`，包括 `STATUS_ORDER`、`STATUS_FILE_MAP`
和 `DOWNSTREAM_IMPACTS`。它只覆盖已批准的活跃范围，不包含未编号的候选方向。这只是启动参考，不是第二份路线图。用之前要和
`milestone.md` 及当前状态文件核对，启动后或内容过时就可以删掉。如果没有兼容的协议，init 会省略这个文件，单行执行仍然可用：

```text
Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop.
COMMIT_POLICY: task
```

上面的内容可以作为普通请求粘贴给任何智能体。装了插件之后，也可以用同一协议的命名空间 skill：Claude Code 用 `/memory-bank:memory-bank-goal M01 -> S01 -> A01?`，Codex 用 `$memory-bank:memory-bank-goal M01 -> S01 -> A01?`。直接安装的 skill 分别用 `/memory-bank-goal` 和 `$memory-bank-goal`。

不带参数运行 goal skill 时，它先核对有效的 `suggested.txt`，展示完整的已解析请求供你确认。文件缺失或过时，就从 `milestone.md` 推导顺序。

#### 如果你用 Claude Code

Claude Code 内置的 `/goal` 是长任务的另一种启动方式。一次性给出完整协议请求、commit 策略和可衡量的完成条件：

```text
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

不带参数运行 `/goal` 可以查看状态，`/goal clear` 可以停止。`memory-bank-goal` skill 仍是与 Codex 共用的可移植启动方式。

#### 如果你用 Codex

直接调用插件 skill：

```text
$memory-bank:memory-bank-goal M01 -> S01 -> A01?
```

直接安装 skill 文件的话，用 `$memory-bank-goal M01 -> S01 -> A01?`。Codex 自定义提示词已经弃用，应改用 skill，所以本仓库不再安装或推荐独立的 `goal.md` 提示词。

#### 其他智能体

把这段内容作为普通请求粘贴过去就行。协议只要求请求里写明文件名，没有任何东西依赖斜杠命令。

`COMMIT_POLICY` 很关键，而且目标循环是对常规规则的一次有意例外。在这次运行期间，它就是全部的 commit 规则。`AGENTS.md` 里可以写「每条状态行就是一个 commit 单元」，但只要写的是 `COMMIT_POLICY: none`，就完全不会产生 commit。这是该协议的默认值，属于正确行为，而不是冲突。想照常按行提交，就写 `task`。优先级依次是请求、`GOAL.md`、`AGENTS.md`，而且只针对 commit，只在这次运行之内。

结尾的 `?` 表示条件里程碑：触发条件不存在就跳过，不是取消。它只用于达成活跃结果时按条件必需的工作；可选的后续工作应保持为未编号的候选方向。

`GOAL.md` 不包含任何项目专有路径、状态线字母或命令。这些内容它从 `AGENTS.md` 和项目记忆库里读，所以同一份文件可以原样用在任何复制了它的项目上。

没有任何地方要求你用它。你可以带上自己的协议，也可以干脆不用，项目记忆库的行为完全一样。之所以提供 `GOAL.md`，只是因为这类协议写起来比较琐碎，而不是因为这里的任何东西依赖它。如果你有自己的协议，把提到 `GOAL.md` 的两处改成指向它，或者直接删掉。这两处分别在 `AGENTS.md` 和 `memory-bank/milestone.md` 里。

## 安装这三个命令

同样是可选的。上面的一切都可以靠输入普通句子完成。这三个命令只是让那三个时刻可重复，并且携带完整指令，而不是你临时转述的版本。

| 命令 | 何时使用 |
|---|---|
| `memory-bank-init` | 一次性：项目还没有 `memory-bank/` 时。它向你提问、提出拆分方案，然后写入文件。 |
| `memory-bank-next` | 日常：处理一行、验证、提交。 |
| `memory-bank-goal` | 想按顺序执行多个里程碑时。 |

`memory-bank-init` 带来的改变最大。它把一个交付边界映射成决策树，把当前依赖已满足的问题组成带编号的 frontier 轮次，并为每个问题附上推荐答案；凡是能从仓库读到的事实都自己去查。在你批准活跃范围和每个文件操作之前，它不写任何文件。你不会看到方括号占位符，因为项目记忆库交付时就已经填好了。（提问技巧改编自 [mattpocock/skills](https://github.com/mattpocock/skills) 的 `grilling` skill，MIT 许可。）

两种智能体读同一种 `SKILL.md` 格式**和同一份清单文件**，所以每个命令只有一份源文件，也只有一个版本需要安装。

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

插件名在你已配置的多个 marketplace 中不唯一时，Codex 要求带上 `@marketplace` 限定，所以值得记住 `memory-bank@tabilet` 这种写法。有新版本发布时，用 `codex plugin marketplace upgrade` 刷新快照。

**插件安装使用命名空间。** Claude Code 用 `/memory-bank:memory-bank-init`、`/memory-bank:memory-bank-next` 和 `/memory-bank:memory-bank-goal`；Codex 用 `$memory-bank:memory-bank-init`、`$memory-bank:memory-bank-next` 和 `$memory-bank:memory-bank-goal`。两者也都仍然支持普通英语请求。

**两种智能体都可以改为把它们当作你自己的文件**，而不是受管理的插件：

```bash
mkdir -p ~/.agents/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.agents/skills 'skills-main/skills'

# Claude Code alternative
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.claude/skills 'skills-main/skills'
```

直接安装 skill 文件时不带命名空间：Claude Code 用 `/memory-bank-init`，Codex 用 `$memory-bank-init`，另外两个依此类推。

想固定版本，把 `refs/heads/main` 换成 `refs/tags/<版本号>`，并把 `skills-main` 改成 `skills-<版本号>`，与该 tarball 内的目录名保持一致。

这个 skill 特意没有命名为 `goal`。Claude Code 有内置的 `/goal` 用于设置停止条件，那是另一回事。两者可以配合使用，见「按顺序执行多个里程碑」一节。

### 如果你已经在用 `/grill-me`

[mattpocock/skills](https://github.com/mattpocock/skills) 的 `/grill-me` 和 `/grilling` 在它们打算停下的地方停下：*"Do not act on it until I confirm we have reached a shared understanding."*（在我确认我们达成共识之前，不要动手）。对一个通用的访谈技巧来说，停在那里是对的，这也正是它能用在任何事情上的原因。

但会话一结束，那份共识也就没了。磁盘上什么都没留下，明天的智能体接不上，也没有可以执行的对象。

`memory-bank-init` 用的是同一套访谈方法，只不过它指向一份会留存下来的产物。相互独立且前置决策已完成的问题会放在同一个 frontier 轮次中，每个问题都有推荐答案；能查到的事实自己去查。需要更专注时可以要求一次只问一个问题。请在**同一个会话里，紧接着 grill 之后**运行它：

```text
/grill-me            # explore the design; no files written
/memory-bank:memory-bank-init    # Claude Code plugin
$memory-bank:memory-bank-init    # Codex plugin
```

它不会重复问你已经确定的事。「能查的自己查，决策才问你」同样适用于对话本身，而不只是仓库，所以刚做完 grill 之后的访谈会很短，大多只是确认一份线与里程碑的拆分方案。

| 会话结束后留下什么 | `/grill-me` 之后 | `memory-bank-init` 之后 |
|---|---|---|
| 决策存放在哪里 | 对话里 | `product.md`、`architecture.md`、`tech-stack.md` |
| 明天的智能体 | 从零开始 | 读 `AGENTS.md` 就知道 |
| 下一步做什么 | 你来决定 | 下一条 `` `[ ]` `` 状态行 |
| 怎么执行 | — | `memory-bank-next`，或用 `memory-bank-goal` 跑一组 |

两者是互补的，不是竞争关系。不产出项目的决策继续用 `/grill-me`，比如架构上的争论、招聘计划或演讲提纲。如果你 grill 的对象是一个下周还得说清自己是什么的代码库，那就该用 `memory-bank-init`。

## 安装 API Harness

本节是可选的，上面的内容并不依赖它，因为这个 harness 只是多提供一个无人值守的循环，用 API 驱动智能体，省去你手动输入。如果 Codex、Claude Code 或别的智能体已经在替你做这件事，可以跳过。

API harness 是账号级工具，因为它可以驱动任何采用这套项目记忆库结构的仓库。它只需要 Python 3。

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

下面的命令直接以名字调用 `tackle-memory-bank-api-loop`，这要求 `~/.local/bin` 在你的 `PATH` 里。如果 `command -v tackle-memory-bank-api-loop` 没有输出，把这一行加进你的 shell 配置文件：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

可执行运行会把由模型生成的命令交给宿主机上的非沙箱 shell，因此 harness 在你明确设置 `ALLOW_UNSANDBOXED_SHELL=1` 或传入 `--allow-unsandboxed-shell` 前会拒绝启动。这只是确认风险，并不提供隔离：命令仍能读取宿主机文件、检查其他进程并访问网络。请在一次性沙箱中运行，并确保目标仓库可以恢复。

shell 命令只收到一个精简环境，provider 凭据变量不会复制进去。需要项目变量时，用 `TOOL_ENV_ALLOW=NAME,OTHER_NAME` 明确传入。这样可以减少意外泄露，但不会让宿主 shell 变得安全。`ALLOW_DANGEROUS_COMMANDS=1` 只是关闭一份很短、可以绕过的命令阻止清单。

只运行一条状态行：

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

循环运行多条状态行：

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

使用兼容 OpenAI API 的服务商：

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.6 \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

使用本地兼容 OpenAI API 的服务：

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

改用 Anthropic（Claude），而不是兼容 OpenAI 的接口：

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

这个 harness 把任务说明直接嵌进 API 提示词。它不调用 Codex CLI，运行时也不依赖外部提示词文件。仓库里保留提示词文件，是为了给嵌入指令留一份一致的人类可读副本，不会装到 Codex 提示词目录。

模型名称会变。示例用的是当前的 `gpt-5.6` family alias 和 `claude-opus-5`，真实运行前请查看官方 [OpenAI model catalog](https://developers.openai.com/api/docs/models) 与 [Anthropic model catalog](https://platform.claude.com/docs/en/about-claude/models/overview)。

### 第一次运行

一次运行先打印仓库、提供方、模型和 API 端点，然后开始处理一条状态行：

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

harness 会有意提前停止，退出码说明原因。`3` 到 `7` 是正常的停止条件，而不是故障。例如 `4` 表示运行前工作区不干净，`6` 表示智能体结束时没有提交。`11` 表示没找到任何 `status-<LANE><NN>.md` 文件，通常说明项目记忆库还没填写。完整对照表见[执行 Harness](docs/EXECUTION_cn.md#退出码)。

## 这个 Harness 的定位

在普通项目工作中，`tackle-memory-bank-api-loop` 是一个执行 harness：反复让智能体在真实仓库上工作，通过 JSON 命令协议提供 shell 能力，并在每次运行之间检查 git 状态。目标路径必须正好是 git worktree 根目录；历史必须正常前进，不能被改写；每次运行必须恰好让一个已有的可执行状态行变成完成或阻塞。同一次运行中可以另建里程碑评审修复 commit。

它会发现全部 `memory-bank/status-<LANE><NN>.md` 文件，报告每条状态线还剩多少可执行行和被阻塞行，让智能体按状态线含义和里程碑优先级挑下一行。某条状态线上的被阻塞行不影响其他状态线。只有当仅剩被阻塞行时，循环才停下来交给人工。

只有当你跨模型、提示词、通过率、评审发现、成本、延迟或回归情况打分时，它才成为模型评测 harness 的一部分。

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
