import json
from collections import Counter

FINESTRA = 50  # puoi mettere 40–60

RUOTE = [
    "Bari","Cagliari","Firenze","Genova","Milano",
    "Napoli","Palermo","Roma","Torino","Venezia"
]

def carica_dati():
    with open("estrazioni.json", "r") as f:
        return json.load(f)

def ultime_estrazioni_ruota(dati, ruota):
    return dati[ruota][-FINESTRA:]

def ultima_estrazione(dati, ruota):
    return dati[ruota][-1]

def frequenze(estrazioni):
    c = Counter()
    for estrazione in estrazioni:
        c.update(estrazione)
    return c

def ritardi(estrazioni):
    rit = {}
    tutte = set(range(1, 91))

    for numero in tutte:
        ritardo = 0
        trovato = False

        for estrazione in reversed(estrazioni):
            if numero in estrazione:
                trovato = True
                break
            ritardo += 1

        if not trovato:
            ritardo = len(estrazioni)

        rit[numero] = ritardo

    return rit

def penalizza_recenti(estrazioni):
    penalita = {}
    recenti = estrazioni[-3:]  # ultime 3

    for i, estrazione in enumerate(reversed(recenti)):
        peso = (3 - i) * 5  # più recente = più penalità
        for n in estrazione:
            penalita[n] = penalita.get(n, 0) + peso

    return penalita

def calcola_score(freq, rit, penalita):
    score = {}

    for n in range(1, 91):
        f = freq.get(n, 0)
        r = rit.get(n, 0)
        p = penalita.get(n, 0)

        # formula bilanciata
        score[n] = (f * 2) + (r * 1.5) - p

    return score

def scegli_top(score, esclusi):
    validi = {k: v for k, v in score.items() if k not in esclusi}
    ordinati = sorted(validi.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in ordinati[:3]]

def genera():
    dati = carica_dati()
    risultati = {}

    for ruota in RUOTE:
        estrazioni = ultime_estrazioni_ruota(dati, ruota)
        ultima = ultima_estrazione(dati, ruota)

        freq = frequenze(estrazioni)
        rit = ritardi(estrazioni)
        penalita = penalizza_recenti(estrazioni)

        score = calcola_score(freq, rit, penalita)

        top3 = scegli_top(score, ultima)

        risultati[ruota] = {
            "ultima_estrazione": ultima,
            "terno": top3,
            "score": int(sum(score[n] for n in top3))
        }

    # TOP generale
    top_global = sorted(
        risultati.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )[:3]

    risultati_finali = {
        "top": {k: v for k, v in top_global},
        "ruote": risultati
    }

    with open("risultati.json", "w") as f:
        json.dump(risultati_finali, f, indent=2)

    print("Motore 9 completato.")

if __name__ == "__main__":
    genera()