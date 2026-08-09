import json
import os
from datetime import datetime

RUOTE = [
    "BARI", "CAGLIARI", "FIRENZE", "GENOVA", "MILANO",
    "NAPOLI", "PALERMO", "ROMA", "TORINO", "VENEZIA", "NAZIONALE"
]

# Numero di colpi utilizzato per la valutazione storica.
CICLO_MAX = 9

# Valori candidati per la trasformazione isotopica/sommativa.
# Il motore sceglie automaticamente quello con il miglior backtest.
SHIFT_CANDIDATI = list(range(1, 46))


def fuori_90(numero):
    numero = int(numero)
    while numero > 90:
        numero -= 90
    while numero <= 0:
        numero += 90
    return numero


def diametrale(numero):
    numero = int(numero)
    return numero + 45 if numero <= 45 else numero - 45


def prepara_ruote(archivio):
    return {
        str(k).upper(): v
        for k, v in archivio.items()
        if isinstance(v, list)
    }


def numeri_estrazione(lista, indice):
    if indice < 0 or indice >= len(lista):
        return []
    riga = lista[indice]
    if not isinstance(riga, list):
        return []
    try:
        return [int(x) for x in riga[:5]]
    except (ValueError, TypeError):
        return []


def costruisci_ambo(origine, shift, metodo):
    ambata = fuori_90(origine + shift)

    if metodo == "DIAMETRALE":
        secondo = diametrale(ambata)
    elif metodo == "SOMMA45":
        secondo = fuori_90(ambata + 45)
    elif metodo == "DIFFERENZA45":
        secondo = fuori_90(ambata - 45)
    else:
        secondo = diametrale(ambata)

    if secondo == ambata:
        return ambata, None

    return ambata, secondo


def valuta_configurazione(lista_origine, lista_target, shift, metodo, fine_idx):
    """
    Backtest walk-forward:
    per ogni estrazione storica fino a fine_idx-1 genera la previsione
    e controlla i successivi CICLO_MAX colpi.
    """
    ambate = 0
    ambi = 0
    vittorie_rapide = 0
    vittorie_ambata = 0
    cicli = 0
    ritardi = []

    # Lasciamo sufficiente spazio per verificare l'intero ciclo.
    ultimo_punto = fine_idx - CICLO_MAX - 1
    if ultimo_punto < 0:
        return None

    for i in range(ultimo_punto + 1):
        origine_nums = numeri_estrazione(lista_origine, i)
        if not origine_nums:
            continue

        origine = origine_nums[0]
        ambata, secondo = costruisci_ambo(origine, shift, metodo)
        if secondo is None:
            continue

        cicli += 1
        trovata_ambata = False
        trovata_ambo = False
        colpo_ambo = None
        colpo_ambata = None

        for c in range(1, CICLO_MAX + 1):
            idx = i + c

            for lista in (lista_origine, lista_target):
                nums = numeri_estrazione(lista, idx)

                if ambata in nums and not trovata_ambata:
                    trovata_ambata = True
                    colpo_ambata = c

                if ambata in nums and secondo in nums and not trovata_ambo:
                    trovata_ambo = True
                    colpo_ambo = c

            if trovata_ambo:
                break

        if trovata_ambo:
            ambi += 1
            ritardi.append(colpo_ambo)
            if colpo_ambo <= 3:
                vittorie_rapide += 1
        elif trovata_ambata:
            ambate += 1
            ritardi.append(colpo_ambata)
            vittorie_ambata += 1

    if cicli == 0:
        return None

    # Score volutamente orientato all'ambo:
    # l'ambata è positiva, ma un ambo secco pesa molto di più.
    # Le vittorie rapide ricevono un bonus.
    percentuale_ambo = ambi / cicli
    percentuale_ambata = ambate / cicli
    percentuale_rapida = vittorie_rapide / cicli

    score = (
        percentuale_ambo * 1000
        + percentuale_rapida * 250
        + percentuale_ambata * 120
    )

    return {
        "score": round(score, 4),
        "cicli": cicli,
        "ambi": ambi,
        "ambate": ambate,
        "vittorie_rapide": vittorie_rapide,
        "percentuale_ambo": round(percentuale_ambo * 100, 2),
        "percentuale_ambata": round(percentuale_ambata * 100, 2),
        "percentuale_rapida": round(percentuale_rapida * 100, 2),
        "ritardi": ritardi
    }


