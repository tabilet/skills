# Tabilet API 控制器 {#tabilet-api-controller}

可选的 `tabilet` 命令会规划一个有界的记忆库工作范围，要求用户对精确方案进行一次确认，随后在本地
Docker 容器中执行获批任务。现有 API 运行器仍是另一条在宿主 shell 中执行的工作流。即使不安装控制器，
七个技能也能独立使用。

控制器使用规范的 Init、Propose 或 Reconcile 技能包作为规划契约。规划工具只读。直接调用技能仍然只负责规划；
控制器的 `confirm` 是一项单独授权，授权范围是展示的精确规划差异和一个有界的本地工作范围。

## 安装并准备 Docker {#install-and-prepare-docker}

需要 Linux、Python 3.9 或更高版本、Git，以及通过 Unix 套接字连接的本地 Docker 守护进程。远程 Docker
上下文和守护进程覆盖变量会被拒绝。Docker Engine 必须支持 `bind-recursive=disabled`。

在 skills 源码检出中安装可执行文件、运行模块和七个经过验证的技能包：

```bash
python3 harness/tabilet_install.py --source skills --controller-source harness
export PATH="$HOME/.local/bin:$PATH"
```

安装器将 `tabilet` 放到 `~/.local/bin`，将控制器模块放到
`~/.local/lib/tabilet/controller`，并将生成的技能哈希清单放到
`${XDG_DATA_HOME:-~/.local/share}/tabilet/skill-bundles`。安装器不会写入项目。运行时会在规划前验证完整技能包，
不需要源码检出或网络。

先在本地准备镜像。例如：

```bash
docker pull python:3.12-slim
```

控制器会在请求模型之前把本地镜像解析为不可变 ID，不会自行拉取或构建镜像。镜像需要包含
`/usr/bin/env`、`/bin/sh` 以及获批验证命令需要的工具。

## 命令 {#commands}

开始一次访谈：

```bash
tabilet chat /absolute/path/to/project --image python:3.12-slim
```

命令会询问使用 Init、Propose 还是 Reconcile，并询问要交付什么。可用 `--operation` 和 `--request` 在命令行
提供答案。提供方设置沿用运行器的环境变量，包括 `LLM_PROVIDER`、`LLM_MODEL`、`LLM_API_KEY`、
`OPENAI_API_KEY` 和 `ANTHROPIC_API_KEY`。

在请求 `confirm` 之前，Tabilet 会展示精确规划差异、选定镜像 ID、里程碑和任务范围、计划提交、外部操作及所有
数值限制。默认限制为 5 行、100 次提供方请求、每行 40 轮模型对话、15 次提交，以及从批准起算的两小时。
Docker 限制为 4 个 CPU、8 GiB 内存、512 个进程，每条命令最多 300 秒。这些是操作上限，不是承诺的美元费用。
可以输入 `reject` 并提供修改意见，以调整范围或限制。输入精确的 `confirm` 之前，不会写项目文件或收据。

这次确认授权一项规划提交，并授权在本地执行有界工作，直至里程碑关闭验证通过。它不授权合并、推送、部署、
发布或其他外部操作。此类操作会记录下来，等待单独处理。必需的人工证据会使工作范围暂停，直到在后续恢复时
提供。模型评审会作为模型证据记录，不会冒充人工证据。

只读查看项目和收据状态：

```bash
tabilet status /absolute/path/to/project
```

对账收据并从已证明的检查点继续：

```bash
tabilet resume /absolute/path/to/project
```

存在多个开放工作范围时，追加 `--receipt UUID`。达到限制后，使用更高数值并单独确认：

```bash
tabilet extend-limit /absolute/path/to/project \
  --limit max_provider_attempts --value 120
```

限额扩展会保留累计用量和批准计时。它要求项目处于干净检查点，并要求用户再次精确输入 `confirm`。

## 收据和恢复 {#receipts-and-recovery}

收据是私有 JSON 文件，位于项目之外的
`${XDG_STATE_HOME:-~/.local/state}/tabilet/receipts/`，权限为 `0600`。状态包括 `approved`、`running`、
`paused`、`needs_review` 和 `completed`。状态命令先读取当前 Markdown，再总结收据；它不会写项目、收据或可选审计库。

恢复流程会在派发之前记录操作意图和用量。它可以继续干净的已准备检查点，也可以记录精确候选提交，前提是其父提交、
树、差异、提交说明、路径、任务状态转换、工作流快照和验证证据都与收据一致。脏状态或无法确定结果的部分操作会进入
`needs_review`。系统不会自动重置、丢弃或重放它。如果无法证明一次可能已经执行的模型请求结果，同样必须人工检查，
即使 Git 显示工作区干净也一样。

按 Ctrl-C 会停止并移除活动容器。干净检查点变为 `paused`；脏或不确定的工作变为 `needs_review`。共享项目锁只保护
Tabilet 启动器，不协调交互式智能体。

## 沙箱和 Git 边界 {#sandbox-and-git-boundary}

每条命令都在新建的无网络容器中运行，具有只读根文件系统、私有可写 `/tmp`，以及 CPU、内存、进程数和命令时间上限。
只有项目以可写方式挂载；项目内 `.git` 以只读方式挂载。提供方凭据、宿主机 home 和 Docker 套接字都不会挂入容器。
守护进程必须位于本地。

此版本支持 `.git` 位于仓库内的标准仓库。它会拒绝链接工作树、子模块、外部 Git 目录、嵌套主机挂载，以及正在使用的
自定义 clean/process 过滤器。宿主 Git 调用会禁用 hook、fsmonitor、外部 diff 和签名，并拒绝可能启动外部命令的仓库设置。
暂存前会检查可能调用 clean/process 过滤器的 Git attributes。内置文本规范化仍然可用。

控制器会检查变更路径是否在获批范围内，并会在宿主提交前验证任务状态转换和必需命令。路径白名单无法证明代码变更在语义上
只涉及所选任务；应在正常代码评审中查看实际差异和测试证据。

## 退出码 {#exit-codes}

控制器专用退出码与运行器代码一起列在[执行指南](../EXECUTION.md#tabilet-controller-exit-codes)：`16` 表示已确认的限制
使工作范围暂停；`17` 表示设置、必需人工证据或需单独处理的外部操作使其暂停；`18` 表示批准输入已过期；`19` 表示共享
启动器锁已占用；`24` 表示提交前验证失败；`25` 表示恢复需要人工检查。

## 可选审计 {#optional-audit}

设置 `TABILET_AUDIT_DB` 时，控制器负责其工作范围的审计生命周期。运行器或技能记录器不得再创建重复运行。审计失败会报告为
缺口，但不会改变收据状态、验证结果或退出状态。Markdown 和私有收据仍是控制器的工作流数据源。

## 验收 {#acceptance}

无凭据的假提供方测试和 Docker 测试分别通过本地或独立 CI 作业运行。Docker 作业要求本地镜像，但不需要提供方凭据。任何付费
实时模型验收都必须单独人工触发，并设置可执行的提供方预算；它不会在 pull request 上自动运行。详见
[模型评估](../MODEL_EVAL.md#tabilet-controller-live-acceptance)。
