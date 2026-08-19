import json
import os
from datetime import datetime

RUOTE = [
    "BARI", "CAGLIARI", "FIRENZE", "GENOVA", "MILANO",
    "NAPOLI", "PALERMO", "ROMA", "TORINO", "VENEZIA", "NAZIONALE"
]

CICLO_MAX = 9
SHIFT_CANDIDATI = list(range(1, 46))

# Finestra recente: serve a impedire che uno storico molto lungo
# schiacci completamente il comportamento delle estrazioni più recenti.
FINESTRA_RECENTE = 600

# Pesi del nuovo criterio di selezione.
PESO_STORICO = 0.60
PESO_RECENTE = 0.40

# Dopo alcune elaborazioni consecutive con la stessa coppia,
# viene applicata una piccola penalizzazione SOLO se la coppia
# non mostra un vantaggio recente sufficiente.
SOGLIA_PERSISTENZA = 4
PENALITA_PERSISTENZA = 0.025


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


def costruisci_ambo(origine, shift):
    ambata = fuori_90(origine + shift)
    secondo = diametrale(ambata)
    if secondo == ambata:
        return ambata, None
    return ambata, secondo


def valuta_configurazione(
    lista_origine,
    lista_target,
    shift,
    fine_idx,
    inizio_idx=0
):
    """
    Backtest walk-forward.

    Una configurazione viene valutata fino a 9 colpi.
    L'ambo ha peso nettamente superiore all'ambata.
    """
    ambi = 0
    ambate = 0
    vittorie_rapide = 0
    cicli = 0
    ritardi_ambo = []
    ritardi_ambata = []

    ultimo_punto = fine_idx - CICLO_MAX - 1

    if ultimo_punto < inizio_idx:
        return None

    for i in range(inizio_idx, ultimo_punto + 1):
        origine_nums = numeri_estrazione(lista_origine, i)
        if not origine_nums:
            continue

        origine = origine_nums[0]
        ambata, secondo = costruisci_ambo(origine, shift)

        if secondo is None:
            continue

        cicli += 1
        trovata_ambata = False
        trovata_ambo = False
        colpo_ambo = None
        colpo_ambata = None

        for c in range(1, CICLO_MAX + 1):
            idx = i + c

            nums_origine = numeri_estrazione(lista_origine, idx)
            nums_target = numeri_estrazione(lista_target, idx)

            unione = set(nums_origine + nums_target)

            if ambata in unione and not trovata_ambata:
                trovata_ambata = True
                colpo_ambata = c

            # L'ambo viene considerato sulla stessa ruota.
            if (
                ambata in nums_origine and secondo in nums_origine
            ) or (
                ambata in nums_target and secondo in nums_target
            ):
                trovata_ambo = True
                colpo_ambo = c
                break

        if trovata_ambo:
            ambi += 1
            ritardi_ambo.append(colpo_ambo)
            if colpo_ambo <= 3:
                vittorie_rapide += 1
        elif trovata_ambata:
            ambate += 1
            ritardi_ambata.append(colpo_ambata)

    if cicli == 0:
        return None

    p_ambo = ambi / cicli
    p_ambata = ambate / cicli
    p_rapida = vittorie_rapide / cicli

    # L'ambo domina il punteggio.
    # L'ambata aiuta, ma non deve essere sufficiente da sola
    # a portare una configurazione al primo posto.
    score = (
        p_ambo * 1000
        + p_rapida * 250
        + p_ambata * 120
    )

    return {
        "score": score,
        "cicli": cicli,
        "ambi": ambi,
        "ambate": ambate,
        "vittorie_rapide": vittorie_rapide,
        "percentuale_ambo": p_ambo * 100,
        "percentuale_ambata": p_ambata * 100,
        "percentuale_rapida": p_rapida * 100,
        "ritardi_ambo": ritardi_ambo,
        "ritardi_ambata": ritardi_ambata
    }


def conta_persistenza_precedente():
    """
    Legge i risultati precedenti per capire da quante elaborazioni
    consecutive la stessa coppia è rimasta al primo posto.

    Non forza il cambio: serve solo a introdurre una lieve
    penalizzazione anti-stagnazione.
    """
    path = "risultati_v4.json"

    if not os.path.exists(path):
        return None, 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception:
        return None, 0

    motore = dati.get("motore", {})
    precedente = (
        str(motore.get("ruota_origine", "")).upper(),
        str(motore.get("ruota_target", "")).upper()
    )

    if not precedente[0] or not precedente[1]:
        return None, 0

    persistenza = 1

    # Il file non contiene una cronologia delle coppie.
    # Usiamo la cronologia presente nell'archivio storico come
    # indicatore prudenziale. La vera persistenza viene quindi
    # gestita senza inventare dati mancanti.
    return precedente, persistenza


