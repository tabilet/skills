# Propose

当一个已初始化的项目需要新功能、需要提升某个候选方向，或者需要调整未来方向时，请使用
**Propose**。它只规划所请求的结果；不负责实现，也不负责验收。对于新的工程评审，请使用
[Reconcile](reconcile.md)。对于尚未建立已初始化的活跃或已退役状态账本的项目，请使用
[Init](init.md)。

| 智能体 | 请求 |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-propose <requested outcome or candidate direction>` |
| Codex plugin | `$memory-bank:memory-bank-propose <requested outcome or candidate direction>` |
| DSH | `/memory-bank-propose <requested outcome or candidate direction>` |

## 会发生什么

Propose 会阅读相关的项目记忆、代码、测试、待处理工作、候选方向和已退役的 ID。它把你的
决定与观察到的事实和假设区分开来。它只询问有实质影响的问题；对待处理里程碑的一个清晰
小改动会直接进入简洁的方案。

单一的批准请求会写明预期结果、负责的里程碑和行、验收与计划中的验证、优先级和依赖关系、
下游变更，以及要创建或编辑的确切文件。如果现有的待处理负责人适用，就复用它。重复的请求
不会创建第二行。候选提升需要就其触发条件、依赖关系和验收做出新的决定；它绝不是自动的。
所请求的功能按已批准的优先级和前置条件排序，不使用工程缺陷严重性标签。

批准之后，Propose 会再次检查受影响的文件、工作区变更以及活跃和已退役的 ID。它只应用已
批准的规划编辑。重大变更或 ID 冲突需要一份修订后的方案。它会保留当前的行结果、计数器、
本地策略和冻结记录。在实现使之成为当前事实之前，计划中的行为一直留在里程碑/状态记录中。

方向的重大变更可能会在项目现有的触发条件下新增一对 `tabilet/evolution/` 文件。一个兼容
且已批准的 `tabilet/GOAL.md` 可能会获得刷新后的 `tabilet/memory-bank/suggested.txt` 启动
引用。对于普通功能或候选提升，这两者都不是自动发生的。

Propose 以规划交接和明确的验证缺口结束。请分别请求
[Next](next.md) 或 [Goal](goal.md) 来实现已批准的工作。

对于 v1.5.0 项目，请先[迁移项目布局](upgrade.md#migrate-a-v150-project-to-v2)。
如果项目的说明尚未采用所请求变更的流程，请接着使用
[Upgrade](upgrade.md#upgrade-workflow-rules)。安装 Propose 不会改变现有的项目记录。
