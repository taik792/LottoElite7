import json
import os
from datetime import datetime

# ============================================================
# LOTTO INTELLIGENCE V11
# ISOTOPIA - MOTORE ORIENTATO ALL'AMBO SECCO
# ============================================================

RUOTE = [
    "BARI", "CAGLIARI", "FIRENZE", "GENOVA", "MILANO",
    "NAPOLI", "PALERMO", "ROMA", "TORINO", "VENEZIA",
    "NAZIONALE"
]

CICLO_MAX = 9
SHIFT_CANDIDATI = range(1, 46)

# Finestra recente usata per capire se una configurazione
# sta funzionando anche nella fase più recente dello storico.
FINESTRA_RECENTE = 600

PESO_STORICO = 0.45
PESO_RECENTE = 0.55


# ============================================================
# FUNZIONI NUMERICHE
# ============================================================

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


def costruisci_ambo(numero_origine, shift):
    ambata = fuori_90(numero_origine + shift)
    secondo = diametrale(ambata)

    if ambata == secondo:
        return ambata, None

    return ambata, secondo


# ============================================================
# LETTURA / NORMALIZZAZIONE
# ============================================================

def prepara_ruote(archivio):
    return {
        str(k).upper(): v
        for k, v in archivio.items()
        if isinstance(v, list)
    }


def numeri_estrazione(lista, indice):
    if not isinstance(lista, list):
        return []

    if indice < 0 or indice >= len(lista):
        return []

    riga = lista[indice]

    if not isinstance(riga, list):
        return []

    try:
        return [int(x) for x in riga[:5]]
    except (ValueError, TypeError):
        return []


def ultima_estrazione(lista):
    if not lista:
        return []

    return numeri_estrazione(
        lista,
        len(lista) - 1
    )


# ============================================================
# ALLINEAMENTO
# ============================================================

def lunghezza_comune(lista_a, lista_b):
    return min(
        len(lista_a),
        len(lista_b)
    )


def indice_coda_comune(lista, posizione, totale_comune):
    """
    Traduce la posizione della coda comune nell'indice reale
    della singola ruota.

    Questo evita il bug V10 che faceva leggere una estrazione
    vecchia quando due ruote avevano lunghezze diverse.
    """
    indice = (
        len(lista)
        - totale_comune
        + posizione
    )

    if indice < 0 or indice >= len(lista):
        return None

    return indice


def numeri_coda_comune(
    lista,
    posizione,
    totale_comune
):
    indice = indice_coda_comune(
        lista,
        posizione,
        totale_comune
    )

    if indice is None:
        return []

    return numeri_estrazione(
        lista,
        indice
    )


def controllo_allineamento(
    archivio_pulito,
    ruote
):
    lunghezze = {
        ruota: len(archivio_pulito[ruota])
        for ruota in ruote
    }

    valori = list(lunghezze.values())

    return {
        "allineamento_ok": (
            min(valori) == max(valori)
        ),
        "lunghezza_minima": min(valori),
        "lunghezza_massima": max(valori),
        "differenza": (
            max(valori) - min(valori)
        ),
        "lunghezze_ruote": lunghezze
    }


# ============================================================
# VERIFICA AMBO SECCO
# ============================================================

def ambo_secco_su_ruota(
    numeri,
    ambata,
    secondo
):
    """
    L'ambo è considerato SECCO solo se entrambi i numeri
    sono presenti nella stessa estrazione della stessa ruota.
    """
    insieme = set(numeri)

    return (
        ambata in insieme
        and secondo in insieme
    )


# ============================================================
# BACKTEST AMBO SECCO
# ============================================================

