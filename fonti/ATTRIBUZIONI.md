# Attribuzioni delle fonti

Generato da `python -m gsp.fonti --attribuzioni`. Non modificare a mano:
le informazioni vivono in `fonti/registro.yaml`.

## ANNCSU - Archivio Nazionale dei Numeri Civici delle Strade Urbane, indirizzario regionale

- **Fonte:** ISTAT e Agenzia delle Entrate
- **Licenza:** CC-BY-4.0
- **URL:** https://www.anncsu.gov.it/it/consultazione-dellarchivio/open-data/
- **Scaricato il:** 2026-07-28
- **Copertura:** None, None
- **Universo:** tutti gli accessi esterni (numeri civici) certificati dai Comuni e conferiti in ANNCSU, per regione, con coordinate. Aggiornamento mensile; la data di creazione e' nel nome del file (20260703). Diciotto campi documentati nel tracciato JSON: fra gli altri ODONIMO (DUG+DUF), CIVICO, ESPONENTE, SPECIFICITA (la numerazione rosso/nero di Firenze e Genova), COORD_X/Y_COMUNE, QUOTA e METODO. L'archivio contiene UN SOLO CSV, da 170 a 240 MB per regione.

> ANNCSU - Archivio Nazionale dei Numeri Civici delle Strade Urbane, Istat e Agenzia delle Entrate, open data ex Reg. (UE) 2023/138

## Medie nazionali della batteria AVQ

- **Fonte:** GSP (derivato)
- **Licenza:** CC-BY-4.0
- **URL:** None
- **Scaricato il:** 2026-08-04
- **Copertura:** IT, 2024
- **Universo:** medie ponderate nazionali delle 23 variabili AVQ, calcolate dai microdati con i pesi COEFIN, universo 15 anni e piu' (ETAMi >= 5), ciascuna sull'universo della propria variabile. NON esiste una fonte ISTAT equivalente: la batteria di fiducia non e' pubblicata in forma aggregata. Le cinque medie che erano cablate nel viewer venivano da un'origine mai identificata (§13.6 punto 7 del riferimento, chiuso il 2/8/2026); ricalcolate coincidono entro 0,045 con quelle cablate, e ora ne coprono ventitre invece di cinque. Il file si autodescrive: porta `fonte`, `metodo`, `avvertenza`, `anni`, `eta_min_ETAMi` e `fattore_grappolo`, e il normalizzatore li riporta nell'impronta — chi la legge sa come e' stato calcolato senza aprire il registro.

> Elaborazione propria su ISTAT, "Aspetti della vita quotidiana - microdati ad uso pubblico", CC BY 4.0

## Aspetti della vita quotidiana - microdati per la ricerca (mIcro.STAT)

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://www.istat.it/microdati/aspetti-della-vita-quotidiana/
- **Scaricato il:** 2026-08-03
- **Copertura:** None, None
- **Universo:** campione dell'indagine multiscopo sulle famiglie, individui residenti in famiglia (esclusi i conviventi in istituto). Unita' CAMPIONARIA, non individuo: ogni record porta COEFIN, coefficiente di riporto all'universo, e rappresenta se stesso piu' altri COEFIN-1. n_misurato registra i RECORD, perche' e' cio' che la pipeline consuma - il pool di donatori e' fatto di record, non di pesi. somma_pesi e n_eff_kish stanno nell'impronta e non vanno confusi con n.

> ISTAT, "Aspetti della vita quotidiana - microdati ad uso pubblico", istat.it, CC BY 4.0

## Tracciato dei microdati AVQ 2024

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** DA_VERIFICARE
- **Scaricato il:** DA_VERIFICARE
- **Copertura:** IT, 2024
- **Universo:** elenco delle variabili dei microdati AVQ 2024 con le rispettive definizioni. Non e' un dato ma il suo dizionario: senza, sigle come FIDUCIA, AMBIENTE, CRONI o BMIMIN non vogliono dire niente. Estratto da data/avq/esplorazione/avq_vars_2024.csv.

> ISTAT, "Aspetti della vita quotidiana - microdati ad uso pubblico", istat.it, CC BY 4.0

## Popolazione residente straniera per cittadinanza, sesso, quartiere e zona - serie storica

