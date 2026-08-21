# Analisi campagne scelta post-diploma

batterie: 3888 · agenti: 432 · modelli: claude-haiku-4.5, deepseek-chat, gpt-4o-mini

## 1. Pulizia del parsing

- claude-haiku-4.5 · prob_universita: pulito 100.0%, None 0.0% (n 1296)
- claude-haiku-4.5 · situazione: pulito 100.0%, None 0.0% (n 1296)
- deepseek-chat · prob_universita: pulito 100.0%, None 0.0% (n 1296)
- deepseek-chat · situazione: pulito 100.0%, None 0.0% (n 1296)
- gpt-4o-mini · prob_universita: pulito 100.0%, None 0.0% (n 1296)
- gpt-4o-mini · situazione: pulito 93.0%, None 0.0% (n 1296)

## 2. Distribuzione delle scelte (H4)

- claude-haiku-4.5: lavoro o ricerca di un lavoro=65.9%  università=34.1%
- deepseek-chat: università=53.1%  lavoro o ricerca di un lavoro=46.8%  ITS o altra formazione=0.1%
- gpt-4o-mini: università=56.4%  ITS o altra formazione=23.1%  lavoro o ricerca di un lavoro=18.8%  altro=1.7%

## 3. Stabilita' fra repliche/rotazioni

- claude-haiku-4.5: agenti con scelta identica su tutte le repliche 94.2% · sd media della prob entro agente 0.98
- deepseek-chat: agenti con scelta identica su tutte le repliche 85.6% · sd media della prob entro agente 5.63
- gpt-4o-mini: agenti con scelta identica su tutte le repliche 32.6% · sd media della prob entro agente 1.13

Le repliche ruotano le opzioni: l'accordo copre insieme rumore e posizione.

## 4. Ancore del continuo

- claude-haiku-4.5: multipli di 10 0.0% · primi valori: 35 (36%), 75 (21%), 25 (17%), 72 (8%), 15 (6%), 45 (6%)
- deepseek-chat: multipli di 10 93.1% · primi valori: 30 (35%), 70 (25%), 50 (11%), 80 (7%), 20 (4%), 85 (4%)
- gpt-4o-mini: multipli di 10 98.2% · primi valori: 70 (76%), 80 (16%), 50 (4%), 60 (2%), 85 (1%), 30 (1%)

## 5. Quota `università` e prob media per asse


### claude-haiku-4.5

- **diploma3**: liceo: 94.7%/70 (n432)  professionale: 0.0%/28 (n432)  tecnico: 7.6%/40 (n432)
- **gen3**: bassa: 30.3%/39 (n432)  diploma: 31.7%/44 (n432)  laurea+: 40.3%/55 (n432)
- **sesso**: F: 34.0%/47 (n648)  M: 34.3%/45 (n648)
- **straniero**: False: 34.9%/47 (n648)  True: 33.3%/46 (n648)
- **eta**: 19: 38.9%/50 (n378)  20: 43.7%/51 (n261)  21: 30.2%/44 (n315)  22: 25.1%/40 (n342)
- **comune**: 017029: 34.2%/46 (n117)  033032: 36.0%/46 (n75)  034027: 36.8%/48 (n117)  035033: 34.9%/46 (n129)  036023: 34.7%/48 (n144)  037006: 35.3%/50 (n201)  038008: 33.8%/44 (n201)  039014: 30.4%/42 (n138)  040012: 28.6%/43 (n84)  099014: 35.6%/46 (n90)

### deepseek-chat

- **diploma3**: liceo: 99.3%/72 (n432)  professionale: 3.7%/27 (n432)  tecnico: 56.2%/49 (n432)
- **gen3**: bassa: 43.3%/43 (n432)  diploma: 53.7%/49 (n432)  laurea+: 62.3%/56 (n432)
- **sesso**: F: 54.9%/50 (n648)  M: 51.2%/49 (n648)
- **straniero**: False: 54.9%/49 (n648)  True: 51.2%/50 (n648)
- **eta**: 19: 65.1%/58 (n378)  20: 59.0%/53 (n261)  21: 48.9%/47 (n315)  22: 39.2%/40 (n342)
- **comune**: 017029: 53.0%/48 (n117)  033032: 53.3%/53 (n75)  034027: 56.4%/52 (n117)  035033: 50.4%/51 (n129)  036023: 50.7%/48 (n144)  037006: 60.2%/54 (n201)  038008: 55.7%/48 (n201)  039014: 48.6%/47 (n138)  040012: 48.8%/46 (n84)  099014: 45.6%/46 (n90)

### gpt-4o-mini

