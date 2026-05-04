# モデル評価 Harness

モデル評価 harness（model eval harness）は、モデル支援のふるまいを測定するための繰り返し可能な仕組みです。プロジェクトがプロンプト、エージェント、分類器、検索、ランキング、生成、コード修復、要約、または通常のソフトウェアテストだけでは不十分なモデル品質に依存するワークフローを持つ場合に有用です。

実行 harness が問うのは、ソフトウェアが正しく動いたか、です。

モデル評価 harness が問うのは、代表的なタスク上でモデルのふるまいが良くなったのか、悪くなったのか、それとも変わらなかったのか、です。

## 例

- ユーザー要求、期待される回答、採点 rubric を含む dataset。
- 新旧プロンプトを比較する prompt regression suite。
- accuracy、pass rate、refusal quality、latency、cost を測定する baseline-vs-candidate 実行。
- 生成された patch を sandbox 内でビルドしてテストする code-repair eval。
- 正しい文書が選択されたかを測定する retrieval eval。
- regression、improvement、未解決の residual を列挙する report。

## この構造での位置づけ

- `memory-bank/product.md` は、どのモデル支援ふるまいが product にとって重要かを示します。
- `memory-bank/architecture.md` は、prompts、datasets、graders、reports の置き場所を記録します。
- `memory-bank/tech-stack.md` は、model providers、local runners、eval commands、environment variables、cost controls、required credentials を記録します。
- `memory-bank/milestone.md` は、eval score や regression review を受け入れ条件の一部にできます。
- `evolution/` は、prompt、model、architecture、benchmark の大きな方向転換を記録します。

## API Loop を Eval にする

同梱の API loop は、それだけで自動的にモデル評価 harness になるわけではありません。制御された比較を実行し、結果を記録したときに、その一部になります。

有用な測定項目:

- モデル名
- プロンプトバージョン
- dataset または todo set
- pass/fail
- ループ反復回数
- テスト結果
- 静的解析結果
- review findings
- 人間による受け入れ
- コスト
- レイテンシ
- 導入された regression
- 残存 failure

## 昇格ルール

新しい model、prompt、または agent workflow を昇格する前に、次を定義します。

- baseline model と prompt
- candidate model と prompt
- dataset または task set
- primary metric
- 許容される regression budget
- 必須の deterministic check
- human review requirements
- report location

昇格ルールは、reviewer が candidate の合格または不合格の理由を説明できる程度に明確であるべきです。

## Reports

eval report には次を列挙します。

- 実行内容
- 変更内容
- aggregate score
- 改善したケース
- regression したケース
- flaky または判定不能なケース
- コストとレイテンシ
- 未解決の residual
- promotion decision

report は eval harness の近く、または文書化された artifact location に保存し、重要な方向転換は `evolution/` からリンクします。
