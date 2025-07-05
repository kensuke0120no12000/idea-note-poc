import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

load_dotenv()

class ClassificationAgent:
    def __init__(self, categories_path="アイデアノート/PoC_Sandbox/data/discovered_categories.json"):
        self.categories = self._load_categories(categories_path)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    def _load_categories(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Categories file not found at {path}")
            return {}

    def classify_logs_in_batch(self, log_entries):
        """複数のログエントリをバッチで分類する"""
        if not self.categories:
            return {}

        category_list_str = "\\n".join([f"- {key}: {value['name']}" for key, value in self.categories.items()])
        
        # 複数のログを整形してプロンプトに含める
        log_entries_str = "\\n---\\n".join([f"LOG_ID: {log['log_id']}\\n" + json.dumps(log, ensure_ascii=False, indent=2) for log in log_entries])

        parser = JsonOutputParser()

        prompt = PromptTemplate(
            template="""以下のイベントログ群を分析し、それぞれがどのカテゴリに属するかを分類してください。
            回答は、必ず指定したJSON形式で、各LOG_IDに対応する最も関連性の高いカテゴリIDを記述してください。

            ## 利用可能なカテゴリ一覧
            {category_list}

            ## 分類対象のイベントログ群
            {log_entries}

            ## 出力フォーマット指示
            {format_instructions}
            """,
            input_variables=["category_list", "log_entries"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | self.llm | parser
        
        print(f"Classifying {len(log_entries)} logs in a single batch...")
        response = chain.invoke({
            "category_list": category_list_str,
            "log_entries": log_entries_str
        })
        
        return response

if __name__ == '__main__':
    # テスト用のダミーログ
    sample_log = {
        "log_id": "log_101",
        "timestamp": "2025-07-05T18:30:00.123456",
        "event_type": "service_error",
        "service": "database",
        "details": {
            "error_code": 503,
            "message": "Database connection refused by server.",
            "severity": "critical"
        }
    }

    agent = ClassificationAgent()
    result_id = agent.classify_log(sample_log)
    
    print(f"Log: {json.dumps(sample_log, indent=2)}")
    print(f"\\nClassified as: {result_id}")
    
    # カテゴリ名も表示してみる
    if result_id in agent.categories:
        print(f"Category Name: {agent.categories[result_id]['name']}") 