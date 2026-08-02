# Fonti da registrare (ricognizione 2/8/2026)

Endpoint unico esterno: https://esploradati.istat.it/SDMXWS/rest
Usato da scripts/istat_sdmx.py e scripts/istat_catalog.py. Limite 4 query/min.

- data/comuni/<cod>/  coppie _raw/_decoded per ~12 tavole censuarie e
  anagrafiche. archiviazione: locale. Un id per tavola, non per comune.
- data/submun/  fonti comunali sub-comunali, tier 1-3. Universo gia'
  documentato nella docstring di scripts/opendata_paese.py: anagrafiche,
  data diversa dal censimento.
- data/avq/  microdati campionari con pesi di riporto. Decidere se
  n_misurato e' il conteggio dei record o la somma dei pesi.
- data/geodata/, data/istat_structures/  non sono distribuzioni:
  servira' un secondo tipo di normalizzatore.

Da chiarire: dataflow e key delle query (il pattern e' in
scripts_archivio/istat_sdmx_piemonte.py, con la nota sul limite di 260
caratteri per segmento di http.sys).

Residuo migrazione: fetch_comune.py importa istat_sdmx come modulo
fratello; istat_sdmx.py e' libreria, va in src/gsp/istat/.
