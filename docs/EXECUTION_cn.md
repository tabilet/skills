# 执行 Harness

执行 harness（execution harness）是在关键运行条件下反复验证项目的一套可执行入口。它可以是程序、脚本、测试目标、Docker Compose 文件，也可以是 CI job。

Markdown 本身不负责执行 harness。Markdown 的作用是说明如何运行、会启动哪些服务、会产生哪些证据，以及哪些失败属于已知或预期情况。

## 示例

- `make test` 目标：运行所有单元测试。
- `make integration` 目标：启动 PostgreSQL 和 MySQL 容器，运行数据库测试，然后停止容器。
- 使用 `testcontainers-go` 启动真实服务的 Go 测试包。
- 构建 CLI、使用 fixture 输入运行、再 diff 生成结果的脚本。
- 在每个 pull request 上运行同一组命令的 CI 工作流。

## 在这套结构中的位置

- `AGENTS.md` 列出智能体应优先运行的关键 harness 命令。
- `memory-bank/tech-stack.md` 记录前置条件、环境变量、Docker image、端口和命令名称。
- `docs/` 保存较长的搭建、清理和故障排查说明。
- `memory-bank/milestone.md` 可以把某个 harness 通过作为验收条件的一部分。
- `memory-bank/status-<LANE><NN>.md` 记录 harness 相关任务是待处理、已完成、被阻塞还是已取消。

## 智能体执行 Harness

本仓库包含的 [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop) 是一个智能体执行 harness。

它会：

- 调用兼容 OpenAI 的 chat-completions API，或在 `LLM_PROVIDER=anthropic` 时调用 Anthropic Messages API；
- 把项目记忆库任务说明直接嵌入 API 调用；
- 通过命令协议向模型提供 shell 能力；
- 发现全部 `memory-bank/status-<LANE><NN>.md` 状态文件，并把每条状态线的可执行行数和被阻塞行数告知模型；
- 当所有状态线都没有可执行状态行时停止；
- 对被阻塞状态行发出警告；只有当仅剩被阻塞状态行时，才停止并交由人工处理；
- 在用户确认模型命令会进入非沙箱宿主 shell 前拒绝可执行工作；
- 只向 shell 传递精简环境，额外项目变量必须明确放行；
- 要求目标路径正好是 git worktree 根目录；
- 每次运行前确认 git worktree 干净；
- 要求模型提交恰好一条完成或阻塞的可执行状态行；
- 允许单独的评审修复 commit，但拒绝改写历史；
- 如果模型留下未提交变更，则停止；
- 如果模型没有产生 commit，则停止；
- 重试临时 API 故障，报告 provider usage，并限制循环次数和对话大小。

`ALLOW_UNSANDBOXED_SHELL=1` 或 `--allow-unsandboxed-shell` 只是确认宿主访问风险，不提供隔离。命令仍能读取宿主文件和进程并访问网络。请在一次性沙箱和可恢复仓库中运行。provider 凭据不会复制到子进程环境，额外变量须经 `TOOL_ENV_ALLOW` 放行，但这些措施都不会构成安全边界；危险命令阻止清单也只是可以绕过的 guardrail。

运行限制可通过 `LLM_API_TIMEOUT`（默认 `120` 秒）、`LLM_MAX_RETRIES`（首次请求后默认重试 `2` 次）和 `MAX_HISTORY_CHARS`（默认 `500000`）配置。`MAX_TOOL_OUTPUT` 仍是每条命令 stdout 与 stderr 合计的字符预算。

### 退出码

harness 通过退出码表达每一种结果。`3` 到 `7` 是正常的停止条件，而不是崩溃：它们表示循环有意把控制权交回给人。

| 退出码 | 含义 |
|---|---|
| `0` | 没有可执行状态行了，无事可做。 |
| `1` | harness 发生了意外的内部故障。 |
| `2` | 未设置 `LLM_MODEL`，或 `LLM_PROVIDER` 不是 `openai`/`anthropic`。 |
| `3` | 只剩下被阻塞的状态行，需要人工解除阻塞。 |
| `4` | 运行前工作区不干净。请先 commit 或 stash。 |
| `5` | 智能体留下了未提交的修改。 |
| `6` | 智能体没有产生 commit。用于避免空转。 |
| `7` | 达到了 `MAX_RUNS` 上限。 |
| `8` | 已提交结果没有恰好包含一次有效状态行转换。 |
| `9` | 智能体改写了历史或离开了原分支。 |
| `10` | 目标仓库中没有 `AGENTS.md`。 |
| `11` | 没有 `memory-bank/`，或其中没有 `status-<LANE><NN>.md` 状态文件。 |
| `12` | 目标路径不是 git worktree 根目录。 |
| `13` | 无法读取 git `HEAD`。 |
| `14` | 可执行工作没有获得非沙箱 shell 确认。 |
| `20` | API 返回了 HTTP 错误。 |
| `21` | 无法连接到 API。 |
| `22` | API 响应结构与预期不符。 |
| `23` | 模型拒绝请求或没有返回可用文本。 |
| `30` | 模型用完了 `MAX_TURNS` 仍未完成一条状态行。 |
| `31` | 对话超过了 `MAX_HISTORY_CHARS`。 |
| `130` | 运行被终端中断。 |

`10` 到 `14` 表示目标或授权尚未准备好。`20` 到 `23` 是提供方或网络问题，不是项目问题。

## Docker 支持的服务

如果测试需要 MySQL 或 PostgreSQL 等服务，优先使用一次性容器，而不是要求开发者在本机安装服务。

典型流程：

1. 使用 Docker Compose、`testcontainers` 或 harness 脚本启动服务容器。
2. 等待健康检查通过。
3. 运行集成测试。
4. 失败时收集日志。
5. 停止并删除容器。

这样可以让本地开发环境和 CI 环境更接近，减少“只在某台机器上失败”的问题。

## 如何记录一个 Harness

每个执行 harness 都应记录：

- 命令；
- 场景；
- 所需服务；
- 环境变量；
- fixture 或 seed data；
- 预期通过输出；
- 产物和日志位置；
- CI job 名称；
- 已知限制或被阻塞状态行。

当前命令列表应放在 `memory-bank/tech-stack.md`。更长的操作细节应放在 `docs/`。