def valuta_configurazione(
    lista_origine,
    lista_target,
    shift,
    posizione_fine,
    posizione_inizio=0
):
    """
    Valuta una configurazione soltanto sulla capacità di
    produrre l'ambo secco.

    Per ogni ciclo:
      - 1° colpo
      - 2° colpo
      - 3° colpo
      - 4°/5° colpo
      - 6°-9° colpo

    viene registrato il PRIMO colpo in cui l'ambo esce
    completo su una delle due ruote.

    Le ambate NON entrano nel punteggio principale.
    """

    totale_comune = lunghezza_comune(
        lista_origine,
        lista_target
    )

    ultimo_ciclo = (
        posizione_fine
        - CICLO_MAX
        - 1
    )

    if (
        totale_comune <= CICLO_MAX + 2
        or ultimo_ciclo < posizione_inizio
    ):
        return None

    cicli = 0

    ambo_1 = 0
    ambo_3 = 0
    ambo_5 = 0
    ambo_9 = 0

    ritardi_ambo = []

    for posizione in range(
        posizione_inizio,
        ultimo_ciclo + 1
    ):
        estrazione_origine = (
            numeri_coda_comune(
                lista_origine,
                posizione,
                totale_comune
            )
        )

        if not estrazione_origine:
            continue

        numero_base = estrazione_origine[0]

        ambata, secondo = costruisci_ambo(
            numero_base,
            shift
        )

        if secondo is None:
            continue

        cicli += 1

        colpo_vincente = None

        for colpo in range(
            1,
            CICLO_MAX + 1
        ):
            futura_posizione = (
                posizione + colpo
            )

            if futura_posizione >= totale_comune:
                break

            nums_origine = (
                numeri_coda_comune(
                    lista_origine,
                    futura_posizione,
                    totale_comune
                )
            )

            nums_target = (
                numeri_coda_comune(
                    lista_target,
                    futura_posizione,
                    totale_comune
                )
            )

            if (
                ambo_secco_su_ruota(
                    nums_origine,
                    ambata,
                    secondo
                )
                or
                ambo_secco_su_ruota(
                    nums_target,
                    ambata,
                    secondo
                )
            ):
                colpo_vincente = colpo
                break

        if colpo_vincente is not None:
            ritardi_ambo.append(
                colpo_vincente
            )

            if colpo_vincente == 1:
                ambo_1 += 1

            if colpo_vincente <= 3:
                ambo_3 += 1

            if colpo_vincente <= 5:
                ambo_5 += 1

            ambo_9 += 1

    if cicli == 0:
        return None

    p1 = ambo_1 / cicli
    p3 = ambo_3 / cicli
    p5 = ambo_5 / cicli
    p9 = ambo_9 / cicli

    # ========================================================
    # SCORE V11
    #
    # L'ambo secco rapido vale molto più dell'ambo tardivo.
    #
    # 1° colpo  -> peso massimo
    # entro 3   -> peso alto
    # entro 5   -> peso medio
    # entro 9   -> peso basso
    #
    # Non viene usata la percentuale di ambata come componente
    # positiva del punteggio.
    # ========================================================

    score = (
        p1 * 1000
        + p3 * 450
        + p5 * 180
        + p9 * 60
    )

    media_colpo = (
        sum(ritardi_ambo) / len(ritardi_ambo)
        if ritardi_ambo
        else None
    )

    return {
        "score": round(score, 4),
        "cicli": cicli,

        "ambi_1_colpo": ambo_1,
        "ambi_entro_3": ambo_3,
        "ambi_entro_5": ambo_5,
        "ambi_entro_9": ambo_9,

        "percentuale_1_colpo": round(
            p1 * 100,
            2
        ),
        "percentuale_entro_3": round(
            p3 * 100,
            2
        ),
        "percentuale_entro_5": round(
            p5 * 100,
            2
        ),
        "percentuale_entro_9": round(
            p9 * 100,
            2
        ),

        "media_colpo_ambo": (
            round(media_colpo, 2)
            if media_colpo is not None
            else None
        ),

        "ritardi_ambo": ritardi_ambo
    }


# ============================================================
# PRECEDENTE
# ============================================================

def leggi_precedente():
    path = "risultati_v4.json"

    if not os.path.exists(path):
        return None

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            dati = json.load(f)

        motore = dati.get(
            "motore",
            {}
        )

        origine = str(
            motore.get(
                "ruota_origine",
                ""
            )
        ).upper()

        target = str(
            motore.get(
                "ruota_target",
                ""
            )
        ).upper()

        if origine and target:
            return origine, target

    except Exception:
        pass

    return None


# ============================================================
# SELEZIONE V11
# ============================================================

