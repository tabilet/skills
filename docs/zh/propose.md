# Propose

已初始化的项目要加个新功能、把某个候选方向提升一下，或者调整未来方向时，用 **Propose**。它负责
把你要的结果规划出来，实现和验收都不归它管。遇到新的工程评审，请用
[Reconcile](reconcile.md)。项目还没有已初始化的活跃或已退役状态账本，请用
[Init](init.md)。

| 智能体 | 请求 |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-propose <requested outcome or candidate direction>` |
| Codex plugin | `$memory-bank:memory-bank-propose <requested outcome or candidate direction>` |
| DSH | `/memory-bank-propose <requested outcome or candidate direction>` |

## 会发生什么

Propose 会去读项目里相关的记忆库、代码、测试、待处理工作、候选方向和已退役的 ID。它把哪些是你
自己的决定、哪些是观察到的事实和假设，分得清清楚楚。它只问那些会真正影响结果的问题；给待处理
里程碑加一个清楚的小改动，直接就能得到一份简洁的方案。

审批只走一次，请求里会写明预期结果、负责的里程碑和状态行、验收与计划中的验证、优先级和依赖
关系、下游要改什么，以及要新建或编辑哪些具体文件。如果已有合适的待处理负责项，就直接复用它。
重复的请求不会开出第二行。候选提升得重新判断触发条件、依赖关系和验收，绝不是自动生效的。
功能请求按已批准的优先级和前置条件排序，不套用工程缺陷那套严重性标签。

批准之后，Propose 会再查一遍受影响的文件、工作区改动和活跃、已退役的 ID，然后只落已批准的
规划改动。出现重大变化或 ID 冲突，就得改一版方案再来。当前各行的结果、计数器、本地策略和
冻结历史都保持不动。计划中的行为一直留在里程碑和状态记录里，直到实现把它变成当前事实。

方向发生重大变化时，可能按项目现有的触发条件新增一对 `tabilet/evolution/` 文件。如果已经有一份
兼容且已批准的 `tabilet/GOAL.md`，也可能顺带刷新 `tabilet/memory-bank/suggested.txt` 这份启动
参考。普通功能或候选提升不会自动做到这两件事。

Propose 最后交出的是一份规划交接，以及明确的验证缺口。要落实已批准的工作，请另外请求
[Next](next.md) 或 [Goal](goal.md)。

v1.5.0 项目请先[迁移项目布局](upgrade.md#migrate-a-v150-project-to-v2)。
如果项目说明还没采用请求变更的流程，接着用
[Upgrade](upgrade.md#upgrade-workflow-rules)。安装 Propose 不会改变现有的项目记录。
