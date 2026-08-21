# Benchmark reali per l'esperimento priors — nota fonti

**nota_benchmark_scelta_v1 — 20 agosto 2026**

I numeri con cui confrontare le risposte LLM, presi da fonte il 20/8/2026
(ricerca web; ogni valore ha accanto fonte, popolazione e definizione).
Sostituiscono i valori «a memoria» usati in fase di disegno, due dei
quali erano sbagliati e sono ritrattati in §5.

---

## 1. Le DUE definizioni, e quale corrisponde al nostro item

I tassi in circolazione appartengono a due famiglie che differiscono di
~20 punti, e confonderle e' l'errore piu' facile:

**(A) Immatricolazione immediata** (amministrativa, universo nazionale):
diplomati dell'anno X immatricolati nell'a.a. X/X+1. Fonte: MUR/ANS,
ripresa da ISTAT (Annuario statistico, cap. 7, tavola «diplomati 2023
immatricolati nello stesso anno»). Livello complessivo: ~1 su 2.

**(B) Iscrizione a un anno dal diploma** (indagine AlmaDiploma):
diplomati iscritti a un corso di laurea a 12 mesi, lavoro incluso.
Complessivo: 71,4% (diplomati 2023). **ATTENZIONE al campione**:
AlmaDiploma copre ~300 scuole aderenti, non e' rappresentativo
nazionale, e i suoi tassi stanno sistematicamente sopra quelli ANS.

**Il nostro item** («iscritto/a a ottobre», finestra 19-22) e' una
quantita' MISTA: per i 19enni ~ (A); per i 20-22enni ~ iscrizione
cumulata, piu' vicina a (B) al netto degli abbandoni. Il confronto
principale va fatto per contrasti (differenze fra gruppi), non per
livelli: i contrasti sono piu' stabili delle quote fra le due
definizioni. Il sottocampione dei 19enni permette il confronto pulito
con (A).

---

## 2. Tipo di diploma (H1) — definizione (A), dati ministeriali

Diplomati ~2022/23, immatricolazione immediata (analisi Skuola.net su
dati MUR, ott. 2023):

| percorso | tasso | dettagli |
|---|---:|---|
| **Licei (tutti)** | **73,6%** | classico 87,3 · scientifico ~87 · scienze applicate 81,6 · internazionale 80,6 · artistico 30,3 · musicale 40,8 |
| **Tecnici** | **34,5%** | economici 36,2 · tecnologici 33,2 |
| **Professionali** | **13,7%** | industria e artigianato 7,5 |

Conferme indipendenti: MUR Notiziario 1/2012 (coorte 2010/11: stessa
gerarchia; artistici 26%); Eduscopio (tecnici ~1/3-1/2, professionali
~1/5); AlmaDiploma «solo studio» a 1 anno: liceali 72, tecnici 37,
professionali 21,5 (coorte 2011).

Contrasti in log-odds (per il confronto coi beta del logit, riferimento
tecnico): **liceo vs tecnico +1,67 · professionale vs tecnico −1,20.**

Nota per la mappa: artistico al 30% conferma l'esclusione della filiera
dalla classe `liceo` (mappa v2).

---

## 3. Istruzione dei genitori (H2) — definizione (B), AlmaDiploma

Iscrizione all'universita' a un anno, per titolo dei genitori:

| coorte | genitore laureato | genitori diplomati | genitori non diplomati |
|---|---:|---:|---:|
| diplomati 2014 (rapp. 2016) | 86% | 64% | 43% |
| diplomati 2018 (rapp. 2020) | **82,2%** | **66,5%** | **51,1%** |
| diplomati 2020 (rapp. 2022)* | 90,7% | 76,6% | — |
| diplomati 2024 (rapp. 2026) | 84,3% | 66,1% | — |

\* coorte covid, quote gonfiate; la riga di riferimento e' il 2018.

Contrasti (2018, log-odds, rif. non diplomati): **laurea+ vs bassa
+1,49 · diploma vs bassa +0,64.** Gerarchia stabile su dieci anni.

Meccanismo a monte (per l'interpretazione, non per il logit): meta'
dell'effetto genitori passa dalla SCELTA della scuola — genitori
laureati fra i diplomati: classico 59%, scientifico 43%, tecnici 13-14%,
professionali 8-11% (AlmaDiploma 2017). Nel nostro disegno questo
canale e' TAGLIATO per costruzione (celle incrociate, genitori
indipendenti dal diploma): il beta LLM su gen3 misura solo l'effetto
DIRETTO, e va confrontato col contrasto condizionale reale, che e' piu'
piccolo del marginale in tabella. Vedi §6.

