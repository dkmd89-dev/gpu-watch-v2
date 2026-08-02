import re

# Lese die originale Datei
with open('app/categories/detectors/storage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze den CONNECTOR um auch "SATA" und andere Wörter zu erlauben
# Original: _CONNECTOR = r"[\s,:/\-()]*"
# Neu: Erlaubt auch Wörter wie "SATA" zwischen Größe und SSD
old_connector = '_CONNECTOR = r"[\\s,:/\\-()]*"'
new_connector = '_CONNECTOR = r"[\\s,:/\\-()]*(?:SATA\\s+)?"'

content = content.replace(old_connector, new_connector)

# Schreibe die Datei zurück
with open('app/categories/detectors/storage.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ storage.py wurde aktualisiert!')