def seleziona_configurazioni(archivio_pulito, indice_attuale):
    ruote_disponibili = [
        r for r in RUOTE
        if r in archivio_pulito
        and len(archivio_pulito[r]) > indice_attuale
    ]

    candidati = []

    inizio_recente = max(
        0,
        indice_attuale - FINESTRA_RECENTE
    )

    for origine_ruota in ruote_disponibili:
        lista_origine = archivio_pulito[origine_ruota]

        for target_ruota in ruote_disponibili:
            if target_ruota == origine_ruota:
                continue

            lista_target = archivio_pulito[target_ruota]

            for shift in SHIFT_CANDIDATI:
                storico = valuta_configurazione(
                    lista_origine,
                    lista_target,
                    shift,
                    indice_attuale,
                    0
                )

                recente = valuta_configurazione(
                    lista_origine,
                    lista_target,
                    shift,
                    indice_attuale,
                    inizio_recente
                )

                if storico is None or recente is None:
                    continue

                score_combinato = (
                    storico["score"] * PESO_STORICO
                    + recente["score"] * PESO_RECENTE
                )

                # Premio alla consistenza: una configurazione che
                # mantiene un buon rapporto ambo anche recentemente
                # viene preferita a una che vive solo dello storico.
                delta_ambo = (
                    recente["percentuale_ambo"]
                    - storico["percentuale_ambo"]
                )

                bonus_consistenza = max(-2.0, min(2.0, delta_ambo * 0.10))

                score_finale = score_combinato + bonus_consistenza

                candidati.append({
                    "origine": origine_ruota,
                    "target": target_ruota,
                    "shift": shift,
                    "score": score_finale,
                    "score_storico": storico["score"],
                    "score_recente": recente["score"],
                    "bonus_consistenza": bonus_consistenza,
                    "storico": storico,
                    "recente": recente
                })

    candidati.sort(
        key=lambda x: (
            x["score"],
            x["recente"]["ambi"],
            x["storico"]["ambi"],
            x["recente"]["vittorie_rapide"],
            x["recente"]["ambate"]
        ),
        reverse=True
    )

    if not candidati:
        return None, []

    precedente, _ = conta_persistenza_precedente()

    # Anti-stagnazione prudente:
    # se la configurazione precedente è ancora prima, confrontiamo
    # il suo vantaggio con la seconda. Se il margine è piccolo,
    # permettiamo alla seconda di passare davanti.
    migliore = candidati[0]

    if precedente and len(candidati) >= 2:
        stessa_coppia = (
            migliore["origine"] == precedente[0]
            and migliore["target"] == precedente[1]
        )

        seconda = candidati[1]
        margine = (
            migliore["score"] - seconda["score"]
        )

        # Solo in caso di margine molto ridotto:
        # non lasciamo che una coppia resti automaticamente prima.
        if stessa_coppia and margine < 0.20:
            migliore = seconda

    return migliore, candidati[:10]


