# Tabilet Memory Bank

[English](https://tabilet.github.io/skills/){ .md-button }

<p class="memory-bank-hero" align="center">
  <a href="../assets/memory-bank-infographic.png" title="打开全尺寸 Memory Bank 信息图">
    <img src="../assets/memory-bank-infographic.png" alt="Memory Bank：用纯 Markdown 保存项目记忆，支撑经过验证的工作和保留下来的历史。七个共享技能：Archive、Init、Propose、Reconcile、Next、Goal 和 Upgrade。" width="820" style="max-width: 100%; height: auto;">
  </a>
</p>

把项目的决策、任务和验证证据都留在纯 Markdown 里。**Memory Bank** 让编码
智能体共享一份记录，写清项目是什么、已经做完什么、接下来该做什么——即使你
开启新会话或换一个智能体，这份记录依然在。

同一套项目文件可以配合 **Claude Code、Codex 或 DeepSeek Harness
(DSH)** 使用。七个可选技能帮你创建和维护它们。文件留在你的仓库里，不用这些
技能也照样能读能改。2.0.0 版本把项目自有的 Memory Bank 文件放在 `tabilet/`
下。

[安装技能](installation.md){ .md-button .md-button--primary }
[开始你的第一个项目](examples.md#a-new-project){ .md-button }

> 智能体提供能力，项目提供记忆。

## 选择你的起点

| 你项目当前的情况 | 从这里开始 |
|---|---|
| 新项目，或者已有代码库但还没有记忆库 | [Init](init.md) 检查项目、询问决策，然后给出方案。范围较大的代码库可能需要先运行 [Archive](archive.md)。 |
| 已经有获批的任务 | [Next](next.md) 负责一个任务；[Goal](goal.md) 负责明确的里程碑顺序。 |
| 有需求中的功能，或需要提升的候选方向 | [Propose](propose.md) 检查当前计划，给出一个规划方案。 |
| 收到新的工程评审 | [Reconcile](reconcile.md) 核查各项发现，给出规划变更。 |
| 项目根目录下还有 v1.5.0 文件 | 先 [迁移到 v2](upgrade.md#migrate-a-v150-project-to-v2)，再运行 v2 工作流。 |
| 迁移后仍在用旧的工作流契约 | [Upgrade](upgrade.md) 在保留任务和历史的前提下，给出规则变更方案。 |

这些是入口，不是每个项目都必须走的顺序。它们之间怎么衔接，见
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

`AGENTS.md` 告诉智能体从哪里开始。记忆库保存当前事实和活跃计划。历史记录
为后续问题留证据，`tabilet/evolution/` 记录方向的变更。状态 ID 在活跃存储
和退役存储之间永久保留。

读取和维护这些文件不需要任何 Memory Bank 运行时。常规的按任务提交流程需要
Git。可选的 [API 运行器](installation.md#the-optional-api-harness) 和一次性
迁移需要 Python；你现有的智能体可以直接处理这些文件。

## 七个技能

| 技能 | 适用场景 |
|---|---|
| [Archive](archive.md) | 范围较大的现有包需要一份以提交为锚点的现状图谱。 |
| [Init](init.md) | 项目还没有里程碑与状态运行器。 |
| [Propose](propose.md) | 需求中的功能、候选方向的提升或未来方向变化需要获批的规划。 |
| [Reconcile](reconcile.md) | 收到新的代码、架构或安全评审。 |
| [Next](next.md) | 实施或继续一个任务，验证它，再按适用的策略提交。 |
| [Goal](goal.md) | 按明确的提交策略和完成条件，依次执行多个里程碑。 |
| [Upgrade](upgrade.md) | 你安装了更新的技能，想稳妥地采用其中的规则。 |

**Init、Archive、Propose、Reconcile 和 Upgrade** 会先提交完整方案等你批准，
然后才写入文件。**Next 和 Goal** 执行你已经授权的工作；它们可以按适用策略
修改代码、更新记录并提交。安装技能并不等于授权工作，也不会迁移现有项目。

## 建议使用的模型 {#suggested-models}

这些技能不要求也不会选择某个特定的大语言模型。它们使用宿主智能体当前选择的模型，
Markdown 状态则可以跨提供方继续使用。不过模型能力仍然重要，因为各工作流的形态并不
相同。下表里的名称只是当前 Codex 的示例，并不是技能能够识别或要求的名称；Codex 以后
可能改名或替换这些模型，其他提供方也有自己的模型名称。

| 工作形态 | 技能 | 能力类型 | 当前 Codex 示例 |
|---|---|---|---|
| 开放式发现与规划 | Init、Propose、Reconcile | 判断力强的深度模型 | Sol，高推理强度 |
| 有明确边界的证据与规则分析，以及实施与评审合并的运行 | Archive、Upgrade、Goal | 推理和工具使用能力强的均衡模型 | Terra，高推理强度 |
| 按已经批准的计划执行一个明确任务 | Next | 适合清晰、可重复工作的快速模型 | Luna，高推理强度；之后手动用 Terra 之类的均衡模型评审 |

请选择宿主智能体中能力最接近的模型。面对含糊的规划和后果重大的评审，应选推理更深入的模型；
面对以证据为主的分析，可选均衡模型；面对验收与验证都很明确的任务，可选快速模型。
如果 Luna 在实施中发现依赖关系不清、需要改变架构，或者验证反复失败，就升级到 Terra
或 Sol。发布前、安全敏感或范围异常广的最终评审应使用 Sol。

技能无法改变父会话的模型。在 Codex 中，请在调用技能之前使用 `/model`，或者用模型
配置启动会话。Goal 同时包含实施和限定轮次的里程碑评审，因此整个运行默认使用 Terra
之类的均衡模型更合适。Next 可以用 Luna 之类的快速模型执行一个明确任务，之后再手动用
Terra 之类的均衡模型评审。如果这个任务会关闭里程碑，并在 Next 内触发结项评审，那么
这次 Next 也应使用均衡模型。任务状态、评审
计数和验收证据在单独评审的交接前后都会保留在项目文件里。

## 长期记忆

在已经采用退役规则的项目里，里程碑的完整规格说明和状态文档会退役到
`tabilet/docs/history/status-<LANE><NN>.md`。标识符继续保留，记录就此冻结，
活跃计划里不再出现它。退役发生在验证、限定轮次的评审关卡、知识整合和下游
协调全部通过之后。任务标记全部完成，并不等于里程碑通过了验收。

离下一个任务最近的是 `lessons.md`，里面收录筛选过、附带证据的经验，比如
某种根因不易察觉的故障模式。旧知识被取代后会追加写入日志，而不是直接覆盖。

这份记忆不会因为一次对话重置、一次智能体更换或一次订阅到期而消失，因为它
属于仓库，而不属于某家厂商。

## DSH 仪表盘

可选的 [tabilet-skills 伴侣](installation.md#deepseek-harness) 会给 DSH
加上一个 **Memory Bank** 侧边栏。你可以浏览所选项目的任务、记忆、记录的
验收证据和历史，然后在现有对话里准备一次技能请求。审阅和发送都由你自己来。

仪表盘只读取你的项目文件，不另外维护一份任务清单，也不会把工作标成完成。
在无界面（headless）配置里装上这个伴侣，七个 v2.0.0 技能就都能用，只是没有
Web 界面。
