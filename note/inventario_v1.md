# Inventario — cosa c'è, a che punto, e cosa costa chiuderlo

**7 agosto 2026** · nota di lavoro

Serve a scegliere guardando invece che ricordando. È la stessa logica del
criterio TVD applicata al progetto: una decisione presa su una misura,
non su un'impressione.

---

## 1. Il quadro

Tre filoni **indipendenti**, un obiettivo in attesa, un'infrastruttura
chiusa.

| | stato | cosa manca |
|---|---|---|
| **A** criterio TVD | scheletro scritto | bibliografia, §3 da completare |
| **B** SIVE-GSP, la taratura | risultati completi | lo stimolo e il POST |
| **C** priors dei modelli | emerso ieri, non previsto | — vedi §4 |
| **D** Caffaro con Tarantino | **in hold fino a settembre** | il corpus |
| **E** infrastruttura GSP | chiusa | rifiniture |

**Caffaro è fermo per un mese**: è il 7 agosto, e in Italia non ci sono
interazioni né dati fino a settembre. Il che libera agosto per A e B.

---

## 2. A — il criterio TVD

**Cos'è.** Una misura per decidere se un attributo debba stare nel modello
congiunto MaxEnt o essere derivato a valle. Distanza in variazione totale
fra composizione condizionata e marginale, calcolata *prima* di costruire.

**Perché vale.** La letteratura si concentra su *come* riprodurre la
congiunta — IPF, reti bayesiane, GAN, VAE. La domanda su *quali* variabili
debbano starci non è trattata come decisione: si risolve per disponibilità
dei dati o per convenienza a valle.

**Cosa c'è.** Lo scheletro (`paper_criterio_scheletro_v1.md`), il modulo
`gsp.tvd`, due applicazioni misurate — titolo di studio e settore
economico — e un controesempio documentato: il livello K10C, che
condiziona su una variabile sola quando ne servirebbero tre, al prezzo di
37 milioni di stati e di una catena di Gibbs riducibile.

**Cosa manca.**

- **La bibliografia**, e in particolare verificare che il gap sia reale.
  È l'affermazione che un revisore controlla per prima. Termini e
  riferimenti nel §8 dello scheletro;
- **la collapsibility** nei modelli log-lineari: se esistesse un teorema
  su quando una variabile si può marginalizzare senza distorcere le
  associazioni residue, il criterio ne diventerebbe la versione operativa.
  Lo rafforzerebbe invece di indebolirlo, e va guardato prima di scrivere
  l'introduzione;
- **la tabella del §3** — le TVD per il titolo di studio nella forma del
  criterio. È l'unica misura mancante.

**Costo.** Basso: nessun esperimento, solo scrittura e ricerca. Due o tre
giornate.

**È indipendente da tutto il resto.** Non tocca SIVE, non tocca Caffaro.

---

## 3. B — SIVE-GSP, la taratura

**Cosa c'è.** Quattro condizioni, tre modelli, tre giudici umani ciechi,
una replica, cinque item. Tutto in `registro_esperimento_sive_gsp_v5.md`.

I risultati che reggono:

| | |
|---|---|
| la narrazione trasmette il latente | Spearman **+0,90**, tre modelli |
| il profilo da solo non differenzia | Spearman +0,06 sulle scale |
| la narrazione *in quanto tale* non sblocca i priors | D piatta come C |
| lo strumento è stabile | replica: guadagno 0,49 contro 0,52 |
| e i giudici umani danno lo stesso ordine | +0,90 / +0,94 / +0,93 |

**Cosa manca: lo stimolo e il POST.** SIVE non misura solo la fedeltà —
misura uno spostamento: batteria PRE → comunicazione del Comune → tre
turni di reazione → batteria POST.

È il pezzo che porta a Caffaro, perché il POSW — la rassicurazione che
funziona da negativo — vive lì.

**Costo.** Alto: con quattro condizioni sono migliaia di chiamate. Ma si
può ridurre scegliendo bene (§4).

---

## 4. C — i priors dei modelli, e perché NON è un terzo filone

Ieri è emerso un risultato non previsto: su `emozione`, **GPT-4o-mini
risponde «preoccupazione» 120 volte su 120** e Haiku 118 su 120. DeepSeek
è l'unico dei tre che produce una distribuzione, e quella distribuzione
dipende da sesso e istruzione secondo stereotipi netti.

La tentazione è farne un lavoro a sé. **Non conviene**, per due ragioni.

**È già il terzo filone e nessuno dei primi due è chiuso.** Aprirne uno
in più significa avere tre cose a metà invece di una finita.

**E come appendice dice quasi tutto quello che direbbe da solo:** due
pagine che spiegano perché un item categoriale non è utilizzabile ovunque
sono un contributo metodologico utile, e non richiedono un articolo.