def cerca_migliore_configurazione(archivio_pulito, indice_attuale):
    """
    Prova tutte le coppie di ruote e tutti gli shift.
    L'origine viene presa dal primo numero della ruota origine.
    La previsione viene verificata su origine + ruota target.
    """
    migliori = []

    ruote_disponibili = [
        r for r in RUOTE
        if r in archivio_pulito and len(archivio_pulito[r]) > indice_attuale
    ]

    for origine_ruota in ruote_disponibili:
        lista_origine = archivio_pulito[origine_ruota]

        for target_ruota in ruote_disponibili:
            if target_ruota == origine_ruota:
                continue

            lista_target = archivio_pulito[target_ruota]

            # La coppia viene valutata con i dati disponibili PRIMA
            # dell'ultima estrazione.
            for shift in SHIFT_CANDIDATI:
                for metodo in ("DIAMETRALE",):
                    risultato = valuta_configurazione(
                        lista_origine,
                        lista_target,
                        shift,
                        metodo,
                        indice_attuale
                    )

                    if risultato is None:
                        continue

                    migliori.append({
                        "origine": origine_ruota,
                        "target": target_ruota,
                        "shift": shift,
                        "metodo": metodo,
                        **risultato
                    })

    if not migliori:
        return None, []

    migliori.sort(
        key=lambda x: (
            x["score"],
            x["ambi"],
            x["vittorie_rapide"],
            x["ambate"]
        ),
        reverse=True
    )

    return migliori[0], migliori[:10]


