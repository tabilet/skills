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
- モデルのコマンドが非サンドボックスのホスト shell で動くことを利用者が承認するまで実行可能な作業を拒否する。
- shell には最小限の環境だけを渡し、追加のプロジェクト変数には明示的な許可を求める。
- 対象パスが git worktree の root そのものであることを求める。
- 各実行前に git worktree が clean であることを確認する。
- モデルに、実行可能な行をちょうど 1 行だけ completed または blocked にして commit させる。
- review 用の別 commit は許すが、履歴の書き換えは拒否する。
- モデルが未 commit の変更を残したら停止する。
- モデルが commit を作らなければ停止する。
- 一時的な API 障害を再試行し、provider usage を報告し、loop 回数と会話サイズを制限する。

`ALLOW_UNSANDBOXED_SHELL=1` または `--allow-unsandboxed-shell` はホストアクセスの承認であり、隔離ではありません。コマンドはホストのファイルやプロセスを読み、ネットワークを利用できます。使い捨て sandbox と復元可能な repository で実行してください。provider の認証情報は子環境へコピーせず、追加変数には `TOOL_ENV_ALLOW` を要求しますが、どちらも security boundary にはなりません。危険コマンドの denylist も回避可能な guardrail にすぎません。

運用上の上限は `LLM_API_TIMEOUT`（既定 `120` 秒）、`LLM_MAX_RETRIES`（最初の試行後に既定 `2` 回再試行）、`MAX_HISTORY_CHARS`（既定 `500000`）で設定できます。`MAX_TOOL_OUTPUT` は各コマンドの stdout と stderr を合わせた文字数上限です。

### 終了コード

harness はすべての結果を終了コードで示します。`3` から `7` はクラッシュではなく正常な停止条件で、ループが意図的に制御を人間へ戻したことを意味します。

| 終了コード | 意味 |
|---|---|
| `0` | 実行可能な行が残っていません。作業なし。 |
| `1` | harness で予期しない内部障害が発生しました。 |
| `2` | `LLM_MODEL` が未設定、または `LLM_PROVIDER` が `openai`/`anthropic` ではありません。 |
| `3` | blocked 行だけが残っています。人間による解除が必要です。 |
| `4` | 実行前に worktree が clean ではありませんでした。先に commit か stash をしてください。 |
| `5` | エージェントが未 commit の変更を残しました。 |
| `6` | エージェントが commit を作りませんでした。空回りを防ぎます。 |
| `7` | `MAX_RUNS` に達しました。 |
| `8` | commit 済みの結果に有効な行の遷移がちょうど 1 つ含まれていません。 |
| `9` | エージェントが履歴を書き換えたか元の branch から移動しました。 |
| `10` | 対象リポジトリに `AGENTS.md` がありません。 |
| `11` | `memory-bank/` がない、またはその中に `status-<LANE><NN>.md` がありません。 |
| `12` | 対象パスが git worktree の root ではありません。 |
| `13` | git `HEAD` を読めませんでした。 |
| `14` | 実行可能な作業に非サンドボックス shell の承認がありません。 |
| `20` | API が HTTP エラーを返しました。 |
| `21` | API に到達できませんでした。 |
| `22` | API のレスポンス形式が想定と異なりました。 |
| `23` | モデルが拒否したか利用可能なテキストを返しませんでした。 |
| `30` | モデルが行を終えないまま `MAX_TURNS` を使い切りました。 |
| `31` | 会話が `MAX_HISTORY_CHARS` を超えました。 |
| `130` | 端末から実行が中断されました。 |

`10` から `14` は対象または承認がまだ整っていないことを示します。`20` から `23` はプロジェクトではなくプロバイダーやネットワークの問題です。

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