def seleziona_configurazione(
    archivio_pulito
):
    ruote = [
        r for r in RUOTE
        if (
            r in archivio_pulito
            and len(
                archivio_pulito[r]
            ) > CICLO_MAX + 2
        )
    ]

    candidati = []

    for origine_ruota in ruote:

        lista_origine = (
            archivio_pulito[
                origine_ruota
            ]
        )

        for target_ruota in ruote:

            if target_ruota == origine_ruota:
                continue

            lista_target = (
                archivio_pulito[
                    target_ruota
                ]
            )

            totale_comune = (
                lunghezza_comune(
                    lista_origine,
                    lista_target
                )
            )

            if totale_comune <= CICLO_MAX + 2:
                continue

            posizione_fine = (
                totale_comune - 1
            )

            posizione_recente = max(
                0,
                posizione_fine
                - FINESTRA_RECENTE
            )

            for shift in SHIFT_CANDIDATI:

                storico = (
                    valuta_configurazione(
                        lista_origine,
                        lista_target,
                        shift,
                        posizione_fine,
                        0
                    )
                )

                recente = (
                    valuta_configurazione(
                        lista_origine,
                        lista_target,
                        shift,
                        posizione_fine,
                        posizione_recente
                    )
                )

                if (
                    storico is None
                    or recente is None
                ):
                    continue

                score_finale = (
                    storico["score"]
                    * PESO_STORICO
                    +
                    recente["score"]
                    * PESO_RECENTE
                )

                # Bonus leggero se la parte recente è migliore
                # dello storico proprio sugli ambi al 1° colpo.
                differenza_rapida = (
                    recente[
                        "percentuale_1_colpo"
                    ]
                    -
                    storico[
                        "percentuale_1_colpo"
                    ]
                )

                bonus_recente = max(
                    -5.0,
                    min(
                        5.0,
                        differenza_rapida * 0.25
                    )
                )

                score_finale += (
                    bonus_recente
                )

                candidati.append({
                    "origine": origine_ruota,
                    "target": target_ruota,
                    "shift": shift,

                    "score": score_finale,

                    "score_storico":
                        storico["score"],

                    "score_recente":
                        recente["score"],

                    "bonus_recente":
                        bonus_recente,

                    "storico":
                        storico,

                    "recente":
                        recente,

                    "estrazioni_comuni":
                        totale_comune
                })

    candidati.sort(
        key=lambda x: (
            x["score"],

            x["recente"][
                "ambi_1_colpo"
            ],

            x["storico"][
                "ambi_1_colpo"
            ],

            x["recente"][
                "ambi_entro_3"
            ],

            x["storico"][
                "ambi_entro_3"
            ]
        ),
        reverse=True
    )

    if not candidati:
        return None, []

    # ========================================================
    # NON FORZIAMO IL CAMBIO DI RUOTE.
    #
    # Se la stessa coppia rimane prima perché ha realmente
    # il miglior score ambo-secco, può rimanere.
    #
    # V11 non deve cambiare ruote artificialmente.
    # ========================================================

    migliore = candidati[0]

    return migliore, candidati[:10]


# ============================================================
# COSTRUZIONE OUTPUT
# ============================================================

