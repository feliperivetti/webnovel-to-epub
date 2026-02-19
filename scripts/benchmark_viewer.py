import json
import os
import sys
from datetime import datetime
from collections import defaultdict

# Fixed path resolution to find benchmarks.jsonl relative to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATH = os.path.join(BASE_DIR, "benchmarks.jsonl")

def load_benchmarks():
    if not os.path.exists(FILE_PATH):
        print(f"❌ No benchmarks found at {FILE_PATH}")
        return []

    data = []
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except Exception:
                continue
    return data

def print_summary(data):
    if not data: return
    
    total_runs = len(data)
    successes = [r for r in data if r.get('status') == 'success']
    
    print("\n📈 BENCHMARK SUMMARY")
    print("-" * 40)
    print(f"Total Runs:      {total_runs}")
    print(f"Success Rate:    {(len(successes)/total_runs)*100:.1f}%")
    
    if successes:
        avg_rate = sum(r.get('chapters_per_second', 0) for r in successes) / len(successes)
        best_run = max(successes, key=lambda x: x.get('chapters_per_second', 0))
        
        print(f"Avg Rate:        {avg_rate:.2f} chapters/sec")
        print(f"Best Perf:       {best_run.get('chapters_per_second')} c/s ({best_run.get('config', {}).get('proxy_mode')})")

    # Group by Proxy Mode
    proxy_stats = defaultdict(list)
    for r in successes:
        mode = r.get('config', {}).get('proxy_mode', 'unknown')
        proxy_stats[mode].append(r.get('chapters_per_second', 0))
    
    print("\n🌍 PERFORMANCE BY PROXY MODE")
    for mode, rates in proxy_stats.items():
        avg = sum(rates) / len(rates)
        print(f"  {mode:<12}: {avg:.2f} c/s avg")

def print_detailed_table(data):
    print("\n📋 DETAILED RUNS")
    print(f"{'TIMESTAMP':<19} | {'DOMAIN':<15} | {'CHAPS':<5} | {'DUR':<6} | {'RATE':<8} | {'MODE'}")
    print("-" * 80)

    for record in reversed(data[-20:]): # Show last 20
        ts = datetime.fromtimestamp(record.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M')
        
        # Extract domain from URL
        target = record.get('target_url', 'unknown')
        domain = target.split('//')[-1].split('/')[0].replace('www.', '')[:15]
        
        caps = record.get('chapters_count', 0)
        dur = f"{record.get('duration_s', 0)}s"
        rate = f"{record.get('chapters_per_second', 0)} c/s"
        
        config = record.get('config', {})
        mode = f"{config.get('proxy_mode')} (W:{config.get('workers')})"
        
        status_icon = "✅" if record.get('status') == 'success' else "❌"
        
        print(f"{ts:<19} | {domain:<15} | {caps:<5} | {dur:<6} | {rate:<8} | {mode} {status_icon}")

if __name__ == "__main__":
    benchmarks = load_benchmarks()
    if benchmarks:
        print_detailed_table(benchmarks)
        print_summary(benchmarks)
    else:
        sys.exit(1)
