# Tabilet Memory Bank

[English](https://tabilet.github.io/skills/){ .md-button }

<p class="memory-bank-hero" align="center">
  <a href="../assets/memory-bank-infographic.png" title="打开全尺寸 Memory Bank 信息图">
    <img src="../assets/memory-bank-infographic.png" alt="Memory Bank：纯 Markdown 项目记忆支撑经过验证的工作与被保留的历史。七个共享技能：Archive、Init、Propose、Reconcile、Next、Goal 和 Upgrade。" width="820" style="max-width: 100%; height: auto;">
  </a>
</p>

把项目的决策、任务和验收证据保存在纯 Markdown 中。**Memory Bank** 为编码
智能体提供一份共享记录，说明项目是什么、已经完成了什么、接下来应当做什么——
即使你开启新会话或更换智能体也不受影响。

同一套项目文件可用于 **Claude Code、Codex 或 DeepSeek Harness
(DSH)**。七个可选技能帮助创建和维护这些文件。文件留在你的代码库中，即使
不使用这些技能也依然可用。2.0.0 版本把项目自有的 Memory Bank 文件放在
`tabilet/` 下。

[安装技能](installation.md){ .md-button .md-button--primary }
[开始你的第一个项目](examples.md#a-new-project){ .md-button }

> 智能体带来能力。项目带来记忆。

## 选择你的起点

| 你项目当前的状况 | 从这里开始 |
|---|---|
| 新项目，或已有代码库但还没有记忆库 | [Init](init.md) 检查项目、询问决策，并给出方案。范围较大的代码库可能需要先运行 [Archive](archive.md)。 |
| 已有获批的任务 | [Next](next.md) 处理一个任务；[Goal](goal.md) 处理明确的里程碑顺序。 |
| 有需求中的功能或候选方向的提升 | [Propose](propose.md) 检查当前计划并给出一个规划方案。 |
| 有新的工程评审 | [Reconcile](reconcile.md) 核查各项发现并给出规划变更。 |
| 项目根目录下还有 v1.5.0 文件 | 先 [迁移到 v2](upgrade.md#migrate-a-v150-project-to-v2)，再运行 v2 工作流。 |
| 迁移后仍在使用旧的工作流契约 | [Upgrade](upgrade.md) 在保留任务和历史的前提下给出规则变更方案。 |

这些是入口，而不是每个项目都必须遵循的顺序。它们如何衔接，见
[完整示例](examples.md)。

## 哪些内容留在你的项目中

```text
your-project/
├── AGENTS.md                 智能体最先读取的内容
├── docs/                     其他项目文档
└── tabilet/
    ├── GOAL.md               可选的多里程碑协议
    ├── memory-bank/
    │   ├── product.md         这是什么，以及不是什么
    │   ├── architecture.md    布局、数据流、边界
    │   ├── tech-stack.md      命令、依赖、验证
    │   ├── lessons.md         仍然适用的经验
    │   ├── milestone.md       活跃里程碑与验收
    │   └── status-M01.md      每个活跃里程碑一个文件
    ├── docs/history/          退役记录；首次需要时创建
    └── evolution/             带版本的方向快照
```

`AGENTS.md` 告诉智能体从哪里开始。记忆库保存当前事实和活跃计划。历史为
后续问题保留证据，`tabilet/evolution/` 记录方向变化。状态 ID 在活跃存储
与退役存储之间保持永久不变。

读取和维护这些文件不需要任何 Memory Bank 运行时。常规的按任务提交流程
需要 Git。可选的 [API 运行器](installation.md#the-optional-api-harness) 和一次性
迁移需要 Python；你现有的智能体可以直接处理这些文件。

## 七个技能

| 技能 | 什么时候用它 |
|---|---|
| [Archive](archive.md) | 范围较大的现有包需要一份以提交为锚点的现状图谱。 |
| [Init](init.md) | 项目还没有里程碑与状态运行器。 |
| [Propose](propose.md) | 需求中的功能、候选方向的提升或未来方向变化需要获批的规划。 |
| [Reconcile](reconcile.md) | 收到新的代码、架构或安全评审。 |
| [Next](next.md) | 实现或继续一个任务，验证它，并按适用的策略提交。 |
| [Goal](goal.md) | 按明确的提交策略和完成条件执行有序的里程碑。 |
| [Upgrade](upgrade.md) | 你安装了更新的技能，想安全地采用它们的规则。 |

**Init、Archive、Propose、Reconcile 和 Upgrade** 在写入之前给出完整方案等待
批准。**Next 和 Goal** 执行你已授权的工作；它们可以按适用策略修改代码、
更新记录并提交。安装技能并不授权工作，也不迁移现有项目。

## 长期记忆

在已采用退役规则的项目中，一个里程碑的完整规格说明和状态文档会退役到
`tabilet/docs/history/status-<LANE><NN>.md`。标识符保持预留，记录被冻结，
活跃计划不再携带它。退役发生在验证、有界评审门禁、知识整合和下游协调之后。
仅凭已完成的任务标记，并不能证明里程碑通过验收。

紧邻下一个任务的是 `lessons.md`：带证据的精选经验，例如一个原因容易被
忽视的故障模式。被取代的知识保存在仅追加的日志中，而不是被覆盖。

这份记忆能跨越对话重置、智能体更换或订阅终止，因为它属于代码库，
而不属于某个供应商。

## DSH 仪表盘

可选的 [tabilet-skills 伴侣](installation.md#deepseek-harness) 会为 DSH
添加一个 **Memory Bank** 侧边栏。浏览所选项目的任务、记忆、记录的验收
证据和历史，然后在现有对话中准备一个技能请求。由你自行审阅并发送。

仪表盘读取你的项目文件。它不会维护第二份任务清单，也不会把工作标记为
完成。在无头配置中安装该伴侣，会暴露全部七个 v2.0.0 技能，但没有 Web
界面。
