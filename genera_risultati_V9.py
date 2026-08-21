import json, os
from datetime import datetime

RUOTE=["BARI","CAGLIARI","FIRENZE","GENOVA","MILANO","NAPOLI","PALERMO","ROMA","TORINO","VENEZIA","NAZIONALE"]
CICLO_MAX=9
SHIFT_CANDIDATI=range(1,46)
FINESTRA_RECENTE=600
PESO_STORICO=0.60
PESO_RECENTE=0.40

def fuori_90(n):
    n=int(n)
    while n>90:n-=90
    while n<=0:n+=90
    return n

def diametrale(n):
    n=int(n)
    return n+45 if n<=45 else n-45

def prepara_ruote(a):
    return {str(k).upper():v for k,v in a.items() if isinstance(v,list)}

def numeri_estrazione(lista,i):
    if not isinstance(lista,list) or i<0 or i>=len(lista): return []
    r=lista[i]
    if not isinstance(r,list): return []
    try:return [int(x) for x in r[:5]]
    except (ValueError,TypeError):return []

def ultima_estrazione(lista):
    return numeri_estrazione(lista,len(lista)-1)

def costruisci_ambo(orig,shift):
    a=fuori_90(orig+shift); b=diametrale(a)
    return (a,None) if a==b else (a,b)

# Allineamento: per il backtest si usa sempre la coda comune.
# La previsione corrente, invece, usa SEMPRE [-1] della singola ruota.
def comune(a,b): return min(len(a),len(b))

def idx_comune(lista,pos,n):
    i=len(lista)-n+pos
    return i if 0<=i<len(lista) else None

def nums_comuni(lista,pos,n):
    i=idx_comune(lista,pos,n)
    return numeri_estrazione(lista,i) if i is not None else []

def controlla(archivio,ruote):
    lens={r:len(archivio[r]) for r in ruote}
    vals=list(lens.values())
    return {"allineamento_ok":min(vals)==max(vals),
            "lunghezza_minima":min(vals),
            "lunghezza_massima":max(vals),
            "differenza":max(vals)-min(vals),
            "lunghezze_ruote":lens}

def valuta(a,b,shift,fine,inizio=0):
    n=comune(a,b)
    ultimo=fine-CICLO_MAX-1
    if n<=CICLO_MAX+2 or ultimo<inizio:return None
    ambi=ambate=rapide=cicli=0
    rit_ambo=[]; rit_ambata=[]
    for pos in range(inizio,ultimo+1):
        x=nums_comuni(a,pos,n)
        if not x:continue
        amb,sec=costruisci_ambo(x[0],shift)
        if sec is None:continue
        cicli+=1; hit_a=False; hit_ambo=False; ca=cb=None
        for c in range(1,CICLO_MAX+1):
            p=pos+c
            if p>=n:break
            xa=nums_comuni(a,p,n); xb=nums_comuni(b,p,n)
            unione=set(xa+xb)
            if amb in unione and not hit_a:
                hit_a=True; ca=c
            if (amb in xa and sec in xa) or (amb in xb and sec in xb):
                hit_ambo=True; cb=c; break
        if hit_ambo:
            ambi+=1; rit_ambo.append(cb)
            if cb<=3:rapide+=1
        elif hit_a:
            ambate+=1; rit_ambata.append(ca)
    if cicli==0:return None
    pa=ambi/cicli; paa=ambate/cicli; pr=rapide/cicli
    return {"score":round(pa*1000+pr*250+paa*120,4),
            "cicli":cicli,"ambi":ambi,"ambate":ambate,
            "vittorie_rapide":rapide,
            "percentuale_ambo":round(pa*100,2),
            "percentuale_ambata":round(paa*100,2),
            "percentuale_rapida":round(pr*100,2),
            "ritardi_ambo":rit_ambo,"ritardi_ambata":rit_ambata}

def precedente():
    if not os.path.exists("risultati_v4.json"):return None
    try:
        with open("risultati_v4.json",encoding="utf-8") as f:d=json.load(f)
        m=d.get("motore",{})
        o=str(m.get("ruota_origine","")).upper()
        t=str(m.get("ruota_target","")).upper()
        return (o,t) if o and t else None
    except Exception:return None