- **Fonte:** Comune di Bologna
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** DA_VERIFICARE
- **Copertura:** 037006, 2024
- **Universo:** residenti STRANIERI per paese di cittadinanza, zona, quartiere e sesso, fonte ANAGRAFICA comunale. E' la piu' ricca delle sei fonti locali su ogni asse: 19 ZONE (contro 4 circoscrizioni a Reggio e 21 quartieri a Forli'), il sesso, e nessun gruppo residuale. Serie storica 1986-2024, 39 annate in un solo file: `anno` e' una COLONNA, non un attributo del file. La pipeline usa l'annata piu' recente (load_bologna prende max(anno)), non tutta la serie. Due colonne distinte per la cittadinanza: `cittadinanza` e' l'area geografica di raggruppamento (11 modalita'), `stato_cittadinanza` e' il paese di dettaglio (180 nella serie, 155 nel 2024). La pipeline usa la seconda.

## Cittadinanze straniere per quartiere

- **Fonte:** Comune di Brescia
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** 2025-07-06
- **Copertura:** None, None
- **Universo:** residenti per CITTADINANZA e quartiere, italiani inclusi: la riga ITALIA e' presente nel file e viene filtrata a valle da opendata_paese.py (riga 97). I totali per quartiere sono quindi popolazione totale, non stranieri. Fonte ANAGRAFICA comunale, di data diversa dal censimento. Non distingue il sesso: lo ricostruisce l'IPF dal margine comunale. E' il margine B dell'IPF, COMPLEMENTARE e non alternativo al censimento (margine A): il censimento porta i ~150 paesi, i livelli corretti e il sesso, la fonte locale porta la geografia. Il gruppo residuale e' il complemento dei paesi nominati IN QUEL QUARTIERE, quindi cambia da file a file: le modalita' vanno da 8 (Caionvico) a 33 (Centro storico nord).

## Titolo di studio della popolazione residente di 6 anni e piu' - Censimento della popolazione 2011

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** DA_VERIFICARE
- **Scaricato il:** 2026-08-04
- **Copertura:** IT, 2011
- **Universo:** popolazione residente di SEI ANNI E PIU' per titolo di studio, sesso, eta' e territorio, al censimento 2011. L'universo a 6 anni copre anche i bin 9-14 della nostra popolazione, che le rilevazioni sulle forze di lavoro (15+) escluderebbero. Circa 457 modalita' di titolo, in una gerarchia codificata a cinque cifre: la prima e' il ramo (1 elementare, 2 media, 3 qualifica 2-3 anni, 4 maturita' 4-5 anni, 5 terziario non universitario, 6 diploma universitario v.o., 7 laurea, 0 laurea magistrale), le successive scendono al tipo di scuola e all'indirizzo. I codici che finiscono in 00 sono totali di ramo. Il ramo 4 ha 27 voci ed e' il livello giusto per una biografia: "istituto tecnico per geometri", "liceo classico", "istituto professionale per i servizi alberghieri".

> ISTAT, "15° Censimento generale della popolazione e delle abitazioni 2011", CC BY 4.0

## CLAIST 2026 - Mappa dei percorsi di istruzione e dei titoli di studio italiani

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** DA_VERIFICARE
- **Scaricato il:** 2026-08-04
- **Copertura:** IT, storicizzata
- **Universo:** tutti i percorsi di istruzione e formazione italiani, ATTUALI E PASSATI, dai servizi per l'infanzia al dottorato. Sostituisce la Classificazione dei titoli di studio del 2003. Struttura gerarchica su SEI livelli: 61 tipologie di programma al primo, circa 20.000 percorsi al sesto, codificati in un COD_CLAIST a 18 digit (3-2-2-4-4-3). Sedici fogli, 29.282 righe in tutto. Il registro normalizza il foglio "Schema sintetico 2026" — 104 righe, 42 titoli — che e' il livello utile per attribuire un titolo a un individuo sintetico: non seimila corsi, non sei categorie. Il livello 2 e' l'ORDINAMENTO, cioe' il decreto di riferimento: e' questo che rende la mappa storicizzata e permette di sapere quali titoli erano ottenibili in quale periodo.

> ISTAT, "CLAIST 2026 - Mappa dei percorsi di istruzione e dei titoli di studio italiani", CC BY 4.0

## Cognomi residenti - Anno 2012

- **Fonte:** Comune di Firenze - Direzione Generale - Servizio Pianificazione, Controllo e Statistica
- **Licenza:** CC-BY-4.0
- **URL:** http://opendata.comune.fi.it/?q=metarepo/datasetinfo&id=cognomi-residenti-2012
- **Scaricato il:** 2026-08-02
- **Copertura:** 048017, 2012
- **Universo:** residenti anagrafici del comune di Firenze, tutte le eta', italiani e stranieri, un record per persona

> Comune di Firenze, "Cognomi residenti - Anno 2012", opendata.comune.fi.it, CC BY 4.0

## Cognomi residenti - Anno 2013

- **Fonte:** Comune di Firenze - Direzione Generale - Servizio Pianificazione, Controllo e Statistica
- **Licenza:** CC-BY-4.0
- **URL:** http://opendata.comune.fi.it/?q=metarepo/datasetinfo&id=cognomi-residenti-2013
- **Scaricato il:** 2026-08-02
- **Copertura:** 048017, 2013
- **Universo:** residenti anagrafici del comune di Firenze, tutte le eta', italiani e stranieri, un record per persona

> Comune di Firenze, "Cognomi residenti - Anno 2013", opendata.comune.fi.it, CC BY 4.0

## Stranieri per quartiere, sesso e nazionalita'

- **Fonte:** Comune di Forli'
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** DA_VERIFICARE
- **Copertura:** 040012, DA_VERIFICARE
- **Universo:** residenti STRANIERI per nazionalita', quartiere e sesso, fonte ANAGRAFICA comunale. Formato lungo (QUARTIERE, STATO, F, M, TOTALE), il piu' semplice fra le fonti locali. Distingue il sesso, come Ravenna e a differenza di Brescia e Reggio. La fonte disaggrega in 41 unita' sub-quartiere che la pipeline aggrega nei 21 quartieri COM_ASC1: la mappa 41 -> 21 vive in gsp.common ed e' referenziata con `parametri_da`. Qui il normalizzatore misura le 41 unita' come stanno sul disco.

## Popolazione residente per eta', sesso e stato civile

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** popolazione residente ANAGRAFICA al 1 gennaio dell'anno indicato. Fonte DCIS: conteggio di iscritti in anagrafe, non stima campionaria. L'anno n corrisponde all'anno n-1 delle tavole censuarie, che sono al 31 dicembre: confrontare n con n non ha senso. Il grezzo contiene i codici aggregati (TOTAL ecc.): obs_somma nell'impronta e' circa 2x la popolazione vera. E' una firma per riconoscere il file, non un conteggio.

> ISTAT, "Popolazione residente per eta', sesso e stato civile", esploradati.istat.it, CC BY 4.0

## Censimento permanente - condizione professionale per cittadinanza

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, popolazione residente al 31 dicembre. Stesso avvertimento sull'universo della condizione professionale di cens_condprof_eta. Il grezzo contiene i codici aggregati.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - condizione professionale per eta'

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, popolazione residente al 31 dicembre. ATTENZIONE all'universo della condizione professionale: le modalita' occupato/disoccupato/inattivo non si applicano a tutta la popolazione, e i bambini stanno in una categoria a parte o sono esclusi. Da verificare sulla codelist prima di usarla come vincolo. Il grezzo contiene i codici aggregati.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - istruzione per cittadinanza

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, popolazione residente al 31 dicembre. Stima integrata, non conteggio esaustivo. Incrocio istruzione x cittadinanza senza l'eta': per l'incrocio con l'eta' serve cens_istruzione_eta. Il grezzo contiene i codici aggregati.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - istruzione per eta'

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, popolazione residente al 31 dicembre (INDICATOR = RESPOP_AV). E' una STIMA integrata da fonti amministrative e indagine campionaria, non un conteggio esaustivo: i vincoli che ne derivano hanno un margine e non sono verita'. Serie storica pluriennale nello stesso file: l'anno usato dalla pipeline va scelto, non e' l'unico presente. Il grezzo contiene i codici aggregati (TOTAL ecc.): obs_somma nell'impronta e' circa 8x la popolazione vera. E' una firma per riconoscere il file, non un conteggio.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - background migratorio per origine dei genitori

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, popolazione residente al 31 dicembre per background migratorio e origine dei genitori. E' la fonte del blocco GC (background x cittadinanza), che contiene 6 zeri strutturali: senza un vincolo congiunto esplicito il MaxEnt assume indipendenza anche dove la relazione e' deterministica, e produce ~30% di combinazioni impossibili. Gli stessi zeri rendono la catena di Gibbs riducibile a lambda*. Il grezzo contiene gli aggregati.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - posizione nella famiglia

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente al 31 dicembre. Descrive la posizione dell'individuo nel nucleo familiare: l'unita' resta l'individuo, ma l'informazione e' relazionale e la pipeline attuale NON modella le famiglie. NESSUNO script la legge (verificato 2/8/2026): scaricata e non usata. Il grezzo contiene gli aggregati.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - posizione professionale

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** … universo ristretto ai soli OCCUPATI … Usata da build_constraints come vincolo C9 SOFT e CONDIZIONALE all'universo occupati (c9_sex_posizione_prof.csv), non come marginale sulla popolazione totale.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - popolazione per sesso, eta' e cittadinanza

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, popolazione residente al 31 dicembre (INDICATOR = RESPOP_AV). Stima integrata, non conteggio esaustivo. Cittadinanza nella dicotomia italiana/straniera, non il paese di dettaglio: per quello serve cens_stranieri_paesi. Il grezzo contiene i codici aggregati (TOTAL ecc.).

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - settore di attivita' economica

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** … universo ristretto ai soli OCCUPATI … Usata da build_constraints come vincolo C9 SOFT e CONDIZIONALE all'universo occupati (c9_sex_posizione_prof.csv), non come marginale sulla popolazione totale.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - stranieri per paese di cittadinanza

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://esploradati.istat.it/SDMXWS/rest
- **Scaricato il:** None
- **Copertura:** None, None
- **Universo:** censimento permanente, stranieri residenti al 31 dicembre per paese di cittadinanza (~150 paesi). Pubblicato SOLO a livello comunale: e' la ragione per cui la pipeline assume paese indipendente dalla geografia dato (area, sesso), e per cui le fonti sub-comunali in data/submun/ sono complementari e non alternative (margine A dell'IPF in opendata_paese.py). Il grezzo contiene gli aggregati.