def costruisci_risultati(
    archivio,
    archivio_pulito,
    migliore,
    top10,
    controllo
):
    origine_ruota = (
        migliore["origine"]
    )

    target_ruota = (
        migliore["target"]
    )

    shift = (
        migliore["shift"]
    )

    lista_origine = (
        archivio_pulito[
            origine_ruota
        ]
    )

    lista_target = (
        archivio_pulito[
            target_ruota
        ]
    )

    # ========================================================
    # ULTIMA ESTRAZIONE REALE
    # ========================================================

    ultima_origine = (
        ultima_estrazione(
            lista_origine
        )
    )

    ultima_target = (
        ultima_estrazione(
            lista_target
        )
    )

    if not ultima_origine:
        raise ValueError(
            "Ultima estrazione origine non valida."
        )

    if not ultima_target:
        raise ValueError(
            "Ultima estrazione target non valida."
        )

    numero_base = (
        ultima_origine[0]
    )

    ambata, secondo = (
        costruisci_ambo(
            numero_base,
            shift
        )
    )

    if secondo is None:
        raise ValueError(
            "Ambo non valido."
        )

    # ========================================================
    # DATA
    # ========================================================

    data_reale = (
        datetime.now().strftime(
            "%d/%m/%Y"
        )
    )

    if isinstance(
        archivio.get(
            "info_concorso"
        ),
        dict
    ):
        data_reale = (
            archivio[
                "info_concorso"
            ].get(
                "data",
                data_reale
            )
        )

    elif isinstance(
        archivio.get("data"),
        str
    ):
        data_reale = (
            archivio["data"]
        )

    # ========================================================
    # TOP 10
    # ========================================================

    top_output = []

    for posizione, candidato in enumerate(
        top10,
        start=1
    ):
        storico = candidato[
            "storico"
        ]

        recente = candidato[
            "recente"
        ]

        top_output.append({
            "posizione":
                posizione,

            "origine":
                candidato["origine"],

            "target":
                candidato["target"],

            "shift":
                candidato["shift"],

            "score":
                round(
                    candidato["score"],
                    4
                ),

            "score_storico":
                round(
                    candidato[
                        "score_storico"
                    ],
                    4
                ),

            "score_recente":
                round(
                    candidato[
                        "score_recente"
                    ],
                    4
                ),

            "bonus_recente":
                round(
                    candidato[
                        "bonus_recente"
                    ],
                    4
                ),

            "ambi_1_colpo":
                storico[
                    "ambi_1_colpo"
                ],

            "ambi_entro_3":
                storico[
                    "ambi_entro_3"
                ],

            "ambi_entro_5":
                storico[
                    "ambi_entro_5"
                ],

            "ambi_entro_9":
                storico[
                    "ambi_entro_9"
                ],

            "percentuale_1_colpo":
                storico[
                    "percentuale_1_colpo"
                ],

            "percentuale_entro_3":
                storico[
                    "percentuale_entro_3"
                ],

            "percentuale_entro_9":
                storico[
                    "percentuale_entro_9"
                ],

            "ambi_1_colpo_recenti":
                recente[
                    "ambi_1_colpo"
                ],

            "ambi_entro_3_recenti":
                recente[
                    "ambi_entro_3"
                ],

            "percentuale_1_colpo_recente":
                recente[
                    "percentuale_1_colpo"
                ],

            "percentuale_entro_3_recente":
                recente[
                    "percentuale_entro_3"
                ],

            "estrazioni_comuni":
                candidato[
                    "estrazioni_comuni"
                ]
        })

    # ========================================================
    # RISULTATO
    # ========================================================

    risultati = {
        "info_concorso": {
            "numero":
                "Lotto Intelligence V11",
            "data":
                data_reale
        },

        "motore": {
            "versione":
                "V11 - Isotopia ambo secco",

            "ruota_origine":
                origine_ruota,

            "ruota_target":
                target_ruota,

            "trasformazione":
                "DIAMETRALE",

            "shift":
                shift,

            "score_backtest":
                round(
                    migliore[
                        "score"
                    ],
                    4
                ),

            "score_storico":
                round(
                    migliore[
                        "score_storico"
                    ],
                    4
                ),

            "score_recente":
                round(
                    migliore[
                        "score_recente"
                    ],
                    4
                ),

            "finestra_recente":
                FINESTRA_RECENTE,

            "peso_storico":
                PESO_STORICO,

            "peso_recente":
                PESO_RECENTE,

            "cicli_testati":
                migliore[
                    "storico"
                ]["cicli"],

            # SOLO AMBI SECCO
            "ambi_1_colpo":
                migliore[
                    "storico"
                ]["ambi_1_colpo"],

            "ambi_entro_3":
                migliore[
                    "storico"
                ]["ambi_entro_3"],

            "ambi_entro_5":
                migliore[
                    "storico"
                ]["ambi_entro_5"],

            "ambi_entro_9":
                migliore[
                    "storico"
                ]["ambi_entro_9"],

            "percentuale_1_colpo":
                migliore[
                    "storico"
                ]["percentuale_1_colpo"],

            "percentuale_entro_3":
                migliore[
                    "storico"
                ]["percentuale_entro_3"],

            "percentuale_entro_5":
                migliore[
                    "storico"
                ]["percentuale_entro_5"],

            "percentuale_entro_9":
                migliore[
                    "storico"
                ]["percentuale_entro_9"],

            "ambi_1_colpo_recenti":
                migliore[
                    "recente"
                ]["ambi_1_colpo"],

            "ambi_entro_3_recenti":
                migliore[
                    "recente"
                ]["ambi_entro_3"],

            "percentuale_1_colpo_recente":
                migliore[
                    "recente"
                ]["percentuale_1_colpo"],

            "percentuale_entro_3_recente":
                migliore[
                    "recente"
                ]["percentuale_entro_3"],

            "media_colpo_ambo":
                migliore[
                    "storico"
                ]["media_colpo_ambo"],

            "estrazioni_comuni_coppia":
                migliore[
                    "estrazioni_comuni"
                ],

            "controllo_allineamento":
                controllo,

            "top10_configurazioni":
                top_output
        },

        "previsioni": {},

        "storico_verificato": []
    }

    # ========================================================
    # PREVISIONE CORRENTE
    # ========================================================

    def blocco_previsione(
        numeri
    ):
        return {
            "numeri_estrazione":
                numeri,

            "tipo_calcolo": (
                f"Isotopia V11: "
                f"{origine_ruota} 1° numero "
                f"({numero_base}) + "
                f"{shift} = {ambata}; "
                f"diametrale = {secondo}"
            ),

            "ambata":
                ambata,

            "ambo":
                [ambata, secondo],

            "ambetti": [
                [
                    ambata,
                    fuori_90(
                        secondo + 1
                    )
                ],
                [
                    ambata,
                    fuori_90(
                        secondo - 1
                    )
                ]
            ]
        }

    risultati[
        "previsioni"
    ][origine_ruota] = (
        blocco_previsione(
            ultima_origine
        )
    )

    risultati[
        "previsioni"
    ][target_ruota] = (
        blocco_previsione(
            ultima_target
        )
    )

    # ========================================================
    # ARCHIVIO STORICO
    #
    # Qui la distinzione è netta:
    # - AMBO SECCO VINCENTE
    # - Ambata Vincente
    # - In gioco
    # - Ciclo concluso
    # ========================================================

    totale_comune = (
        lunghezza_comune(
            lista_origine,
            lista_target
        )
    )

    ultima_posizione = (
        totale_comune - 1
    )

    for distanza in range(
        1,
        min(
            10,
            ultima_posizione
        ) + 1
    ):
        posizione = (
            ultima_posizione
            - distanza
        )

        estrazione = (
            numeri_coda_comune(
                lista_origine,
                posizione,
                totale_comune
            )
        )

        if not estrazione:
            continue

        numero_storico = (
            estrazione[0]
        )

        ambata_storica, secondo_storico = (
            costruisci_ambo(
                numero_storico,
                shift
            )
        )

        if secondo_storico is None:
            continue

        stato = "In gioco"
        colpo = None
        tipo = None

        for c in range(
            1,
            CICLO_MAX + 1
        ):
            p = (
                posizione + c
            )

            if p >= totale_comune:
                break

            nums_o = (
                numeri_coda_comune(
                    lista_origine,
                    p,
                    totale_comune
                )
            )

            nums_t = (
                numeri_coda_comune(
                    lista_target,
                    p,
                    totale_comune
                )
            )

            if (
                ambo_secco_su_ruota(
                    nums_o,
                    ambata_storica,
                    secondo_storico
                )
                or
                ambo_secco_su_ruota(
                    nums_t,
                    ambata_storica,
                    secondo_storico
                )
            ):
                stato = (
                    "AMBO SECCO VINCENTE!"
                )
                colpo = c
                tipo = "ambo_secco"
                break

            if (
                ambata_storica in nums_o
                or
                ambata_storica in nums_t
            ):
                if (
                    stato == "In gioco"
                ):
                    stato = (
                        "Ambata Vincente"
                    )
                    colpo = c
                    tipo = "ambata"

        if (
            stato == "In gioco"
            and distanza > CICLO_MAX
        ):
            stato = (
                "Ciclo concluso "
                "(No esito)"
            )

        risultati[
            "storico_verificato"
        ].append({
            "data":
                f"Concorso Arretrat. -{distanza}",

            "ambata":
                ambata_storica,

            "ambo":
                f"{ambata_storica} - "
                f"{secondo_storico}",

            "colpo":
                colpo,

            "tipo_esito":
                tipo,

            "stato":
                stato
        })

    return risultati


