# 安装、更新、移除

用你已经在用的智能体就行。技能只需要装一次，之后切到你要动手的项目里，打开这个智能体。
**安装只是给智能体加命令，不会创建项目的记忆库，也不会升级它。**

| 你的环境 | 安装方式 |
|---|---|
| Claude Code | 装 `tabilet` 市场里的 `memory-bank` 插件 |
| Codex | 用 Codex CLI 装同一个 `memory-bank` 插件 |
| DSH Web 或无界面（headless） | 装 `tabilet-skills` 伴侣，或者用源码检出里的七个文件系统包 |
| 手动安装 | 把完整的技能文件夹放进智能体的技能目录 |

规范的七个技能和 DSH 伴侣共用同一套项目 Markdown。2.0.0 版把项目自有文件放在
`tabilet/` 下。现有的 v1.5.0 项目需要[一次性迁移](upgrade.md#migrate-a-v150-project-to-v2)，
这一步必须显式执行。另外，迁移和可选的 API 运行器都要有 Python。

## Claude Code

下面两条要在 **Claude Code 里**运行：

```text
/plugin marketplace add tabilet/skills
/plugin install memory-bank@tabilet
```

在你的项目里新开一个会话，然后发送：

```text
/memory-bank:memory-bank-init
```

只有项目还没有初始化记忆库时，才用它。否则请按你要做的工作
[选择相应的工作流](examples.md)。

## Codex

下面两条要在**终端里**运行：

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

然后在你的项目里新开一个 Codex 会话并发送：

```text
$memory-bank:memory-bank-init
```

`@tabilet` 这个限定符用来标明市场。如果你的 Codex 版本没有提供插件命令，就走
[纯文件方式](#as-plain-files-you-own)。

## DeepSeek Harness {#deepseek-harness}

想要 **Memory Bank 侧边栏和全部七个技能**，就在 Web 配置里装预构建的 v2.0.0 伴侣。
在运行 DSH 的机器上打开一个终端，执行：

```bash
dsh plugin --profile web add \
  https://github.com/tabilet/tabilet-skills/releases/download/v2.0.0/tabilet-skills-2.0.0.tgz \
  --ignore-scripts
```

无界面场景则把 `--profile web` 换成 `--profile headless`。只在真正需要它的配置里安装。
这条 GitHub release 途径不需要 npm 账号。

重启 DSH，为你的项目选中一个会话，然后在右侧边栏打开 **Memory Bank**。展开
**Prepare a workflow request**，挑一个技能，看一眼预览，再把它插入空白草稿。
**请求要由你自己发送。** 草稿里已经有文本或附件时，改成手动复制预览内容。
无界面配置照样加载这些技能，只是没有侧边栏。

该伴侣已在 Linux 上验证通过，用的是 Node **24.14.1** 和锁定的 DSH **0.1.5-rc.2** 组件；
另有一个隔离的 rc.1 启动器，跑的是 rc.2 组件。

只要**技能、不要仪表盘**，就走[纯文件方式](#as-plain-files-you-own)。把 v2.0.0 检出里
七个完整文件夹全部复制到 `$DSH_HOME/skills`，通常是 `~/.dsh/skills`。文件系统途径的
全 rc.1 兼容性是单独测过的。

### 使用 Memory Bank 面板

面板跟着所选会话的项目走。**Overview** 显示活跃里程碑和任务数量；**Tasks** 提供筛选、
搜索和完整备注；**Acceptance** 显示已记录的验证和评审证据；**Memory** 保存当前项目事实；
**History** 按需打开保留的记录；**Compatibility** 报告缺失文件、不支持的格式、冲突的任务
状态，以及哪个已安装的技能来源优先生效。

面板可见时，外部文件改动会通过变更通知和五秒刷新周期显示出来。面板获得焦点也会刷新，
另外还提供手动刷新。读取不完整，或者读取被拒绝，都会作为警告留在界面上。

浏览和准备请求都不发起模型调用，也不写项目文件。预览不是执行，更不是审批：
发送预览是你自己的动作，所选技能仍然按自己的审批边界执行。任务标记全部完成，
并不等于里程碑通过了验收。遇到较旧的项目格式，请准备一个 [Upgrade](upgrade.md) 请求，
并把界面上显示的警告一并带上。

## 调用技能 {#invoke-a-skill}

技能请求要发在**智能体对话**里，而不是 shell 里。前缀取决于你的安装方式：

| 安装方式 | 对话请求示例 |
|---|---|
| Claude Code 插件 | `/memory-bank:memory-bank-next` |
| Codex 插件 | `$memory-bank:memory-bank-next` |
| DSH 伴侣或文件系统 | `/memory-bank-next` |
| Claude Code 纯文件 | `/memory-bank-next` |
| Codex 纯文件 | `$memory-bank-next` |

需要时把 `init`、`archive`、`propose`、`reconcile`、`upgrade` 或 `goal` 换成 `next`。
每个技能的输入和审批边界，[技能指南](init.md)里都有说明。用 Goal 时，请求里要写上明确
的顺序和[提交策略](goal.md)。

## 作为你自有的纯文件 {#as-plain-files-you-own}

把 v2.0.0 源码克隆到一个单独目录（七个技能全在里面）：

```bash
git clone --branch v2.0.0 --depth 1 https://github.com/tabilet/skills.git
```

把该检出 `skills/` 目录下的每个 `memory-bank-*` 文件夹，复制到你的智能体对应的目录：

| 智能体 | 个人技能目录 |
|---|---|
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| DSH | `$DSH_HOME/skills/`，通常是 `~/.dsh/skills/` |

要复制**完整文件夹**，随附的模板和参考文档一起带上。只复制 `SKILL.md`，有些工作流
就缺东西了。同名文件夹已经存在的话，先检查、备份，再替换；无关的技能别动。
每次改动安装之后，都重开一个新会话。

## 项目文件

[Init](init.md) 在你批准方案之后准备好项目专属文件。如果你更想手动设置，把 release
检出里的 `template/` 复制到一个新项目：

```bash
cp -R /path/to/skills/template/. /path/to/new-project/
```

方括号里的占位符是故意留的：填上你项目自己的事实、计划和验证命令。项目已经存在的话，
就把适用的规则合并进去，保留它原有的说明，千万别用模板盖掉当前状态。动手之前，
先记录具体的交付边界、里程碑验收、任务行和验证命令。入口仍然是 `AGENTS.md`；
如果你的智能体读的是别的说明文件名，就让那个文件指向 `AGENTS.md`。
[第一个项目演练](examples.md#a-new-project)讲了挑任务之前该检查哪些东西。

## 可选的 API 运行器 {#the-optional-api-harness}

独立的 API 运行器需要 **Python 3 和 Git**，还要配好所选模型提供方的凭据。它只用 Python
标准库。

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

如果你已经在用编码智能体，这个运行器可以跳过。真要用它，起点得是一个已初始化的项目：
项目就在 Git 工作区的根目录上，有干净的已提交基线，还有一个已获批的可执行任务。
请在一次性沙箱里运行它，因为运行器会在宿主 shell 里执行模型给出的命令，不提供隔离。
设置 `ALLOW_UNSANDBOXED_SHELL=1` 就等于确认了这种访问权限。

环境里已经设好 `OPENAI_API_KEY` 时，把模型和项目占位符换成实际值，再运行：

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_PROVIDER=openai LLM_MODEL=your-model MAX_RUNS=1 \
  ~/.local/bin/tackle-memory-bank-api-loop /absolute/path/to/project
```

用 Anthropic 的话，设好 `ANTHROPIC_API_KEY`，配一个兼容的模型，并使用
`LLM_PROVIDER=anthropic`。向提供方发请求可能产生费用。端点设置、超时、重试和额外限制，
请看该可执行文件的 `--help`。

API 运行器要求每次运行都留下一次提交。碰到脏状态、缺少提交、无效的任务转换，或者同时
有多行处于进行中，它都会停下来。退出码 `7` 表示已经跑满请求的运行次数上限；退出码 `3`
表示剩下的全是阻塞工作；退出码 `0` 表示没有可执行的行了，而不是每个里程碑都过了评审。
事后请检查记录的验证和关闭证据。同一个活跃账本上，别同时再跑另一个智能体。

## 更新

Claude Code 用自带的 `/plugin` 管理器更新已安装的插件。Codex 则刷新市场快照，再重装：

```bash
codex plugin marketplace upgrade tabilet
codex plugin add memory-bank@tabilet
```

DSH 伴侣要在每个适用的配置里安装选定的已发布 release 归档，然后重启。文件系统安装的话，
先停掉正在用这些包的会话，检查并备份已安装的文件夹，再用所选 release 里的完整文件夹替换。
无关的技能要保留；项目或用户的覆盖设置可能压过新包，记得检查。

**更新已安装的技能不会迁移项目规则。** 想检查现有项目、批准具体的规则合并，请用
[Upgrade](upgrade.md)。任务状态、永久 ID、本地策略和历史都要原样保留。

## 移除

按你的安装方式执行对应的卸载命令：

| 安装方式 | 命令及运行位置 |
|---|---|
| Claude Code 插件 | 在 Claude Code 里运行 `/plugin uninstall memory-bank@tabilet` |
| Codex 插件 | 在终端里运行 `codex plugin remove memory-bank@tabilet` |
| DSH Web 伴侣 | 在终端里运行 `dsh plugin --profile web remove tabilet-skills` |

如果你在无界面配置里也装过 DSH，那处安装要单独移除。纯文件安装只移除确定属于
memory-bank 的技能文件夹。项目 Markdown 留在项目里，移除之后照样能用。

## 如果技能或仪表盘缺失

- 确认所选会话指向的确实是你想要的那个项目。
- 安装后重开一个新会话。改过配置就重启 DSH。
- 核对上面的调用前缀。在 DSH Web 里安装，并不会把伴侣装进无界面配置。
- 在 DSH 的 **Compatibility** 视图里看看生效的技能来源是哪个。项目里或用户目录下已有的
  副本，可能压过随附的版本。
- `skills` 仓库自己在 `template/tabilet/memory-bank/` 下有一个示例；它没有活跃的项目
  记忆库，仪表盘自然没东西可显示。
