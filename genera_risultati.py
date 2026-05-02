// ===== MOTORE 9 PRO COMPLETO =====

function generaRisultatiPRO(datiStorici) {

    let output = {
        top: {}
    };

    Object.entries(datiStorici).forEach(([ruota, storico]) => {

        let stats = analizzaStorico(storico);

        let terno = generaTernoPRO(stats, storico[0]);

        let score = calcolaScorePRO(terno, stats);

        output.top[ruota] = {
            ultima_estrazione: storico[0],
            numeri: terno,
            score: score
        };

    });

    return output;
}


// ===== ANALISI STORICO =====
function analizzaStorico(storico) {

    let freq = {};
    let ritardo = {};

    for (let i = 1; i <= 90; i++) {
        freq[i] = 0;
        ritardo[i] = 0;
    }

    storico.forEach((estrazione) => {

        estrazione.forEach(n => {
            freq[n]++;
            ritardo[n] = 0;
        });

        for (let i = 1; i <= 90; i++) {
            if (!estrazione.includes(i)) {
                ritardo[i]++;
            }
        }
    });

    return { freq, ritardo };
}


// ===== GENERAZIONE TERNO =====
function generaTernoPRO(stats, ultima) {

    let pool = [];

    for (let i = 1; i <= 90; i++) {

        if (ultima.includes(i)) continue;

        let valore =
            stats.ritardo[i] * 3 +
            (10 - stats.freq[i]) * 2;

        pool.push({ n: i, v: valore });
    }

    pool.sort((a, b) => b.v - a.v);

    let candidati = pool.slice(0, 25).map(x => x.n);

    let terno = [];

    while (terno.length < 3) {
        let n = candidati[Math.floor(Math.random() * candidati.length)];
        if (!terno.includes(n)) terno.push(n);
    }

    return terno;
}


// ===== SCORE =====
function calcolaScorePRO(terno, stats) {

    let score = 0;

    terno.forEach(n => {
        score += stats.ritardo[n] * 4;
        score += (10 - stats.freq[n]) * 2;
    });

    score += Math.abs(terno[0] - terno[1]);
    score += Math.abs(terno[1] - terno[2]);

    score += Math.random() * 10;

    return Math.floor(score);
}