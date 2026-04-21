import json
from datetime import datetime

with open("risultati.json") as f:
    risultati = json.load(f)

with open("estrazioni.json") as f:
    estrazioni = json.load(f)

try:
    with open("storico.json") as f:
        storico = json.load(f)
except:
    storico = []

oggi = str(datetime.now())

for ruota, dati in risultati.items():

    ambo = dati["ambo"]
    ultima = estrazioni[ruota][-1]

    presi = [n for n in ambo if n in ultima]

    esito = "❌"
    if len(presi) == 2:
        esito = "🎯 AMBO"
    elif len(presi) == 1:
        esito = "✔ 1 numero"

    storico.append({
        "data": oggi,
        "ruota": ruota,
        "ambo": ambo,
        "estrazione": ultima,
        "esito": esito
    })

with open("storico.json", "w") as f:
    json.dump(storico, f, indent=2)

print("📊 Tracking aggiornato")