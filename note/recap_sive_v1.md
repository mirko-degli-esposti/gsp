# SIVE — dove siamo, e dove stanno note e codice del χ²

**v1 — 15 settembre 2026** · nota di orientamento, non permanente
Ricostruita dal `registro_esperimento_sive_gsp_v5.md` (6 agosto) e da
`sive_paper_v6.tex`. Non contiene numeri nuovi: raccoglie quelli già
misurati e dice quali reggono, quali valgono per un solo modello e
quali sono ancora aperti.

---

## 1. L'esperimento del χ² — cosa c'è e dove

La domanda era: in condizione C (solo profilo demografico, nessuna
storia) il modello risponde in modo **uniforme**, o l'emozione dichiarata
dipende da età, sesso, istruzione, posizione?

### Le note

| dove | cosa |
|---|---|
| registro v5, **§8** | l'origine: in C le scale numeriche sono piatte ma i categoriali no — 62–75% «preoccupazione», zero «sollievo» |
| registro v5, **§9** | la misura su 600 agenti: χ² per variabile, la falsificazione dell'età, lo stereotipo di sesso e istruzione |
| registro v5, **§10** | il groundstate a vuoto e la **correzione**: quei priors sono di DeepSeek, non degli LLM |
| registro v5, §12 | la mappa dei file |

### Il codice (`scripts/narrativa/`)

| script | ruolo nel χ² |
|---|---|
| `campiona_agenti.py` | il campione: livello A, riproducibile da `(comune, variabile, n, seed)` — per la §9: Brescia 017029, PUNTIFI10, **n 600, seed 7** |
| `harness.py` | la campagna: condizione C, solo item `emozione`, T 0,3, nessuna storia da generare, 600 chiamate |
| **`analizza_demo.py`** | il χ² vero e proprio: risposte × attributo, celle attese, p |
| `groundstate.py` | il fattoriale ridotto (livello 0: nessun profilo; livello 1: un attributo alla volta; livello 2: sei interazioni), tre modelli |
| `analizza_item.py` | tutti e cinque gli item, da cui è nata la §8 |

### I dati (`dati/campagne/`)

```
campagna_..._n600_s7_emozione_C_t03.json      la §9, DeepSeek
emo_*/                                        solo `emozione`, una cartella per modello
                                              (gpt-4o-mini 120/120, haiku 118/120 preoccupazione)
groundstate/                                  livelli 0 e 1, tre modelli, T 1,0
```

### I numeri, per non doverli ricercare

Su 600 agenti, DeepSeek, condizione C, item `emozione`:

| variabile | χ² | p | esito |
|---|---|---|---|
| **sesso** | **71,6** | <0,001 | struttura |
| **istruzione** | **36,3** | <0,001 | struttura |
| posizione | 8,2 | 0,041 | forse |
| età | 7,4 | 0,283 | nessuna |

```
donne    72% preoccupazione ·  1% rabbia · 17% speranza · 10% indifferenza
uomini   54% preoccupazione · 14% rabbia ·  7% speranza · 25% indifferenza

istruzione alta   26% speranza · 1% rabbia
istruzione bassa   5% speranza · 9% rabbia
```

L'età a n=120 dava p = 0,007 con sette celle attese sotto cinque; a
n=600 è scesa a 0,283. Era rumore, e il campione grande ha falsificato
un segnale e confermato l'altro.

### Le tre cose da tenere a mente quando lo si riprende

**Vale per DeepSeek.** GPT-4o-mini e Haiku rispondono «preoccupazione»
nel 100% e 98% dei casi con i profili completi, e nel 100% in ogni cella
del groundstate a T 1,0. Dove non c'è varianza non c'è struttura da
misurare; un modello che dice sempre la stessa parola è **muto**, non
neutro — potrebbe avere stereotipi fortissimi e non manifestarli.

**A vuoto DeepSeek è ottimista** (50% speranza, 25% indifferenza, 22%
preoccupazione, 2% rabbia) e col solo profilo diventa 62–75%
preoccupato. Il profilo non aggiunge una sfumatura: ribalta la risposta.

**Tre spiegazioni, nessuna verificata**: la domanda ha una risposta
ovvia per due modelli su tre; GPT e Haiku sono più allineati e la
risposta prudente vince sempre; oppure DeepSeek è solo più rumoroso e il
χ² di 71,6 misura struttura nel rumore. Contro l'ultima c'è che la
struttura è ordinata come uno stereotipo da manuale — emozioni passive
alle donne, attive agli uomini — e il rumore non produce quello. Ma non
è una dimostrazione.

### Cosa lo chiuderebbe (proposte, non fatte)

- **Il test del rumore**, che è l'ipotesi scomoda: rigirare gli stessi
  600 profili con 5 repliche ciascuno. Se la varianza entro agente è
  dello stesso ordine di quella fra gruppi, il χ² misura campionamento;
  se lo stereotipo di sesso si ripete replica per replica, è del modello.
  3.000 chiamate, solo `emozione`, costo trascurabile.
