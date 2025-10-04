# README.md
# wap-mha-yea-matt-repo

Simple example: two independent "egg collector" components that produce JSON records, and one aggregator that collects their outputs and writes a combined result.

How to run (from repo root):
1. cd src
2. python run_collectors.py

What each file does:
- collector_a.py: simulates Collector A, writes JSON to stdout
- collector_b.py: simulates Collector B, writes JSON to stdout
- aggregator.py: imports collectors, runs them (concurrently), normalizes and writes combined JSON to combined_output.json
- run_collectors.py: entrypoint that runs aggregator and prints result
