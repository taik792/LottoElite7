import json
from collections import Counter

DISTANZA_MIN = 6
ULTIME_ESTRAZIONI = 20


def carica_estrazioni():
    with open("estrazioni.json", "r") as f:
        return json.load(f)


def prendi_ultime(estrazioni_ruota):
    # prende le ultime N estrazioni (le più recenti)
    return estrazioni_ruota[-ULTIME_ESTRAZIONI:]


def calcola_frequenze(estrazioni):
    freq = Counter()
    for estrazione in estrazioni:
        for n in estrazione:
            freq[n] += 1
    return freq


def applica_filtro_distanza(numeri):
    filtrati = []
    for n in numeri:
        if all(abs(n - x) >= DISTANZA_MIN for x in filtrati):
            filtrati.append(n)
    return filtrati


def genera_terno(freq):
    # ordina per frequenza
    numeri_ordinati = [n for n, _ in freq.most_common()]

    # applica filtro distanza
    filtrati = applica_filtro_distanza(numeri_ordinati)

    # fallback se meno di 3 numeri
    if len(filtrati) < 3:
        return numeri_ordinati[:3]

    return filtrati[:3]


def calcola_score(terno, freq):
    return round(sum(freq[n] for n in terno) * 1.5, 2)


def genera_risultati():
    estrazioni = carica_estrazioni()

    risultati = {
        "top": {},
        "jolly": {},
        "ruote": {}
    }

    classifica = []

    for ruota, dati in estrazioni.items():
        ultime = prendi_ultime(dati)
        freq = calcola_frequenze(ultime)

        terno = genera_terno(freq)
        score = calcola_score(terno, freq)

        risultati["ruote"][ruota] = {
            "ultima_estrazione": ultime[-1],
            "numeri": terno,
            "score": score
        }

        classifica.append((ruota, terno, score, ultime[-1]))

    # TOP 3
    top3 = sorted(classifica, key=lambda x: x[2], reverse=True)[:3]

    for ruota, numeri, score, ultima in top3:
        risultati["top"][ruota] = {
            "numeri": numeri,
            "score": score
        }

    # JOLLY = primo classificato
    if top3:
        r = top3[0]
        risultati["jolly"][r[0]] = {
            "numeri": r[1]
        }

    return risultati


def salva_risultati():
    risultati = genera_risultati()
    with open("risultati.json", "w") as f:
        json.dump(risultati, f, indent=2)


if __name__ == "__main__":
    salva_risultati()