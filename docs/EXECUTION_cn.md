# Execution Harness

Execution harness 是在重要条件下重复运行项目的一种方式。它通常是程序、脚本、测试 target、Docker Compose 文件或 CI job。

Markdown 本身不会执行 harness。Markdown 负责告诉人和 agent 如何运行它、它会启动哪些服务、会产生什么证据，以及哪些失败是已知或预期的。

## 示例

- `make test` target：运行所有单元测试。
- `make integration` target：启动 PostgreSQL 和 MySQL 容器，运行数据库测试，然后停止容器。
- 使用 `testcontainers-go` 启动真实服务的 Go 测试包。
- 构建 CLI、用 fixture 输入运行它、再 diff 生成结果的脚本。
- 在每个 pull request 上运行同样命令的 CI workflow。

## 它放在哪里

- `AGENTS.md` 列出 agent 应该运行的关键 harness 命令。
- `memory-bank/tech-stack.md` 记录前置条件、环境变量、Docker image、端口和命令名称。
- `docs/` 保存长篇 setup、teardown 和 troubleshooting 说明。
- `memory-bank/milestone.md` 可以把某个 harness 通过作为 acceptance 的一部分。
- `memory-bank/status.md` 记录 harness 相关行是 pending、complete、blocked 还是 cancelled。

## Agent Execution Harness

本仓库包含的 [.local/bin/tackle-memory-bank-api-loop](../.local/bin/tackle-memory-bank-api-loop) 是一个 agent execution harness。

它会：

- 调用兼容 OpenAI 的 chat-completions API；
- 把 memory-bank 任务说明直接嵌入 API 调用；
- 给模型一个 shell 命令协议；
- 在没有可执行行时停止；
- 在存在 blocked 行时停止；
- 每次运行前检查 git worktree 是否干净；
- 要求模型提交自己的工作；
- 如果模型留下未提交变更就停止；
- 如果模型没有产生 commit 就停止；
- 限制循环次数。

## Docker 支持的服务

对于需要 MySQL 或 PostgreSQL 等服务的测试，优先使用一次性容器，而不是要求本机安装服务。

典型流程：

1. 用 Docker Compose、`testcontainers` 或 harness 脚本启动服务容器。
2. 等待 health check 通过。
3. 运行集成测试。
4. 失败时收集日志。
5. 停止并删除容器。

这样可以让本地开发机器和 CI 环境更接近。

## 如何记录一个 Harness

每个 execution harness 应该记录：

- command；
- scenario；
- required services；
- environment variables；
- fixture or seed data；
- expected passing output；
- artifact and log locations；
- CI job name；
- known limitations or blocked rows。

当前命令列表属于 `memory-bank/tech-stack.md`。更长的操作细节属于 `docs/`。
