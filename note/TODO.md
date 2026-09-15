# TODO — ripresa lavori


- Milano: 10 combinazioni impossibili (unica della flotta) — spiegare prima del deposito

- [ ] 2026-09-02 [campagna-ER-posas] 13 comuni con lon/lat nulli (piacentini e parmensi): collocazione per sezione ok, coordinate no — guardare ANNCSU o join_civici_sezioni
- [ ] 2026-09-02 [campagna-ER-posas] il viewer non dice nulla quando la mappa del comune non ha coordinate: tela vuota senza spiegazione


- **Sbloccare Z2 per l'hold-out.** Oggi `cs_build --senza Z2` fallisce con
  `KeyError`: alla riga ~729 `get_block("Z2_zona_sesso_eta_cittad")` serve a
  costruire Z5 per IPF, e se Z2 non è registrato il blocco non c'è. La
  costruzione e la registrazione vanno separate — costruire il dataframe di
  Z2 e passarlo a Z5 direttamente, registrandolo nel constraint set solo se
  `--senza` non lo esclude. Mezz'ora di lavoro. Serve se un referee chiede
  l'ablation estesa: Z2 è il blocco più grande (384 celle a Forlì) e porta
  la cittadinanza alla zona, cioè è il canale che fa ricostruire Z5 al 76%.
  Attesa: senza Z2 la geografia della cittadinanza non sopravvive, perché
  nessun altro blocco la lega alla zona — quindi un risultato simile a Z3
  (94%). Gerarchia delle dipendenze: Z1 → Z2 → Z5; foglie escludibili oggi:
  Z3, Z4, Z5.

  - **Soglia sui target infinitesimi.** Le celle con massa sotto ~1e-6 vanno
  dichiarate zeri strutturali invece che vincoli con target positivo. A
  Forlì due celle a 1e-9 (stranieri anziani maschi in una zona) portano il
  99,6% del pavimento e lo rendono illeggibile: 3.189% contro il 13% che si
  avrebbe senza. La macchina per dichiarare gli zeri esiste già e funziona
  (34 celle a Forlì, tutte con osservato 0, verificate). Costo: nullo alla
  prossima rigenerazione. Effetto sul paper: il capoverso su Forlì in §6 si
  accorcia da sé.