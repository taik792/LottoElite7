ULTIME_ESTRAZIONI = 300
FILTRO_ATTIVITA = 150

def prendi_ultime_estrazioni(lista):
    if not lista:
        return []
    return lista[-ULTIME_ESTRAZIONI:]

def prendi_recenti(lista):
    if not lista:
        return []
    return lista[-FILTRO_ATTIVITA:]