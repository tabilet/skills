# 最小限のエンジニアリング Harness

コーディングエージェントは、プロジェクトが自分自身を説明できるとき——これが何で、何が終わっていて、次が何か——うまく動きます。そのための一般的な方法は、CLI、スキャフォールド、スラッシュコマンド群、生成された成果物のフォルダといったシステムを丸ごと導入することです。半年後には、自分のコードと同じくらいそのシステムのファイルを保守していて、プロジェクトは自分の規約ではなくそのシステムの規約の中で生きています。

このリポジトリは逆に賭けます。markdown ファイル 5〜6 個をプロジェクトにコピーし、完全にあなたのものにする。インストールする CLI も、覚える語彙も、必須のものもありません。役目を終えた日に削除してかまいません。

**ここにあるものは動きません。** このリポジトリはコピー*元*となる出発点です——`template/` をプロジェクトへ、`harness/` は必要ならホームディレクトリへ。その後、あなたのプロジェクトはこのリポジトリに依存せず、リンクも残りません。それが狙いです。手元に残るものはあなたのものです。

プロジェクトは最終的にこうなります。

```text
your-project/
├── AGENTS.md              エージェントが最初に読むもの
├── memory-bank/           いま真であること
│   ├── product.md         これが何で、何ではないか
│   ├── architecture.md    レイアウト、データフロー、境界
│   ├── tech-stack.md      コマンド、依存関係、検証方法
│   ├── milestone.md       milestone と受け入れ基準
│   └── status-M01.md      milestone ごとに 1 ファイル、タスクごとに 1 行
└── evolution/             方向が変わった理由と時期
```

本文を通じて **harness** とは、何かが動くことを証明する繰り返し実行可能なコマンド——テストスイート、CI job、スクリプト——を指します。プロジェクトは自分の harness を `tech-stack.md` に定義します。このリポジトリはさらに任意の harness を 1 つ同梱しています。API 経由でエージェントを動かし、memory bank を無人で進めるループです。