# ============================================================
# MAIN
# ============================================================

def elabora_motore_v11():

    if not os.path.exists(
        "estrazioni.json"
    ):
        print(
            "ERRORE: "
            "estrazioni.json non trovato."
        )
        return

    with open(
        "estrazioni.json",
        "r",
        encoding="utf-8"
    ) as f:
        archivio = json.load(f)

    archivio_pulito = (
        prepara_ruote(
            archivio
        )
    )

    ruote_valide = [
        r for r in RUOTE
        if (
            r in archivio_pulito
            and len(
                archivio_pulito[r]
            ) > CICLO_MAX + 2
        )
    ]

    if len(ruote_valide) < 2:
        print(
            "ERRORE: servono almeno "
            "due ruote valide."
        )
        return

    controllo = (
        controllo_allineamento(
            archivio_pulito,
            ruote_valide
        )
    )

    migliore, top10 = (
        seleziona_configurazione(
            archivio_pulito
        )
    )

    if migliore is None:
        print(
            "ERRORE: nessuna "
            "configurazione valida."
        )
        return

    risultati = (
        costruisci_risultati(
            archivio,
            archivio_pulito,
            migliore,
            top10,
            controllo
        )
    )

    with open(
        "risultati_v4.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            risultati,
            f,
            indent=4,
            ensure_ascii=False
        )

    motore = risultati[
        "motore"
    ]

    origine = motore[
        "ruota_origine"
    ]

    target = motore[
        "ruota_target"
    ]

    ambo = risultati[
        "previsioni"
    ][origine]["ambo"]

    print(
        "=============================================="
    )
    print(
        "LOTTO INTELLIGENCE V11"
    )
    print(
        "ISOTOPIA - AMBO SECCO"
    )
    print(
        "=============================================="
    )

    print(
        f"Ruote        : "
        f"{origine} -> {target}"
    )

    print(
        f"Shift        : "
        f"+{motore['shift']}"
    )

    print(
        f"Ambata       : "
        f"{risultati['previsioni'][origine]['ambata']}"
    )

    print(
        f"AMBO SECCO   : "
        f"{ambo[0]} - {ambo[1]}"
    )

    print(
        "----------------------------------------------"
    )

    print(
        f"Cicli        : "
        f"{motore['cicli_testati']}"
    )

    print(
        f"Ambo 1°      : "
        f"{motore['ambi_1_colpo']} "
        f"({motore['percentuale_1_colpo']}%)"
    )

    print(
        f"Ambo <=3     : "
        f"{motore['ambi_entro_3']} "
        f"({motore['percentuale_entro_3']}%)"
    )

    print(
        f"Ambo <=5     : "
        f"{motore['ambi_entro_5']} "
        f"({motore['percentuale_entro_5']}%)"
    )

    print(
        f"Ambo <=9     : "
        f"{motore['ambi_entro_9']} "
        f"({motore['percentuale_entro_9']}%)"
    )

    print(
        "----------------------------------------------"
    )

    print(
        f"Score        : "
        f"{motore['score_backtest']}"
    )

    print(
        f"Score storico: "
        f"{motore['score_storico']}"
    )

    print(
        f"Score recente: "
        f"{motore['score_recente']}"
    )

    print(
        "----------------------------------------------"
    )

    print(
        "CONTROLLO ALLINEAMENTO"
    )

    print(
        f"Min estrazioni: "
        f"{controllo['lunghezza_minima']}"
    )

    print(
        f"Max estrazioni: "
        f"{controllo['lunghezza_massima']}"
    )

    print(
        f"Differenza    : "
        f"{controllo['differenza']}"
    )

    print(
        "----------------------------------------------"
    )

    print(
        "TOP 3 AMBO SECCO"
    )

    for candidato in motore[
        "top10_configurazioni"
    ][:3]:
        print(
            f"{candidato['posizione']}. "
            f"{candidato['origine']} -> "
            f"{candidato['target']} "
            f"+{candidato['shift']} | "
            f"score {candidato['score']} | "
            f"1° colpo "
            f"{candidato['ambi_1_colpo']}"
        )

    print(
        "=============================================="
    )


if __name__ == "__main__":
    elabora_motore_v11()
