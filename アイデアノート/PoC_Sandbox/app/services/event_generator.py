import random
from typing import Dict, Any

def generate_dummy_event() -> Dict[str, Any]:
    """
    ダミーのイベントデータを生成する。
    """
    event_types = ["user_login", "item_purchase", "system_alert"]
    event_type = random.choice(event_types)
    
    event_payload = {
        "event_type": event_type,
        "raw_event": {}
    }

    if event_type == "user_login":
        event_payload["raw_event"] = {
            "user_id": f"user_{random.randint(100, 999)}",
            "ip_address": f"192.168.1.{random.randint(1, 254)}"
        }
    elif event_type == "item_purchase":
        event_payload["raw_event"] = {
            "product_id": f"prod_{random.randint(1000, 9999)}",
            "quantity": random.randint(1, 5),
            "price": round(random.uniform(10.0, 500.0), 2)
        }
    elif event_type == "system_alert":
        event_payload["raw_event"] = {
            "service": random.choice(["database", "api_gateway", "auth_service"]),
            "severity": random.choice(["info", "warning", "critical"]),
            "message": "Service is experiencing high latency."
        }
        
    return event_payload 