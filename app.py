import json
from analisi_ambi import analizza_ruote

def main():
    with open("estrazioni.json") as f:
        dati = json.load(f)

    risultati = analizza_ruote(dati)

    with open("risultati.json", "w") as f:
        json.dump(risultati, f, indent=2)

if __name__ == "__main__":
    main()