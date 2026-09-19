# Init

把你的想法或者现有的代码库，变成一个项目专属的记忆库。Init 先看看手头有哪些证据，拿不准的
决策再问你，然后给出里程碑，让你走到下一个可以验证的结果。你把整个方案批准之后，它才落笔写
文件。

在项目会话里发送请求：

| 智能体 | 会话中的请求 |
|---|---|
| Claude Code 插件 | `/memory-bank:memory-bank-init` |
| Codex 插件 | `$memory-bank:memory-bank-init` |
| DSH | `/memory-bank-init` |

不需要参数。你也可以附上一段说明，讲清打算做什么。如果是直接装到技能目录，请参见
[调用前缀](installation.md#invoke-a-skill)。

## 何时使用

只给一个没初始化过里程碑和状态运行器的项目用。全新项目、从来没有过这类运行器的现有项目，
以及做完 [Archive](archive.md) 预检的现有项目，都算。

项目里已经有 `tabilet/memory-bank/milestone.md`，而且带着活跃状态文件**或者有效的已索引退役
历史**，就说明它初始化过了。这时想加功能或提升某个候选方向，用 [Propose](propose.md)；来了
新评审，用 [Reconcile](reconcile.md)；想采用更新的工作流规则，用 [Upgrade](upgrade.md)。
记录缺失或者对不上，需要的是排查，不是推倒重来。

## 三个阶段

**发现。** Init 先读仓库，读不出来的决策再问。问题按轮次编号发给你，每一轮都附上推荐答案和
相关取舍。后一轮建立在前一轮的回答上；没有固定问卷，能探查的范围也不设上限。

**提议。** 它会给出边界、建议的活跃视野、通道含义、候选方向，以及每一项文件操作。你没全部
批准之前，它一个字都不写。

**写入。** 它按随附的写入约定执行已批准的操作。方括号占位符你一个都看不到，因为记忆库交到你
手上时就已经填好了。

*（访谈技巧改编自 [mattpocock/skills](https://github.com/mattpocock/skills) 里的 `grilling` 技能，MIT。）*

## 活跃视野

产出把信息分成三类：

```text
tabilet/memory-bank/product.md       产品是什么，以及它的领域不变量
tabilet/memory-bank/architecture.md  系统现在是什么样
tabilet/memory-bank/tech-stack.md    命令、依赖与验证
tabilet/memory-bank/lessons.md       至今仍会改变决策的经验
tabilet/memory-bank/milestone.md     活跃视野与后续方向
tabilet/memory-bank/status-*.md      每个实现单元对应一行任务粒度的状态行
```

**活跃视野**是能走到下一个有意义、可验证结果的最小依赖闭合里程碑集合。永久状态 ID 只发给
这个视野。

后头的想法留在 Candidate Directions 里，不编号，但带提升触发器。仓库调研注意到了它们，并不
因此就发状态 ID，启动参考里也永远不出现。

> Archive 记录已经存在的东西。Init 决定接下来做什么。

## Archive 预检之后

Init 不会从零再把整个包压缩一遍。它拿已经验证过的上下文证据，保留冻结的归档，把当前产品摘要
和架构摘要稳妥地并到一起，只对剩下的交付决策做访谈。

## 启动参考

项目里有已获批准、版本兼容的 `tabilet/GOAL.md` 时，Init 还会写
`tabilet/memory-bank/suggested.txt`。这是一份用完就丢的启动请求，其中包含建议的状态顺序、
文件映射和下游影响。

它只是启动输入，不是项目事实。它不进必读清单；用之前先对照 `milestone.md` 和当前状态文件核
一遍，一旦启动完成或者过期就删掉。没有兼容协议时，Init 直接省略它，单任务执行照样可用。

## 验证结果

查看 `tech-stack.md` 里的 **Execution harnesses** 表格：它应当写明实际的验证命令，以及一次通过
能证明什么。开始执行之前，先把缺的验证补上。适用的检查全部通过、验收要求也都满足，任务才算
走到 `[+]`。

接下来可以用 [Next](next.md) 请求一个已批准的任务，或者用 [Goal](goal.md) 指定明确的里程碑
顺序。初始化不会启动实现。
