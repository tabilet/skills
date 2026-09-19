# 示例

为你想做的工作选择一个技能。下面的每个箭头都是一次独立的请求：规划方案
需要批准，实现需要各自的授权。箭头不是 shell 命令，也不代表可以自动启动
下一个工作流。

## 哪种工作流合适

| 情况 | 工作流 |
|---|---|
| 新项目，或没有运行器的小型现有包 | [init](init.md) → 获批方案 → [next](next.md) 或 [goal](goal.md) |
| 需要事实性上下文图谱的范围较大的现有包 | [archive](archive.md) → 已验证的预检 → [init](init.md) → 执行 |
| 已初始化且有一个就绪任务的项目 | [next](next.md) |
| 有多个获批里程碑需要按顺序执行 | [goal](goal.md) |
| 已初始化的项目需要实现需求中的功能或提升候选方向 | [propose](propose.md) → 获批的规划变更 → 单独请求的执行 |
| 收到新的工程评审 | [reconcile](reconcile.md) → 获批的规划变更 → 单独请求的执行 |
| 现有项目需要更新工作流规则 | [upgrade](upgrade.md) → 获批的规则合并 → 单独请求的执行 |
| 当前里程碑已具备关闭条件 | 由它的执行工作流完成评审与关闭，包括在项目已采用该生命周期时进行退役。无需调用 archive。 |

## 新项目 {#a-new-project}

为你的智能体安装技能，然后在终端中创建一个项目目录。例如：

```bash
mkdir order-tracker
cd order-tracker
git init
```

在该目录中打开你的智能体，描述你想要的结果。对 Claude Code 插件，
发送：

```text
/memory-bank:memory-bank-init
I want a local order tracker. The first usable version should record items and
quantities, calculate totals, and save orders between sessions. Ask about the
decisions you need, then show the complete proposal before writing.
```

在 Codex 中，把第一行替换为 `$memory-bank:memory-bank-init`；在 DSH 中，
使用 `/memory-bank-init`。

回答关于范围、行为、约束和验证的发现阶段问题。Init 会给出活跃里程碑和
全部文件变更的方案。审阅该方案，必要时要求修正，并在它符合你想要的项目时
批准它。

获批的文件写入之后，检查以下几点：

- `product.md` 描述了预期结果和排除项。
- `architecture.md` 区分了现有实现与拟议工作。
- `tech-stack.md` 列出了可用于验证项目的命令。
- `milestone.md` 定义了验收标准以及活跃里程碑的顺序。
- 各状态文件把该项工作拆分为带永久 ID 的具体任务。

然后向 [Next](next.md) 发送一次单独的请求：

| 智能体 | 执行一个任务 |
|---|---|
| Claude Code 插件 | `/memory-bank:memory-bank-next` |
| Codex 插件 | `$memory-bank:memory-bank-next` |
| DSH | `/memory-bank-next` |

检查改动过的代码、验证结果、任务备注，并在策略要求时检查提交。对另一个
任务重复 Next，或者在你准备好授权明确的里程碑顺序和提交策略时使用
[Goal](goal.md)。初始化本身从不启动实现。

## 现有代码库

代码库中已经积累了多年的决策，分散在源码、测试、清单、CI，以及在不同
时间点编写的文档里。有些彼此一致；有些已经过时。

先确认哪些事实有当前代码和测试的支持。对于范围较大的包，Archive 会在
Init 给出交付工作之前保留一份已验证的上下文图谱。证据缺口始终是缺口，
直到你决定它是否属于该计划。

```text
existing facts -> current project map -> approved milestones -> implementation
new review     -> current-state validation -> reconciled milestones -> implementation
```

让 [Init](init.md) 检查代码库，并判断它是否需要 [Archive](archive.md)
预检。如果确实需要，单独请求 Archive，批准它给出的上下文和文件操作，并
等到每一个选定的上下文都通过验证。然后回到 Init 规划交付工作。现有项目
规则和已验证的上下文记录都会被保留。

## 项目进行中收到评审

收到四项发现。在修复其中任何一项之前，[reconcile](reconcile.md) 会先确认
它们针对当前代码库是否仍然成立，然后为每一项给出处置建议：已确认、重复、
已解决、超出归属范围、暂缓。

已确认的工作会落入一个开放的里程碑，或一个带溯源关系的新修复里程碑。
已完成的历史永远不会被重新打开。下游的待处理里程碑会在实现开始之前更新，
因为一项发现可能改变多个里程碑共同依赖的假设。

## 有数月历史的项目

对于已采用退役规则的项目，一旦某个里程碑通过了验证、其评审门禁、知识
整合和下游协调，它的完整规格说明和状态文档就会退役到
`tabilet/docs/history/`，其标识符保持预留，活跃计划不再携带它。

紧邻下一个任务的是 `lessons.md`。一个已完成的里程碑可能包含每一条任务
备注和测试结果；而持久留存的经验是：只用单件订单的测试掩盖了一个数量
缺陷，因此今后的定价测试需要多件订单的用例。

对于按旧规则创建的项目，使用 [Upgrade](upgrade.md) 把随附的契约与当前
项目进行比较。在保留任务结果、永久 ID、评审计数器和冻结记录的前提下，
批准具体的规则合并。安装更新的技能并不会采用退役机制，也不会移动现有
里程碑。
