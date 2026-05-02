import json
import random

# ===== ANALISI STORICO =====
def analizza_storico(storico):

    freq = {i:0 for i in range(1,91)}
    ritardo = {i:0 for i in range(1,91)}

    for estrazione in storico:

        for n in estrazione:
            freq[n] += 1
            ritardo[n] = 0

        for i in range(1,91):
            if i not in estrazione:
                ritardo[i] += 1

    return freq, ritardo


# ===== GENERA TERNO PRO =====
def genera_terno(freq, ritardo, ultima):

    pool = []

    for i in range(1,91):

        if i in ultima:
            continue

        valore = ritardo[i]*3 + (10 - freq[i])*2
        pool.append((i, valore))

    pool.sort(key=lambda x: x[1], reverse=True)

    candidati = [n for n,_ in pool[:25]]

    terno = []

    while len(terno) < 3:
        n = random.choice(candidati)
        if n not in terno:
            terno.append(n)

    return terno


# ===== SCORE =====
def calcola_score(terno, freq, ritardo):

    score = 0

    for n in terno:
        score += ritardo[n]*4
        score += (10 - freq[n])*2

    score += abs(terno[0]-terno[1])
    score += abs(terno[1]-terno[2])

    score += random.randint(0,10)

    return score


# ===== GENERATORE PRINCIPALE =====
def genera_risultati(dati_storici):

    output = {"top": {}}

    for ruota, storico in dati_storici.items():

        freq, ritardo = analizza_storico(storico)

        ultima = storico[0]

        terno = genera_terno(freq, ritardo, ultima)

        score = calcola_score(terno, freq, ritardo)

        output["top"][ruota] = {
            "ultima_estrazione": ultima,
            "numeri": terno,
            "score": score
        }

    return output


# ===== ESEMPIO DATI =====
dati_storici = {
    "Bari": [
        [42,46,49,16,36],
        [2,58,76,30,50],
        [68,50,33,31,23]
    ],
    "Genova": [
        [21,43,79,20,7],
        [1,8,15,17,38],
        [22,34,29,35,86]
    ]
}


# ===== ESECUZIONE =====
risultati = genera_risultati(dati_storici)

with open("risultati.json", "w") as f:
    json.dump(risultati, f, indent=2)

print("File risultati.json generato.")