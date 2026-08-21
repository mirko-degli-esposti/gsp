# Analisi campagne scelta post-diploma

batterie: 1296 · agenti: 432 · modelli: deepseek-chat

## 1. Pulizia del parsing

- deepseek-chat · prob_universita: pulito 100.0%, None 0.0% (n 1296)
- deepseek-chat · situazione: pulito 100.0%, None 0.0% (n 1296)

## 2. Distribuzione delle scelte (H4)

- deepseek-chat: università=53.1%  lavoro o ricerca di un lavoro=46.8%  ITS o altra formazione=0.1%

## 3. Stabilita' fra repliche/rotazioni

- deepseek-chat: agenti con scelta identica su tutte le repliche 85.6% · sd media della prob entro agente 5.63

Le repliche ruotano le opzioni: l'accordo copre insieme rumore e posizione.

## 4. Ancore del continuo

- deepseek-chat: multipli di 10 93.1% · primi valori: 30 (35%), 70 (25%), 50 (11%), 80 (7%), 20 (4%), 85 (4%)

## 5. Quota `università` e prob media per asse


### deepseek-chat

- **diploma3**: liceo: 99.3%/72 (n432)  professionale: 3.7%/27 (n432)  tecnico: 56.2%/49 (n432)
- **gen3**: bassa: 43.3%/43 (n432)  diploma: 53.7%/49 (n432)  laurea+: 62.3%/56 (n432)
- **sesso**: F: 54.9%/50 (n648)  M: 51.2%/49 (n648)
- **straniero**: False: 54.9%/49 (n648)  True: 51.2%/50 (n648)
- **eta**: 19: 65.1%/58 (n378)  20: 59.0%/53 (n261)  21: 48.9%/47 (n315)  22: 39.2%/40 (n342)
- **comune**: 017029: 53.0%/48 (n117)  033032: 53.3%/53 (n75)  034027: 56.4%/52 (n117)  035033: 50.4%/51 (n129)  036023: 50.7%/48 (n144)  037006: 60.2%/54 (n201)  038008: 55.7%/48 (n201)  039014: 48.6%/47 (n138)  040012: 48.8%/46 (n84)  099014: 45.6%/46 (n90)

(quota/prob; il segno di H1-H3 si legge qui, la stima nel §7)

## 6. La qualifica triennale (H5)


Se le due colonne coincidono, il modello non distingue il non-accesso: H5 confermata.

## 7. Logit  P(scelta = universita')


### deepseek-chat
    intercetta             beta  -0.215  (se 0.441)
    diploma3=liceo         beta  +5.804  (se 0.637)
    diploma3=professionale beta  -4.630  (se 0.357)
    gen3=diploma           beta  +1.371  (se 0.272)
    gen3=laurea+           beta  +2.731  (se 0.307)
    sesso=F                beta  +0.889  (se 0.224)
    straniero              beta  -0.998  (se 0.258)
    eta-19                 beta  -0.754  (se 0.103)
    comune=033032          beta  -0.053  (se 0.607)
    comune=034027          beta  +0.570  (se 0.526)
    comune=035033          beta  +0.057  (se 0.507)
    comune=036023          beta  -0.034  (se 0.466)
    comune=037006          beta  +0.655  (se 0.457)
    comune=038008          beta  +1.478  (se 0.468)
    comune=039014          beta  -0.172  (se 0.500)
    comune=040012          beta  +0.672  (se 0.546)
    comune=099014          beta  -0.963  (se 0.576)

Il confronto con i coefficienti reali (MUR/AlmaDiploma, stessa specificazione) sta nella nota: i riferimenti vanno presi da fonte, non a memoria.

