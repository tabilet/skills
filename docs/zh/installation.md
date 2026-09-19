# 安装、更新、移除

选择你已经在用的智能体。安装一次技能，然后在你想要处理的项目中打开该智能体。
**安装只会添加命令；它不会创建或升级项目的记忆库。**

| 你的环境 | 安装方式 |
|---|---|
| Claude Code | 来自 `tabilet` 市场的 `memory-bank` 插件 |
| Codex | 通过 Codex CLI 安装同一个 `memory-bank` 插件 |
| DSH Web 或无头模式 | `tabilet-skills` 伴侣，或七个源码检出文件系统包 |
| 手动安装 | 放入智能体技能目录的完整技能文件夹 |

规范的七个技能与 DSH 伴侣使用同一套项目 Markdown。2.0.0 版本把项目自有文件放在
`tabilet/` 下。现有的 v1.5.0 项目需要显式执行[一次性迁移](upgrade.md#migrate-a-v150-project-to-v2)。
该迁移以及可选的 API 运行器都需要 Python。

## Claude Code

在 **Claude Code 内部**运行：

```text
/plugin marketplace add tabilet/skills
/plugin install memory-bank@tabilet
```

在你的项目中打开一个新会话，然后发送：

```text
/memory-bank:memory-bank-init
```

仅当项目还没有已初始化的记忆库时才使用 Init。否则，针对你想做的工作
[选择相应的工作流](examples.md)。

## Codex

在**终端中**运行：

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

然后在你的项目中打开一个新的 Codex 会话并发送：

```text
$memory-bank:memory-bank-init
```

`@tabilet` 限定符用于标识市场。如果你的 Codex 版本没有提供插件命令，请使用
[纯文件方式](#as-plain-files-you-own)。

## DeepSeek Harness {#deepseek-harness}

若需要 **Memory Bank 侧边栏和全部七个技能**，请在你的 Web 配置中安装预构建的
v2.0.0 伴侣。在运行 DSH 的机器上的终端中执行：

```bash
dsh plugin --profile web add \
  https://github.com/tabilet/tabilet-skills/releases/download/v2.0.0/tabilet-skills-2.0.0.tgz \
  --ignore-scripts
```

无头使用时，把 `--profile web` 替换为 `--profile headless`。只在你需要它的配置中
安装。这条 GitHub release 途径不需要 npm 账号。

重启 DSH，为你的项目选择一个会话，然后在右侧边栏打开 **Memory Bank**。展开
**Prepare a workflow request**，选择一个技能，审阅预览内容，再把它插入空白草稿。
**请求由你自己发送。** 如果草稿中已经有文本或附件，请改为复制预览内容。
无头配置会加载这些技能，但没有侧边栏。

该伴侣已在 Linux 上使用 Node **24.14.1** 和锁定的 DSH **0.1.5-rc.2** 组件验证通过，
另有一个使用 rc.2 组件的隔离 rc.1 启动器。

若只需要**不带仪表盘的技能**，请使用[纯文件方式](#as-plain-files-you-own)。把
v2.0.0 检出中的全部七个完整文件夹复制到 `$DSH_HOME/skills`，通常是
`~/.dsh/skills`。文件系统途径保留其单独测试过的全 rc.1 兼容性。

### 使用 Memory Bank 面板

该面板跟随所选会话对应的项目。**Overview** 显示活跃里程碑和任务数量；**Tasks**
提供筛选、搜索和完整备注。**Acceptance** 显示已记录的验证和评审证据。**Memory**
保存当前项目事实，**History** 按需打开保留的记录。**Compatibility** 报告缺失文件、
不支持的格式、冲突的任务状态，以及哪个已安装的技能来源优先生效。

当面板可见时，外部文件改动会通过变更通知和五秒刷新周期显示出来。它还会在获得
焦点时刷新，并提供手动刷新。不完整或被拒绝的读取会作为警告保持可见。

浏览和准备请求不会发起模型调用，也不会写入项目文件。预览不是执行，也不代表批准：
你要在对话中发送它，而所选技能仍保留其批准边界。仅凭已完成的任务标记无法确立
里程碑验收。对于较旧的项目格式，请准备一个 [Upgrade](upgrade.md) 请求，并附上
显示出的警告。

## 调用技能 {#invoke-a-skill}

技能请求要发送到**智能体对话**中，而不是你的 shell 里。前缀取决于你的安装方式：

| 安装方式 | 对话请求示例 |
|---|---|
| Claude Code 插件 | `/memory-bank:memory-bank-next` |
| Codex 插件 | `$memory-bank:memory-bank-next` |
| DSH 伴侣或文件系统 | `/memory-bank-next` |
| Claude Code 纯文件 | `/memory-bank-next` |
| Codex 纯文件 | `$memory-bank-next` |

按需把 `next` 替换为 `init`、`archive`、`propose`、`reconcile`、`upgrade` 或 `goal`。
[技能指南](init.md)解释了每个技能的输入和批准边界。使用 Goal 时，请附上明确的
顺序和[提交策略](goal.md)。

## 作为你自有的纯文件 {#as-plain-files-you-own}

把 v2.0.0 源码克隆到一个单独的目录（七个技能）：

```bash
git clone --branch v2.0.0 --depth 1 https://github.com/tabilet/skills.git
```

把该检出的 `skills/` 目录中每个 `memory-bank-*` 文件夹复制到你的智能体对应的
目标位置：

| 智能体 | 个人技能目录 |
|---|---|
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| DSH | `$DSH_HOME/skills/`，通常是 `~/.dsh/skills/` |

复制**完整文件夹**，包括其中随附的模板和参考文档。只复制 `SKILL.md` 会让部分
工作流不完整。替换同名现有文件夹之前，先检查并备份它；不要动无关的技能。更改
安装后请开始一个新会话。

## 项目文件

[Init](init.md) 在你批准其方案之后准备项目专属文件。如果你更愿意手动设置，请把
release 检出中的 `template/` 复制到一个新项目：

```bash
cp -R /path/to/skills/template/. /path/to/new-project/
```

方括号中的占位符是有意保留的：请用你项目的事实、计划和验证命令填充它们。对于
现有项目，合并适用的规则并保留它原有的说明；不要把模板直接覆盖到它的当前状态上。
执行之前，记录具体的交付边界、里程碑验收、任务行和验证命令。让 `AGENTS.md` 保持
为入口；如果你的智能体读取另一个说明文件名，就让那个文件指向 `AGENTS.md`。
[第一个项目演练](examples.md#a-new-project)展示了在选择任务之前应当检查什么。

## 可选的 API 运行器 {#the-optional-api-harness}

独立的 API 运行器需要 **Python 3 和 Git**，以及你所选模型提供方的凭据。它只使用
Python 标准库。

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

使用你现有的编码智能体时，可以跳过这个运行器。若要使用它，请从一个已初始化的
项目开始，位于其 Git 工作区根目录，具备干净的已提交基线和一个获批的可执行任务。
在一次性沙箱中运行它：运行器本身会在宿主 shell 中执行模型给出的命令，不提供隔离。
`ALLOW_UNSANDBOXED_SHELL=1` 表示你确认这一访问权限。

在环境中已设置 `OPENAI_API_KEY` 的情况下，替换模型和项目占位符并运行：

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_PROVIDER=openai LLM_MODEL=your-model MAX_RUNS=1 \
  ~/.local/bin/tackle-memory-bank-api-loop /absolute/path/to/project
```

对于 Anthropic，请设置 `ANTHROPIC_API_KEY`，并使用 `LLM_PROVIDER=anthropic` 搭配
兼容的模型。向提供方发送请求可能会产生费用。使用该可执行文件的 `--help` 查看
端点设置、超时、重试和其他限制。

API 运行器要求每次运行都产生一次提交，并在遇到脏状态、缺少提交、无效的任务转换
或多行处于进行中时停止。退出码 `7` 表示已达到请求的运行次数上限；退出码 `3`
表示只剩下被阻塞的工作。退出码 `0` 表示不再有可执行的行，而不是每个里程碑都
通过了评审。之后请检查已记录的验证和关闭证据。不要同时对同一个活跃账本运行
另一个智能体。

## 更新

对于 Claude Code，使用它的 `/plugin` 管理器更新已安装的插件。对于 Codex，刷新
市场快照并重新安装插件：

```bash
codex plugin marketplace upgrade tabilet
codex plugin add memory-bank@tabilet
```

对于 DSH 伴侣，在每个适用的配置中安装所选已发布 release 归档，然后重启。对于
文件系统安装，先停止正在使用这些包的会话，检查并备份已安装的文件夹，再用所选
release 中的完整文件夹替换它们。保留无关的技能，并检查可能优先于新包的项目或
用户覆盖。

**更新已安装的技能不会迁移项目规则。** 使用 [Upgrade](upgrade.md) 检查现有项目
并批准具体的规则合并。保持任务状态、永久 ID、本地策略和历史完整不变。

## 移除

使用与你安装方式对应的卸载命令：

| 安装方式 | 命令及运行位置 |
|---|---|
| Claude Code 插件 | 在 Claude Code 中运行 `/plugin uninstall memory-bank@tabilet` |
| Codex 插件 | 在终端中运行 `codex plugin remove memory-bank@tabilet` |
| DSH Web 伴侣 | 在终端中运行 `dsh plugin --profile web remove tabilet-skills` |

如果你还在无头配置中安装了 DSH，请单独移除该安装。对于纯文件安装，只移除已确认
的 memory-bank 技能文件夹。项目 Markdown 仍留在项目中，移除后依然可用。

## 如果技能或仪表盘缺失

- 确认所选会话指向的是你想要的项目。
- 安装后开始一个新会话。更改配置后重启 DSH。
- 检查上面的调用前缀。在 DSH Web 中安装，并不会把伴侣安装到无头配置。
- 在 DSH 的 **Compatibility** 视图中检查生效的技能来源。现有的项目或用户副本
  可能优先于随附的版本。
- `skills` 仓库本身在 `template/tabilet/memory-bank/` 中有一个示例；它没有可供
  仪表盘显示的活跃项目记忆库。
