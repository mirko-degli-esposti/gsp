# TODO — ripresa lavori

- [ ] 2026-08-28 [campagna-ER-posas] nohup campagna_fetch: 450 celle (~6-10h), rete dipartimento
- [ ] 2026-08-28 [campagna-ER-posas] valida: salvare le misure nelle celle (righe C2, scarto C5) — punti calibrazione: Fiorenzuola ?, Cesena 0,12%
- [ ] 2026-08-28 [campagna-ER-posas] emetti: fix messaggio "presente (presente)"
- [ ] 2026-08-28 [campagna-ER-posas] riapri: preservare il 'quando' originale della cella
- [ ] 2026-08-28 [campagna-ER-posas] C5 censuarie: filtri totali multiformi PER TAVOLA (GENDER=T misurato in istruzione_eta)
- [ ] 2026-08-28 [campagna-ER-posas] range C2 da irrigidire quando la campagna dà punti oltre i 2 del pilota
- [ ] 2026-08-28 [campagna-ER-posas] verifica_articolazione_tutti: lanciare, chiudere i 45 da_verificare
- [ ] 2026-08-28 [campagna-ER-posas] Fiorenzuola: frammenti emessi (033021:K6C:19563), promozione in flotta = decisione da prendere
- [ ] 2026-08-28 [campagna-ER-posas] CESENA: decisione livello — vedi punto Animarium, probabile K9C via pipeline standard, NON via campagna
- [ ] 2026-08-28 [campagna-ER-posas] Animarium: verificare claim "capoluoghi di provincia" vs assenza di Cesena (FC ha DUE capoluoghi)
- ramo convivenze modificato post-report-v1.0: HEAD non riproduce nuclei_*.csv pubblicati (~530 righe/città con sez. speciale; misurato su Parma, 3 anelli su 4 identici). Dichiarare nella versione-paper; riallineamento pieno alla v2
- Milano: 10 combinazioni impossibili (unica della flotta) — spiegare prima del deposito
- rigenera.sh: --confronta deve fallire se l'archivio non esiste (controllo prima dell'azione)