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
    Score misto:
    + frequenza storica
    + ritardo utile
    """

    frequenza = 0
    ritardo = 0

    # frequenza totale
    for estrazione in storico_ruota:
        if numero in estrazione:
            frequenza += 1

    # ritardo: quante estrazioni fa è uscito
    trovato = False
    for i, estrazione in enumerate(reversed(storico_ruota), start=1):
        if numero in estrazione:
            ritardo = i
            trovato = True
            break

    if not trovato:
        ritardo = len(storico_ruota)

    # score finale
    score = (frequenza * 20) + (ritardo * 5)

    return score


def trova_ambo_forte(nome_ruota, storico_ruota):
    """
    Regole:
    - esclude numeri ultima estrazione
    - evita numeri troppo vicini
    - evita consecutivi
    - sceglie miglior score
    """

    if not storico_ruota:
        return None

    ultima_estrzione = storico_ruota[-1]

    candidati = [
        n for n in range(1, 91)
        if n not in ultima_estrzione
    ]

    miglior_ambo = None
    miglior_score = -1

    for n1, n2 in combinations(candidati, 2):

        # sicurezza doppia
        if n1 in ultima_estrzione or n2 in ultima_estrzione:
            continue

        # evita numeri consecutivi / troppo vicini
        if abs(n1 - n2) < 8:
            continue

        score = (
            score_numero(n1, storico_ruota)
            + score_numero(n2, storico_ruota)
        )

        if score > miglior_score:
            miglior_score = score
            miglior_ambo = [n1, n2]

    if not miglior_ambo:
        return None

    return {
        "ruota": nome_ruota,
        "numeri": miglior_ambo,
        "score": miglior_score,
        "ultima_estrazione": ultima_estrzione
    }


def genera_risultati():
    dati = carica_estrazioni()

    risultati = []

    for ruota in RUOTE_ORDINE:
        if ruota not in dati:
            continue

        risultato = trova_ambo_forte(
            ruota,
            dati[ruota]
        )

        if risultato:
            risultati.append(risultato)

    # ordinamento TOP per score
    top = sorted(
        risultati,
        key=lambda x: x["score"],
        reverse=True
    )[:3]

    jolly = top[:1]

    output = {
        "top": top,
        "jolly": jolly,
        "ambo_forte": risultati
    }

    with open("risultati.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("risultati.json generato correttamente")


if __name__ == "__main__":
    genera_risultati()