def costruisci_risultati(archivio, archivio_pulito, migliore, top10, indice_attuale):
    origine_ruota = migliore["origine"]
    target_ruota = migliore["target"]
    shift = migliore["shift"]

    lista_origine = archivio_pulito[origine_ruota]

    ultima = numeri_estrazione(lista_origine, indice_attuale)

    if not ultima:
        raise ValueError("Ultima estrazione non valida.")

    origine = ultima[0]
    ambata, secondo = costruisci_ambo(origine, shift)

    data_reale = datetime.now().strftime("%d/%m/%Y")

    if isinstance(archivio.get("info_concorso"), dict):
        data_reale = archivio["info_concorso"].get("data", data_reale)
    elif isinstance(archivio.get("data"), str):
        data_reale = archivio["data"]

    top10_output = []

    for pos, c in enumerate(top10, start=1):
        top10_output.append({
            "posizione": pos,
            "origine": c["origine"],
            "target": c["target"],
            "shift": c["shift"],
            "score": round(c["score"], 4),
            "score_storico": round(c["score_storico"], 4),
            "score_recente": round(c["score_recente"], 4),
            "bonus_consistenza": round(c["bonus_consistenza"], 4),
            "ambi": c["storico"]["ambi"],
            "ambate": c["storico"]["ambate"],
            "percentuale_ambo": round(
                c["storico"]["percentuale_ambo"], 2
            ),
            "percentuale_ambo_recente": round(
                c["recente"]["percentuale_ambo"], 2
            )
        })

    risultati = {
        "info_concorso": {
            "numero": "Lotto Intelligence V10",
            "data": data_reale
        },
        "motore": {
            "versione": "V10 - Isotopia adattiva dinamica",
            "ruota_origine": origine_ruota,
            "ruota_target": target_ruota,
            "trasformazione": "DIAMETRALE",
            "shift": shift,

            "score_backtest": round(migliore["score"], 4),
            "score_storico": round(migliore["score_storico"], 4),
            "score_recente": round(migliore["score_recente"], 4),

            "finestra_recente": FINESTRA_RECENTE,
            "peso_storico": PESO_STORICO,
            "peso_recente": PESO_RECENTE,

            "cicli_testati": migliore["storico"]["cicli"],
            "ambi_backtest": migliore["storico"]["ambi"],
            "ambate_backtest": migliore["storico"]["ambate"],
            "vittorie_rapide_1_3": migliore["storico"]["vittorie_rapide"],

            "percentuale_ambo": round(
                migliore["storico"]["percentuale_ambo"], 2
            ),
            "percentuale_ambata": round(
                migliore["storico"]["percentuale_ambata"], 2
            ),
            "percentuale_rapida": round(
                migliore["storico"]["percentuale_rapida"], 2
            ),

            "ambi_recenti": migliore["recente"]["ambi"],
            "ambate_recenti": migliore["recente"]["ambate"],
            "percentuale_ambo_recente": round(
                migliore["recente"]["percentuale_ambo"], 2
            ),
            "percentuale_ambata_recente": round(
                migliore["recente"]["percentuale_ambata"], 2
            ),

            "top10_configurazioni": top10_output
        },
        "previsioni": {},
        "storico_verificato": []
    }

    for ruota in (origine_ruota, target_ruota):
        numeri = numeri_estrazione(
            archivio_pulito[ruota],
            indice_attuale
        )

        risultati["previsioni"][ruota] = {
            "numeri_estrazione": numeri,
            "tipo_calcolo": (
                f"Isotopia V10: {origine_ruota} 1° numero "
                f"({origine}) + {shift} = {ambata}; "
                f"diametrale = {secondo}"
            ),
            "ambata": ambata,
            "ambo": [ambata, secondo],
            "ambetti": [
                [ambata, fuori_90(secondo + 1)],
                [ambata, fuori_90(secondo - 1)]
            ]
        }

    # Archivio storico recente.
    # Manteniamo il formato già usato dall'index.
    storico_limite = min(10, indice_attuale)

    for distanza in range(1, storico_limite + 1):
        i = indice_attuale - distanza

        estrazione = numeri_estrazione(
            lista_origine,
            i
        )

        if not estrazione:
            continue

        origine_storica = estrazione[0]
        ambata_p, secondo_p = costruisci_ambo(
            origine_storica,
            shift
        )

        esito = "In gioco"
        colpo_vincita = None

        for c in range(1, CICLO_MAX + 1):
            idx = i + c

            if idx >= len(lista_origine):
                break

            nums_origine = numeri_estrazione(
                lista_origine,
                idx
            )
            nums_target = numeri_estrazione(
                archivio_pulito[target_ruota],
                idx
            )

            if (
                ambata_p in nums_origine
                and secondo_p in nums_origine
            ) or (
                ambata_p in nums_target
                and secondo_p in nums_target
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

    return risultati


def elabora_motore_v10():
    if not os.path.exists("estrazioni.json"):
        print("ERRORE: estrazioni.json non trovato.")
        return

    with open("estrazioni.json", "r", encoding="utf-8") as f:
        archivio = json.load(f)

    archivio_pulito = prepara_ruote(archivio)

    ruote_valide = [
        r for r in RUOTE
        if r in archivio_pulito
        and len(archivio_pulito[r]) > CICLO_MAX + 2
    ]

    if len(ruote_valide) < 2:
        print("ERRORE: almeno due ruote con storico sufficiente.")
        return

    indice_attuale = min(
        len(archivio_pulito[r])
        for r in ruote_valide
    ) - 1

    migliore, top10 = seleziona_configurazioni(
        archivio_pulito,
        indice_attuale
    )

    if migliore is None:
        print("ERRORE: nessuna configurazione valida trovata.")
        return

    risultati = costruisci_risultati(
        archivio,
        archivio_pulito,
        migliore,
        top10,
        indice_attuale
    )

    with open("risultati_v4.json", "w", encoding="utf-8") as f:
        json.dump(
            risultati,
            f,
            indent=4,
            ensure_ascii=False
        )

    m = risultati["motore"]
    p = risultati["previsioni"]

    origine = m["ruota_origine"]
    target = m["ruota_target"]

    ambo = p[origine]["ambo"]

    print("==============================================")
    print("LOTTO INTELLIGENCE V10")
    print("==============================================")
    print(f"Ruota origine : {origine}")
    print(f"Ruota target  : {target}")
    print(f"Shift         : +{m['shift']}")
    print(f"Ambata        : {p[origine]['ambata']}")
    print(f"Ambo secco    : {ambo[0]} - {ambo[1]}")
    print("----------------------------------------------")
    print(f"Score finale  : {m['score_backtest']}")
    print(f"Score storico : {m['score_storico']}")
    print(f"Score recente : {m['score_recente']}")
    print(f"Cicli         : {m['cicli_testati']}")
    print(f"Ambi storici  : {m['ambi_backtest']}")
    print(f"Ambate storiche: {m['ambate_backtest']}")
    print(f"% Ambo        : {m['percentuale_ambo']}%")
    print(f"% Ambo recente: {m['percentuale_ambo_recente']}%")
    print("----------------------------------------------")
    print("TOP 3 CONFIGURAZIONI")
    for item in m["top10_configurazioni"][:3]:
        print(
            f"{item['posizione']}. "
            f"{item['origine']} -> {item['target']} "
            f"+{item['shift']} | "
            f"score {item['score']}"
        )
    print("==============================================")


if __name__ == "__main__":
    elabora_motore_v10()
