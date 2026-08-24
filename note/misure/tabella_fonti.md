| id | ente | universe | temporal ref. | accessed | licence | stor. | used by | ring |
|---|---|---|---|---|---|---|---|---|
| `istat_anag_sesso_eta_statociv` | ISTAT | popolazione residente ANAGRAFICA al 1 gennaio dell'anno ind… | 1_gennaio (N) |  | CC-BY-4.0 | locale | build_constraints.py, enrich.py | **1** |
| `istat_cens_condprof_cittadinanza` | ISTAT | censimento permanente, popolazione residente al 31 dicembre… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `istat_cens_condprof_eta` | ISTAT | censimento permanente, popolazione residente al 31 dicembre… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `istat_cens_istruzione_cittadinanza` | ISTAT | censimento permanente, popolazione residente al 31 dicembre… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `istat_cens_istruzione_eta` | ISTAT | censimento permanente, popolazione residente al 31 dicembre… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `istat_cens_migr_backg` | ISTAT | censimento permanente, popolazione residente al 31 dicembre… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `istat_cens_posizione_prof` | ISTAT | … universo ristretto ai soli OCCUPATI … Usata da build_cons… | 31_dicembre (qualunqu… |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `istat_cens_settore_prof` | ISTAT | … universo ristretto ai soli OCCUPATI … Usata da build_cons… | 31_dicembre (qualunqu… |  | CC-BY-4.0 | locale | build_constraints.py | **1** |
| `brescia_cittadinanza_quartieri` | Comune di Brescia | residenti per CITTADINANZA e quartiere, italiani inclusi: l… |  | 2026-08-11 | CC-BY-4.0 | locale | enrich.py | **12** |
| `forli_cittadinanza_quartieri` | Comune di Forli' | residenti STRANIERI per nazionalita', quartiere e sesso, fo… | 31 dicembre 2021 | 2026-08-11 | CC-BY-4.0 (presunta) | locale | enrich.py | **12** |
| `istat_cens_stranieri_paesi` | ISTAT | censimento permanente, stranieri residenti al 31 dicembre p… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_constraints.py, enrich.py, common… | **12** |
| `ravenna_cittadinanza_aree` | Comune di Ravenna — Ufficio S… | residenti con cittadinanza STRANIERA per nazionalita' e are… | 31 dicembre 2023 | 2026-08-11 | pubblico-dominio | locale | enrich.py | **12** |
| `reggio_cittadinanza_circoscrizioni` | Comune di Reggio nell'Emilia | residenti stranieri per nazionalita' e circoscrizione, font… | 2013 | 2026-08-11 | CC-BY | locale | enrich.py | **12** |
| `bologna_cittadinanza_zone` | Comune di Bologna — U.I. Uffi… | residenti STRANIERI per paese di cittadinanza, zona, quarti… |  | 2026-08-11 | CC-BY-4.0 | locale | enrich.py | **123** |
| `parma_microdati_residenti` | Comune di Parma — Ufficio Sta… | anagrafe comunale COMPLETA, una riga per residente: 202.111… | 1 gennaio 2025 | 2026-08-11 | CC-BY-4.0 | locale | enrich.py | **12V** |
| `istat_cens_sesso_eta_cittadinanza` | ISTAT | censimento permanente, popolazione residente al 31 dicembre… | 31_dicembre (N-1) |  | CC-BY-4.0 | locale | build_zona_tables.py, build_constraints… | **13** |
| `istat_sezioni_2023` | ISTAT | censimento permanente 2023, conteggi per SEZIONE di censime… | 31_dicembre | 2026-08-02 | CC-BY-4.0 | locale | build_sezioni.py, enrich.py, common.py | **13** |
| `avq_microdati` | ISTAT | campione dell'indagine multiscopo sulle famiglie, individui… | anno_indagine | 2026-08-03 | CC-BY-4.0 | locale | assign_avq.py | **2** |
| `avq_tracciato_2024` | ISTAT | elenco delle variabili dei microdati AVQ 2024 con le rispet… |  | 2026-08-03 | CC-BY-4.0 | git |  | **2** |
| `anncsu_indirizzario` | ISTAT e Agenzia delle Entrate | tutti gli accessi esterni (numeri civici) certificati dai C… |  | 2026-07-28 | CC-BY-4.0 | locale | scripts/vincoli/join_civici_sezioni.py | **3** |
| `istat_sezioni_2023_tracciato` | ISTAT | codebook delle 138 colonne dei file regionali: NOME_CAMPO -… |  | 2026-08-02 | CC-BY-4.0 | git |  | **3** |
| `istat_sezioni_shp` | ISTAT | geometrie delle sezioni di censimento, edizione 2021, in WG… |  |  | CC-BY-4.0 | locale | scripts/vincoli/join_civici_sezioni.py | **3W** |
| `istat_unioni_civili_2023` | ISTAT | Indagine individuale ed ESAUSTIVA di fonte Stato Civile, is… |  | 2026-08-07 | CC-BY-4.0 | locale | gsp.nucleo | **4** |
| `repertorio_nuclei_v1` | GSP (derivato) | Configurazioni di nucleo familiare con le loro probabilita'… |  | 2026-08-11 | derivata: CC-BY-4.0 dalle f… | locale | gsp.nucleo, scripts/attributi/assign_nu… | **4** |
| `cens2011_caratt_attl` | ISTAT | OCCUPATI (`TIPO_DATO = EMPLP`) per caratteristiche dell'att… |  | 2026-08-05 | CC-BY-4.0 | locale | gsp.lavoro | **D** |
| `cens2011_titolo_studio` | ISTAT | popolazione residente di SEI ANNI E PIU' per titolo di stud… |  | 2026-08-04 | CC-BY-4.0 | locale |  | **D** |
| `claist_2026` | ISTAT | tutti i percorsi di istruzione e formazione italiani, ATTUA… |  | 2026-08-04 | CC-BY-4.0 | locale |  | **D** |
| `cognomi_wiki_MA_ARAB` | Wikipedia | 65 cognomi di origine marocchina, arabi e berberi, dalle vo… |  | 2026-08-04 | CC-BY-SA-4.0 | locale | gsp.nomi | **D** |
| `cognomi_wiki_NG_YORUBA` | Wiktionary | 107 cognomi yoruba dalla categoria Wiktionary, con l'etimol… |  | 2026-08-04 | CC-BY-SA-4.0 | locale | gsp.nomi | **D** |
| `firenze_cognomi_2013` | Comune di Firenze - Direzione… | residenti anagrafici del comune di Firenze, tutte le eta', … |  | 2026-08-02 | CC-BY-4.0 | git |  | **D** |
| `modena_nomi_residenti` | Comune di Modena | STOCK dei residenti anagrafici del comune di Modena, NON i … | 31_dicembre | 2026-08-03 | CC-BY-4.0 | locale | gsp.nomi | **D** |
| `popular_names_cognomi` | Andy Boothe (sigpwned) | cognomi PIU' DIFFUSI per paese, con forma localizzata e rom… |  | 2026-08-04 | CC0-1.0 | locale | gsp.nomi | **D** |
| `popular_names_nomi` | Andy Boothe (sigpwned) | nomi propri piu' diffusi per paese, 2.370 voci da 106 paesi… |  | 2026-08-04 | CC0-1.0 | locale | gsp.nomi | **D** |
| `firenze_cognomi_2012` | Comune di Firenze - Direzione… | residenti anagrafici del comune di Firenze, tutte le eta', … |  | 2026-08-02 | CC-BY-4.0 | git |  | **V** |
| `parma_codifica_campi` | Comune di Parma — Ufficio Sta… | codebook a DUE livelli: campo -> codice -> etichetta. Diver… |  | 2026-08-11 | CC-BY-4.0 | locale | enrich.py | **V** |
| `eusilc_puf_it` | Eurostat | DIECI ANNATE, quaranta CSV. Nomi con la lettera del file MI… |  | 2026-08-05 | accesso pubblico previa acc… | locale | scripts/diagnostica/eusilc_grafo.py | **VI** |
| `eusilc_target_variables_2013` | Eurostat | Definizione ufficiale di tutte le variabili target EU-SILC:… |  | 2026-08-05 | documento pubblico Eurostat… | locale | note/eusilc_exploration_v3.md | **VI** |
| `avq_medie_nazionali` | GSP (derivato) | medie ponderate nazionali delle 23 variabili AVQ, calcolate… |  | 2026-08-04 | CC-BY-4.0 | git | animarium | **W** |
| `istat_cens_posizione_famiglia` | ISTAT | censimento permanente al 31 dicembre. Descrive la posizione… | 31_dicembre |  | CC-BY-4.0 | locale |  | **—** |

Legend: 1–4 rings; D derived layers; V validation/exploration; W viewer only; I infrastructure; — registered, not used.
Sources per destination (a source may feed several): 1: 17, 2: 9, 3: 6, 4: 2, D: 9, V: 5, W: 2, I: 2; total sources: 39.
