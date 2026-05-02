import json

# -----------------------------
# CARICA STORICO
# -----------------------------
with open("estrazioni.json") as f:
    storico = json.load(f)

# -----------------------------
# FREQUENZA
# -----------------------------
def calcola_frequenze(estrazioni):
    freq = {n:0 for n in range(1,91)}
    for estr in estrazioni:
        for n in estr:
            freq[n] += 1
    return freq

# -----------------------------
# RITARDO (quante estrazioni non esce)
# -----------------------------
def calcola_ritardi(estrazioni):
    ritardi = {}
    for n in range(1,91):
        ritardo = 0
        for estr in estrazioni:
            if n in estr:
                break
            ritardo += 1
        ritardi[n] = ritardo
    return ritardi

# -----------------------------
# GENERA TERNO (DETERMINISTICO)
# -----------------------------
def genera_terno(freq, ritardi):
    numeri = list(range(1,91))

    # score combinato
    ranking = sorted(
        numeri,
        key=lambda n: (ritardi[n]*2 - freq[n]),
        reverse=True
    )

    # prendi i migliori 3
    return ranking[:3]

# -----------------------------
# SCORE
# -----------------------------
def calcola_score(terno, freq, ritardi):
    score = 0

    for n in terno:
        score += ritardi[n]*3
        score -= freq[n]

    # distanza numerica
    score += max(terno) - min(terno)

    return score

# -----------------------------
# GENERAZIONE RUOTE
# -----------------------------
ruote = {}

for ruota, estrazioni in storico.items():
    freq = calcola_frequenze(estrazioni)
    ritardi = calcola_ritardi(estrazioni)

    terno = genera_terno(freq, ritardi)
    score = calcola_score(terno, freq, ritardi)

    ruote[ruota] = {
        "ultima_estrazione": estrazioni[0],
        "numeri": terno,
        "score": score
    }

# -----------------------------
# ORDINAMENTO
# -----------------------------
ordinate = sorted(ruote.items(), key=lambda x: x[1]["score"], reverse=True)

top3 = ordinate[:3]
jolly = top3[0]

output = {
    "top": dict(top3),
    "jolly": {jolly[0]: jolly[1]},
    "ruote": ruote
}

# -----------------------------
# SALVA
# -----------------------------
with open("risultati.json", "w") as f:
    json.dump(output, f, indent=2)

print("✅ MOTORE 9 PRO VERO ATTIVO")