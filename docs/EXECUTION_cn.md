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
- 每次运行前确认 git worktree 干净；
- 要求模型提交自己的工作；
- 如果模型留下未提交变更，则停止；
- 如果模型没有产生 commit，则停止；
- 限制循环运行次数。

### 退出码

harness 通过退出码表达每一种结果。`3` 到 `7` 是正常的停止条件，而不是崩溃：它们表示循环有意把控制权交回给人。

| 退出码 | 含义 |
|---|---|
| `0` | 没有可执行状态行了，无事可做。 |
| `2` | 未设置 `LLM_MODEL`，或 `LLM_PROVIDER` 不是 `openai`/`anthropic`。 |
| `3` | 只剩下被阻塞的状态行，需要人工解除阻塞。 |
| `4` | 运行前工作区不干净。请先 commit 或 stash。 |
| `5` | 智能体留下了未提交的修改。 |
| `6` | 智能体没有产生 commit。用于避免空转。 |
| `7` | 达到了 `MAX_RUNS` 上限。 |
| `10` | 目标仓库中没有 `AGENTS.md`。 |
| `11` | 没有 `memory-bank/`，或其中没有 `status-<LANE><NN>.md` 状态文件。 |
| `12` | 目标路径不在 git worktree 中。 |
| `13` | 无法读取 git `HEAD`。 |
| `20` | API 返回了 HTTP 错误。 |
| `21` | 无法连接到 API。 |
| `22` | API 响应结构与预期不符。 |
| `30` | 模型用完了 `MAX_TURNS` 仍未完成一条状态行。 |

`10` 到 `13` 表示目标仓库尚未准备好。`20` 到 `22` 是提供方或网络问题，不是项目问题。

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
