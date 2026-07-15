import json
import urllib.request

API = "http://localhost:8000/api/ingest/"


def send(evt):
    req = urllib.request.Request(
        API,
        data=json.dumps(evt).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        print(evt["order_id"], evt["status"], "->", r.read().decode())


events = [
    {"order_id": "A1", "status": "created",  "event_timestamp": "2025-01-01T10:00:00Z", "source": "payment_processor"},
    {"order_id": "A1", "status": "paid",     "event_timestamp": "2025-01-01T10:05:00Z", "source": "payment_processor"},
    {"order_id": "A1", "status": "paid",     "event_timestamp": "2025-01-01T10:05:00Z", "source": "payment_processor"},  # duplicate
    {"order_id": "B2", "status": "shipped",  "event_timestamp": "2025-01-01T12:00:00Z", "source": "trading_platform"},
    {"order_id": "B2", "status": "processing","event_timestamp": "2025-01-01T11:00:00Z", "source": "payment_processor"},  # old, arrives late
    {"order_id": "C3", "status": "paid",     "event_timestamp": "2025-01-01T09:00:00Z", "source": "payment_processor"},
    {"order_id": "C3", "status": "pending",  "event_timestamp": "2025-01-01T09:30:00Z", "source": "trading_platform"},   # conflict, later wins
]

for e in events:
    send(e)