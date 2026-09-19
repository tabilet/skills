# Goal

按照项目的 `tabilet/GOAL.md` 协议，依次执行或继续执行记忆库中的里程碑。

在项目里开启的会话中发送下面其中一条，把 ID 换成你已经批准的里程碑顺序：

| 智能体 | 会话中的请求 |
|---|---|
| Claude Code plugin | `/memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| Codex plugin | `$memory-bank:memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |
| DSH | `/memory-bank-goal M01 -> M02. COMMIT_POLICY: task. EXTERNAL_MUTATIONS: none.` |

要带上一个可衡量的完成条件，比如两个里程碑都满足各自文档规定的验收、验证、评审和收尾要求。
如果你是直接安装到技能目录，请参见
[调用前缀](installation.md#invoke-a-skill)。

末尾带 `?`，比如 `A01?`，表示这是一个条件里程碑。只要它文档里的触发条件不成立，执行时就跳过它，
既不算完成，也不算取消。更靠后的候选方向不是条件里程碑，也不该写进执行顺序。

## 何时使用

当多个里程碑需要按既定顺序依次跑完，而不是一次只做一个任务时。

没有给出顺序时，技能会拿 `tabilet/memory-bank/suggested.txt` 与当前里程碑和状态文件核对。它优先采用
一个有效的建议顺序，或者从 `milestone.md` 推导出一个，然后把完整请求摆出来供你确认。顺序有歧义
时它会来问你。没有 `tabilet/GOAL.md`，这套工作流就走不下去；
单任务执行仍可通过 [Next](next.md) 使用。

## GOAL.md 是可选做法，不是必需项

`tabilet/GOAL.md` 只是一个可选协议。它得靠显式调用才生效，不会自动起作用：不管你用哪个智能体，启动
一次运行的请求都要点名这个文件、执行顺序和提交策略。

```text
Using tabilet/GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: all required and triggered milestones meet their
documented acceptance, verification, review, and closure requirements.
```

这段内容可以粘贴给任何智能体。协议里没有项目专有的路径、通道字母或命令 —— 这些都从 `AGENTS.md`
和记忆库中读取 —— 所以同一个文件在任何复制它的项目里都能原样使用。

同一套项目文件也能配合另一种协议或单任务执行使用。`memory-bank-goal` 技能则明确要求
`tabilet/GOAL.md`；至于项目要不要采用这个协议，仍然由你决定。

## 真正起决定作用的是 COMMIT_POLICY

!!! note "把提交策略写清楚"
    一次 goal 运行期间，`COMMIT_POLICY` 就是**全部**提交规则。
    `AGENTS.md` 可能写着每个状态行都是一个提交单元，但
    `COMMIT_POLICY: none` —— 也就是该协议的默认值 —— 表示完全不产生任何提交。
    这是正确行为，不是规则冲突。

想要常规的逐行提交就写 `task`，想让改动保持未提交就写 `none`。优先级顺序是：请求高于
`tabilet/GOAL.md`，后者高于 `AGENTS.md`。提交策略的例外只在这次运行期间有效；
其他适用的项目规则照常生效。

## 内置的 `/goal` 是另一回事

智能体原生的 goal 功能可以让一个目标跨多轮持续有效。它替代不了本项目的协议，也不会替你隐式选中
`tabilet/GOAL.md`。如果要用原生 `/goal` 的持续执行来跑这套工作流，请把协议、提交策略和可衡量的
完成条件都写清楚：

```text
/goal Using tabilet/GOAL.md, reconcile tabilet/memory-bank/suggested.txt against the current
memory bank, then execute the resolved loop. COMMIT_POLICY: task.
EXTERNAL_MUTATIONS: none.
Completion condition: every required status is complete, every triggered conditional
status is complete, and every milestone's documented verification passes.
```

这个技能刻意没有取名 `goal`，这样一来它就不会模糊或遮蔽那个内置功能。

## 唯一的执行所有者

一个活跃账本只有一个执行所有者，哪怕有多个会话或启动器可用。原生待办和原生 goal 状态能帮
运行时保持连续性，但连续性从来不等于验收。

验收结论来自项目需求、实际验证和评审证据。进程成功退出，里程碑照样可能没做完。
