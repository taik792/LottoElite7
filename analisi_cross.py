def analisi_cross_ruote(dati):
    segnali = []

    ruote = list(dati.keys())

    for i, ruota1 in enumerate(ruote):
        ultima1 = dati[ruota1][-1]

        for j, ruota2 in enumerate(ruote):
            if ruota1 == ruota2:
                continue

            ultime2 = dati[ruota2][-3:]  # guardiamo le ultime 3

            numeri2 = [n for estrazione in ultime2 for n in estrazione]

            match = [n for n in ultima1 if n in numeri2]

            if match:
                segnali.append({
                    "da": ruota1,
                    "a": ruota2,
                    "numeri": match,
                    "forza": len(match)
                })

    return segnali