> ISTAT, "Censimento permanente della popolazione", esploradati.istat.it, CC BY 4.0

## Censimento permanente - dati per sezione di censimento, file regionali 2023

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://www.istat.it/notizia/dati-per-sezioni-di-censimento/
- **Scaricato il:** 2026-08-02
- **Copertura:** None, None
- **Universo:** censimento permanente 2023, conteggi per SEZIONE di censimento. L'unita' e' la sezione, non l'individuo: ogni riga porta ~130 conteggi. La geometria e' quella del censimento 2021 (SEZ21_ID), i dati sono 2023: anni diversi per griglia e contenuto. COM_ASC1/2/3 sono le sub-aree amministrative, presenti solo dove il comune e' articolato: e' la fonte della gerarchia zona/quartiere. I CSV per citta' in data/submun/ sono DERIVATI, prodotti da build_sezioni.py filtrando su PROCOM.

> ISTAT, "Dati per sezioni di censimento 2023", istat.it, CC BY 4.0

## Tracciato dei file regionali per sezione, 2023

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** https://www.istat.it/notizia/dati-per-sezioni-di-censimento/
- **Scaricato il:** 2026-08-02
- **Copertura:** IT, 2023
- **Universo:** codebook delle 138 colonne dei file regionali: NOME_CAMPO -> DEFINIZIONE. Non e' un dato ma il suo dizionario: senza, colonne come P14 o ST2_B non vogliono dire niente.

