import os
import json
from services.category_discovery_agent import CategoryDiscoveryAgent
from services.knowledge_synthesis_agent import KnowledgeSynthesisAgent

class StrategicPipeline:
    def __init__(self, base_dir="アイデアノート/PoC_Sandbox/data"):
        self.base_dir = base_dir
        self.logs_dir = os.path.join(base_dir, "raw_event_logs")
        self.categories_path = os.path.join(base_dir, "discovered_categories.json")
        self.knowledge_dir = os.path.join(base_dir, "synthesized_knowledge")
        
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)

    def run(self, n_clusters=5):
        """戦略ループのパイプライン全体を実行する"""
        
        print("--- Step 1: Running Category Discovery Agent ---")
        discovery_agent = CategoryDiscoveryAgent(logs_dir=self.logs_dir, n_clusters=n_clusters)
        discovered_categories = discovery_agent.discover_categories()
        
        if not discovered_categories:
            print("No categories discovered. Halting pipeline.")
            return

        with open(self.categories_path, 'w', encoding='utf-8') as f:
            json.dump(discovered_categories, f, ensure_ascii=False, indent=4)
        print(f"\\nDiscovered categories saved to {self.categories_path}")
        
        print("\\n--- Step 2: Running Knowledge Synthesis Agent for each category ---")
        synthesis_agent = KnowledgeSynthesisAgent(logs_dir=self.logs_dir, categories_path=self.categories_path)
        
        for category_id in discovered_categories.keys():
            print(f"\\nSynthesizing knowledge for '{category_id}'...")
            
            article = synthesis_agent.synthesize_knowledge_for_category(category_id)
            
            # 生成された記事をファイルに保存
            article_filename = f"{category_id}_manual.md"
            output_path = os.path.join(self.knowledge_dir, article_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(article)
            
            print(f"Knowledge article for '{category_id}' saved to {output_path}")
            
        print("\\n--- Strategic Pipeline finished successfully! ---")


if __name__ == '__main__':
    pipeline = StrategicPipeline()
    pipeline.run(n_clusters=5) # クラスタ数（＝生成されるカテゴリ数）を指定 