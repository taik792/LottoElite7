import json

with open("estrazioni.json") as f:
    estrazioni = json.load(f)

ruote = list(estrazioni.keys())

test_totali = 0

caldi_presenze = 0
caldi_ambi = 0

freddi_presenze = 0
freddi_ambi = 0

ciclo_presenze = 0
ciclo_ambi = 0

for ruota in ruote:

    dati = estrazioni[ruota]

    for i in range(30, len(dati)-1):

        storico = dati[:i]
        target = dati[i]

        ultime = storico[-30:]

        freq = {}

        for estr in ultime:
            for n in estr:
                freq[n] = freq.get(n,0)+1

        ordinati = sorted(freq.items(), key=lambda x:x[1], reverse=True)

        numeri_caldi = [ordinati[0][0], ordinati[1][0]]
        numeri_freddi = [ordinati[-1][0], ordinati[-2][0]]

        # ciclometria semplice
        ciclo = []
        for n in ultime[-1]:
            ciclo.append((n + 30) % 90 or 90)

        ciclo = ciclo[:2]

        # controlli CALDI
        if numeri_caldi[0] in target or numeri_caldi[1] in target:
            caldi_presenze += 1

        if numeri_caldi[0] in target and numeri_caldi[1] in target:
            caldi_ambi += 1

        # controlli FREDDI
        if numeri_freddi[0] in target or numeri_freddi[1] in target:
            freddi_presenze += 1

        if numeri_freddi[0] in target and numeri_freddi[1] in target:
            freddi_ambi += 1

        # controlli CICLOMETRIA
        if ciclo[0] in target or ciclo[1] in target:
            ciclo_presenze += 1

        if ciclo[0] in target and ciclo[1] in target:
            ciclo_ambi += 1

        test_totali += 1


print("\nTEST COMPLETATO")
print("Test totali:", test_totali)

print("\n--- NUMERI CALDI ---")
print("Presenze:", caldi_presenze)
print("Ambi:", caldi_ambi)
print("Percentuale ambi:", round((caldi_ambi/test_totali)*100,3),"%")

print("\n--- NUMERI FREDDI ---")
print("Presenze:", freddi_presenze)
print("Ambi:", freddi_ambi)
print("Percentuale ambi:", round((freddi_ambi/test_totali)*100,3),"%")

print("\n--- CICLOMETRIA ---")
print("Presenze:", ciclo_presenze)
print("Ambi:", ciclo_ambi)
print("Percentuale ambi:", round((ciclo_ambi/test_totali)*100,3),"%")