def elabora_motore_v9():
    if not os.path.exists("estrazioni.json"):
        print("ERRORE: estrazioni.json non trovato.")
        return

    with open("estrazioni.json", "r", encoding="utf-8") as f:
        archivio = json.load(f)

    archivio_pulito = prepara_ruote(archivio)

    ruote_valide = [
        r for r in RUOTE
        if r in archivio_pulito and len(archivio_pulito[r]) > CICLO_MAX + 2
    ]

    if len(ruote_valide) < 2:
        print("ERRORE: non ci sono almeno due ruote con storico sufficiente.")
        return

    # Per la selezione della configurazione usiamo tutto lo storico
    # precedente all'ultima estrazione.
    indice_attuale = min(
        len(archivio_pulito[r]) for r in ruote_valide
    ) - 1

    migliore, top10 = cerca_migliore_configurazione(
        archivio_pulito,
        indice_attuale
    )

    if migliore is None:
        print("ERRORE: nessuna configurazione valida trovata.")
        return

    origine_ruota = migliore["origine"]
    target_ruota = migliore["target"]
    shift = migliore["shift"]
    metodo = migliore["metodo"]

    lista_origine = archivio_pulito[origine_ruota]

    # Previsione corrente: usa l'ultima estrazione disponibile.
    ultima = numeri_estrazione(lista_origine, indice_attuale)
    if not ultima:
        print("ERRORE: ultima estrazione non valida.")
        return

    origine = ultima[0]
    ambata, secondo = costruisci_ambo(origine, shift, metodo)

    # Data concorso
    data_reale = datetime.now().strftime("%d/%m/%Y")
    if isinstance(archivio.get("info_concorso"), dict):
        data_reale = archivio["info_concorso"].get("data", data_reale)
    elif isinstance(archivio.get("data"), str):
        data_reale = archivio["data"]

    risultati = {
        "info_concorso": {
            "numero": "Lotto Intelligence V9",
            "data": data_reale
        },
        "motore": {
            "versione": "V9 - Isotopia adattiva",
            "ruota_origine": origine_ruota,
            "ruota_target": target_ruota,
            "trasformazione": metodo,
            "shift": shift,
            "score_backtest": migliore["score"],
            "cicli_testati": migliore["cicli"],
            "ambi_backtest": migliore["ambi"],
            "ambate_backtest": migliore["ambate"],
            "vittorie_rapide_1_3": migliore["vittorie_rapide"],
            "percentuale_ambo": migliore["percentuale_ambo"],
            "percentuale_ambata": migliore["percentuale_ambata"],
            "top10_configurazioni": top10
        },
        "previsioni": {},
        "storico_verificato": []
    }

    # Manteniamo la stessa struttura del vecchio index:
    # due ruote, numeri estrazione, ambata, ambo, ambetti.
    for ruota in (origine_ruota, target_ruota):
        numeri = numeri_estrazione(archivio_pulito[ruota], indice_attuale)

        risultati["previsioni"][ruota] = {
            "numeri_estrazione": numeri,
            "tipo_calcolo": (
                f"Isotopia V9: {origine_ruota} 1° numero "
                f"({origine}) +{shift} → {ambata}; "
                f"diametrale → {secondo}"
            ),
            "ambata": ambata,
            "ambo": [ambata, secondo],
            "ambetti": [
                [ambata, fuori_90(secondo + 1)],
                [ambata, fuori_90(secondo - 1)]
            ]
        }

    # Storico recente, nello stesso formato del vecchio JSON.
    storico_limite = min(10, indice_attuale)

    for distanza in range(1, storico_limite + 1):
        i = indice_attuale - distanza
        estrazione = numeri_estrazione(lista_origine, i)
        if not estrazione:
            continue

        origine_storica = estrazione[0]
        ambata_p, secondo_p = costruisci_ambo(
            origine_storica, shift, metodo
        )

        esito = "In gioco"
        colpo_vincita = None

        for c in range(1, CICLO_MAX + 1):
            idx = i + c
            if idx >= len(lista_origine):
                break

            nums_origine = numeri_estrazione(lista_origine, idx)
            nums_target = numeri_estrazione(
                archivio_pulito[target_ruota], idx
            )

            if (
                ambata_p in nums_origine and secondo_p in nums_origine
            ) or (
                ambata_p in nums_target and secondo_p in nums_target
            ):
                esito = "AMBO SECCO VINCENTE!"
                colpo_vincita = c
                break

            if (
                ambata_p in nums_origine
                or ambata_p in nums_target
            ):
                if esito == "In gioco":
                    esito = "Ambata Vincente"
                    colpo_vincita = c

        if esito == "In gioco" and distanza > CICLO_MAX:
            esito = "Ciclo concluso (No esito)"

        risultati["storico_verificato"].append({
            "data": f"Concorso Arretrat. -{distanza}",
            "ambata": ambata_p,
            "ambo": f"{ambata_p} - {secondo_p}",
            "colpi": (
                f"Esito al {colpo_vincita}° colpo"
                if colpo_vincita
                else f"{distanza}° Colpo"
            ),
            "stato": esito
        })

    with open("risultati_v4.json", "w", encoding="utf-8") as f:
        json.dump(risultati, f, indent=4, ensure_ascii=False)

    print("==============================================")
    print("LOTTO INTELLIGENCE V9")
    print("==============================================")
    print(f"Ruota origine : {origine_ruota}")
    print(f"Ruota target  : {target_ruota}")
    print(f"Trasformazione: {metodo}")
    print(f"Shift         : +{shift}")
    print(f"Ambata       : {ambata}")
    print(f"Ambo secco   : {ambata} - {secondo}")
    print("----------------------------------------------")
    print(f"Score backtest       : {migliore['score']}")
    print(f"Cicli testati        : {migliore['cicli']}")
    print(f"Ambi secchi          : {migliore['ambi']}")
    print(f"Ambate               : {migliore['ambate']}")
    print(f"Ambi entro 1-3 colpi : {migliore['vittorie_rapide']}")
    print("==============================================")


if __name__ == "__main__":
    elabora_motore_v9()
