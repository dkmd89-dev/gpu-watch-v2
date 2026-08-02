cd /home/robin/gpu-watch-v2
cat > test_sata.py << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

from matcher import load_rules, evaluate

cfg = load_rules('app/rules')
print("Geladene Kategorien:", cfg.get('categories', []))

title = 'Samsung 870 EVO 500GB SATA SSD 2.5 Zoll'
price = 20.0
r = evaluate(title, price, cfg)

print(f"Title: {title}")
print(f"Matched: {r.matched}")
print(f"Category: {r.category}")
print(f"Rule: {r.rule_label}")
print(f"Price history model: {r.price_history_model}")
EOF

python3 test_sata.py
