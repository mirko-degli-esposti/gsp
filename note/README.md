# note/

*For the external reader.* These are the **working notes** of the GSP project,
written in Italian, for the author, while the work was being done. They are
versioned here because the technical report cites them by name and version,
and because the reasoning behind each design choice — and each retraction — is
here and nowhere else. They are drafts: numbers, variable names and
conclusions change between versions; the version the report cites is the one
that was current when that section was written. Superseded versions are in
`storico/`, raw run logs in `misure/`. Three conventions hold throughout:
a note that evolves is `nome_vNN.md` and only the highest version is current;
every quantitative claim is marked *misurato* (measured, log in `misure/`),
*dichiarato* (taken from a source or assumed) or *aperto* (undecided); a
falsified prediction or withdrawn claim keeps its original text and gets a
dated correction beside it — nothing is silently removed. Where the report and
a note disagree, the report is later and wins.

The rest of this file is the author's map of the notes.

---

# Le note — cosa c'è e quando serve

**Aggiornato il 18 agosto 2026** (precedente: 9 agosto)

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

## Sempre in memoria — i sette che servono ovunque

| documento | cosa contiene |
|---|---|
| `fonti_e_pacchetto_v8.md` | l'infrastruttura, le fonti (39 al 18 agosto), i quattro attributi derivati, **il criterio TVD** (§8), i principi (§12), le trappole (§14) |
| `GSP_popolazioni_full_riferimento_v24.md` | cosa c'è nei file di popolazione: attributi, codifiche, limiti, come si aggiunge un comune. §2.4 per gli attributi che **non** ci sono |
| `piano_trattamento_v2.md` | cosa esce e in quale forma: i tre regimi, cosa in un record è davvero reale, i limiti dichiarati. È il documento da mostrare a un terzo |
| `design_animarium_v13.md` | il visualizzatore: modello dei dati, viste, classi di garanzia, regime pubblico |
| `nota_biografia_v2.md` | i tre strati e i tre livelli di certezza A/B/C; perché il persona-prompt è un prodotto diverso dalla biografia |
| `nota_code_puntifi10_v2.md` | l'esperimento sulle code: i donatori, i due modi di campionare e cosa costano |
| `registro_esperimento_sive_gsp_v5.md` | il registro degli esperimenti LLM sulle popolazioni GSP: condizioni Brescia, storie, confronto multi-modello, priori demografici |

---

## Tematiche — si caricano quando ci si lavora

| documento | quando serve |
|---|---|
| `nota_settore_economico_v3.md` | rifare o discutere la scelta di dove sta un attributo; contiene la misura che ha deciso `gsp.lavoro` e i due errori di lettura che l'hanno preceduta |
| `nota_nucleo_familiare_v3.md` | progettare l'anello 4 o discutere la struttura familiare; contiene le cinque misure su Parma, la decisione (ruolo a valle, ampiezza vincolata per sezione), due previsioni falsificate e la refutazione del codebook della fornitura |
| `nota_repertorio_avq_v3.md` | costruire l'assemblaggio dei nuclei; contiene il repertorio delle firme (8.443 nuclei AVQ), le configurazioni interne — divari d'età, genere del riferimento, cittadinanza — e i criteri di compatibilità che ne discendono. **[versione da verificare: v1 al 9 agosto, l'anello 4 in produzione cita v3]** |
| `nota_segnale_compositivo_v3.md` | lavorare sulla varianza compositiva UE/non-UE fra zone, o sul condizionamento geografico del paese |
| `nota_background_sezione_v1.md` | raffinare l'anello 3 con `EM1`–`EM6`, o discutere la risoluzione geografica del background; contiene M-EM sulle undici città, la modifica proposta a `enrich.py` e la falsificazione di una previsione basata su `nota_segnale_compositivo_v3` |
| `nota_combinazioni_impossibili_v2.md` | toccare `cs_build`, le esclusioni α=0, o la riducibilità del Gibbs |
| `paper_criterio_scheletro_v1.md` | scrivere l'articolo sul criterio; contiene la nota bibliografica su cosa cercare. Terzo caso applicativo in `nota_nucleo_familiare_v1_1.md`, di forma diversa: decide **quale scala geografica** serve, non se una variabile stia nel joint |
| `eusilc_exploration_v1.md`, `v2.md` | valutare EU-SILC come fonte per reddito e condizioni di vita |
| `animarium_report_skeleton_v0.1.md` | lo scheletro del report tecnico per arXiv (in inglese): sezioni, per ciascuna la nota da cui attinge e lo stato rerun/reported. |

---

## I PDF — riferimenti, non note

Sono materiale esterno o prodotti finiti, e si caricano solo per lavorarci
sopra.

| | |
|---|---|
| `sive_paper_v6.pdf` | il paper SIVE sottomesso a JASSS (arXiv:2607.00910): metodo, criteri C1-C7, protocollo di validazione |
| `maxent_pcd_paper_4_arxiv.pdf` | il paper MaxEnt-PCD in revisione a TKDD (arXiv:2603.27312) |
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

In `misure/` stanno le uscite grezze degli script diagnostici, citate per
nome dalle note che ne riportano i numeri. Non si caricano mai: servono a
verificare una cifra quando serve.

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

---

## Nota per il repository pubblico

Dal 18 agosto 2026 questa cartella resta nel repository che verrà reso
pubblico insieme al report tecnico. Non viene ripulita: sono bozze tecniche,
e la storia di git le conserverebbe comunque. La sezione in inglese in testa a
questo file dice al lettore esterno cosa sono e come leggerle.