- **Un quarto modello che vari.** Gemini flash (che ora usiamo per i
  testi di `volti`) e un modello open di altra famiglia: se un secondo
  modello varia e mostra lo stesso ordine, il risultato smette di essere
  «di DeepSeek».
- **Il formato della domanda** (§13): se il 5 in C è astensione e non
  posizione, si sposta riformulando — «diresti che ti fidi?» oppure
  «commenta e poi valuta». Dieci agenti bastano, e serve anche per
  sapere se il determinismo di GPT/Haiku sui categoriali è della
  domanda o del modello.

---

## 2. SIVE — il quadro in due esperimenti

### SIVE-Montelago (il paper, v6)

*Calibrating the Instrument: Controllability of an LLM-Driven Synthetic
Population* — target JASSS; la v6 nel progetto è la versione arXiv con
autore visibile (la riga anonima è commentata).

Comune fittizio, 120 personas con latente noto e nascosto (fiducia
istituzionale LOW/MED/HIGH, 40+40+40), sette condizioni sulla rete
idrica (POS, POS2, POSW, POSW2, NEG, PLA, CTRL), batteria PRE → stimolo →
tre reazioni → POST, 13 chiamate per agente per condizione. DeepSeek,
sweep t ∈ {0,2, 0,5, 0,7}, 9.240 righe di questionario e 2.160
trascrizioni.

**Tutti e sette i criteri passano a tutte le temperature.**

| criterio | risultato (t=0,2) |
|---|---|
| C1 fedeltà | r = 0,891 su fiducia (0,911 / 0,900 alle altre t); adeguatezza sotto soglia solo a 0,2 (0,762) |
| C2 stabilità PRE fra condizioni | r_min 0,858–0,876, e cresce con t |
| C3 rumore | σ_cross ≈ 1,4; **σ_instr ≈ 0,77**, invariante in t, dipendente dal profilo; bias di replica dentro la ROPE |
| C4 placebo | PLA − CTRL = −0,025 |
| C5 sensibilità | POS +0,16 · POSW2 +0,11 · CTRL −0,04 · PLA −0,07 · **POSW −0,51** · NEG −1,65 |
| C6 ordinamento | τ = 1,000 (0,905 a t=0,5); era 0,600 n.s. col disegno a sei condizioni |
| C7 ricezione | tutte le condizioni on-topic spostano `adeguatezza` rispetto a CTRL (min 0,26, max 1,73) |

I tre risultati che il paper porta come contributo: il **ciclo
POSW/POSW2** (uno stimolo pensato come debolmente positivo letto dallo
strumento come negativo, diagnosticato — nessuna azione, nessuna
tempistica, passività istituzionale — corretto, ordinamento
ripristinato); il **meccanismo di amplificazione** per gruppo (POS e
POSW2 abbassano il LOW e alzano MED e HIGH; NEG toglie di più a chi si
fidava di più); e il **rumore dello strumento** misurato a profilo fisso,
metà di quello cross-agente, SNR 2,35 invece di 1,29.

Limiti dichiarati: un solo modello (con l'impegno a replicare con Haiku),
una sola lingua, 40 per gruppo. Dati: repo e explorer
`montelago-explorer`.

### SIVE-GSP (il registro, v5)

La domanda che Montelago lascia aperta: il prompt conteneva **due**
veicoli del latente, l'etichetta `persona` («sfiduciato critico», 117
stringhe su 120) e la storia. L'ablazione:

| | riceve | stato |
|---|---|---|
| A | persona + storia | Montelago, non replicata col nuovo harness |
| B | profilo + storia che codifica il latente | fatta, 120 |
| C | profilo soltanto | fatta, 120 (600 per `emozione`) |
| D | profilo + storia neutra | fatta, 60 |

Campione **reale**: Brescia, occupati, PUNTIFI10 come latente, 40+40+40,
seed 0 — Brescia per il pool di donatori (replica 0,8%). Harness nuovo:
ogni item parte dal solo prompt di sistema, l'agente non sa cosa ha
risposto prima.

**Cosa regge (tre modelli: DeepSeek, Haiku 4.5, GPT-4o-mini):**

| | B | C | D |
|---|---|---|---|
| Spearman col latente | **+0,90** | +0,06 | ~0 |
| guadagno per livello | 0,52 / 0,55 / 0,59 | 0,01 / −0,00 / 0,02 | 0,01 |
| livello | LOW 2,6 · MED 4,6 · HIGH 6,9 | **5,02 / 3,96 / 5,44** | C + 0,30 / 0,90 / 0,35 |

- La narrazione trasmette il latente, quasi linearmente, e lo fa per tre
  famiglie di modelli con un guadagno che varia di sette centesimi.
- Il profilo da solo non differenzia **sulle scale numeriche**: chi
  costruisse agenti dai soli dati censuari otterrebbe cloni. È il
  risultato più solido dell'esperimento.
