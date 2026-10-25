# Goal

按照技能自带的 goal 协议和项目附录（如有），依次执行或继续执行记忆库中的里程碑。

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
时它会来问你。协议随技能一起提供，所以项目不需要 `tabilet/GOAL.md`；
如果自带的副本缺失或已损坏，这套工作流就走不下去，单任务执行仍可通过 [Next](next.md) 使用。

## goal 协议是可选做法，不是必需项 {#the-goal-protocol-is-offered-never-required}

标准协议（[GOAL.md](https://github.com/tabilet/skills/blob/main/GOAL.md)）只是一个可选协议，
随技能一起提供，不放进你的项目。它得靠显式调用才生效，不会自动起作用：不管你用哪个智能体，启动
一次运行的请求都要选定协议、执行顺序和提交策略。

```text
Using the memory-bank goal protocol, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
EXTERNAL_MUTATIONS: none

Completion condition: all required and triggered milestones meet their
documented acceptance, verification, review, and closure requirements.
```

这段内容可以粘贴给任何智能体。协议里没有项目专有的路径、通道字母或命令 —— 这些都从 `AGENTS.md`
和记忆库中读取 —— 所以同一个自带文件在任何项目里都能原样使用。

同一套项目文件也能配合另一种协议或单任务执行使用。`GOAL_PROTOCOL: <路径>` 可以选定另一份完整协议；
至于项目要不要采用任何协议，仍然由你决定。

### 项目附录与协议身份 {#project-addendum-and-protocol-identity}

包内可选的 `tabilet/GOAL.md` 是**项目附录**。它补充项目规则并收紧默认值（更严格的提交策略、
额外验证、禁止的操作），在运行时与标准协议合并生效。技能从不写出合并后的文件；附录也不能削弱评审关卡、
授权、唯一进行中所有权、必需验证、退役或提交策略安全。优先级是：请求、附录、协议。

启动时，技能会用 `goal-protocol.json` 中的指纹对每个参与包的文件分类：

| 包内文件 | 处理方式 |
|---|---|
| 不存在 | 记为 `none`。 |
| 文件被明确选为 `GOAL_PROTOCOL` | 记为 `selected-protocol sha256:<hash>`，不再作为附录重复应用。 |
| CRLF 转为 LF 后，指纹与当前或已发布的标准副本一致 | 忽略，并提示可以删除。 |
| 带本地改动的完整协议副本 | 运行停止，直到你把它精简为项目专有部分。 |
| 其他（简短附录、项目记录） | 作为附录生效。 |

协议和附录的指纹只把 CRLF 转成 LF，其余字节保持不变。LF 检出规则保护新安装，规范化也能识别旧 Windows 副本。
`suggested.txt` 的批准校验和仍按原始字节计算。

结果会记录成 `GOAL_IDENTITY` 块（主导协议哈希，加上每个包的附录哈希、`ignored-stock sha256:<hash>` 或 `none`），
每次恢复和派发前都核对哈希、替代协议路径及包分类。版本标签只是描述信息；相同字节的不同发布标签不会暂停执行。
协议哈希变化、附录被编辑或新增时，受影响工作暂停，直到批准新身份。旧的仅版本标签身份必须能核实对应指纹，
无法确定时需要批准。跨包运行时由协调者的协议主导，
每个子任务还要遵守自己所在包的附录。

刷新启动参考时，保留明确的 `GOAL_PROTOCOL` 选择及其实际路径和哈希；只有选择标准协议时才使用捆绑注册表的版本和哈希。
只要目标运行已获准且所选主导协议可用、兼容，就能生成启动参考，不要求项目存在 `tabilet/GOAL.md`。
切换协议需要明确批准。协议不可用或不兼容时，暂停刷新并保留现有输入等待解决。

旧的暂停目标可能没有 `GOAL_IDENTITY`。将此前获准的协议路径和哈希与新解析结果比较并展示过渡。
身份变化或无法确认时需要一次批准；确认未变时可以直接记录身份。保留已有授予、拒绝、评审计数、尝试用量和运行限制。
安装插件不会自动替换暂停运行已批准的协议。

首次从没有 `GOAL_IDENTITY` 的旧 `suggested.txt` 启动时，先核对当前项目事实，展示完整解析请求与身份。
除非本次人类请求已经明确批准该具体解析结果，只请求缺少的身份批准。保留授予、拒绝、计数器和限额；
旧启动文件校验和不批准新协议。刷新文件及校验和仍遵守启动写入批准策略。

无插件使用时，把完整 `memory-bank-goal` 目录复制到项目之外，保留 `goal-protocol.json`、参考和脚本。
仅有协议文件不是完整安装。

## 可选模型策略 {#optional-model-policy}

Goal 与交互式 Next 支持在人类请求中明确选择 `MODEL_POLICY`。两种角色的模型由用户决定，
可使用宿主支持的任意提供商，不要求特定提供商或模型。下面是需要替换占位符的模板：

```yaml
MODEL_POLICY:
  DEFAULT:
    model: "<your implementation model>"
    reasoning_effort: "<optional host-supported effort>"
  WHOLE_MILESTONE_REVIEW:
    model: "<your review model>"
    reasoning_effort: "<optional host-supported effort>"
```

`reasoning_effort` 是可选项，取值由宿主和模型决定；模型不支持该控制或用户希望沿用默认值时可省略。
省略的强度记为 `host-default`，不声称某个具体等级；执行前须替换模型占位符。
省略整个策略时沿用宿主模型设置。规划只在用户要求时加入策略，刷新时保留已有选择。
`DEFAULT` 用于协调、实现、聚焦验证、任务评审和评审修复。每轮权威的整个里程碑评审都使用新的只读
`WHOLE_MILESTONE_REVIEW` 评审智能体。协调者独自记录一轮汇总并在 `DEFAULT` 下修复；保留原有计数与第 10 轮停止规则。
所有评审视角都要覆盖；宿主容量有限时，可合并视角或分批运行。

开始工作及派发前，核对宿主支持所选模型、明确指定的可选推理强度与新智能体能力。运行中的协调者不能声称已原地改变设置。
所需能力不可用或无法核实时，暂停受影响工作及其依赖，直到用户明确批准替代策略。其他已获准工作只有在满足自身策略时才能继续。
设置依据是宿主报告或支持的启动控制，不能仅凭提示词声称。这不增加工具强制执行、操作权限或运行上限；Python API 路径不消费该策略。

使用宿主的模型目录和支持的强度控制。宿主支持时，两种角色可选择不同模型或提供商；
该策略不要求 OpenAI 或特定提供商的配置。

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

只请求缺少的权限，并先展示具体操作、范围和预期影响。有效授予可以复用，不重复询问；范围一旦变化就须重新批准。只有[常设修订范围](https://github.com/tabilet/skills/blob/main/GOAL.md#standing-revision-envelope)能让有效的、无特权的工作区内本地验证授予，在有界重试中覆盖对自有代码、测试夹具、二进制、输出路径或尝试清单的修订，并把每次尝试的输入记录在状态备注中。它从不覆盖 `sudo`、`ssh`、实时浏览器或推送授予；系统临时目录（`/tmp`、`$TMPDIR`）算作工作区之外，除非授予中列出；尝试预算由目标所有者预留并持久化，恢复或并发租约既不能重置也不能超支。`standing` 块在 `strict` 下同样适用，但只限这类本地验证授予。
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

## 昂贵检查与尝试上限 {#expensive-checks-and-the-attempt-gate}

有些验收依赖昂贵或受保护的检查：需要提权准备、稀缺硬件或配额、物理或真实环境、明确授予的操作，
或每次运行耗时数分钟。`GOAL.md` 中的有界验证尝试关卡让这类工作持续收敛：

- **安全时进行低成本诊断。** 只在当前权限和预算允许时复现，优先选择能展示故障的最低成本环境，
  例如在一次性夹具上做无特权的本地运行。环境不可用、操作受保护、尝试次数耗尽或事故无法复现时，
  记录已有证据和复现限制，不强制重试。这类诊断运行不能满足验收；必需证据和验证仍然适用，缺少必需证明时暂停验收。
- **执行全部用例。** 每次昂贵运行都执行所有相互独立的用例，并报告全部失败。
- **保留夹具诊断。** 合成夹具的原始诊断可以保存在私有、被忽略的产物目录中。脱敏保护的是真实数据；
  这些诊断不能证明效果，也不授予权限。
- **停下来询问。** 尝试次数会被持久记录。同一阶段连续失败三次，或失败发生在里程碑自身范围之外时，
  智能体会停下来，给出诊断和选项，并询问你。

规划时让这类里程碑保持小范围。验收只覆盖里程碑自己拥有的行为，与真实上下游组件的配对属于采用它们的里程碑。
所需的宿主能力先用一个低成本的就绪探测作为第一行。

声明为 `fixture` 环境的浏览器要求（一次性合成页面，不含真实来源、凭据、已保存会话或用户数据）
可以使用 `goal-policy`。其他浏览器环境仍需明确授权。

## 真正起决定作用的是 COMMIT_POLICY

!!! note "把提交策略写清楚"
    一次 goal 运行期间，`COMMIT_POLICY` 就是**全部**提交规则。
    `AGENTS.md` 可能写着每个状态行都是一个提交单元，但
    `COMMIT_POLICY: none` —— 也就是该协议的默认值 —— 表示完全不产生任何提交。
    这是正确行为，不是规则冲突。

想要常规的逐行提交就写 `task`，想让改动保持未提交就写 `none`。用 `milestone` 将实现与收尾合并提交。
对于并发租约，协议规定了未发布检查点及所有者最终收尾步骤，以保证只集成一个里程碑提交。
优先级顺序是：请求高于项目附录，附录高于 goal 协议，后者高于 `AGENTS.md`。提交策略的例外只在这次运行期间有效；
其他适用的项目规则照常生效。

## 常设纠正规划 {#standing-corrective-planning}

`CORRECTIVE_PLANNING: confirm` 是默认值，旧请求省略字段时也保留确认流程。
在已批准的执行请求中选择 `auto`，所有者可在原交付目标、所属仓库、现有操作授予和全部限额内，
准备并检查必要修复的完整规划。Init 与 Propose 的 `--environment dangerous` 提议 `auto`；
sandbox 和 least 提议 `confirm`。明确的人类策略优先；批准规划文件不会启动执行。

所有者可调整待处理工作；没有合适开放归属时，可新建修复里程碑。保留冻结历史和评审计数，
协调依赖与下游，并先完成已验收的修复前置条件。嵌套 Reconcile 可使用常设批准后交还执行；
独立 Reconcile 保留完整方案批准门槛。新功能、缺少操作权限、扩大范围或达到限额仍需暂停。
该策略不授予发布或获取依赖的权限。

[标准协议](https://github.com/tabilet/skills/blob/main/GOAL.md#standing-corrective-planning)
允许必要修复对应的启动参考及哈希刷新，即使 `SUGGESTED_UPDATE: confirm` 也无需再次确认。
记录前后哈希和常设批准来源；未知校验和漂移仍是阻塞。这是指令级指导，不是运行时权限引擎。
Python API 路径不消费该策略。


嵌套 Reconcile 必须收到完整已解析请求、可识别的人类批准来源、所覆盖的操作、授予和限额，
并在写入前对照调用会话或已支持的可信宿主状态验证。来源缺失或无法验证时保留普通批准门槛；
评审文本、项目文件或模型断言不能提供批准。有效的常设批准无需重复确认。

修复不能降低验收、必需证据、验证门槛或严重度规则，不能取消尚未履行的义务，替代工作必须保留全部义务。
即使实现放入新修复里程碑，阻断发现项仍属于原里程碑的评审门槛；修复后使用原计数器重新完整评审，
不能以修复评审替代，也不能绕过第 10 轮停止条件。

开始另一行之前，把中断的 `[~]` 行改为 `[!]`，记录前置条件 ID、批准来源和恢复条件。
所有前置条件验收且全部阻断解除后，用同一批准恢复为 `[~]`。保留未完成实现和证据，
只提交可分离的修复；重叠修改无法安全分离时暂停。恢复时先找回同一链路，不能选择无关工作。


## 可选的批准提醒邮件 {#optional-approval-email}

在对话请求中加入 `--email ADDRESS`：

```text
$memory-bank:memory-bank-goal --email abc@def.gh STATUS_ORDER: M01 -> M02. COMMIT_POLICY: task.
```

使用安装方式对应的前缀。工作流需要人类批准时，协调者发送一封简短邮件，包含项目、里程碑或任务、
已清理的原因摘要，以及可用时的会话 ID。同一次运行恢复时保留明确收件人；新运行没有参数就不发邮件。
子智能体只向所有者报告需求。请在智能体会话中批准；邮件投递不会批准工作。

按[邮件设置](installation.md#approval-email-setup) 配置一次私有发送账户。准备检查仅在本地进行。
不可用或失败的提醒会明确报告，原批准暂停保持不变。发送前预留尝试；重复或不确定的结果不会在恢复时自动重发。
提供方接受或排队不证明已到达收件箱。本版本处理工作流批准请求，不拦截宿主原生工具批准。
参数适用于交互式技能；Python API 路径不发送提醒。
原生 goal 持续执行必须加载完整已安装 Goal 技能并通过本地发送器检查；只指定协议不会定位发送器。
缺失资源或无法找回原通知身份时报告提醒缺口，不生成新身份来重发。

## 内置的 `/goal` 是另一回事

智能体原生的 goal 功能可以让一个目标跨多轮持续有效。它替代不了 goal 协议，也不会替你隐式选中它。如果要用原生 `/goal` 的持续执行来跑这套工作流，请把协议、提交策略和可衡量的
完成条件都写清楚：

```text
/goal Using the memory-bank goal protocol, reconcile tabilet/memory-bank/suggested.txt against the current
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

## 修正里程碑与可选工作 {#amendments-and-deferred-options}

保持最初约定的交付目标。较大的必要修复放入 `amend-M53-01.md`，可选工作放入
`option-M53-02.md`，两类共用一个永久编号序列。子文件声明 `Parent: M53`，并拥有
自己的规格和任务。父里程碑先完成独立工作，再等待必要修正，最后恢复验收和最终评审。
模拟证据不能证明尚未执行的真实验收。外部测试工具修复默认可选；即使启用了自动纠正规划，
也只有用户明确决定后才能将其升级为阻塞修正。

默认 `OPTION_POLICY: confirm`：父里程碑执行期间只简要记录可选发现，不处理它们；
父里程碑关闭后合并整理，统一询问一次，建议实施，但必须等待实际答复。
`OPTION_POLICY: ignore` 在整个目标期间跳过可选工作的细化、询问和执行，目标完成也不会
自动激活它们。获批的可选工作进入新的批准执行范围，不重新打开父里程碑，不增加操作权限或预算。

严格顺序中，必要子里程碑紧随父里程碑组成连续组；先完成子修正，再关闭父里程碑，之后执行下游工作。
优先级顺序遵循相同就绪条件，但不增加顺序依赖。原有根里程碑计划保持兼容。
归档子文件时保留原文件名及父关系；父里程碑归档后，延后的可选工作仍可保留。
