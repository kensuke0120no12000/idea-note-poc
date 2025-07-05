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
    def __init__(self, logs_dir="アイデアノート/PoC_Sandbox/data/raw_event_logs", max_clusters=10):
        self.logs_dir = logs_dir
        self.max_clusters = max_clusters # 試行する最大クラスタ数
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

    def _find_optimal_k(self, vectors):
        """エルボー法を用いて最適なクラスタ数(k)を決定する"""
        sse = []
        k_range = range(2, self.max_clusters + 1) # 2クラスタから試行
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(vectors)
            sse.append(kmeans.inertia_) # inertia_はSSEを返す

        # SSEの減少率が最も大きい点を「肘」とする
        if len(sse) < 2:
            return 2 # データが少ない場合はデフォルト値

        deltas = np.diff(sse, 2) # 2階差分を取る
        optimal_k = k_range[np.argmax(deltas) + 1] # 差分が最大の点が肘
        print(f"Optimal number of clusters (k) found: {optimal_k}")
        return optimal_k

    def discover_categories(self):
        """ログをクラスタリングし、新しいカテゴリ名をバッチ処理で一度に生成する"""
        if not self.logs or len(self.logs) < 2:
            print("Not enough logs to perform clustering.")
            return {}

        log_texts = [self._get_text_for_embedding(log) for log in self.logs]
        vectors = self.embedding_model.embed_documents(log_texts)
        
        optimal_k = self._find_optimal_k(np.array(vectors))
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto').fit(vectors)
        
        # 各クラスタのサンプルログを準備
        cluster_samples_for_prompt = ""
        for i in range(optimal_k):
            cluster_logs = [self.logs[j] for j, label in enumerate(kmeans.labels_) if label == i]
            if not cluster_logs:
                continue
            
            sample_logs_text = "\\n".join([json.dumps(log, ensure_ascii=False) for log in cluster_logs[:5]])
            cluster_samples_for_prompt += f"\\n--- Cluster {i+1} Samples ---\\n{sample_logs_text}\\n"

        prompt = PromptTemplate.from_template(
            """以下の複数のイベントログのグループ（クラスタ）があります。
            それぞれのクラスタについて、内容を代表する簡潔で分かりやすい「カテゴリ名」を提案してください。
            回答は、"cluster_1": "カテゴリ名1", "cluster_2": "カテゴリ名2", ... のようなJSON形式で記述してください。

            ## 分析対象のログサンプル群
            {cluster_samples}

            ## 出力JSON:
            """
        )

        chain = prompt | self.llm
        
        print(f"Generating names for {optimal_k} categories in a single batch...")
        response_content = chain.invoke({"cluster_samples": cluster_samples_for_prompt}).content
        
        try:
            # LLMの出力（文字列）をJSONとしてパース
            # マークダウンのコードブロック(` ```json ... ``` `)を除去
            if "```json" in response_content:
                response_content = response_content.split("```json")[1].split("```")[0]
            elif "```" in response_content:
                response_content = response_content.split("```")[1].split("```")[0]

            response = json.loads(response_content)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Error: Failed to decode LLM response as JSON. Error: {e}\\nResponse:\\n{response_content}")
            return {}

        # LLMの回答を整形して最終的な出力を作成
        discovered_categories = {}
        for i, (key, value) in enumerate(response.items()):
            # keyが "cluster_1" や "category_1" のような形式を想定
            new_key = f"category_{i+1}"
            # valueがカテゴリ名そのものであるか、辞書に含まれているかを考慮
            if isinstance(value, dict) and 'name' in value:
                 discovered_categories[new_key] = {'name': value['name']}
            elif isinstance(value, str):
                 discovered_categories[new_key] = {'name': value}
            else:
                 print(f"Warning: Unexpected format for cluster {key}: {value}")
                 discovered_categories[new_key] = {'name': 'Unnamed Category'}
            
            print(f"Generated Category {i+1}: {discovered_categories[new_key]['name']}")

        return discovered_categories

if __name__ == '__main__':
    agent = CategoryDiscoveryAgent()
    categories = agent.discover_categories()
    
    # 結果をファイルに保存
    output_path = "アイデアノート/PoC_Sandbox/data/discovered_categories.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)
        
    print(f"\\nDiscovered categories saved to {output_path}") 