def seleziona(a):
    ruote=[r for r in RUOTE if r in a and len(a[r])>CICLO_MAX+2]
    cand=[]
    for o in ruote:
        for t in ruote:
            if o==t:continue
            lo,lt=a[o],a[t]
            n=comune(lo,lt)
            if n<=CICLO_MAX+2:continue
            fine=n-1
            rec=max(0,fine-FINESTRA_RECENTE)
            for shift in SHIFT_CANDIDATI:
                st=valuta(lo,lt,shift,fine,0)
                rr=valuta(lo,lt,shift,fine,rec)
                if st is None or rr is None:continue
                delta=rr["percentuale_ambo"]-st["percentuale_ambo"]
                bonus=max(-2.0,min(2.0,delta*0.10))
                score=st["score"]*PESO_STORICO+rr["score"]*PESO_RECENTE+bonus
                cand.append({"origine":o,"target":t,"shift":shift,"score":score,
                             "score_storico":st["score"],"score_recente":rr["score"],
                             "bonus_consistenza":bonus,"storico":st,"recente":rr,
                             "estrazioni_comuni":n})
    cand.sort(key=lambda x:(x["score"],x["recente"]["ambi"],x["storico"]["ambi"],
                            x["recente"]["vittorie_rapide"],x["recente"]["ambate"]),reverse=True)
    if not cand:return None,[]
    old=precedente(); best=cand[0]
    if old and len(cand)>1 and (best["origine"],best["target"])==old:
        if best["score"]-cand[1]["score"]<0.20:best=cand[1]
    return best,cand[:10]

def costruisci_risultati(archivio,a,best,top,check):
    o,t,shift=best["origine"],best["target"],best["shift"]
    lo,lt=a[o],a[t]
    uo,ut=ultima_estrazione(lo),ultima_estrazione(lt)
    if not uo or not ut:raise ValueError("Ultima estrazione non valida.")
    origine=uo[0]; amb,sec=costruisci_ambo(origine,shift)
    if sec is None:raise ValueError("Ambo non valido.")
    data=datetime.now().strftime("%d/%m/%Y")
    if isinstance(archivio.get("info_concorso"),dict):data=archivio["info_concorso"].get("data",data)
    elif isinstance(archivio.get("data"),str):data=archivio["data"]
    topout=[]
    for p,c in enumerate(top,1):
        topout.append({"posizione":p,"origine":c["origine"],"target":c["target"],"shift":c["shift"],
                       "score":round(c["score"],4),"score_storico":round(c["score_storico"],4),
                       "score_recente":round(c["score_recente"],4),"bonus_consistenza":round(c["bonus_consistenza"],4),
                       "ambi":c["storico"]["ambi"],"ambate":c["storico"]["ambate"],
                       "percentuale_ambo":round(c["storico"]["percentuale_ambo"],2),
                       "percentuale_ambo_recente":round(c["recente"]["percentuale_ambo"],2),
                       "estrazioni_comuni":c["estrazioni_comuni"]})
    pbase=lambda nums:{"numeri_estrazione":nums,
                       "tipo_calcolo":f"Isotopia V10.1: {o} 1° numero ({origine}) + {shift} = {amb}; diametrale = {sec}",
                       "ambata":amb,"ambo":[amb,sec],
                       "ambetti":[[amb,fuori_90(sec+1)],[amb,fuori_90(sec-1)]]}
    res={"info_concorso":{"numero":"Lotto Intelligence V10.1","data":data},
         "motore":{"versione":"V10.1 - Isotopia adattiva dinamica","ruota_origine":o,"ruota_target":t,
                   "trasformazione":"DIAMETRALE","shift":shift,
                   "score_backtest":round(best["score"],4),"score_storico":round(best["score_storico"],4),
                   "score_recente":round(best["score_recente"],4),"finestra_recente":FINESTRA_RECENTE,
                   "peso_storico":PESO_STORICO,"peso_recente":PESO_RECENTE,
                   "cicli_testati":best["storico"]["cicli"],"ambi_backtest":best["storico"]["ambi"],
                   "ambate_backtest":best["storico"]["ambate"],"vittorie_rapide_1_3":best["storico"]["vittorie_rapide"],
                   "percentuale_ambo":round(best["storico"]["percentuale_ambo"],2),
                   "percentuale_ambata":round(best["storico"]["percentuale_ambata"],2),
                   "percentuale_rapida":round(best["storico"]["percentuale_rapida"],2),
                   "ambi_recenti":best["recente"]["ambi"],"ambate_recenti":best["recente"]["ambate"],
                   "percentuale_ambo_recente":round(best["recente"]["percentuale_ambo"],2),
                   "percentuale_ambata_recente":round(best["recente"]["percentuale_ambata"],2),
                   "estrazioni_comuni_coppia":best["estrazioni_comuni"],
                   "controllo_allineamento":check,"top10_configurazioni":topout},
         "previsioni":{o:pbase(uo),t:pbase(ut)},"storico_verificato":[]}
    n=comune(lo,lt); last=n-1
    for dist in range(1,min(10,last)+1):
        pos=last-dist; e=nums_comuni(lo,pos,n)
        if not e:continue
        ap,sp=costruisci_ambo(e[0],shift)
        stato="In gioco"; cv=None
        for c in range(1,CICLO_MAX+1):
            pp=pos+c
            if pp>=n:break
            xa=nums_comuni(lo,pp,n); xb=nums_comuni(lt,pp,n)
            if (ap in xa and sp in xa) or (ap in xb and sp in xb):
                stato="AMBO SECCO VINCENTE!";cv=c;break
            if ap in xa or ap in xb:
                if stato=="In gioco":stato="Ambata Vincente";cv=c
        if stato=="In gioco" and dist>CICLO_MAX:stato="Ciclo concluso (No esito)"
        res["storico_verificato"].append({"data":f"Concorso Arretrat. -{dist}",
                                          "ambata":ap,"ambo":f"{ap} - {sp}",
                                          "colpi":f"Esito al {cv}° colpo" if cv else f"{dist}° Colpo",
                                          "stato":stato})
    return res

