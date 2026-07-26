"""
Motore 9 - SCAFFOLD iniziale

NOTA:
Questo file è una base strutturata per il nuovo motore.
Mantiene la stessa filosofia di input/output del Motore 8 ma è
pensato per essere esteso con:
- score adattivo
- memoria delle previsioni
- penalità dinamiche
- backtest

Da completare progressivamente.
"""

import json
from itertools import combinations

TOP_JOLLY = 3
TOP_FORTE = 5
COLPI_VALIDITA = 6

with open("estrazioni.json","r",encoding="utf-8") as f:
    estrazioni = json.load(f)

def frequenza(numero, storico, finestra=20):
    return sum(1 for e in storico[-finestra:] if numero in e)

def ritardo(numero, storico):
    for i, e in enumerate(reversed(storico), start=1):
        if numero in e:
            return i
    return len(storico)

def distanza(n1,n2):
    d=abs(n1-n2)
    return min(d,90-d)

def score_ambo(n1,n2,storico):
    score=0.0
    score += frequenza(n1,storico,10)*8
    score += frequenza(n2,storico,10)*8
    score += ritardo(n1,storico)*2
    score += ritardo(n2,storico)*2

    d=distanza(n1,n2)
    if d in (9,18,27,36,45):
        score+=80
    if d<=2:
        score-=40

    ultimi244=storico[-244:]
    if not any(n1 in e and n2 in e for e in ultimi244):
        score+=60

    return round(score,2)

def colpi_rimanenti(storico,ambo):
    colpi=0
    for e in reversed(storico):
        colpi+=1
        if ambo[0] in e or ambo[1] in e:
            break
    return max(0,COLPI_VALIDITA-colpi)

ordine=["Bari","Cagliari","Firenze","Genova","Milano","Napoli","Palermo","Roma","Torino","Venezia"]

risultati=[]
usati=set()

for ruota in ordine:
    storico=estrazioni[ruota]
    candidati=[]
    for a,b in combinations(range(1,91),2):
        key=(a,b)
        if key in usati:
            continue
        s=score_ambo(a,b,storico)
        candidati.append((s,[a,b]))
    candidati.sort(reverse=True,key=lambda x:x[0])

    for s,ambo in candidati:
        cr=colpi_rimanenti(storico,ambo)
        if cr>0:
            usati.add(tuple(ambo))
            risultati.append({
                "ruota":ruota,
                "ambo":ambo,
                "score":s,
                "ultima_estrazione":storico[-1],
                "colpi_rimanenti":cr
            })
            break

jolly=sorted(risultati,key=lambda x:x["score"],reverse=True)[:TOP_JOLLY]
forte=sorted(risultati,key=lambda x:x["score"],reverse=True)[:TOP_FORTE]

out={
    "ruote":risultati,
    "jolly":jolly,
    "ambo_forte":forte,
    "previsioni_attive":[r for r in risultati if r["colpi_rimanenti"]>0]
}

with open("risultati.json","w",encoding="utf-8") as f:
    json.dump(out,f,indent=4,ensure_ascii=False)

print("Motore 9 scaffold completato.")
