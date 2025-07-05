import json
import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class KnowledgeSynthesisAgent:
    def __init__(self, logs_dir="アイデアノート/PoC_Sandbox/data/raw_event_logs", categories_path="アイデアノート/PoC_Sandbox/data/discovered_categories.json"):
        self.logs_dir = logs_dir
        self.categories = self._load_json(categories_path)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

    def _load_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found at {path}")
            return None

    def synthesize_knowledge_for_category(self, category_id, log_ids):
        """特定のカテゴリに属するログから、ナレッジ記事を生成する"""
        if not self.categories or category_id not in self.categories:
            return f"Category ID '{category_id}' not found."

        category_name = self.categories[category_id]['name']

        # 該当するログファイルの内容を読み込む
        log_contents = []
        for log_id in log_ids:
            log_path = os.path.join(self.logs_dir, f"{log_id}.json")
            log_data = self._load_json(log_path)
            if log_data:
                log_contents.append(log_data)
        
        if not log_contents:
            return f"No logs found for category '{category_name}'."

        logs_str = "\\n---\\n".join([json.dumps(log, ensure_ascii=False, indent=2) for log in log_contents])

        prompt = PromptTemplate.from_template(
            """あなたは、シニアレベルのサイト信頼性エンジニア(SRE)です。
            以下の複数のイベントログは、すべて「{category_name}」という共通の問題カテゴリに分類されています。

            これらのログ全体を分析し、以下の項目を含む、詳細で実用的な技術ナレッジベースの記事をマークダウン形式で作成してください。

            - **問題の概要**: このカテゴリの問題が何であるかを簡潔に説明してください。
            - **考えられる根本原因**: これらのログから推測される、問題の根本的な原因をいくつか挙げてください。
            - **ビジネスへの影響**: この問題が引き起こす可能性のある、サービスやユーザーへの影響を説明してください。
            - **推奨される一次対応**: 問題発生時に、エンジニアが最初に行うべき具体的な確認手順や応急処置をリストアップしてください。
            - **恒久的な解決策/予防策**: この問題を将来的に防ぐための、より根本的な解決策やアーキテクチャの改善案を提案してください。

            ## 分析対象のログ群
            {logs_data}

            ## 生成するナレッジ記事（マークダウン形式）
            # {category_name} 対応マニュアル
            """
        )

        chain = prompt | self.llm
        response = chain.invoke({
            "category_name": category_name,
            "logs_data": logs_str
        })

        return f"# {category_name} 対応マニュアル\\n" + response.content.strip()

# このファイル単体での実行ロジックは、パイプラインに統合されたため不要。
# if __name__ == '__main__':
#     agent = KnowledgeSynthesisAgent()
#     
#     # テストとして、発見されたカテゴリの1つからナレッジを生成する
#     # 例: 'category_4' (システムリソース枯渇とデータベース接続障害)
#     target_category_id = "category_4"
#     
#     print(f"Synthesizing knowledge for '{target_category_id}'...")
#     knowledge_article = agent.synthesize_knowledge_for_category(target_category_id, ["log_id_1", "log_id_2"])
#     
#     print("\\n--- Generated Knowledge Article ---")
#     print(knowledge_article)
#
#     # 生成したナレッジをファイルに保存
#     output_dir = "アイデアノート/PoC_Sandbox/data/synthesized_knowledge"
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#     
#     output_path = os.path.join(output_dir, f"{target_category_id}_manual.md")
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(knowledge_article)
#         
#     print(f"\\nKnowledge article saved to {output_path}")

# もし単体テストが必要な場合は、分類済みのログIDリストを別途用意する必要がある。 