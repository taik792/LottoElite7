import json
from itertools import combinations

with open("estrazioni.json") as f:
    estrazioni = json.load(f)

print("\nANALISI AMBI ULTIME 200 ESTRAZIONI\n")

for ruota in estrazioni:

    dati = estrazioni[ruota][-200:]   # ultime 200 estrazioni

    conteggio = {}

    for estrazione in dati:

        ambi = combinations(estrazione,2)

        for a in ambi:

            a = tuple(sorted(a))

            conteggio[a] = conteggio.get(a,0)+1

    top = sorted(conteggio.items(), key=lambda x:x[1], reverse=True)[:10]

    print("\nRUOTA:", ruota)

    for ambo, n in top:

        print(ambo,"uscito",n,"volte nelle ultime 200")