> ISTAT, "Dati per sezioni di censimento 2023", istat.it, CC BY 4.0

## Basi territoriali - sezioni di censimento 2021, shapefile

- **Fonte:** ISTAT
- **Licenza:** CC-BY-4.0
- **URL:** DA_VERIFICARE
- **Scaricato il:** 2026-07-28
- **Copertura:** None, None
- **Universo:** geometrie delle sezioni di censimento, edizione 2021, in WGS84. Una regione per istanza: R03 Lombardia, R08 Emilia-Romagna, R16 Puglia. E' la GEOMETRIA, non i dati: i conteggi per sezione stanno in `istat_sezioni_2023`, che ha edizione dei dati 2023 su geometria 2021 — lo stesso disallineamento che produce `sezioni_2023_non_nello_shapefile.csv` in ogni cartella regionale.

> ISTAT, "Basi territoriali e variabili censuarie", CC BY 4.0

## Nomi maggiormente frequenti dei residenti, per sesso

- **Fonte:** Comune di Modena
- **Licenza:** CC-BY-4.0
- **URL:** https://dati.emilia-romagna.it/dataset/nomi-maggiormente-frequenti-di-sesso-maschile-dal-2012-al-2022
- **Scaricato il:** 2026-08-03
- **Copertura:** 036023, 2012-2024
- **Universo:** STOCK dei residenti anagrafici del comune di Modena, NON i nati dell'anno: la descrizione del catalogo dice "attribuiti ai nati" ma i valori lo smentiscono (1.390 ANTONIO nel 2015 non sono neonati). Esattamente 50 nomi per sesso e per anno, 650 righe per file. Non distingue eta' ne' cittadinanza: e' una lista unica per sesso, ed e' la ragione per cui il repertorio dichiara `condiziona: [sesso]` e non `[sesso, coorte]`.

