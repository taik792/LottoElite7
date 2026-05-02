import json
from collections import defaultdict

# ===== CONFIG =====
FINESTRA = 20          # quante estrazioni considerare
PESO_RECENTE = 2.0     # quanto pesano le più recenti
PENALITA_ULTIMA = 0.6  # penalità se numero nell'ultima estrazione
BONUS_RITARDO = 0.15   # bonus per numeri assenti da più tempo

# ===== CARICA DATI =====
with open("estrazioni.json") as f:
    dati = json.load(f)

ruote = {}

# ===== ANALISI =====
for ruota, estrazioni in dati.items():

    # inverti → recente prima
    estrazioni = estrazioni[::-1]

    ultime = estrazioni[:FINESTRA]

    score_numeri = defaultdict(float)

    # ===== CALCOLO PESI =====
    for idx, estr in enumerate(ultime):

        # peso temporale (più recente = più peso)
        peso = PESO_RECENTE - (idx / FINESTRA)

        for n in estr:
            score_numeri[n] += peso

    # ===== PENALITA ULTIMA ESTRAZIONE =====
    ultima = ultime[0]
    for n in ultima:
        score_numeri[n] *= PENALITA_ULTIMA

    # ===== BONUS RITARDO =====
    # trova quanto tempo è passato dall'ultima uscita
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

    # ===== SELEZIONE TOP 3 =====
    top3 = sorted(score_numeri.items(), key=lambda x: x[1], reverse=True)[:3]
    numeri = [n for n, _ in top3]

    score = round(sum(v for _, v in top3), 2)

    ruote[ruota] = {
        "numeri": numeri,
        "score": score,
        "ultima_estrazione": ultima
    }

# ===== TOP GENERALE =====
top = sorted(
    [{"ruota": r, **d} for r, d in ruote.items()],
    key=lambda x: x["score"],
    reverse=True
)[:3]

# ===== JOLLY (miglior ruota) =====
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

print("GENERATO MOTORE 9 PRO EVOLUTO")