### La domanda che questo apre: si può proseguire con B senza chiudere C?

**Sì, sulle scale numeriche. No, sui categoriali.**

La taratura chiede: *l'agente esibisce il livello che la storia gli ha
dato?* La risposta è Spearman +0,90 su tutti e tre i modelli, con
guadagni 0,52-0,59.

> Quel risultato è **invariante**. I priors riguardano il livello di
> partenza, non la capacità di seguire il segnale. E il confronto
> appaiato B−C cancella il prior per costruzione: se un modello parte da
> 4 e un altro da 5,5, la differenza fra le due condizioni sullo stesso
> agente è la stessa.

Ma i priors mordono sui categoriali:

**Se lo stimolo si misura su `fiducia_istituzione`** — quanto POST−PRE si
sposta — la taratura regge su tutti e tre i modelli e i priors sono
irrilevanti.

**Se si misura su `emozione`** — «lo stimolo sposta l'agente da
preoccupazione a sollievo?» — allora con GPT e Haiku non si misura nulla:
uno spostamento su una costante non esiste.

E il POSW di SIVE stava proprio lì: un comunicato tranquillizzante che
aumenta la preoccupazione si vede bene sulle emozioni.

### La conseguenza operativa

```
misura principale     fiducia_istituzione, credibilita, adeguatezza_info
                      su tutti e tre i modelli

misura secondaria     emozione, su DeepSeek soltanto
                      dichiarando perché

appendice             perché un item categoriale non è utilizzabile
                      ovunque, e come verificarlo prima di usarlo
```

**E una regola che vale oltre questo caso:**

> Prima di usare un item categoriale in un esperimento con agenti,
> verificare che il modello scelto **vari**. Un modello che risponde
> sempre la stessa parola è muto sulla questione, non neutro — e uno
> spostamento su una costante non è misurabile.

Il controllo costa cinque chiamate per cella.

---

## 5. Le rifiniture, che si allungano da giorni

**Corte, un pomeriggio ciascuna**

- `--riempi-sha` dentro `gsp.fonti`, accanto a `--verifica`
- le etichette di blocco disallineate in `build_constraints` (C3/C4/C6)
- `c9_sex_posizione_prof` costruito a ogni rigenerazione e mai letto — ora
  anche superato da `gsp.lavoro`
- `resolve_pop_file` con regole diverse fra script
- il riepilogo dell'harness muto quando l'item tarato non è eseguito
- i toni pinyin nei nomi cinesi, non normalizzati come per lo yoruba

**Fonti da registrare**

- `istat_structures` (120 MB), `istat_catalog`
- le licenze dei sette portali comunali, tutte `DA_VERIFICARE`

**Con più sostanza**

- il ramo straniero: il 23,5% scoperto, con le due mail a Forebears e
  Behind the Name
- CLAIST non collegato a `gsp.istruzione`
- `gsp.lavoro` non condiziona sull'età (TVD fino a 0,27 sulle classi
  estreme)
- la riponderazione per titolo: costruita, spenta, da valutare
- EU-SILC come fonte per reddito e condizioni di vita

---

## 6. Cosa farei ad agosto

**A, il criterio TVD.** È l'unico che si chiude senza esperimenti, non
dipende da nessun altro, e agosto è il mese giusto per la scrittura e la
ricerca bibliografica — che sono lavoro solitario.

E ha una proprietà che gli altri non hanno: **il materiale è tutto
misurato**. Non serve altro che scriverlo bene.

**Poi B, lo stimolo**, con due decisioni da prendere prima:

**Il comune esplicito o no** (§14 del registro). Gli agenti di Brescia
riconoscono la città nel 17% dei casi, e una comunicazione su un tema
ambientale potrebbe attivare associazioni con la contaminazione reale.
Interessante o disastroso a seconda di cosa si misura, e va deciso.

**Quale stimolo.** Se l'obiettivo è arrivare a Caffaro, tanto vale
sceglierne uno che assomigli a una comunicazione di rischio ambientale
invece che a un avviso generico: progettarlo pensandoci risparmia un giro.

**C resta appendice**, e le rifiniture si fanno negli intervalli.

---

## Riferimenti

| | |
|---|---|
| A | `paper_criterio_scheletro_v1.md` · `nota_settore_economico_v3.md` · `gsp.tvd` |
| B | `registro_esperimento_sive_gsp_v5.md` · `nota_code_puntifi10_v2.md` |
| C | idem §9, §10 |
| D | `sive_paper_v6.pdf` · `report_simcomm.pdf` |
| E | `fonti_e_pacchetto_v8.md` · `piano_trattamento_v2.md` |
