import json
import os

DATA_DIR = "data"

def trim_last_50_entries(file_path, backup=True):
    """Löscht die letzten 50 Einträge aus einer JSON-Datei."""
    
    full_path = os.path.join(DATA_DIR, file_path)
    
    # Prüfen ob Datei existiert
    if not os.path.exists(full_path):
        print(f"❌ Datei nicht gefunden: {full_path}")
        return
    
    # Backup erstellen
    if backup:
        backup_path = full_path + ".backup"
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Backup erstellt: {backup_path}")
    
    # Datei laden
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data)
    print(f"📊 Datei: {file_path}")
    print(f"   Original: {original_count} Einträge")
    
    if original_count <= 50:
        new_data = []
        print(f"   ⚠️  Weniger als 50 Einträge, lösche alle {original_count}")
    else:
        new_data = data[:-50]
        print(f"   Nach Löschung: {len(new_data)} Einträge (-50)")
    
    # Datei überschreiben
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ {full_path} aktualisiert\n")

# Beide Dateien verarbeiten
trim_last_50_entries("found.json", backup=True)
trim_last_50_entries("seen.json", backup=True)

print("🎯 Fertig! Die letzten 50 Einträge wurden gelöscht.")
