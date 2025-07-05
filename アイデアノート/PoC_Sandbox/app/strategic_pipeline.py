import os
import json
import glob
import numpy as np
from services.category_discovery_agent import CategoryDiscoveryAgent
from services.classification_agent import ClassificationAgent
from services.knowledge_synthesis_agent import KnowledgeSynthesisAgent
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sklearn.cluster import KMeans

class StrategicPipeline:
    def __init__(self, base_dir="アイデアノート/PoC_Sandbox/data"):
        self.base_dir = base_dir
        self.logs_dir = os.path.join(base_dir, "raw_event_logs")
        self.categories_path = os.path.join(base_dir, "discovered_categories.json")
        self.classified_logs_path = os.path.join(base_dir, "classified_logs.json")
        self.knowledge_dir = os.path.join(base_dir, "synthesized_knowledge")
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)

    def _get_text_for_embedding(self, log):
        # ... (This is duplicated, could be a shared util) ...
        details = log.get("details", {})
        text = f"Event Type: {log.get('event_type', 'N/A')}. "
        if "message" in details:
            text += f"Message: {details['message']}. "
        if "reason" in details:
            text += f"Reason: {details['reason']}. "
        if "service" in log:
            text += f"Service: {log['service']}. "
        return text

    def run(self):
        """戦略ループのパイプライン全体を実行する"""
        
        # --- Step 1: カテゴリ発見 ---
        print("--- Step 1: Running Category Discovery Agent ---")
        discovery_agent = CategoryDiscoveryAgent(logs_dir=self.logs_dir)
        discovered_categories = discovery_agent.discover_categories()
        
        if not discovered_categories:
            print("No categories discovered. Halting pipeline.")
            return

        with open(self.categories_path, 'w', encoding='utf-8') as f:
            json.dump(discovered_categories, f, ensure_ascii=False, indent=4)
        print(f"\\nDiscovered category definitions saved to {self.categories_path}")

        # --- Step 2: カテゴリの重心計算 & ログの分類 ---
        print("\\n--- Step 2: Calculating Centroids and Classifying Logs ---")
        
        # 全ログのベクトルを一度だけ計算
        all_logs = discovery_agent.logs
        log_texts = [self._get_text_for_embedding(log) for log in all_logs]
        log_vectors = self.embedding_model.embed_documents(log_texts)
        log_vector_map = {log['log_id']: vec for log, vec in zip(all_logs, log_vectors)}

        # カテゴリごとのログIDを取得 (これはDiscoveryAgentの内部情報に依存しているため、本来は分離すべき)
        # PoCのため、ここでは再度クラスタリングを実行してログの割り当てを取得
        optimal_k = len(discovered_categories)
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init='auto').fit(log_vectors)
        
        # 重心計算
        category_centroids = {}
        for i in range(optimal_k):
            cluster_indices = np.where(kmeans.labels_ == i)[0]
            if len(cluster_indices) > 0:
                centroid = np.mean(np.array(log_vectors)[cluster_indices], axis=0)
                category_id = f"category_{i+1}"
                category_centroids[category_id] = centroid

        # 分類エージェントを重心で初期化
        classification_agent = ClassificationAgent(category_centroids=category_centroids)
        
        # 分類実行
        classified_data = {cat_id: [] for cat_id in discovered_categories.keys()}
        classified_data["unclassified"] = [] # 未分類カテゴリを追加

        for log in all_logs:
            category_id = classification_agent.classify_log(log)
            classified_data[category_id].append(log['log_id'])
        
        print(f"Classification complete. Unclassified logs: {len(classified_data['unclassified'])}")
        with open(self.classified_logs_path, 'w', encoding='utf-8') as f:
            json.dump(classified_data, f, ensure_ascii=False, indent=4)
        print(f"Classification results saved to {self.classified_logs_path}")

        # --- Step 3: ナレッジ合成 ---
        print("\\n--- Step 3: Running Knowledge Synthesis Agent for each category ---")
        synthesis_agent = KnowledgeSynthesisAgent(logs_dir=self.logs_dir, categories_path=self.categories_path)
        
        for category_id, log_ids in classified_data.items():
            if not log_ids:
                print(f"\\nSkipping knowledge synthesis for empty category '{category_id}'.")
                continue
                
            print(f"\\nSynthesizing knowledge for '{category_id}' ({len(log_ids)} logs)...")
            
            article = synthesis_agent.synthesize_knowledge_for_category(category_id, log_ids)
            
            article_filename = f"{category_id}_manual.md"
            output_path = os.path.join(self.knowledge_dir, article_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(article)
            
            print(f"Knowledge article for '{category_id}' saved to {output_path}")
            
        print("\\n--- Strategic Pipeline finished successfully! ---")


if __name__ == '__main__':
    pipeline = StrategicPipeline()
    pipeline.run() 