- **diploma3**: liceo: 90.3%/75 (n432)  professionale: 22.7%/66 (n432)  tecnico: 56.2%/70 (n432)
- **gen3**: bassa: 45.8%/68 (n432)  diploma: 55.1%/71 (n432)  laurea+: 68.3%/73 (n432)
- **sesso**: F: 60.2%/72 (n648)  M: 52.6%/69 (n648)
- **straniero**: False: 56.5%/70 (n648)  True: 56.3%/71 (n648)
- **eta**: 19: 66.4%/71 (n378)  20: 57.5%/71 (n261)  21: 58.1%/70 (n315)  22: 43.0%/69 (n342)
- **comune**: 017029: 57.3%/70 (n117)  033032: 53.3%/69 (n75)  034027: 59.8%/71 (n117)  035033: 51.2%/70 (n129)  036023: 55.6%/71 (n144)  037006: 63.7%/72 (n201)  038008: 56.7%/71 (n201)  039014: 51.4%/70 (n138)  040012: 58.3%/70 (n84)  099014: 51.1%/70 (n90)

(quota/prob; il segno di H1-H3 si legge qui, la stima nel §7)

## 6. La qualifica triennale (H5)

- claude-haiku-4.5 · professionale: SOLO qualifiche (n432, prob 28.3) — riferimento reale ~0 per non-accesso; confronto interno impossibile
- claude-haiku-4.5 · tecnico: prob qualifica 32.9 (n39) vs maturita' 40.7 (n393) · univ 0.0% vs 8.4%
- deepseek-chat · professionale: SOLO qualifiche (n432, prob 27.4) — riferimento reale ~0 per non-accesso; confronto interno impossibile
- deepseek-chat · tecnico: prob qualifica 35.1 (n39) vs maturita' 50.7 (n393) · univ 20.5% vs 59.8%
- gpt-4o-mini · professionale: SOLO qualifiche (n432, prob 66.4) — riferimento reale ~0 per non-accesso; confronto interno impossibile
- gpt-4o-mini · tecnico: prob qualifica 69.5 (n39) vs maturita' 70.5 (n393) · univ 30.8% vs 58.8%

Se le due colonne coincidono, il modello non distingue il non-accesso: H5 confermata.

## 7. Logit  P(scelta = universita')


### claude-haiku-4.5  **[quasi-separazione: i beta oltre ~8 si leggono come 'oltre soglia']**
    intercetta             beta  -5.390  (se 0.877)
    diploma3=liceo         beta  +8.960  (se 0.802)
    diploma3=professionale beta -15.344  (se 246.496)
    gen3=diploma           beta  +0.365  (se 0.450)
    gen3=laurea+           beta  +4.295  (se 0.723)
    sesso=F                beta  +0.023  (se 0.322)
    straniero              beta  -1.023  (se 0.367)
    eta-19                 beta  -0.747  (se 0.174)
    comune=033032          beta  -0.797  (se 0.756)
    comune=034027          beta  +0.891  (se 0.741)
    comune=035033          beta  +2.162  (se 0.837)
    comune=036023          beta  +2.201  (se 0.726)
    comune=037006          beta  +0.694  (se 0.697)
    comune=038008          beta  +2.609  (se 0.742)
    comune=039014          beta  -0.292  (se 0.613)
    comune=040012          beta  +1.085  (se 0.873)
    comune=099014          beta  +0.886  (se 0.785)

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

### gpt-4o-mini
    intercetta             beta  -0.220  (se 0.298)
    diploma3=liceo         beta  +2.154  (se 0.200)
    diploma3=professionale beta  -1.617  (se 0.163)
    gen3=diploma           beta  +0.571  (se 0.175)
    gen3=laurea+           beta  +1.415  (se 0.184)
    sesso=F                beta  +0.663  (se 0.148)
    straniero              beta  -0.018  (se 0.160)
    eta-19                 beta  -0.336  (se 0.065)
    comune=033032          beta  -0.351  (se 0.395)
    comune=034027          beta  +0.030  (se 0.339)
    comune=035033          beta  -0.232  (se 0.334)
    comune=036023          beta  -0.068  (se 0.316)
    comune=037006          beta  +0.212  (se 0.303)
    comune=038008          beta  +0.121  (se 0.308)
    comune=039014          beta  -0.113  (se 0.323)
    comune=040012          beta  +0.547  (se 0.364)
    comune=099014          beta  -0.234  (se 0.366)

Il confronto con i coefficienti reali (MUR/AlmaDiploma, stessa specificazione) sta nella nota: i riferimenti vanno presi da fonte, non a memoria.

## 8. Concordanza fra modelli

- rho Spearman prob per agente claude-haiku-4.5 ~ deepseek-chat: +0.831 (n 432)
- rho Spearman prob per agente claude-haiku-4.5 ~ gpt-4o-mini: +0.706 (n 432)
- rho Spearman prob per agente deepseek-chat ~ gpt-4o-mini: +0.700 (n 432)