def elabora_motore_v10():
    if not os.path.exists("estrazioni.json"):
        print("ERRORE: estrazioni.json non trovato.");return
    with open("estrazioni.json",encoding="utf-8") as f:archivio=json.load(f)
    a=prepara_ruote(archivio)
    ruote=[r for r in RUOTE if r in a and len(a[r])>CICLO_MAX+2]
    if len(ruote)<2:
        print("ERRORE: almeno due ruote con storico sufficiente.");return
    check=controlla(a,ruote)
    best,top=seleziona(a)
    if best is None:
        print("ERRORE: nessuna configurazione valida trovata.");return
    res=costruisci_risultati(archivio,a,best,top,check)
    with open("risultati_v4.json","w",encoding="utf-8") as f:json.dump(res,f,indent=4,ensure_ascii=False)
    m=res["motore"];p=res["previsioni"];o=m["ruota_origine"];t=m["ruota_target"];am=p[o]["ambo"]
    print("==============================================")
    print("LOTTO INTELLIGENCE V10.1")
    print("==============================================")
    print(f"Ruota origine : {o}")
    print(f"Ruota target  : {t}")
    print(f"Shift         : +{m['shift']}")
    print(f"Ambata        : {p[o]['ambata']}")
    print(f"Ambo secco    : {am[0]} - {am[1]}")
    print("----------------------------------------------")
    print(f"Ultima {o}: {p[o]['numeri_estrazione']}")
    print(f"Ultima {t}: {p[t]['numeri_estrazione']}")
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
    print("CONTROLLO ALLINEAMENTO")
    print(f"Min estrazioni: {check['lunghezza_minima']}")
    print(f"Max estrazioni: {check['lunghezza_massima']}")
    print(f"Differenza    : {check['differenza']}")
    print("----------------------------------------------")
    print("TOP 3 CONFIGURAZIONI")
    for x in m["top10_configurazioni"][:3]:
        print(f"{x['posizione']}. {x['origine']} -> {x['target']} +{x['shift']} | score {x['score']}")
    print("==============================================")

if __name__=="__main__":elabora_motore_v10()
