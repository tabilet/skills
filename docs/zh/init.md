# Init

把你的想法或既有代码库变成项目专属的记忆库。Init 会检查可用的证据，就不确定的决策向你提问，
并提出达成下一个可验证结果所需的里程碑。只有在你批准完整提案之后，它才会写入文件。

在项目的会话中发送请求：

| 智能体 | 会话中的请求 |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-init` |
| Codex plugin | `$memory-bank:memory-bank-init` |
| DSH | `/memory-bank-init` |

不需要任何参数。你也可以附上一段说明，描述你想构建什么。如果是直接安装到技能目录，
请参见[调用前缀](installation.md#invoke-a-skill)。

## 何时使用

在尚未初始化里程碑与状态运行器的项目上使用一次。这包括全新的项目、从未有过这类运行器的
既有项目，以及完成 [Archive](archive.md) 预检之后的既有项目。

一个已存在的 `tabilet/memory-bank/milestone.md`，只要它带有活跃状态文件**或有效的已索引退役
历史**，就说明项目已经初始化。若要处理请求的功能或候选提升，请使用 [Propose](propose.md)；
若要处理新的评审，请使用 [Reconcile](reconcile.md)；若要采用更新的工作流规则，请使用
[Upgrade](upgrade.md)。缺失或不一致的记录需要检查，它们不是推倒重来的许可。

## 三个阶段

**发现。** Init 会先读仓库，再就它无法从证据中确定的决策提问。问题以编号轮次提出，并附带
推荐答案和相关的取舍。每一轮都建立在此前答案的基础上；没有固定问卷，也不限制它能探索的范围。

**提议。** 它会呈现边界、提议的活跃视界、通道含义、候选方向以及每一项文件操作。在你全部批准
之前，不会写入任何内容。

**写入。** 它会按照捆绑的写入契约执行已批准的操作。你永远不会看到方括号占位符，因为记忆库
到手时就已经填充完毕。

*（访谈技巧改编自 [mattpocock/skills](https://github.com/mattpocock/skills) 中的 `grilling` 技能，MIT。）*

## 活跃视界

输出把信息分成三类：

```text
tabilet/memory-bank/product.md       产品是什么，以及它的领域不变量
tabilet/memory-bank/architecture.md  系统当前是什么样
tabilet/memory-bank/tech-stack.md    命令、依赖与验证
tabilet/memory-bank/lessons.md       仍会改变决策的经验教训
tabilet/memory-bank/milestone.md     活跃视界与后续方向
tabilet/memory-bank/status-*.md      每个实现单元对应一行任务粒度的状态行
```

**活跃视界**是能够达成下一个有意义的、可验证结果的最小依赖闭合里程碑集合。永久状态标识
只分配给该视界。

后续的想法保持不编号，留在 Candidate Directions 中并带有提升触发条件。它们不会仅仅因为仓库
调研注意到了它们就获得状态 ID，也绝不会出现在启动参考中。

> Archive 记录已存在的内容。Init 决定接下来做什么。

## Archive 预检之后

Init 不会第二次从零开始压缩代码包。它会消费已验证的上下文证据，保留冻结的归档，安全地合并
当前的产品与架构摘要，并只针对剩余的交付决策进行访谈。

## 启动参考

当项目中存在已批准且兼容的 `tabilet/GOAL.md` 时，Init 还会写入
`tabilet/memory-bank/suggested.txt`：一份可丢弃的启动请求，其中包含提议的状态顺序、文件映射
和下游影响。

它是启动输入，不是项目事实。它不在必读顺序之内；使用前应先对照 `milestone.md` 和当前状态
文件进行检查，一旦启动完成或已经过期就删除。若没有兼容的协议，Init 会省略它，而单任务执行
仍然可用。

## 验证结果

检查 `tech-stack.md` 中的 **Execution harnesses** 表格：它应指明实际的验证命令，以及一次通过
能确立什么。在开始执行之前先解决缺失的验证。只有当适用的检查全部通过、验收要求得到满足之后，
任务才会到达 `[+]`。

然后通过 [Next](next.md) 请求一个已批准的任务，或通过 [Goal](goal.md) 请求明确的里程碑顺序。
初始化不会启动实现。
