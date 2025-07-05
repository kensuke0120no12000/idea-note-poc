import json
import os
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

class ClassificationAgent:
    def __init__(self, category_centroids):
        self.category_centroids = category_centroids
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    def _get_text_for_embedding(self, log):
        """ログからベクトル化に適したテキストを抽出・整形する"""
        details = log.get("details", {})
        text = f"Event Type: {log.get('event_type', 'N/A')}. "
        if "message" in details:
            text += f"Message: {details['message']}. "
        if "reason" in details:
            text += f"Reason: {details['reason']}. "
        if "service" in log:
            text += f"Service: {log['service']}. "
        return text

    def classify_log(self, log_entry, similarity_threshold=0.75):
        """ベクトル距離に基づいて単一のログを分類し、未知カテゴリを検知する"""
        if not self.category_centroids:
            return "unclassified"
            
        log_text = self._get_text_for_embedding(log_entry)
        log_vector = self.embedding_model.embed_query(log_text)
        
        best_match_category = "unclassified"
        max_similarity = -1.0
        
        for cat_id, centroid_vector in self.category_centroids.items():
            similarity = cosine_similarity([log_vector], [centroid_vector])[0][0]
            if similarity > max_similarity:
                max_similarity = similarity
                best_match_category = cat_id
        
        if max_similarity < similarity_threshold:
            return "unclassified"
        
        return best_match_category

    def classify_logs_in_batch(self, log_entries):
        """複数のログエントリをバッチで分類する"""
        if not self.category_centroids:
            return {}

        category_list_str = "\\n".join([f"- {key}: {value['name']}" for key, value in self.category_centroids.items()])
        
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

        chain = prompt | self.embedding_model | parser
        
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
    if result_id in agent.category_centroids:
        print(f"Category Name: {agent.category_centroids[result_id]['name']}") 