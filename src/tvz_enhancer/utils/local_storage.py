import os
import json
from collections import defaultdict

# Definiraj putanju do datoteke za lokalne događaje
local_data_path = os.path.join(os.path.dirname(__file__), "../resources/data/kalendar_events.json")

def save_local_events(events):
    try:
        serializable_events = {key: value for key, value in events.items()}
        print(f"Pokušavam spremiti događaje u: {local_data_path}")
        print(f"Sadržaj za spremanje: {serializable_events}")
        with open(local_data_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_events, f, ensure_ascii=False, indent=4)
        print("Događaji uspješno spremljeni.")
    except Exception as e:
        print(f"Greška prilikom spremanja: {e}")




def load_local_events():
    if os.path.exists(local_data_path):
        with open(local_data_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return data
            except json.JSONDecodeError:
                print("Greška prilikom učitavanja JSON-a. Datoteka može biti oštećena.")
                return {}
    return {}

