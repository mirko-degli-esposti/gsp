# Le note — cosa c'è e quando serve

**Aggiornato il 6 agosto 2026**

Serve a due cose: sapere quale documento contiene cosa senza aprirli
tutti, e decidere cosa caricare nella memoria di progetto.

## Il criterio

> Si carica ciò che contiene **giudizio**, non ciò che contiene
> **istruzioni**.

Le note registrano decisioni con le loro ragioni, e quelle non si
ricostruiscono dal codice: perché K10C è stato abbandonato, perché la
coppia settore-professione si estragga insieme, perché `donor_id` sia
`"2024:12345"` invece di un indice.

Il codice invece si legge quando serve, ed è sempre aggiornato — al
contrario di una sua descrizione. **Gli script non vanno in memoria**,
con l'eccezione di quello su cui si sta lavorando in quel momento.

---

## Sempre in memoria — i sei che servono ovunque

| documento | cosa contiene |
|---|---|
| `fonti_e_pacchetto_v8.md` | l'infrastruttura, le 37 fonti, i quattro attributi derivati, **il criterio TVD** (§8), i principi (§12), le trappole (§14) |
| `GSP_popolazioni_full_riferimento_v22.md` | cosa c'è nei file di popolazione: attributi, codifiche, limiti, come si aggiunge un comune. §2.4 per gli attributi che **non** ci sono |
| `piano_trattamento_v2.md` | cosa esce e in quale forma: i tre regimi, cosa in un record è davvero reale, i limiti dichiarati. È il documento da mostrare a un terzo |
| `design_animarium_v13.md` | il visualizzatore: modello dei dati, viste, classi di garanzia, regime pubblico |
| `nota_biografia_v1.md` | i tre strati e i tre livelli di certezza A/B/C; perché il persona-prompt è un prodotto diverso dalla biografia |
| `nota_code_puntifi10_v2.md` | l'esperimento in corso: le code, i donatori, i due modi di campionare e cosa costano |

---

## Tematiche — si caricano quando ci si lavora

| documento | quando serve |
|---|---|
| `nota_settore_economico_v3.md` | rifare o discutere la scelta di dove sta un attributo; contiene la misura che ha deciso `gsp.lavoro` e i due errori di lettura che l'hanno preceduta |
| `nota_segnale_compositivo_v3.md` | lavorare sulla varianza compositiva UE/non-UE fra zone, o sul condizionamento geografico del paese |
| `nota_combinazioni_impossibili_v2.md` | toccare `cs_build`, le esclusioni α=0, o la riducibilità del Gibbs |
| `paper_criterio_scheletro_v1.md` | scrivere l'articolo sul criterio; contiene la nota bibliografica su cosa cercare |
| `eusilc_exploration_v1.md`, `v2.md` | valutare EU-SILC come fonte per reddito e condizioni di vita |

---

## I PDF — riferimenti, non note

Sono materiale esterno o prodotti finiti, e si caricano solo per lavorarci
sopra.

| | |
|---|---|
| `sive_paper_v6.pdf` | il paper SIVE sottomesso a JASSS: metodo, criteri C1-C7, protocollo di validazione |
| `maxent_pcd_paper_4_arxiv.pdf` | il paper MaxEnt-PCD in revisione a TKDD |
| `gsp_paper_main_v2.pdf` | il paper GSP |
| `report_simcomm.pdf` | il report SimComm |
| `PRISMUS_final_proposal.pdf` | la proposta |
| `abstract_AMPS_Dublin_2027.pdf` | l'abstract sottomesso |
| `collaboration_proposal_pachet_v4.pdf` | la proposta di collaborazione |
| `Pachet_Zucker_MaxEnt_synthPop.pdf` | il preprint di riferimento sul rilassamento MaxEnt |
| `gibbs_pcd_note.pdf`, `maxent_duality_note.pdf`, `synth_dataset_note.pdf` | note tecniche sul solver |
| `agentsociety2_notes*.pdf` | appunti su AgentSociety |
| `urbia_progress_report.pdf` | il report UrbIA |
| `2602_03545v1.pdf` | paper esterno |

---

## In `storico/`

Le versioni superate. Non si caricano mai, ma si conservano perché una
nota dice **cosa è cambiato e perché**, e a volte la ragione di una
scelta sta nella versione in cui è stata presa.

`scripts/riordina_note.py` tiene l'ultima versione di ogni famiglia e
archivia le altre.

---

## Come si aggiorna una nota

**Una versione nuova** quando cambia la sostanza: una misura corretta, una
decisione ribaltata, una sezione che non c'era. Il vecchio va in
`storico/` e il nuovo dichiara in testa cosa sostituisce e perché.

**Una patch senza bump** quando si corregge un percorso, un rimando o un
refuso. Bumpare per ogni `sed` rende il changelog illeggibile, che è
l'opposto di quello che serve.

**E i numeri si riportano dalla misura, mai dalla memoria.** Quattro volte
in tre giorni un valore trascritto si è rivelato calcolato su supporti
diversi: se una nota riporta una TVD, deve dire su quali dati e con quale
comando.

---

## Cosa NON è in memoria e va chiesto quando serve

Il codice — `src/gsp/`, `scripts/` — e i dati. Si leggono dal disco:
`git log`, `sed -n`, `grep` bastano quasi sempre, e il risultato è
aggiornato mentre una descrizione invecchia.

Se in una conversazione serve capire cosa fa un modulo, la strada è
guardarlo, non averlo caricato.
