import json
import os
from datetime import datetime

FILE_PATH = "benchmarks.jsonl"

def load_benchmarks():
    if not os.path.exists(FILE_PATH):
        print("No benchmarks found yet.")
        return []

    data = []
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except Exception:
                continue
    return data

def print_table(data):
    # Header
    print(f"{'TIMESTAMP':<20} | {'TARGET':<20} | {'CHAPTERS':<8} | {'DURATION':<10} | {'RATE (c/s)':<10} | {'CONFIG':<30}")
    print("-" * 110)

    for record in data:
        ts = datetime.fromtimestamp(record.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')
        target = record.get('target_url', 'unknown')[:18]
        caps = record.get('chapters_count', 0)
        dur = f"{record.get('duration_s', 0)}s"
        rate = record.get('chapters_per_second', 0)
        
        config = record.get('config', {})
        conf_str = f"P:{config.get('proxy_mode')} W:{config.get('workers')}"
        
        print(f"{ts:<20} | {target:<20} | {caps:<8} | {dur:<10} | {rate:<10} | {conf_str:<30}")

if __name__ == "__main__":
    benchmarks = load_benchmarks()
    if benchmarks:
        print_table(benchmarks)
