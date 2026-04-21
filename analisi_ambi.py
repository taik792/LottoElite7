from collections import Counter

FINESTRA = 200  # puoi cambiare: 100 / 200 / 300


# =========================
# CICLOMETRIA VERA (RITARDO)
# =========================
def calcola_ritardi(estrazioni):
    ritardi = {n: None for n in range(1, 91)}

    for i, estrazione in enumerate(estrazioni):
        for numero in estrazione:
            if ritardi[numero] is None:
                ritardi[numero] = i

    # numeri mai usciti → massimo ritardo
    for n in ritardi:
        if ritardi[n] is None:
            ritardi[n] = len(estrazioni)

    return ritardi


# =========================
# SATURAZIONE
# =========================
def calcola_saturazione(numeri):
    freq = Counter(numeri)
    return round(sum(freq.values()) / len(freq), 2)


# =========================
# ANALISI SINGOLA RUOTA
# =========================
def analizza_ruota(nome, estrazioni):

    # 🔥 FIX FONDAMENTALE (tu hai vecchio → nuovo)
    estrazioni = list(reversed(estrazioni))

    # taglio finestra
    estrazioni = estrazioni[:FINESTRA]

    # ultima estrazione (ora è corretta)
    ultima = estrazioni[0]

    # tutti i numeri
    numeri = [n for e in estrazioni for n in e]

    # frequenze
    freq = Counter(numeri)

    # numeri più frequenti (caldi)
    caldi = [n for n, _ in freq.most_common(2)]

    # ambo
    ambo = caldi[:2]

    # ciclometria vera
    ritardi = calcola_ritardi(estrazioni)
    ciclo = [ritardi[ambo[0]], ritardi[ambo[1]]]

    # saturazione
    saturazione = calcola_saturazione(numeri)

    # indice (frequenza / ritardo)
    indice = [
        round(freq[ambo[0]] / (ciclo[0] + 1), 2),
        round(freq[ambo[1]] / (ciclo[1] + 1), 2),
    ]

    return {
        "ruota": nome,
        "ultima": ultima,
        "caldi": caldi,
        "ambo": ambo,
        "ciclo": ciclo,
        "indice": indice,
        "saturazione": saturazione,
    }


# =========================
# ANALISI COMPLETA
# =========================
def analizza_ruote(dati):
    risultati = {}

    for ruota, estrazioni in dati.items():
        risultati[ruota] = analizza_ruota(ruota, estrazioni)

    return risultati