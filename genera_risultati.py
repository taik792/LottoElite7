import json
from collections import Counter

# ===== CARICA DATI =====
with open("estrazioni.json") as f:
    dati = json.load(f)

ruote = {}

# ===== ANALISI =====
for ruota, estrazioni in dati.items():

    # 🔥 FIX: inverti ordine (ora: recente → vecchio)
    estrazioni = estrazioni[::-1]

    # prendi ultime 20 estrazioni REALI
    recenti = estrazioni[:20]

    numeri = []
    for estr in recenti:
        numeri.extend(estr)

    conteggio = Counter(numeri)

    # prendi top 3
    top3 = [n for n, _ in conteggio.most_common(3)]

    score = sum(conteggio[n] for n in top3)

    ruote[ruota] = {
        "numeri": top3,
        "score": score,
        "ultima_estrazione": estrazioni[0]
    }

# ===== TOP =====
top = sorted(
    [{"ruota": r, **d} for r, d in ruote.items()],
    key=lambda x: x["score"],
    reverse=True
)[:3]

# ===== JOLLY =====
jolly = top[0]

# ===== OUTPUT =====
output = {
    "top": top,
    "jolly": jolly,
    "ruote": ruote
}

with open("risultati.json", "w") as f:
    json.dump(output, f, indent=2)

print("OK GENERATO")