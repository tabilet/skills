# 最小限のエンジニアリング Harness

このリポジトリは、軽量なプロジェクト運用システムを作るためにそのままコピーできる出発点です。中心になる要素は次のとおりです。

- `AGENTS.md`: エージェントの bootstrap guide。
- `memory-bank/`: 現在のプロジェクトの source of truth。
- `evolution/`: 方向転換のバージョン化された履歴。
- 実行 harness: ソフトウェアが動くことを証明する繰り返し可能なコマンド。
- モデル評価 harness: モデル支援のふるまいを測定する繰り返し可能な評価。

目的は文書量を増やすことではありません。人間とエージェントが同じ簡潔な運用マニュアルを共有し、そのマニュアルを実行可能な harness に接続することです。

## このリポジトリに含まれるもの

プロジェクトレベルのサンプルファイル:

- [AGENTS.md](AGENTS.md)
- [memory-bank/product.md](memory-bank/product.md)
- [memory-bank/architecture.md](memory-bank/architecture.md)
- [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
- [memory-bank/milestone.md](memory-bank/milestone.md)
- [memory-bank/status.md](memory-bank/status.md)
- [evolution/prompt-v1.md](evolution/prompt-v1.md)
- [evolution/result-v1.md](evolution/result-v1.md)

ユーザーアカウントレベルのサンプルファイル:

- [.local/bin/tackle-memory-bank-api-loop](.local/bin/tackle-memory-bank-api-loop)
- [.codex/prompts/tackle-next-memory-bank-todo.md](.codex/prompts/tackle-next-memory-bank-todo.md)

Harness 参考資料:

- [実行 Harness](docs/EXECUTION_ja.md)
- [モデル評価 Harness](docs/MODEL_EVAL_ja.md)

## 新規プロジェクトをセットアップする

### 手動

新しいプロジェクトルートで実行します。

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

コピーしたファイルを次の順序で編集します。

1. `memory-bank/product.md`: プロジェクトが何であり、何ではないかを定義する。
2. `memory-bank/architecture.md`: レイアウト、データフロー、境界を定義する。
3. `memory-bank/tech-stack.md`: コマンド、依存関係、harness を定義する。
4. `memory-bank/milestone.md`: 最初の milestone を定義する。
5. `memory-bank/status.md`: 最初の実行可能な行を定義する。
6. `evolution/prompt-v1.md`: 初期方向を記録する。
7. `evolution/result-v1.md`: 現在の開始状態を記録する。
8. `AGENTS.md`: プレースホルダーをプロジェクト固有のコマンドとルールに置き換える。

`README.md` は簡潔でユーザー向けに保ちます。長い参考資料は `docs/` に置きます。

### AI エージェントの助けを借りる

新規プロジェクトでは、サンプルファイルを初期構造として使い、プロダクトを説明したうえで AI エージェントに内容を埋めてもらえます。

警告: これらのファイルを既存プロジェクトにコピーすると、ディスク上の既存ファイルを上書きする可能性があります。先にバックアップするか、現在の作業を commit してください。

新しいプロジェクトルートで実行します。

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

プロダクト、ユーザー、境界、コマンド、最初の milestone が明確になるまでエージェントと対話します。その後、次を埋めるよう依頼します。

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

プロンプト例:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, and make
memory-bank/status.md contain the first actionable milestone rows.
```

## 既存プロジェクトをセットアップする

### 手動

既存プロジェクトでは、書く前に読みます。

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

その後:

1. ルート README、エージェントガイド、docs、パッケージ README、主要パッケージコメントを読む。
2. このリポジトリから `AGENTS.md`、`memory-bank/`、`evolution/` をコピーする。
3. 想像上の書き直しではなく、プロジェクトが既に述べている内容から memory bank を埋める。
4. 安定した長い参考資料を `docs/` に移す。
5. 重複した roadmap/status 情報を `memory-bank/milestone.md` と `memory-bank/status.md` に変換する。
6. 既知の不足は隠さず `status.md` に残す。

### AI エージェントの助けを借りる

既存プロジェクトでは、エージェントに棚卸しと最初の memory-bank draft を任せられます。既に有用な README、docs、パッケージコメント、テスト、CI ファイルがある場合に特に有効です。

警告: これらのサンプルファイルを既存プロジェクトにコピーすると、既存の `AGENTS.md`、`memory-bank/`、`evolution/` を上書きする可能性があります。先に commit する、バックアップを作る、または一時ディレクトリにコピーしてからエージェントに merge を依頼してください。

既存プロジェクトルートで実行します。

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

書く前にプロジェクトを読むようエージェントに依頼します。

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in memory-bank/status.md.
Do not invent product direction that is not supported by the existing project.
```

エージェントは次を行うべきです。

1. 既存の markdown とソースレイアウトを棚卸しする。
2. コマンド、依存関係、テスト、harness を特定する。
3. 現在のプロジェクト事実から memory bank を埋める。
4. 長い参考資料を `docs/` に移す、または要約する。
5. `README.md` を簡潔でユーザー向けに保つ。
6. 未解決の不足を pending または blocked 行として `memory-bank/status.md` に残す。

## Memory Bank を使う

Codex や Claude Code のようなエージェントでは、ユーザー側のワークフローは次のように入力するだけで済みます。

```text
tackle next pending item in memory bank
```

エージェントは `memory-bank/status.md` の次の実行可能な行を見つけ、そのタスクを完了し、必要な検証を実行し、memory bank を更新し、範囲の明確な git commit を作るべきです。その行が milestone の最後の未完了項目である場合、エージェントは先に `memory-bank/milestone.md` の milestone review を実行します。その review では、プロダクト方向、アーキテクチャ境界、milestone 目標、または public/private contract の方向が実質的に変わったため `evolution/` に新バージョンが必要かも判断します。

内部では、通常のエージェントワークフローは次のとおりです。

1. `AGENTS.md` を読む。
2. `AGENTS.md` に列挙された順序で memory bank ファイルを読む。
3. 範囲の明確なタスクまたは status 行を 1 つだけ処理する。
4. scope、architecture、tools、milestone acceptance、status が変わった場合、対応する memory-bank ファイルを更新する。
5. 検証が通った後にだけ、行を `[+]` にする。
6. その行を範囲の明確な commit として提出する。
7. milestone が完了したら、続ける前に `memory-bank/milestone.md` の milestone review 手順を実行する。
8. `evolution/` を確認し、review が実際の方向、境界、milestone、contract の変化を見つけた場合にだけ新バージョンを追加する。

Status 行は次のマーカーを使います。

| 記号 | 意味 |
|---|---|
| `[ ]` | 未着手 |
| `[+]` | 完了 |
| `[~]` | 進行中 |
| `[!]` | ブロック中 |
| `[X]` | キャンセル済み |

## API Harness をインストールする

API harness は、この memory-bank 構造に従う任意のプロジェクトを駆動できるため、アカウントレベルのツールです。

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/.local/bin/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/.codex/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

1 行だけ実行する:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

ループを実行する:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

OpenAI 互換プロバイダーを使う:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.5 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

ローカルの OpenAI 互換サーバーを使う:

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

この harness はタスク指示を API prompt に埋め込みます。Codex CLI は呼び出さず、実行時に外部 prompt ファイルも必要としません。prompt ファイルは、人間とエージェントが再利用できる参考として含まれています。

## この Harness の意味

通常のプロジェクト作業では、`tackle-memory-bank-api-loop` は実行 harness です。リポジトリに対してエージェントを繰り返し実行し、制御されたコマンドプロトコルで shell アクセスを与え、実行間の git 状態を確認します。

モデル、プロンプト、pass rate、review findings、cost、latency、regressions を横断して結果を採点するときにだけ、model eval harness の一部になります。

詳しく読む:

- [実行 Harness](docs/EXECUTION_ja.md)
- [モデル評価 Harness](docs/MODEL_EVAL_ja.md)

## メンテナンスルール

- `AGENTS.md` は短く保つ。
- プロジェクトの `README.md` はユーザー向けに保つ。
- 長い説明は `docs/` に置く。
- 現在の事実は `memory-bank/` に置く。
- 過去の方向スナップショットは `evolution/` に置く。
- コードや docs の変更を説明する同じ commit で memory を更新する。
- 実際の方向転換がある場合にだけ、新しい evolution バージョンを追加する。
- 有用な内容を merge したら、重複 docs は削除する。
