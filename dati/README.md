# dati/ — materiale degli esperimenti LLM su popolazioni GSP

Questa cartella contiene gli **input e gli output degli esperimenti di
simulazione con LLM** condotti sulle popolazioni sintetiche GSP (condizioni
Brescia, confronto multi-modello, groundstate, giudizio umano). È il materiale
citato nella Parte V del report tecnico e nel registro
`registro_esperimento_sive_gsp`.

Nessun individuo qui descritto esiste: gli agenti sono campionati da una
popolazione simulata da aggregati ISTAT (vedi `note/piano_trattamento`).

## Struttura

| cartella | contenuto | regime |
|---|---|---|
| `agenti/` | campioni di agenti per comune, livello, n e seed; attributi demografici, derivati e vettore AVQ | **persona** |
| `agenti/*_storie*.json`, `*_neutre*.json` | storie in prima persona generate da un LLM a partire dall'agente | narrativo (testo generato) |
| `campagne/` | risposte dei modelli agli item della batteria, per agente (`uid`), condizione e modello | risultati |
| `campagne/groundstate/` | misure di stato base senza profilo | risultati |
| `giudizio/` | materiale per il giudizio umano (chiave e pagina) | risultati |

Il campo `uid` (`{comune}-{indice}`) collega ogni risposta al suo agente.

## Regime dei file `agenti/`

I file `agenti/agenti_*.json` sono nel regime **persona**: contengono ciò che
serve a costruire un prompt (sesso, età, stato civile, cittadinanza, istruzione,
condizione, settore, zona, quartiere, vettore AVQ) e **non** contengono nome,
via, civico, coordinate né identificativo del donatore AVQ. È lo stesso
perimetro del bundle pubblico di Animarium; l'intestazione di ogni file lo
dichiara (`regime`, `campi_rimossi`, `regime_applicato`).

**Nota storica, dichiarata.** Fino al commit che introduce questo README, gli
stessi file portavano tre campi in più: `nome` (generato dai repertori
onomastici, plausibile e collidente per costruzione), `via` (senza numero
civico) e `donor_id`. Sono stati rimossi il 18 agosto 2026 per coerenza con il
regime pubblico, senza rigenerare il campione: `uid`, seed e attributi sono
identici. Le versioni precedenti restano nella storia del repository; non
contengono civico né coordinata, che non hanno mai lasciato la macchina di
generazione.

## Le storie

I file `*_storie*.json` sono l'input effettivo delle campagne pubblicate e non
vengono rigenerati: rigenerarli cambierebbe i risultati che citiamo. Sono testo
prodotto da un LLM su un agente che non esiste; il nome che vi compare è
generato e non corrisponde ad alcuna persona.

## Riproducibilità

Ogni file di campagna dichiara in testa `modello`, `temperatura`, `condizioni`,
`items` e il file di storie usato. Le risposte dei modelli non sono
deterministiche: rilanciare una campagna riproduce le statistiche aggregate
(Spearman, distribuzioni per item), non le singole risposte.
