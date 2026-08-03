# 最小限のエンジニアリング Harness

コーディングエージェントは、プロジェクトが自分自身を説明できるとき——これが何で、何が終わっていて、次が何か——うまく動きます。そのための一般的な方法は、CLI、スキャフォールド、スラッシュコマンド群、生成された成果物のフォルダといったシステムを丸ごと導入することです。半年後には、自分のコードと同じくらいそのシステムのファイルを保守していて、プロジェクトは自分の規約ではなくそのシステムの規約の中で生きています。

このリポジトリは逆に賭けます。小さな markdown ファイル群をプロジェクトにコピーし、完全にあなたのものにします。必須のプロジェクト CLI や runtime はありません。任意のプラグインでファイルを生成し、任意の API runner で無人実行できますが、どちらもプロジェクトの依存関係にはなりません。

**最終的に手に入るものはあなたのものです。** このリポジトリはコピー*元*となる出発点です。`template/` をプロジェクトへ、`harness/` は必要なら home ディレクトリへ。その後、プロジェクトはこのリポジトリに依存せず、リンクも残りません。

3 つの任意の skill が、そのコピーと記入を代行できます（[3 つのコマンドをインストールする](#3-つのコマンドをインストールする)を参照）。上の前提は変わりません。生成されたファイルはあなたのものになり、あとから更新されることはなく、アンインストールしてもプロジェクトはそのままです。

プロジェクトは最終的にこうなります。

```text
your-project/
├── AGENTS.md              エージェントが最初に読むもの
├── GOAL.md                任意の複数 milestone 用プロトコル
├── memory-bank/           いま真であること
│   ├── product.md         これが何で、何ではないか
│   ├── architecture.md    レイアウト、データフロー、境界
│   ├── tech-stack.md      コマンド、依存関係、検証方法
│   ├── milestone.md       milestone と受け入れ基準
│   └── status-M01.md      milestone ごとの永続ファイル、タスクごとに 1 行
└── evolution/             バージョン化された方向スナップショット
    ├── prompt-v1.md       初期方針
    └── result-v1.md       そこから生じた状態
```

*memory bank* という用語は [Cline](https://docs.cline.bot/best-practices/memory-bank) が広めたものです。ここにあるのは同じ発想の別実装で、ランタイムを持たないただのファイル群です。

本文を通じて **harness** とは、何かが動くことを証明する繰り返し実行可能なコマンド——テストスイート、CI job、スクリプト——を指します。プロジェクトは自分の harness を `tech-stack.md` に定義します。このリポジトリはさらに任意の harness を 1 つ同梱しています。API 経由でエージェントを動かし、memory bank を無人で進めるループです。

他の言語版: [🇬🇧 English](README.md) · [🇨🇳 中文](README_cn.md) · [🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## はじめに

**はじめてですか？** [docs/TUTORIAL.md](docs/TUTORIAL.md) は、空のディレクトリから最初のコミットまで、おもちゃのプロジェクトを 20 分で辿ります。セットアップは `memory-bank-init` が行います。この README の残りはリファレンスで、チュートリアルはそこを通る案内付きの道筋です。

**memory bank を使うのに必要なのは `git` だけです。** memory bank はただの markdown なので、日々のワークフロー——Codex や Claude Code のようなエージェントに次の未処理項目を任せること——にランタイムは一切不要です。

**Python 3 が必要なのは任意の API harness だけ**です。[API Harness をインストールする](#api-harness-をインストールする)で説明する無人実行ループのことです。標準ライブラリしか使わないため、`pip` で入れるものはありません。すでに使っているエージェントから memory bank を動かすなら、まるごと省略できます。

後述の既存プロジェクト向け手順では、最初の棚卸しに [ripgrep](https://github.com/BurntSushi/ripgrep)（`rg`）も使います。

このリポジトリを一度 clone してください。以下の `cp` コマンドの `/path/to/skills` は、その clone を指します:

**最短の方法に clone は不要です。** プラグインをインストールし、名前空間付きの init skill に質問させて memory bank を書かせます:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
/memory-bank:memory-bank-init
```

Claude Code のプロジェクト（空でも既存でも）でこれらを実行し、質問に答えてください。Codex での同等の方法と、ファイルをそのまま使う選択肢は[3 つのコマンドをインストールする](#3-つのコマンドをインストールする)にあります。

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

任意の API runner と、リポジトリ内だけに置く人間向け指示コピー:

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

3 つの skill は [skills/](skills/) にあります。Claude Code と Codex は同じ `SKILL.md` 形式を読むので、skill ごとにソースは 1 つです:

- [memory-bank-init](skills/memory-bank-init/SKILL.md)
- [memory-bank-next](skills/memory-bank-next/SKILL.md)
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md)

`.claude-plugin/` には、同じプラグインを Claude Code と Codex にインストールするための互換マニフェストが入っています。`template/` にベンダー固有のファイルはありません。

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

[3 つのコマンド](#3-つのコマンドをインストールする)をインストールしていれば、`memory-bank-init` がこの節の作業をすべて行います。質問し、レーンと milestone の案を提示し、承認を待ってから、記入済みのファイルを書きます。以下の 2 つの手順は、同じ作業を手作業で行うものです。

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

`memory-bank-init` はこのケースにも対応し、しかも素のプロンプトより上手くこなします。リポジトリがすでに述べていること（README、テスト、ビルドや CI の設定）を読み、そこから分からない決定だけを尋ねます。多くの場合、非目標、境界、作業の順序です。

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

memory bank に対して作業を進める方法は 4 つあり、どれも任意です。memory bank 自体はただの markdown なので、単独でも成立します。

| 実行方法 | 範囲 | 必要なもの |
|---|---|---|
| エージェントに依頼を打つ | 1 行ずつ、あなたがループの中にいる | なし |
| [`memory-bank-next`](#3-つのコマンドをインストールする) | 同じだが、言い換えではなく完全な指示を伴う | 任意の skills |
| [API harness](#api-harness-をインストールする) | 1 回の実行につき 1 行、無人 | Python 3 |
| [ゴールループ](#複数の-milestone-を順番に実行する) | 複数の milestone を順番に | `GOAL.md` と通常の依頼または任意の skill |

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

これは常駐ではなく、呼び出して使います。どのエージェントでも、実行を開始するリクエストは同じ内容です。ファイル、順序、commit ポリシーを明示します:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

上のブロックは、どのエージェントにも通常の依頼として貼り付けられます。プラグインを入れた場合は、同じプロトコルを `/memory-bank:memory-bank-goal M01 -> S01 -> A01?`（Claude Code）または `$memory-bank:memory-bank-goal M01 -> S01 -> A01?`（Codex）で実行できます。skill ファイルを直接入れた場合は `/memory-bank-goal` と `$memory-bank-goal` です。

#### Claude Code を使う場合

Claude Code の組み込み `/goal` は、長い実行のための任意の代替ランチャーです。完全なプロトコル依頼、commit 方針、測定可能な完了条件を一緒に渡します:

```text
/goal Using GOAL.md, execute this loop. STATUS_ORDER: M01 -> S01 -> A01? COMMIT_POLICY: task. Completion condition: every non-skipped row in those milestones is `[+]` and the required verification passes.
```

引数なしの `/goal` で状態を表示し、`/goal clear` で停止します。`memory-bank-goal` skill は Codex と共有できる移植可能なランチャーです。

#### Codex を使う場合

プラグイン skill を直接呼び出します:

```text
$memory-bank:memory-bank-goal M01 -> S01 -> A01?
```

skill ファイルを直接インストールした場合は `$memory-bank-goal M01 -> S01 -> A01?` を使います。Codex のカスタムプロンプトは skill を優先する形で非推奨になったため、このリポジトリは独立した `goal.md` プロンプトをインストールも推奨もしません。

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
| `memory-bank-init` | 一度だけ。`memory-bank/` がまだないプロジェクトで。質問し、分割案を提示し、それからファイルを書きます。 |
| `memory-bank-next` | 毎日。1 行を実装し、検証し、コミットします。 |
| `memory-bank-goal` | 複数の milestone を順番に実行したいとき。 |

体験を最も変えるのは `memory-bank-init` です。推奨する回答を添えて 1 問ずつ尋ね、リポジトリから読み取れることは聞かずに自分で調べ、分割案をあなたが承認するまで何も書きません。角括弧のプレースホルダーを目にすることはなく、memory bank は記入済みで届きます。（インタビュー手法は [mattpocock/skills](https://github.com/mattpocock/skills) の `grilling` skill を参考にしています。MIT ライセンス。）

どちらのエージェントも同じ `SKILL.md` 形式を読むので、コマンドごとにソースは 1 つです:

どちらのエージェントも同じ `SKILL.md` 形式**と同じマニフェスト**を読むので、コマンドごとにソースは 1 つ、インストールするリリースも 1 つです。

**Claude Code:**

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

**Codex** は独自のプラグイン機構を持ち、フォールバックとして `.claude-plugin/plugin.json` を読むので、同じリポジトリがそのまま使えます:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

設定済みの marketplace 間でプラグイン名が一意でない場合、Codex は `@marketplace` 修飾を要求します。`memory-bank@tabilet` の形を覚えておくとよいでしょう。新しいバージョンが出たら `codex plugin marketplace upgrade` でスナップショットを更新します。

**プラグインからの呼び出しには名前空間が付きます。** Claude Code は `/memory-bank:memory-bank-init`、`/memory-bank:memory-bank-next`、`/memory-bank:memory-bank-goal` を使い、Codex は `$memory-bank:memory-bank-init`、`$memory-bank:memory-bank-next`、`$memory-bank:memory-bank-goal` を使います。どちらでも普通の文章による依頼も使えます。

**どちらのエージェントでも**、管理されたプラグインではなく自分が所有するファイルとして入れることもできます:

```bash
mkdir -p ~/.agents/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.agents/skills 'skills-main/skills'

# Claude Code alternative
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.claude/skills 'skills-main/skills'
```

skill ファイルを直接インストールした場合は名前空間なしです。Claude Code では `/memory-bank-init`、Codex では `$memory-bank-init` を使い、ほかの 2 つも同じ形式です。

バージョンを固定するには `refs/heads/main` を `refs/tags/<バージョン>` に、`skills-main` をその tarball 内のディレクトリ名 `skills-<バージョン>` に変えてください。

この skill をあえて `goal` という名前にしていないのは、Claude Code に停止条件を設定する組み込みの `/goal` があり、別物だからです。両者は併用できます。「複数の milestone を順番に実行する」を参照してください。

### すでに `/grill-me` を使っている場合

[mattpocock/skills](https://github.com/mattpocock/skills) の `/grill-me` と `/grilling` は、意図した場所で止まります: *"Do not act on it until I confirm we have reached a shared understanding."*（共通理解に達したと私が確認するまで実行しないこと）。汎用のインタビューとしてはそこで止まるのが正しく、だからこそあらゆる対象に使えます。

ですがセッションが終わると、その理解も一緒に終わります。ディスクには何も残らず、明日のエージェントは引き継げず、実行する対象もありません。

`memory-bank-init` は同じインタビューの規律を、残る成果物へ向けたものです——1 問ずつ、推奨する回答を添えて、調べられる事実は聞かずに調べます。**grill の直後、同じセッションで**実行してください:

```text
/grill-me            # explore the design; no files written
/memory-bank:memory-bank-init    # Claude Code plugin
$memory-bank:memory-bank-init    # Codex plugin
```

すでに決めたことを聞き直すことはありません。「事実は調べ、決定は尋ねる」はリポジトリだけでなく会話にも適用されるので、grill を終えた直後のインタビューは短くなります。多くはレーンと milestone の分割案を確認するだけです。

| | `/grill-me` の後 | `memory-bank-init` の後 |
|---|---|---|
| 決定がある場所 | 会話の中 | `product.md`、`architecture.md`、`tech-stack.md` |
| 明日のエージェント | ゼロから | `AGENTS.md` を読めば分かる |
| 次の行動 | あなたが決める | 次の `` `[ ]` `` 行 |
| 実行手段 | — | `memory-bank-next`、まとめてなら `memory-bank-goal` |

この 2 つは競合ではなく補完です。プロジェクトを生まない決定——アーキテクチャの議論、採用計画、講演の構成——には `/grill-me` を使い続けてください。grill の対象が、来週も自分が何であるかを知っている必要のあるコードベースなら `memory-bank-init` です。

## API Harness をインストールする

このセクションは任意です。ここまでの内容はこれなしで成立します。harness は、あなたが手で入力する代わりに API 経由でエージェントを動かす無人ループを足すだけです。Codex や Claude Code など、すでに使っているエージェントがその役割を果たしているなら省略してかまいません。

API harness は、この memory-bank 構造に従う任意のプロジェクトを駆動できるため、アカウントレベルのツールです。 必要なのは Python 3 だけです。

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

以下のコマンドは `tackle-memory-bank-api-loop` を名前で呼び出すため、`~/.local/bin` が `PATH` に含まれている必要があります。`command -v tackle-memory-bank-api-loop` が何も出力しない場合は、次の行を shell の設定ファイルに追加してください。

```bash
export PATH="$HOME/.local/bin:$PATH"
```

1 行だけ実行する:

```bash
LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

ループを実行する:

```bash
LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

OpenAI 互換プロバイダーを使う:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.6 \
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

この harness はタスク指示を API prompt に埋め込みます。Codex CLI は呼び出さず、実行時に外部 prompt ファイルも必要としません。prompt ファイルは埋め込み指示と同期する人間向けコピーとしてリポジトリに残し、Codex の prompt ディレクトリにはインストールしません。

モデル名は変わります。例では現在の `gpt-5.6` family alias と `claude-opus-5` を使っています。実際の実行では公式の [OpenAI model catalog](https://developers.openai.com/api/docs/models) と [Anthropic model catalog](https://platform.claude.com/docs/en/about-claude/models/overview) を確認してください。

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
