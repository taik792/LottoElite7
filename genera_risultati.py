import json

# ===== CARICA DATI =====
with open("estrazioni.json") as f:
    dati = json.load(f)

risultati = []

# ===== CALCOLO =====
for ruota, estrazioni in dati.items():
    for estr in estrazioni:

        numeri = estr[:3]

        # score serio (non random)
        score = sum(numeri) + len(set(estr))

        risultati.append({
            "ruota": ruota,
            "numeri": numeri,
            "score": score,
            "ultima": estr
        })

# ===== ORDINA =====
risultati.sort(key=lambda x: x["score"], reverse=True)

# ===== TOP =====
top3 = risultati[:3]

top = []
for t in top3:
    top.append({
        "ruota": t["ruota"],
        "numeri": t["numeri"],
        "score": t["score"]
    })

# ===== JOLLY =====
jolly = {
    "ruota": top3[0]["ruota"],
    "numeri": top3[0]["numeri"]
}

# ===== RUOTE =====
ruote = {}
viste = set()

for r in risultati:
    if r["ruota"] not in viste:
        viste.add(r["ruota"])
        ruote[r["ruota"]] = {
            "ultima_estrazione": r["ultima"],
            "numeri": r["numeri"],
            "score": r["score"]
        }

# ===== OUTPUT =====
output = {
    "top": top,
    "jolly": jolly,
    "ruote": ruote
}

with open("risultati.json", "w") as f:
    json.dump(output, f, indent=2)