---

## 4. Sesso, eta', cittadinanza (H3 e controlli)

**Sesso** (AlmaDiploma, diplomati 2020 a 1 anno): iscritte 79,6% contro
iscritti 71,1% → contrasto F−M ~ +0,46 log-odds (marginale).

**Eta'** (MUR Notiziario 1/2012; forma, non livello): si immatricola
nello stesso anno del diploma >70% dei 18enni, ~50% dei 19enni, ~30%
dei 20enni, a scendere. Gradiente fortemente negativo: il beta di
`eta-19` deve uscire negativo e grande (H3).

**Cittadinanza** — IL BUCO. Il tasso di passaggio dei diplomati
stranieri non circola in forma divulgata. Due punti fermi:
- la selezione avviene A MONTE: tasso di scolarita' 17-18 anni dei
  cittadini non italiani 77,4% (MIM, a.s. 2020/21) contro >95%
  complessivo — chi arriva al diploma e' gia' selezionato;
- la fonte da cui estrarre il numero: ISTAT, Annuario statistico
  (cap. 7, tavola diplomati→immatricolati per caratteristiche) e MUR
  focus «studenti con cittadinanza non italiana». **DA COMPLETARE**
  prima di leggere il beta `straniero` come confronto quantitativo;
  fino ad allora, solo il segno.

---

## 5. Ritrattazioni dei valori «a memoria»

1. «liceo ~80, tecnico 35-40, professionale ~15» → sostanzialmente
   giusti (73,6 / 34,5 / 13,7), liceo un po' sovrastimato.
2. «genitori laureati ~75% vs ~30%» → **sbagliato in ampiezza**: il
   divario reale e' 82 vs 51 (definizione B), ~30 punti e non ~45.
   H2 va giudicata contro +1,49 log-odds, non contro il ricordo.
3. Nessuna fonte trovata per un «tasso stranieri» citabile: il valore
   non era nemmeno da ritrattare — non esisteva.

---

## 6. Come si usa questa nota nell'analisi

1. **Contrasti, non livelli**: confrontare i beta LLM con i contrasti
   in log-odds qui sopra; i livelli assoluti dipendono dalla
   definizione (A/B) e dalla finestra.
2. **Marginale ≠ parziale, e il verso del distorsore e' noto**: i
   contrasti reali qui sono MARGINALI e nel mondo reale diploma e
   genitori sono correlati (§3), quindi ciascun marginale ingloba parte
   dell'altro effetto. I beta LLM del nostro disegno sono invece
   quasi-parziali (celle incrociate ~bilanciate). Conseguenza: usare i
   marginali reali come metro RENDE PIU' DIFFICILE confermare H1
   (beta diploma LLM > reale gia' gonfiato) e PIU' FACILE H2 — quindi
   una H1 confermata e' robusta, una H2 confermata va pesata. Il
   confronto pulito richiederebbe i contrasti condizionali reali
   (microdati AlmaDiploma o letteratura): aperto.
3. **Il sottocampione 19enni** contro la definizione (A); il campione
   pieno contro contrasti, con la finestra dichiarata.
4. **Qualifiche (H5)**: escluse da tutti i tassi qui sopra (che contano
   maturita'). Il riferimento reale per una qualifica triennale e'
   ~0 per definizione di non-accesso.

## Fonti (consultate 20/8/2026)

- MUR/Skuola.net via TGcom24, «Un diplomato su due si iscrive...»,
  ott. 2023 (tassi per indirizzo, dati ministeriali)
- MUR-USTAT, Notiziario 1/2012, «Il passaggio dalla scuola secondaria
  all'Universita'» (gradiente d'eta'; coorte 2010/11)
- AlmaDiploma/AlmaLaurea: Rapporto 2020 (diplomati 2018), Rapporto 2022
  via InfoData-Sole24Ore (diplomati 2020; sesso), Rapporto 2025
  (diplomati 2023: 71,4% a un anno), Rapporto 2026 via stampa
  (diplomati 2024), Convegno 2017 (genitori per indirizzo)
- Eduscopio, «Dati e metodologia» (ordini di grandezza per indirizzo)
- MIM, «Studenti con cittadinanza non italiana», lug. 2022 (scolarita')
- ISTAT, Annuario statistico 2025, cap. 7 (tavola diplomati 2023
  immatricolati stesso anno — da spogliare per sesso/cittadinanza)
