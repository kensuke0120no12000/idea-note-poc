import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
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

    def classify_log(self, log_entry):
        """単一のログエントリを、既存のカテゴリに分類する"""
        if not self.categories:
            return "No categories available for classification."

        # 分類しやすいようにカテゴリ情報を整形
        category_list_str = "\\n".join([f"- {key}: {value['name']}" for key, value in self.categories.items()])
        log_entry_str = json.dumps(log_entry, ensure_ascii=False, indent=2)

        prompt = PromptTemplate.from_template(
            """以下のイベントログを分析し、最も関連性の高いカテゴリを一つだけ選んでください。
            回答は、選択したカテゴリのID（例: "category_1"）のみを記述してください。他のテキストは一切含めないでください。

            ## 利用可能なカテゴリ一覧
            {category_list}

            ## 分類対象のイベントログ
            {log_entry}

            最も関連性の高いカテゴリID:"""
        )

        chain = prompt | self.llm
        response = chain.invoke({
            "category_list": category_list_str,
            "log_entry": log_entry_str
        })
        
        # 回答からカテゴリIDを抽出
        classified_category_id = response.content.strip()
        
        return classified_category_id

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