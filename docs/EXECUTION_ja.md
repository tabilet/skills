# 実行 Harness

実行 harness（execution harness）は、重要な条件下でプロジェクトを繰り返し実行するための仕組みです。通常はプログラム、スクリプト、テストターゲット、Docker Compose ファイル、または CI job として用意します。

Markdown 自体は harness を実行しません。Markdown は、人間とエージェントに対して、実行方法、起動するサービス、生成される証拠、既知または想定済みの失敗を説明します。

## 例

- すべてのユニットテストを実行する `make test` ターゲット。
- PostgreSQL と MySQL のコンテナを起動し、データベーステストを実行してからコンテナを停止する `make integration` ターゲット。
- `testcontainers-go` で実サービスを起動する Go テストパッケージ。
- CLI をビルドし、fixture 入力で実行し、生成結果を diff するスクリプト。
- すべての pull request で同じコマンドを実行する CI workflow。

## この構造での位置づけ

- `AGENTS.md` には、エージェントが実行すべき重要な harness コマンドを列挙します。
- `memory-bank/tech-stack.md` には、前提条件、環境変数、Docker image、ポート、コマンド名を記録します。
- `docs/` には、長めのセットアップ、後片付け、トラブルシューティングのメモを置きます。
- `memory-bank/milestone.md` では、harness の成功を受け入れ条件の一部にできます。
- `memory-bank/status-<LANE><NN>.md` には、harness 関連の行が pending、complete、blocked、cancelled のどれかを記録します。

## エージェント実行 Harness

同梱の [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop) は、エージェント実行 harness です。

これは次を行います。

- OpenAI 互換の chat-completions API、または `LLM_PROVIDER=anthropic` のとき Anthropic Messages API を呼び出す。
- memory-bank のタスク指示を API 呼び出しに直接埋め込む。
- モデルに shell コマンドプロトコルを与える。
- すべての `memory-bank/status-<LANE><NN>.md` レーンファイルを検出し、各レーンの実行可能行数と blocked 行数をモデルに伝える。
- どのレーンにも実行可能な行が残っていなければ停止する。
- blocked 行は警告として報告し、blocked 行だけが残った場合にのみ人間のレビューのために停止する。
- 各実行前に git worktree が clean であることを確認する。
- モデルに自身の作業を commit させる。
- モデルが未 commit の変更を残したら停止する。
- モデルが commit を作らなければ停止する。
- ループ回数を制限する。

### 終了コード

harness はすべての結果を終了コードで示します。`3` から `7` はクラッシュではなく正常な停止条件で、ループが意図的に制御を人間へ戻したことを意味します。

| 終了コード | 意味 |
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

`10` から `13` は対象リポジトリがまだ整っていないことを示します。`20` から `22` はプロジェクトではなくプロバイダーやネットワークの問題です。

## Docker で支えるサービス

MySQL や PostgreSQL などのサービスが必要なテストでは、ローカルサービスのインストールを必須にするのではなく、使い捨てコンテナを優先します。

典型的な流れ:

1. Docker Compose、`testcontainers`、または harness スクリプトでサービスコンテナを起動する。
2. health check が通るまで待つ。
3. integration test を実行する。
4. 失敗時にログを収集する。
5. コンテナを停止して削除する。

これにより、ローカルの開発マシンと CI 環境を近づけられます。

## Harness の記録方法

各実行 harness について、次を記録します。

- コマンド
- シナリオ
- 必要なサービス
- 環境変数
- fixture または seed data
- 期待される成功時の出力
- artifact とログの場所
- CI job 名
- 既知の制限または blocked 行

有効なコマンド一覧は `memory-bank/tech-stack.md` に置きます。より長い運用詳細は `docs/` に置きます。
