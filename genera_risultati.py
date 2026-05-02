import json
from collections import defaultdict

# ===== CONFIG =====
FINESTRA = 20
PESO_RECENTE = 2.0
PENALITA_ULTIMA = 0.4
BONUS_RITARDO = 0.25

# ===== FUNZIONE DISTANZA =====
def distanza_ok(numeri):
    numeri = sorted(numeri)
    for i in range(len(numeri)-1):
        if abs(numeri[i] - numeri[i+1]) < 3:
            return False
    return True

# ===== CARICA DATI =====
with open("estrazioni.json") as f:
    dati = json.load(f)

ruote = {}

# ===== ANALISI =====
for ruota, estrazioni in dati.items():

    # inverti: recente → vecchio
    estrazioni = estrazioni[::-1]

    ultime = estrazioni[:FINESTRA]

    score_numeri = defaultdict(float)

    # ===== PESO TEMPORALE =====
    for idx, estr in enumerate(ultime):
        peso = PESO_RECENTE - (idx / FINESTRA)

        for n in estr:
            score_numeri[n] += peso

    # ===== PENALITA ULTIMA =====
    ultima = ultime[0]
    for n in ultima:
        if n in score_numeri:
            score_numeri[n] *= PENALITA_ULTIMA

    # ===== RITARDI =====
    ritardi = {}
    for numero in range(1, 91):
        ritardo = 0
        for estr in ultime:
            if numero in estr:
                break
            ritardo += 1
        ritardi[numero] = ritardo

    for n in score_numeri:
        score_numeri[n] += ritardi[n] * BONUS_RITARDO

    # ===== SELEZIONE TOP3 CON FILTRO =====
    candidati = sorted(score_numeri.items(), key=lambda x: x[1], reverse=True)

    top3 = []
    for n, _ in candidati:
        top3.append(n)
        if len(top3) == 3:
            if distanza_ok(top3):
                break
            else:
                top3.pop()

    score = round(sum(score_numeri[n] for n in top3), 2)

    ruote[ruota] = {
        "numeri": top3,
        "score": score,
        "ultima_estrazione": ultima
    }

# ===== TOP GENERALE =====
top = sorted(
    [{"ruota": r, **d} for r, d in ruote.items()],
    key=lambda x: x["score"],
    reverse=True
)[:3]

# ===== JOLLY =====
jolly = {
    "ruota": top[0]["ruota"],
    "numeri": top[0]["numeri"]
}

# ===== OUTPUT =====
output = {
    "top": top,
    "jolly": jolly,
    "ruote": ruote
}

with open("risultati.json", "w") as f:
    json.dump(output, f, indent=2)

print("OK GENERATO MOTORE 9 PRO STABILE")