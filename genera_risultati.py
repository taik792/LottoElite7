# genera_risultati.py
# MOTORE 7 - TERNO STRATEGICO
# 3 numeri per ruota TOP
# obiettivo: aumentare probabilità AMBO + possibilità TERNO

import json
from itertools import combinations

RUOTE_ORDINE = [
    "Bari",
    "Cagliari",
    "Firenze",
    "Genova",
    "Milano",
    "Napoli",
    "Palermo",
    "Roma",
    "Torino",
    "Venezia"
]


def carica_estrazioni():
    with open("estrazioni.json", "r", encoding="utf-8") as f:
        return json.load(f)


def score_numero(numero, storico_ruota):
    """
    Score:
    - frequenza storica
    - ritardo utile
    """

    frequenza = 0
    ritardo = 0

    for estrazione in storico_ruota:
        if numero in estrazione:
            frequenza += 1

    trovato = False
    for i, estrazione in enumerate(reversed(storico_ruota), start=1):
        if numero in estrazione:
            ritardo = i
            trovato = True
            break

    if not trovato:
        ritardo = len(storico_ruota)

    return (frequenza * 20) + (ritardo * 5)


def trova_terno_forte(nome_ruota, storico_ruota):
    """
    Regole:
    - esclude numeri ultima estrazione
    - evita numeri troppo vicini
    - crea TERNO e non solo AMBO
    """

    if not storico_ruota:
        return None

    ultima_estrazione = storico_ruota[-1]

    candidati = [
        n for n in range(1, 91)
        if n not in ultima_estrazione
    ]

    # ordina per score
    candidati = sorted(
        candidati,
        key=lambda n: score_numero(n, storico_ruota),
        reverse=True
    )

    terno = []

    for numero in candidati:
        valido = True

        for già in terno:
            if abs(numero - già) < 5:
                valido = False
                break

        if valido:
            terno.append(numero)

        if len(terno) == 3:
            break

    if len(terno) < 3:
        return None

    score_totale = sum(
        score_numero(n, storico_ruota)
        for n in terno
    )

    return {
        "ruota": nome_ruota,
        "numeri": sorted(terno),
        "score": score_totale,
        "ultima_estrazione": ultima_estrazione
    }


def genera_risultati():
    dati = carica_estrazioni()

    risultati = []

    for ruota in RUOTE_ORDINE:
        if ruota not in dati:
            continue

        risultato = trova_terno_forte(
            ruota,
            dati[ruota]
        )

        if risultato:
            risultati.append(risultato)

    risultati = sorted(
        risultati,
        key=lambda x: x["score"],
        reverse=True
    )

    top = risultati[:3]
    jolly = top[:1]

    output = {
        "top": top,
        "jolly": jolly,
        "terno_forte": risultati
    }

    with open("risultati.json", "w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("Motore 7 - risultati.json generato correttamente")


if __name__ == "__main__":
    genera_risultati()