> Comune di Modena, "Nomi maggiormente frequenti", via dati.emilia-romagna.it, CC BY 4.0

## Descrizione e codifica dei campi, 2025

- **Fonte:** Comune di Parma
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** 2025-07-28
- **Copertura:** 034027, 2025
- **Universo:** codebook a DUE livelli: campo -> codice -> etichetta. Diverso dai tracciati visti finora, che sono a un livello (variabile -> descrizione). Cittad ha 225 codici, Relpar 30, Tipores e Sesso 2; ETA, Ncomp, Quartiere e SEZ21 non hanno codici, solo la descrizione del campo. Senza questo file i microdati sono numeri senza significato: 'Cittad = 201' non vuole dire niente.

## Popolazione residente 2025 - microdati individuali

- **Fonte:** Comune di Parma
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** 2025-07-28
- **Copertura:** 034027, 2025
- **Universo:** anagrafe comunale COMPLETA, una riga per residente: 202.111 individui, italiani inclusi. E' l'unica fonte locale a microdato individuale e non a conteggio aggregato, e la sola con risoluzione di SEZIONE (1.320 sezioni contro i 13 quartieri). opendata_paese.py filtra Cittad != 100 per tenere i soli stranieri (36.327, il 18%): il filtro e' a valle, la fonte ha tutti. Porta due variabili che nessun'altra fonte locale ha, Ncomp (numero componenti) e Relpar (relazione di parentela): non servono all'IPF sul paese, ma sono struttura FAMILIARE, e insieme alla tavola ISTAT cens_posizione_famiglia sono il materiale gia' disponibile per quando le famiglie verranno modellate.

## Popolazione residente con cittadinanza straniera per aree territoriali

- **Fonte:** Comune di Ravenna
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** DA_VERIFICARE
- **Copertura:** None, None
- **Universo:** residenti con cittadinanza STRANIERA per nazionalita' e area territoriale, fonte ANAGRAFICA comunale. A differenza di Brescia e Reggio, questa fonte DISTINGUE IL SESSO: e' l'unica delle locali a farlo, e l'IPF non deve ricostruirlo dal margine comunale. Non contiene gli italiani: i totali sono gia' i soli stranieri. Dieci aree territoriali piu' la colonna aggregata "T O T A L I", che va esclusa, e una riga finale "TOTALE", idem.

## Nazionalita' piu' numerose per circoscrizione, 2013

- **Fonte:** Comune di Reggio nell'Emilia
- **Licenza:** DA_VERIFICARE
- **URL:** DA_VERIFICARE
- **Scaricato il:** DA_VERIFICARE
- **Copertura:** 035033, 2013
- **Universo:** residenti stranieri per nazionalita' e circoscrizione, fonte ANAGRAFICA comunale. Matrice larga: nazionalita' sulle righe, le 4 circoscrizioni sulle colonne. Non distingue il sesso: lo ricostruisce l'IPF dal margine comunale, come per Brescia. Contiene una modalita' residuale dichiarata, "Altre nazionalita'", che l'IPF tratta come complemento dei paesi nominati e non come un paese: la sua quota sulla massa totale sta in `residuo_quota` nell'impronta, e dice quanta informazione la fonte porta davvero.
