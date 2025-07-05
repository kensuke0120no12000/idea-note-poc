import json
import os
import random
from datetime import datetime, timedelta

def generate_strategic_logs(output_dir="アイデアノート/PoC_Sandbox/data/raw_event_logs", num_logs=100):
    """
    戦略ループの分析対象となる、多様なダミーイベントログを生成する。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    user_ids = [f"user_{random.randint(100, 200)}" for _ in range(10)]
    product_ids = [f"prod_{random.randint(1000, 1050)}" for _ in range(10)]
    error_messages = [
        "Database connection timed out.",
        "Payment gateway API returned 503 Service Unavailable.",
        "User authentication failed: invalid token.",
        "Disk space is critically low on server node-A.",
        "Unexpected null pointer exception in inventory service.",
        "Failed to process message from queue: malformed JSON."
    ]
    ip_addresses = [f"192.168.1.{random.randint(1,20)}" for _ in range(5)] # 意図的に重複させる

    for i in range(1, num_logs + 1):
        log_type = random.choice(["purchase", "login_failure", "system_error"])
        
        timestamp = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        
        log_entry = {
            "log_id": f"log_{i:03d}",
            "timestamp": timestamp.isoformat(),
        }

        if log_type == "purchase":
            log_entry.update({
                "event_type": "item_purchase",
                "user_id": random.choice(user_ids),
                "details": {
                    "product_id": random.choice(product_ids),
                    "quantity": random.randint(1, 3),
                    "price": round(random.uniform(50.0, 200.0), 2),
                    "success": random.choices([True, False], weights=[9, 1], k=1)[0] # 10%で失敗
                }
            })
        elif log_type == "login_failure":
            log_entry.update({
                "event_type": "user_login_attempt",
                "user_id": random.choice(user_ids),
                 "details": {
                    "ip_address": random.choice(ip_addresses),
                    "reason": "Invalid credentials",
                    "success": False
                }
            })
        elif log_type == "system_error":
             log_entry.update({
                "event_type": "service_error",
                "service": random.choice(["database", "api_gateway", "auth_service", "inventory_service"]),
                 "details": {
                    "error_code": random.choice([500, 503, 401]),
                    "message": random.choice(error_messages),
                    "severity": random.choice(["warning", "critical", "error"])
                }
            })
        
        file_path = os.path.join(output_dir, f"log_{i:03d}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=4)

    print(f"{num_logs} strategic log files generated in {output_dir}")

if __name__ == '__main__':
    generate_strategic_logs() 