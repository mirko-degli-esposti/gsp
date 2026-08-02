# Attribuzioni delle fonti

Generato da `python -m gsp.fonti --attribuzioni`. Non modificare a mano:
le informazioni vivono in `fonti/registro.yaml`.

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