- La narrazione *in quanto tale* non sblocca i priors: D ha la stessa
  pendenza di C. Ma D è spostata in alto, e i giudici umani spiegano
  perché: le storie neutre non sono neutre, descrivono un Comune che fa
  cose che funzionano.
- I **livelli** non sono trasportabili fra modelli (1,48 punti di scarto
  in C); le **differenze** e gli **ordinamenti** sì.
- Replica: guadagno 0,49 contro 0,52, mediane uguali. Scala 0-10 invece
  di 1-10: nessun cambiamento, la compressione non è della scala.
- Tre giudici umani ciechi: Spearman 0,90–0,94 come i modelli, ma
  guadagno **0,73 contro 0,55** senza sovrapposizione. La compressione è
  nel modo in cui il modello usa i numeri, non nelle storie.
- Le tre scale (fiducia, credibilità, adeguatezza) misurano una cosa
  sola: entro gruppo correlano 0,75–0,80. I categoriali reggono: 92%
  rabbia nel LOW, 0% nell'HIGH; il MED distribuito su quattro opzioni.

**Cosa vale solo per DeepSeek:**

- la §8 (in C non è neutro: 62–75% preoccupazione, «parlare coi vicini»
  72%), la §9 (χ² su sesso e istruzione) e la lettura «il 5 non è
  neutralità, è il rifugio di una scala numerica». Tutto vero per
  DeepSeek e non misurabile per gli altri due, che sono deterministici.
- «il modello immagina la sfiducia come attivismo»: «contattare il
  Comune» vince in tutti i gruppi, contro la letteratura che associa la
  sfiducia al ritiro.

**Scelte di disegno da ricordare:** T storie 0,8 (misurata) e T risposte
0,3 (scelta) — due usi opposti dello stesso parametro; il comune non è
nominato nel prompt e il modello lo indovina nel 17% dei casi a Brescia
(83% a Bologna, 0% a Castenaso): l'esperimento ha la proprietà di
Montelago per caso, non per progetto; le variabili AVQ non entrano nel
profilo.

### Come si incastrano

Montelago dice che lo strumento è controllabile quando il latente entra
per etichetta e storia. SIVE-GSP dice che **basta la storia**, che il
profilo demografico da solo produce cloni sui numeri, e — solo per
DeepSeek — che sui categoriali il profilo invece si usa, secondo
stereotipi. Il ponte fra i due non è ancora stato attraversato: la
condizione A col nuovo harness (o le 120 personas di Montelago rifatte
girare) darebbe insieme il confronto completo e la verifica che i due
harness siano equivalenti.

---

## 3. Cosa resta aperto

Dal §13 del registro e dai limiti del paper, in ordine di quanto costa:

1. **Formato della domanda** — dieci agenti. Chiude «astensione o
   posizione» e dice se il determinismo di GPT/Haiku è della domanda.
2. **Test del rumore sul χ²** — 3.000 chiamate su `emozione`. Decide se
   il 71,6 è struttura o campionamento (§1 di questa nota).
3. **Condizione A** col nuovo harness, o Montelago rifatta: ponte fra i
   due esperimenti e verifica dei due harness.
4. **Replica di Montelago con Haiku** — promessa nel paper (§Limitations);
   SIVE-GSP ha già tre modelli, Montelago ne ha uno.
5. **Storie neutre migliori** — vietare le concessive («ma», «però»,
   «anche se»). Rifinitura, non requisito: il controllo attuale è
   caratterizzato.
6. **Lo stimolo e il POST** — il secondo esperimento, migliaia di
   chiamate. Da decidere prima: il fondo da cui si parte (in C il PRE è
   già al 62–75% di preoccupazione, i delta verso il sollievo saranno
   amplificati e quelli verso la rabbia compressi); comune esplicito o
   fittizio (§14: a Brescia uno stimolo ambientale può attivare la
   contaminazione reale); un tema che assomigli a una comunicazione di
   rischio ambientale, se la meta è Caffaro. E la domanda in più che
   B e D permettono: un agente senza storia reagisce come uno con
   storia?

Minori (§15): toni pinyin nei nomi cinesi non normalizzati; il rilevatore
di monotonia cerca parole e non forme narrative; l'harness è muto quando
si esegue un item diverso da `fiducia_istituzione`.

---

## 4. Il rapporto con `volti`

Nessuno scientifico, ed è voluto: `volti` è lo strato espositivo e non
misura niente. Ma il χ² è il motivo per cui alcune scelte di `volti`
sono quelle che sono — il profilo passato ai generatori è lo stesso
(anagrafica, titolo, mestiere, quartiere, mai AVQ), e la §9 mostra cosa
un modello ci legge dentro quando è costretto a scegliere: emozioni
passive alle donne, rabbia a chi ha la licenza media. Le immagini e le
voci fanno lo stesso, in modo meno misurabile. Per questo l'aspetto
fisico viene estratto dal dado e non lasciato al modello, e per questo
niente fenotipo o accento condizionato all'origine.