他の言語版: [🇬🇧 English](README.md) · [🇨🇳 中文](README_cn.md) · [🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## はじめに

**memory bank を使うのに必要なのは `git` だけです。** memory bank はただの markdown なので、日々のワークフロー——Codex や Claude Code のようなエージェントに次の未処理項目を任せること——にランタイムは一切不要です。

**Python 3 が必要なのは任意の API harness だけ**です。[API Harness をインストールする](#api-harness-をインストールする)で説明する無人実行ループのことです。標準ライブラリしか使わないため、`pip` で入れるものはありません。すでに使っているエージェントから memory bank を動かすなら、まるごと省略できます。

後述の既存プロジェクト向け手順では、最初の棚卸しに [ripgrep](https://github.com/BurntSushi/ripgrep)（`rg`）も使います。

このリポジトリを一度 clone してください。以下の `cp` コマンドの `/path/to/skills` は、その clone を指します:

**最短の方法に clone は不要です。** 3 つのコマンドをインストールし、`/memory-bank-init` に質問させて memory bank を書かせます:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

プロジェクト（空でも既存でも）で `/memory-bank-init` を実行し、質問に答えてください。Codex での同等の方法と、ファイルをそのまま使う選択肢は[3 つのコマンドをインストールする](#3-つのコマンドをインストールする)にあります。

ファイルを手作業で扱う場合は、このリポジトリを一度 clone します。以下の `cp` コマンドの `/path/to/skills` はその clone を指します:

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

clone 自体で何かを実行することはありません。中からファイルをコピーして使います。`template/` はプロジェクトへ、`harness/` はホームディレクトリへコピーします。

## このリポジトリに含まれるもの

プロジェクトレベルのサンプルファイル:

- [template/AGENTS.md](template/AGENTS.md)
- [template/GOAL.md](template/GOAL.md) — 複数 milestone の実行プロトコル
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

ユーザーアカウントレベルのサンプルファイル:

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

3 つのスラッシュコマンドは [harness/skills/](harness/skills/) にあります。Claude Code と Codex は同じ `SKILL.md` 形式を読むので、コマンドごとにソースは 1 つです:

- [memory-bank-init](harness/skills/memory-bank-init/SKILL.md)
- [memory-bank-next](harness/skills/memory-bank-next/SKILL.md)
- [memory-bank-goal](harness/skills/memory-bank-goal/SKILL.md)

`.claude-plugin/` には、これらを Claude Code プラグインとしてインストールするためのマニフェストが入っています。`template/` にベンダー固有のファイルはありません。

Harness 参考資料:

- [実行 Harness](docs/EXECUTION_ja.md)
- [モデル評価 Harness](docs/MODEL_EVAL_ja.md)

## 記入後の memory bank の例

テンプレートはプレースホルダーのままです。以下は同じ memory bank を小さなショッピングサービス向けに記入したもので、道順の前に行き先を見せます。

`memory-bank/product.md` は最初 `[project-name] is [one or two sentences describing the project]` で、記入後はこうなります。

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

`memory-bank/milestone.md` は他のすべての構成を決めるファイルです。レーンに名前を与え、それぞれが何を担当するかを示します。

```markdown
## Status ID Pattern

M01, M02, ...   Default lane: cross-cutting work, infrastructure, chores
S01, S02, ...   Storefront: cart, checkout, product pages
A01, A02, ...   Accounting: pricing, invoices, payment reconciliation

Lane meanings:

- `M`: anything that does not belong to a product domain.
- `S`: shopping surface. Owned by the storefront team.
- `A`: money. Changes here need a second reviewer.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| S01 | [status-S01.md](status-S01.md) | Cart and checkout. |
| A02 | [status-A02.md](status-A02.md) | Payment contract. |

## S01 - Cart And Checkout

**Goal.** A shopper can fill a cart and complete a purchase.

**Scope.**

- Cart CRUD behind `POST /cart`.
- Line-item and order-total pricing.
- Handoff to the payment provider.

**Acceptance.** `make test` passes, and a scripted end-to-end purchase
succeeds against the staging payment sandbox.
```

続いて `memory-bank/status-S01.md` がその milestone の行を持ちます。

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**各マーカーを囲むバッククォートは必須です。** harness が一致させるのは `` `[ ]` `` であり、`[ ]` ではありません。`| Item | [ ] | Notes |` と書かれた行は黙って無視され、harness は「No actionable memory-bank rows remain」と表示して正常終了します。作業が終わったかのように見えてしまいます。

## 新規プロジェクトをセットアップする

[3 つのコマンド](#3-つのコマンドをインストールする)をインストールしていれば、`/memory-bank-init` がこの節の作業をすべて行います。質問し、レーンと milestone の案を提示し、承認を待ってから、記入済みのファイルを書きます。以下の 2 つの手順は、同じ作業を手作業で行うものです。

### 手動

新しいプロジェクトルートで実行します。

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

コピーしたファイルを次の順序で編集します。

1. `memory-bank/product.md`: プロジェクトが何であり、何ではないかを定義する。
2. `memory-bank/architecture.md`: レイアウト、データフロー、境界を定義する。
3. `memory-bank/tech-stack.md`: コマンド、依存関係、harness を定義する。
4. `memory-bank/milestone.md`: 最初の milestone を定義する。
5. `memory-bank/status-M01.md`: 最初の実行可能な行を定義する。後述の「記入後の status ファイルの例」を参照。マーカーのバッククォートが重要です。
6. `evolution/prompt-v1.md`: 初期方向を記録する。
7. `evolution/result-v1.md`: 現在の開始状態を記録する。
8. `AGENTS.md`: プレースホルダーをプロジェクト固有のコマンドとルールに置き換える。

`README.md` は簡潔でユーザー向けに保ちます。長い参考資料は `docs/` に置きます。

### エージェントを接続する

`AGENTS.md` は Agentic AI Foundation が管理する[オープンなベンダー中立標準](https://agents.md)です。ほとんどのコーディングエージェントは設定なしでこれを読みます。Codex, Cursor, Gemini CLI, GitHub Copilot, Devin, Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, Amp などが対応しています。

`template/` には特定ベンダー向けのファイルを一切含めていません。別のファイル名を読むエージェントを使っている場合は、いずれずれていく複製を持つのではなく、1 行で `AGENTS.md` に橋渡ししてください。

| エージェント | 橋渡し |
|---|---|
| 上記のいずれか | 対応不要 |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`、または `@AGENTS.md` と書いた `CLAUDE.md` |
| 独自ファイルを読むその他のツール | 同様に symlink か import で `AGENTS.md` を指す |

Windows で symlink を作るには管理者権限か開発者モードが必要なので、import 形式をおすすめします。

### AI エージェントの助けを借りる

新規プロジェクトでは、サンプルファイルを初期構造として使い、プロダクトを説明したうえで AI エージェントに内容を埋めてもらえます。

警告: これらのファイルを既存プロジェクトにコピーすると、ディスク上の既存ファイルを上書きする可能性があります。先にバックアップするか、現在の作業を commit してください。

新しいプロジェクトルートで実行します。

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

プロダクト、ユーザー、境界、コマンド、最初の milestone が明確になるまでエージェントと対話します。その後、次を埋めるよう依頼します。

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status-M01.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

プロンプト例:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the status
ID lanes in memory-bank/milestone.md, and make memory-bank/status-M01.md contain
the first actionable milestone rows.
```

## 既存プロジェクトをセットアップする

`/memory-bank-init` はこのケースにも対応し、しかも素のプロンプトより上手くこなします。リポジトリがすでに述べていること（README、テスト、ビルドや CI の設定）を読み、そこから分からない決定だけを尋ねます。多くの場合、非目標、境界、作業の順序です。

### 手動

既存プロジェクトでは、書く前に読みます。

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

その後:

1. ルート README、エージェントガイド、docs、パッケージ README、主要パッケージコメントを読む。
2. このリポジトリから `template/` をコピーする。
3. 想像上の書き直しではなく、プロジェクトが既に述べている内容から memory bank を埋める。
4. 安定した長い参考資料を `docs/` に移す。
5. 重複した roadmap/status 情報を `memory-bank/milestone.md` と `memory-bank/status-<LANE><NN>.md` に変換する。
6. 既知の不足は隠さず `status-<LANE><NN>.md` に残す。

### AI エージェントの助けを借りる

既存プロジェクトでは、エージェントに棚卸しと最初の memory-bank draft を任せられます。既に有用な README、docs、パッケージコメント、テスト、CI ファイルがある場合に特に有効です。

警告: これらのサンプルファイルを既存プロジェクトにコピーすると、既存の `AGENTS.md`、`memory-bank/`、`evolution/` を上書きする可能性があります。先に commit する、バックアップを作る、または一時ディレクトリにコピーしてからエージェントに merge を依頼してください。

既存プロジェクトルートで実行します。

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

書く前にプロジェクトを読むようエージェントに依頼します。

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
memory-bank/status-<LANE><NN>.md file.
Do not invent product direction that is not supported by the existing project.
```

エージェントは次を行うべきです。

1. 既存の markdown とソースレイアウトを棚卸しする。
2. コマンド、依存関係、テスト、harness を特定する。
3. 現在のプロジェクト事実から memory bank を埋める。
4. 長い参考資料を `docs/` に移す、または要約する。
5. `README.md` を簡潔でユーザー向けに保つ。
6. 未解決の不足を pending または blocked 行として `memory-bank/status-<LANE><NN>.md` に残す。

## Memory Bank を使う

memory bank に対して作業を進める方法は 3 つあり、どれも任意です。memory bank 自体はただの markdown なので、単独でも成立します。

| 実行方法 | 範囲 | 必要なもの |
|---|---|---|
| エージェントに依頼を打つ | 1 行ずつ、あなたがループの中にいる | なし |
| [`/memory-bank-next`](#3-つのコマンドをインストールする) | 同じだが、言い換えではなく完全な指示を伴う | 3 つのコマンド |
| [API harness](#api-harness-をインストールする) | 1 回の実行につき 1 行、無人 | Python 3 |
| [ゴールループ](#複数の-milestone-を順番に実行する) | 複数の milestone を順番に | `/goal` コマンド |

Codex や Claude Code のようなエージェントでは、ユーザー側のワークフローは次のように入力するだけで済みます。

```text
tackle next pending item in memory bank
```

エージェントは `memory-bank/status-<LANE><NN>.md` の次の実行可能な行を見つけ、そのタスクを完了し、必要な検証を実行し、memory bank を更新し、範囲の明確な git commit を作るべきです。その行が milestone の最後の未完了項目である場合、エージェントは先に `memory-bank/milestone.md` の milestone review を実行します。その review では、プロダクト方向、アーキテクチャ境界、milestone 目標、または public/private contract の方向が実質的に変わったため `evolution/` に新バージョンが必要かも判断します。

これらを信頼する前に、エージェントに検証対象を与えてください。`memory-bank/tech-stack.md` の **Execution harnesses** 表に、プロジェクトが動くことを証明するコマンド——`make test`、`npm test`、スクリプトなど、すでに実行しているもの——と、それが何を証明するかを書きます。そのコマンドが通るまで、行を `[+]` にすべきではありません。これがないと「検証が通ってから完了にする」には指す先がなく、エージェントが自分で検証の意味を決めてしまいます。

内部では、通常のエージェントワークフローは次のとおりです。

1. `AGENTS.md` を読む。
2. `AGENTS.md` に列挙された順序で memory bank ファイルを読む。
3. 範囲の明確なタスクまたは status 行を 1 つだけ処理する。
4. scope、architecture、tools、milestone acceptance、status が変わった場合、対応する memory-bank ファイルを更新する。
5. 検証が通った後にだけ、行を `[+]` にする。
6. その行を範囲の明確な commit として提出する。
7. milestone が完了したら、続ける前に `memory-bank/milestone.md` の milestone review 手順を実行する。
8. `evolution/` を確認し、review が実際の方向、境界、milestone、contract の変化を見つけた場合にだけ新バージョンを追加する。

### ステータス ID レーン

Status ファイルは `memory-bank/status-<LANE><NN>.md` という名前にします。レーン文字が作業の分類を表し、数字は 2 桁のゼロ埋めです。会計の milestone は `status-A01.md` や `status-A02.md`、買い物の milestone は `status-S01.md` になります。ドメインレーンに分類できない作業は既定の `M` を使います。1 つのレーンは最大 99 ファイルまでで、埋まったら 3 桁目を足さずに新しい文字を使います。`memory-bank/milestone.md` が各文字の意味を記録し、ID の再利用を防ぎます。

**レーンの選び方。** レーンは長く続く作業の筋であって、milestone でもスプリントでもありません。チームや優先度や日付ではなく、ドメイン——変更がプロダクトのどの部分に属するか——で分類してください。ドメインはその三つより長生きします。まずは `M` だけで始め、あるドメインの行が他を埋もれさせるほど増えたとき、あるいは独自のレビュー周期が必要になったときに初めて文字を分けます。2〜3 レーンが普通の定常状態で、1 本のまま長く進むプロジェクトもあります。

分け足りないのは直すのが簡単です。新しい文字を開いて新しい作業をそこに置けば済みます。分けすぎはそうはいきません。status ファイルができた時点で ID は再利用も改名もされないため、後悔したレーンはツリーに残り続けます。迷ったら `M` に置いてください。

Status 行は次のマーカーを使います。

| 記号 | 意味 |
|---|---|
| `[ ]` | 未着手 |
| `[+]` | 完了 |
| `[~]` | 進行中 |
| `[!]` | ブロック中 |
| `[X]` | キャンセル済み |

### 複数の milestone を順番に実行する

上のワークフローは 1 行ずつ進みます。決められた順序で複数の milestone を消化したい場合は、[GOAL.md](template/GOAL.md) はそのための protocol の一つです。各 milestone の開始前に依存関係を照合し、閉じた milestone の下流を照合し、判断や権限が足りないときは推測せず停止します。

常駐ではなく、呼び出して使います。Codex にも Claude Code にも `/goal` コマンドがあり（Claude Code のものは goal の条件が満たされるまでターンをまたいで動き続けます）、リクエストでファイルと順序を指定します。

これは常駐ではなく、呼び出して使います。どのエージェントでも、実行を開始するリクエストは同じ内容です。ファイル、順序、commit ポリシーを明示します:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

その内容をどう送るかは異なります。`/goal` はエージェントごとに同じコマンドではないからです。自分が使うものの節を読んでください。

#### Claude Code を使う場合

`/goal` は組み込みコマンドですが、タスクを開始するためのものでは**ありません**。停止条件——「Claude が停止する前に確認する目標」——を設定するもので、1 回返答して終わるのではなく、セッションがターンをまたいで作業を続けます。

そのためメッセージは 2 通になります。上記の内容を通常のメッセージとして送り、次に実行の終了を判定する条件を設定します:

```text
/goal every row in M01 and S01 is `[+]` and the required verification passes
```

`/goal active` で現在の条件を表示、`/goal clear` で早期終了します。条件は 4000 文字までで、信頼済みワークスペースが必要です。設定やポリシーで hooks が無効な場合は使用できません。

この内容自体を再利用したい場合は、プロジェクトコマンドとして保存します。ただし `.claude/commands/goal.md` という名前は組み込みコマンドが使っているので避けてください。`.claude/commands/milestones.md` にして `/milestones` で呼び出します。

#### Codex を使う場合

組み込みの `/goal` はありません。カスタムプロンプトは `~/.codex/prompts/` 内の markdown ファイルで、ファイル名で呼び出します。つまりコマンドを自分で作り、順序を引数として受け取らせることができます。`~/.codex/prompts/goal.md` を作成します:

```markdown
---
description: Execute an ordered set of milestones using GOAL.md.
argument-hint: M01 -> S01 -> A01?
---

Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS
COMMIT_POLICY: task
```

あとは 1 通のメッセージで実行できます:

```text
/goal M01 -> S01 -> A01?
```

これは同梱の [tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md) プロンプトと同じ仕組みで、同じディレクトリにインストールされます。

#### その他のエージェント

この内容を通常のリクエストとして貼り付けてください。プロトコルに必要なのはファイル名を挙げることだけで、スラッシュコマンドの有無には依存しません。

`COMMIT_POLICY` は重要で、ゴールループは通常の規則に対する意図的な例外です。その実行のあいだ、これが commit 規則のすべてになります。`AGENTS.md` が「1 行が 1 commit 単位」と書いていても、`COMMIT_POLICY: none`——この protocol の既定値——は commit を一切作らないという意味であり、これは矛盾ではなく正しい挙動です。通常どおり行ごとに commit したいときは `task` と書きます。優先順位はリクエスト、`GOAL.md`、`AGENTS.md` の順で、commit にだけ、その実行の中でだけ適用されます。

末尾の `?` は条件付きを表し、トリガーがなければ cancel ではなく skip されます。

`GOAL.md` にはプロジェクト固有のパス、レーン文字、コマンドは含まれません。それらは `AGENTS.md` と memory bank から読み取るため、コピーしたどのプロジェクトでも同じファイルがそのまま使えます。

使うことを求めてはいません。`/goal` はあなたのエージェントのコマンドであって、この harness のものではありません。自前の protocol を持ち込んでも、何も使わなくても、memory bank のふるまいは変わりません。`GOAL.md` を同梱しているのは、この種の protocol を書くのが面倒だからであって、ここにある何かがそれに依存しているからではありません。自前のものがあるなら、`GOAL.md` に触れている 2 か所——`AGENTS.md` と `memory-bank/milestone.md`——をそちらに向けるか、削除してください。

## 3 つのコマンドをインストールする

これも任意です。上記はすべて普通の文を入力すれば動きます。この 3 つのコマンドは、その 3 つの場面を再現可能にし、あなたの言い換えではなく完全な指示を運ぶだけのものです。

| コマンド | 使う場面 |
|---|---|
| `/memory-bank-init` | 一度だけ。`memory-bank/` がまだないプロジェクトで。質問し、分割案を提示し、それからファイルを書きます。 |
| `/memory-bank-next` | 毎日。1 行を実装し、検証し、コミットします。 |
| `/memory-bank-goal` | 複数の milestone を順番に実行したいとき。 |

体験を最も変えるのは `/memory-bank-init` です。推奨する回答を添えて 1 問ずつ尋ね、リポジトリから読み取れることは聞かずに自分で調べ、分割案をあなたが承認するまで何も書きません。角括弧のプレースホルダーを目にすることはなく、memory bank は記入済みで届きます。（インタビュー手法は [mattpocock/skills](https://github.com/mattpocock/skills) の `grilling` skill を参考にしています。MIT ライセンス。）

どちらのエージェントも同じ `SKILL.md` 形式を読むので、コマンドごとにソースは 1 つです:

```bash
# Claude Code — as a plugin, updates when this repo ships
/plugin marketplace add tabilet/skills
/plugin install memory-bank

# Claude Code — or as plain files you own and can edit
cp -R /path/to/skills/harness/skills/. ~/.claude/skills/

# Codex
cp -R /path/to/skills/harness/skills/. ~/.codex/skills/
```

プラグインがインストールするのは**生成器**であって、生成物ではありません。プロジェクトに書き込まれた内容はあなたのもので、ここから更新されることはなく、アンインストールしても残ります。

この skill をあえて `goal` という名前にしていないのは、Claude Code に停止条件を設定する組み込みの `/goal` があり、別物だからです。両者は併用できます。「複数の milestone を順番に実行する」を参照してください。

## API Harness をインストールする

このセクションは任意です。ここまでの内容はこれなしで成立します。harness は、あなたが手で入力する代わりに API 経由でエージェントを動かす無人ループを足すだけです。Codex や Claude Code など、すでに使っているエージェントがその役割を果たしているなら省略してかまいません。

API harness は、この memory-bank 構造に従う任意のプロジェクトを駆動できるため、アカウントレベルのツールです。 必要なのは Python 3 だけです。

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

以下のコマンドは `tackle-memory-bank-api-loop` を名前で呼び出すため、`~/.local/bin` が `PATH` に含まれている必要があります。`command -v tackle-memory-bank-api-loop` が何も出力しない場合は、次の行を shell の設定ファイルに追加してください。

```bash
export PATH="$HOME/.local/bin:$PATH"
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

OpenAI 互換のパスではなく Anthropic（Claude）を使う場合:

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

この harness はタスク指示を API prompt に埋め込みます。Codex CLI は呼び出さず、実行時に外部 prompt ファイルも必要としません。prompt ファイルは、人間とエージェントが再利用できる参考として含まれています。

### 最初の実行

実行はまずリポジトリ、プロバイダー、モデル、API エンドポイントを表示し、それから 1 行の作業に取りかかります。

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

harness は意図的に早く停止し、その理由は終了コードが示します。`3` から `7` は失敗ではなく正常な停止条件です。たとえば `4` は実行前に worktree が clean でなかったこと、`6` はエージェントが commit せずに終わったことを表します。`11` は `status-<LANE><NN>.md` ファイルが見つからないという意味で、通常は memory bank がまだ記入されていないことを示します。一覧は[実行 Harness](docs/EXECUTION_ja.md#終了コード)にあります。

## この Harness の意味

通常のプロジェクト作業では、`tackle-memory-bank-api-loop` は実行 harness です。リポジトリに対してエージェントを繰り返し実行し、制御されたコマンドプロトコルで shell アクセスを与え、実行間の git 状態を確認します。

すべての `memory-bank/status-<LANE><NN>.md` ファイルを検出し、各レーンの実行可能行と blocked 行の数を報告したうえで、レーンの意味と milestone の優先度に従って次の行をエージェントに選ばせます。あるレーンの blocked 行が他のレーンの作業を止めることはありません。blocked 行だけが残ったときにのみ、人間のレビューのためにループが停止します。

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
