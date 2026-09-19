# Goal

使用项目的 `tabilet/GOAL.md` 协议，按顺序执行或继续执行记忆库中的里程碑。

在项目的会话中发送下面某一条命令，并把其中的 ID 换成你已批准的里程碑顺序：

| 智能体 | 会话中的请求 |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| Codex plugin | `$memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| DSH | `/memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |

请附上一个可衡量的完成条件，例如两个里程碑都满足各自文档中规定的验收、验证、评审和关闭要求。
如果是直接安装到技能目录，请参见
[调用前缀](installation.md#invoke-a-skill)。

结尾的 `?`（例如 `A01?`）标记一个条件里程碑。当它文档中规定的触发条件不存在时会被跳过，
既不标记为已完成，也不标记为已取消。更靠后的候选方向不是条件里程碑，也不属于执行顺序。

## 何时使用

当多个里程碑需要按既定顺序运行，而不是一次只处理一个任务时使用。

当没有提供顺序时，该技能会拿 `tabilet/memory-bank/suggested.txt` 与当前里程碑和状态文件进行核对。
它会优先采用有效的建议顺序，或者从 `milestone.md` 推导出一个顺序，然后展示完整请求以供确认。
当顺序存在歧义时它会询问你。缺少 `tabilet/GOAL.md` 会中断此工作流；
单任务执行仍可通过 [Next](next.md) 使用。

## GOAL.md 是可选的，绝非必需

`tabilet/GOAL.md` 是一个可选协议。它是被显式调用的，而不是始终生效的：无论你使用哪个
智能体，启动一次运行的请求都要指明该文件、执行顺序和提交策略。

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: all required and triggered milestones meet their
documented acceptance, verification, review, and closure requirements.
```

你可以把这段内容粘贴给任何智能体。该协议不包含项目特有的路径、通道字母或命令 —— 这些
都从 `AGENTS.md` 和记忆库中读取 —— 因此同一个文件在任何复制它的项目中都能原样使用。

同一套项目文件也能配合另一种协议或单任务执行使用。`memory-bank-goal` 技能明确要求
`tabilet/GOAL.md`；但项目是否采用该协议仍然是可选的。

## 真正起决定作用的是 COMMIT_POLICY

!!! note "明确指定提交策略"
    在一次 goal 运行期间，`COMMIT_POLICY` 就是**全部**提交规则。
    `AGENTS.md` 可能会说每个状态行都是一个提交单元，但
    `COMMIT_POLICY: none` —— 该协议的默认值 —— 表示完全不产生任何提交。
    这是正确行为，而不是冲突。

当你需要常规的逐行提交时写 `task`，当你希望改动保持未提交时写 `none`。请求的优先级高于
`tabilet/GOAL.md`，而后者高于 `AGENTS.md`。提交策略的例外只在这次运行期间有效；
其他适用的项目规则仍然有效。

## 内置的 `/goal` 是另一回事

智能体原生的 goal 功能可以让一个目标在多个轮次之间保持活跃。它不会取代本项目的协议，
也不会隐式选择 `tabilet/GOAL.md`。如果要把原生 `/goal` 的持续执行用于此工作流，请明确
写出协议、提交策略和可衡量的完成条件：

```text
/goal Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current
memory bank, then execute the resolved loop. COMMIT_POLICY: task.
EXTERNAL_MUTATIONS: none.
Completion condition: every required status is complete, every triggered conditional
status is complete, and every milestone's documented verification passes.
```

该技能刻意不命名为 `goal`，这样就不会模糊或遮蔽那个内置功能。

## 唯一的执行所有者

一个活跃账本只有一个执行所有者，即使同时存在多个会话或启动器也是如此。原生待办事项和
原生 goal 状态有助于运行时保持连续性；它们永远不能确立验收结论。

验收来自项目需求、实际验证和评审证据。一次成功的进程退出之后，仍可能留下未完成的
里程碑。
