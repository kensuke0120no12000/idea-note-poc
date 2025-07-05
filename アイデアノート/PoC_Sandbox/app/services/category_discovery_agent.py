import json
import os
import glob
from sklearn.cluster import KMeans
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import numpy as np
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

class CategoryDiscoveryAgent:
    def __init__(self, logs_dir="アイデアノート/PoC_Sandbox/data/raw_event_logs", n_clusters=5):
        self.logs_dir = logs_dir
        self.n_clusters = n_clusters
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0) # 2.5-flashを利用
        self.logs = self._load_logs()
        
    def _load_logs(self):
        log_files = glob.glob(os.path.join(self.logs_dir, "*.json"))
        logs = []
        for file in log_files:
            with open(file, 'r', encoding='utf-8') as f:
                logs.append(json.load(f))
        return logs

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

    def discover_categories(self):
        """ログをクラスタリングし、新しいカテゴリを発見する"""
        if not self.logs:
            print("No logs found.")
            return {}

        # 1. 各ログをベクトル化
        log_texts = [self._get_text_for_embedding(log) for log in self.logs]
        vectors = self.embedding_model.embed_documents(log_texts)
        
        # 2. KMeansでクラスタリング
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init='auto').fit(vectors)
        labels = kmeans.labels_

        # 3. 各クラスタのサマリーをLLMに生成させる
        discovered_categories = {}
        for i in range(self.n_clusters):
            cluster_logs = [self.logs[j] for j, label in enumerate(labels) if label == i]
            
            # クラスタ内のログの一部をプロンプトに含める
            sample_logs_text = "\\n".join([json.dumps(log, ensure_ascii=False) for log in cluster_logs[:5]]) # 最大5件
            
            prompt = PromptTemplate.from_template(
                """以下のイベントログ群は、ある共通の問題やパターンによってグループ化されています。
                このグループ全体を代表する、簡潔で分かりやすい「カテゴリ名」を提案してください。
                カテゴリ名は、問題の本質を捉えた名詞句（例：「データベース接続のタイムアウト」、「特定のIPからのログイン失敗多発」）にしてください。

                ログサンプル:
                {sample_logs}

                提案するカテゴリ名:"""
            )
            
            chain = prompt | self.llm
            response = chain.invoke({"sample_logs": sample_logs_text})
            category_name = response.content.strip()
            
            discovered_categories[f"category_{i+1}"] = {
                "name": category_name,
                "log_ids": [log['log_id'] for log in cluster_logs]
            }
            print(f"Generated Category: {category_name}")

        return discovered_categories

if __name__ == '__main__':
    agent = CategoryDiscoveryAgent(n_clusters=5)
    categories = agent.discover_categories()
    
    # 結果をファイルに保存
    output_path = "アイデアノート/PoC_Sandbox/data/discovered_categories.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)
        
    print(f"\\nDiscovered categories saved to {output_path}") 