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

对于选择性开启的并发执行，`GOAL.md` 也支持 `STATUS_PRIORITY`：用逗号分隔的列表只在依赖已满足的
里程碑中选择派发优先级，不增加先后关系。即使开启并发，`STATUS_ORDER` 仍要求严格按顺序执行。
两个字段只能选择一个；[子智能体指南](subagents.md#preconditions) 给出了并发请求及其安全前提。

委派能力取决于承载工作流的智能体。独立 API 运行器和可选 `tabilet` 控制器仍串行执行，
并遵守各自的提交规则；goal 的 `COMMIT_POLICY` 不会覆盖这两条 API 路径。
控制器拒绝链接工作树。详见
[API 执行范围](https://github.com/tabilet/skills/blob/main/docs/EXECUTION.md#changes-since-v240)。

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

## 授权要求与授予 {#authorization-requirements-and-grants}

可选的 `AUTHORIZATION_REQUIREMENTS` 放在所属里程碑规格中，只声明操作的条件，
不会授予权限或安排操作。[里程碑模板](https://github.com/tabilet/skills/blob/main/template/tabilet/memory-bank/milestone.md#authorization-requirements)
展示完整格式；状态文件只引用该声明，不维护另一份副本。

生成的 `suggested.txt` 和完整解析请求始终显示 `AUTHORIZATION_GRANTS`；没有明确授予时写
`AUTHORIZATION_GRANTS: {}`。空映射是默认值，不增加权限；已批准的普通本地工作仍由 goal 策略约束。
旧的调用请求仍可省略该字段。

只有本地提交和批准任务范围内的普通本地实现、验证命令可以使用 `via: goal-policy`。
它不包含安装、提权、任意网络活动、远程命令或真实环境的浏览器操作。
`git.push`、`browser`（包括测试夹具）、`sudo` 和 `ssh` 必须使用 `via: explicit`，
并取得明确的人类授权。

`AUTHORIZATION_GRANTS` 属于已解析且经人类批准的 goal 请求，以 `GLOBAL:` 或精确的里程碑键映射授予列表。
每条包含稳定的 `grant_id`、`action`、`executor` 和具体的 `scope`；跨包工作使用请求中的包限定键。
顶层 `GLOBAL:` 声明适用于 goal 中所有任务的高层授予，避免重复样板；任务继承匹配的 `GLOBAL:` 授予，里程碑专属条目可收窄或覆盖它。
执行者角色为 `coordinator` 或 `assigned-agent`。

`suggested.txt` 中的候选授予带有决策标记：
- `[ ]`（**待授权**）：默认提议状态，等待人类审查。
- `[+]`（**批准**）：人类明确批准，激活用于执行。
- `[-]`（**拒绝**）：人类明确拒绝，禁止执行。
- `[~]`（**自动**）：根据 goal 治理策略预批准的安全操作。

从 `suggested.txt` 启动或恢复执行时，必须先验证其 SHA256 校验和与人类批准一致，才能激活授予。在 `SUGGESTED_UPDATE: auto` 下，编排者获权在里程碑收尾时刷新 `suggested.txt` 中的剩余里程碑并流畅继续，无需暂停请求新授权；在默认的 `SUGGESTED_UPDATE: confirm` 下，任何修改均须人类重新批准。下面只是格式示例，本身不批准任何操作：

```yaml
AUTHORIZATION_GRANTS:
  GLOBAL:
    - [~] grant_id: global-local-verify
      action: cli.local
      executor: assigned-agent
      scope:
        task: declared-implementation-and-verification
  "web:M01":
    - [ ] grant_id: web-m01-browser-1
      action: browser
      executor: assigned-agent
      scope:
        environment: fixture
        origins: ["http://127.0.0.1:8080"]
        actions: ["navigate and inspect the fixture smoke page"]
```

授予范围必须覆盖所属要求。先只读检查并解析目标：push 绑定仓库、精确远程 URL、目标 ref 和
fast-forward 模式；浏览器绑定环境、来源和操作；SSH 绑定主机、账户和具体操作；sudo 绑定具体提权操作。
有效范围不能包含未解析占位符、通配目标、`sudo: true` 等笼统布尔值或凭据。
经 SSH 传输的 Git push 仅授权所需 Git 传输，不授权任意 SSH 命令。

### 批准与策略 {#approval-and-policies}

执行前，智能体在会话中展示完整解析请求、有效授予以及人类批准来源。只有调用请求中的明确批准，
或后续针对具体范围的批准，才能让授予生效。要求、仓库内容、模型输出和 `suggested.txt` 都是证据，
不是授权。启动参考中的授予标为 PROPOSED — NOT APPROVED；批准规划文件修改不激活它们。

保留 `COMMIT_POLICY`、`INTEGRATION`、`EXTERNAL_MUTATIONS` 和项目限制，并明确协调冲突：

- `COMMIT_POLICY: none` 仍禁止提交，即使存在提交授予。
- `INTEGRATION: local-rebase-ff` 不授予远程 push 权限。
- push 或远程修改授予必须先明确协调禁止外部修改的策略。

只请求缺少的权限，并先展示具体操作、范围和预期影响。有效授予可以复用，不重复询问；范围变化须重新批准。
每次受保护操作前检查权限。缺少授权只暂停受影响工作和依赖项；独立且已获授权的工作可在顺序和所有权规则下继续。
必要任务或验收操作未执行时不能收尾；仅有要求声明不意味着必须执行该操作。

### 委派、恢复与限制 {#delegation-resume-and-limits}

每个子智能体获得完整请求与批准上下文，以及按里程碑、分配任务、角色、范围和写入所有权收窄的有效子集。
完整请求中超出该子集的部分只作上下文。只读评审者没有修改权限；子智能体不能扩大或转移授予。
详见[子智能体简报](subagents.md#authorization-in-child-briefs)。

授予只适用于批准的 goal 与任务分配。恢复时使用会话，以及已支持保存这些信息的可信宿主状态，保留批准范围。
不引入审计依赖或仓库批准台账。沉默、状态标记、审计记录、以前的运行和智能体写的状态文字都不能证明批准。
批准来源缺失时应澄清；副作用不确定时不能自动重放。

缺少字段时保留旧行为，不增加权限，也不自动迁移；[Upgrade](upgrade.md) 提供明确采用流程。
宿主和工具权限、沙箱、批准审查及凭据要求仍有效。这些是指令级规则，不是工具级或操作系统强制执行。
Python 运行器和控制器不消费 goal 授予；控制器继续排除外部操作。

## 真正起决定作用的是 COMMIT_POLICY

!!! note "把提交策略写清楚"
    一次 goal 运行期间，`COMMIT_POLICY` 就是**全部**提交规则。
    `AGENTS.md` 可能写着每个状态行都是一个提交单元，但
    `COMMIT_POLICY: none` —— 也就是该协议的默认值 —— 表示完全不产生任何提交。
    这是正确行为，不是规则冲突。

想要常规的逐行提交就写 `task`，想让改动保持未提交就写 `none`。用 `milestone` 将实现与收尾合并提交。
对于并发租约，`GOAL.md` 规定了未发布检查点及所有者最终收尾步骤，以保证只集成一个里程碑提交。
优先级顺序是：请求高于
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
