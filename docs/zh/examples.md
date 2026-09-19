# 示例

选哪个技能，取决于你想做的工作。下面每一个箭头都是一次独立请求：规划方案
要等你批准，实施要另外授权。箭头不是 shell 命令，也不代表可以自动启动
下一个工作流。

## 哪种工作流合适

| 情况 | 工作流 |
|---|---|
| 新项目，或没有运行器的小型现有包 | [init](init.md) → 获批方案 → [next](next.md) 或 [goal](goal.md) |
| 范围较大、需要事实性上下文图谱的现有包 | [archive](archive.md) → 已验证的预检 → [init](init.md) → 执行 |
| 已初始化、有一个就绪任务的项目 | [next](next.md) |
| 有多个获批里程碑，需要按顺序执行 | [goal](goal.md) |
| 已初始化的项目要做需求中的功能，或提升候选方向 | [propose](propose.md) → 获批的规划变更 → 另行请求执行 |
| 收到新的工程评审 | [reconcile](reconcile.md) → 获批的规划变更 → 另行请求执行 |
| 现有项目需要更新工作流规则 | [upgrade](upgrade.md) → 获批的规则合并 → 另行请求执行 |
| 当前里程碑已经可以关闭 | 由它的执行工作流负责评审和关闭；如果项目已经采用这套生命周期，退役也一并处理。不需要调用 archive。 |

## 新项目 {#a-new-project}

先为你的智能体装上技能，然后在终端里创建一个项目目录。例如：

```bash
mkdir order-tracker
cd order-tracker
git init
```

在那个目录里打开你的智能体，描述你想要的结果。以 Claude Code 插件为例，
发送：

```text
/memory-bank:memory-bank-init
I want a local order tracker. The first usable version should record items and
quantities, calculate totals, and save orders between sessions. Ask about the
decisions you need, then show the complete proposal before writing.
```

在 Codex 里把第一行换成 `$memory-bank:memory-bank-init`；在 DSH 里用
`/memory-bank-init`。

回答发现阶段的问题，涉及作用域、行为、约束和验证。Init 会给出活跃里程碑
以及全部文件变更的方案。审阅这份方案，需要改就提出，确认它符合你想要的项目
后就批准。

文件按方案写入之后，逐项确认：

- `product.md` 写清了预期结果和排除项。
- `architecture.md` 区分了现有实现和拟议工作。
- `tech-stack.md` 列出了可用于验证项目的命令。
- `milestone.md` 定义了验收标准，以及活跃里程碑的顺序。
- 各状态文件把这项工作拆成带永久 ID 的具体任务。

然后再单独给 [Next](next.md) 发一次请求：

| 智能体 | 执行一个任务 |
|---|---|
| Claude Code 插件 | `/memory-bank:memory-bank-next` |
| Codex 插件 | `$memory-bank:memory-bank-next` |
| DSH | `/memory-bank-next` |

检查改动过的代码、验证结果和任务备注，策略要求提交时再看提交。下一个任务
照旧重复 Next；等你准备好授权明确的里程碑顺序和提交策略，就改用
[Goal](goal.md)。初始化本身不会启动任何实施。

## 现有代码库

仓库里已经积累了很多年的决策，散落在源码、测试、清单、CI，以及不同时期
写的文档中。有些彼此一致，有些已经过时。

先确认哪些事实有当前代码和测试支撑。对于范围较大的包，Archive 会先保留一份
经过验证的上下文图谱，之后 Init 再规划交付工作。只要还没决定一项证据是否
纳入计划，它就是缺口。

```text
existing facts -> current project map -> approved milestones -> implementation
new review     -> current-state validation -> reconciled milestones -> implementation
```

让 [Init](init.md) 检查代码库，判断是否需要 [Archive](archive.md) 预检。
如果需要，就单独请求 Archive，批准它提出的上下文和文件操作，然后等到每个
选定的上下文都通过验证。之后回到 Init，规划交付工作。现有的项目规则和已验证
的上下文记录都会保留下来。

## 项目进行中收到评审

收到四项发现。动手修之前，[reconcile](reconcile.md) 会先确认它们针对当前
仓库是否还成立，然后给每一项一个处置建议：已确认、重复、已解决、超出归属
范围、暂缓。

已确认的工作要么并进一个开放的里程碑，要么单开一个记录来源关系的新修复
里程碑。已经完成的历史永远不会重新打开。下游待处理的里程碑会在实施开始前
更新，因为一项发现可能改变多个里程碑共同依赖的前提。

## 有数月历史的项目

项目一旦采用退役规则，某个里程碑只要依次走完验证、评审关卡、知识整合和
下游协调，它的完整规格说明和状态文档就会退役到 `tabilet/docs/history/`，
标识符继续保留，活跃计划里不再出现它。

离下一个任务最近的是 `lessons.md`。一个已完成的里程碑可能记下了每一条任务
备注和测试结果；真正值得留下来的经验是这样一条：测试只用单件订单，掩盖了
一个数量缺陷，所以今后的定价测试需要覆盖多件订单。

对于按旧规则创建的项目，用 [Upgrade](upgrade.md) 把随附的契约和当前项目
比一比。在保留任务结果、永久 ID、评审计数器和冻结记录的前提下，批准具体的
规则合并。装上更新的技能，并不会采用退役机制，也不会移动现有里程碑。
