import os
import json
import glob
from services.category_discovery_agent import CategoryDiscoveryAgent
from services.knowledge_synthesis_agent import KnowledgeSynthesisAgent
from services.classification_agent import ClassificationAgent

class StrategicPipeline:
    def __init__(self, base_dir="アイデアノート/PoC_Sandbox/data"):
        self.base_dir = base_dir
        self.logs_dir = os.path.join(base_dir, "raw_event_logs")
        self.categories_path = os.path.join(base_dir, "discovered_categories.json")
        self.classified_logs_path = os.path.join(base_dir, "classified_logs.json")
        self.knowledge_dir = os.path.join(base_dir, "synthesized_knowledge")
        
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)

    def run(self):
        """戦略ループのパイプライン全体を実行する"""
        
        print("--- Step 1: Running Category Discovery Agent ---")
        discovery_agent = CategoryDiscoveryAgent(logs_dir=self.logs_dir)
        discovered_categories = discovery_agent.discover_categories()
        
        if not discovered_categories:
            print("No categories discovered. Halting pipeline.")
            return

        with open(self.categories_path, 'w', encoding='utf-8') as f:
            json.dump(discovered_categories, f, ensure_ascii=False, indent=4)
        print(f"\\nDiscovered category definitions saved to {self.categories_path}")
        
        print("\\n--- Step 2: Running Classification Agent in batch mode ---")
        classification_agent = ClassificationAgent(categories_path=self.categories_path)
        all_logs = discovery_agent.logs
        
        classification_results = classification_agent.classify_logs_in_batch(all_logs)

        classified_data = {category_id: [] for category_id in discovered_categories.keys()}
        for log_id, category_id in classification_results.items():
            if category_id in classified_data:
                classified_data[category_id].append(log_id)
            else:
                print(f"Warning: Log {log_id} classified as unknown category '{category_id}'. Skipping.")

        with open(self.classified_logs_path, 'w', encoding='utf-8') as f:
            json.dump(classified_data, f, ensure_ascii=False, indent=4)
        print(f"\\nClassification results saved to {self.classified_logs_path}")

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