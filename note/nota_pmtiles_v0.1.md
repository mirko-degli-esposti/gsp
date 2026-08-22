# Base cartografica statica con PMTiles — ricetta per la v1.1

**Versione 0.1 — 22 agosto 2026.** Da eseguire per la v1.1 del viewer;
la v1.0 esce con default «nessuna base» e provider esterni opt-in
(pannello, selettore `fondo`). Obiettivo: nessun servizio esterno — un
solo file statico interrogato per range HTTP, lo stesso meccanismo del
Parquet.

---

## 1. Cosa è PMTiles

Un archivio a file singolo di tile (vettoriali o raster) con un indice
interno: il client chiede byte range, il server è un file server
qualsiasi — Cloudflare Pages va bene com'è, nessun tile server, nessuna
chiave. È l'analogo cartografico del nostro Parquet a row group.

Due strade dentro il formato:

| | vettoriale | raster |
|---|---|---|
| sorgente | build Protomaps (OSM) già pronti | da generare noi |
| resa | serve uno stile + renderer JS | `drawImage` come oggi |
| peso (Italia, z0–14) | ~3–4 GB mondo intero; estratto Italia ~300–500 MB | dipende da zoom, vedi §3 |
| integrazione nel pannello | riscrittura della mappa (MapLibre o protomaps-js) | **minima**: cambia solo `urlTile` |

**Scelta: raster.** Il pannello disegna tile raster su canvas a mano
(`tile()`, `disegnaFondo()`); con il raster cambia una funzione, con il
vettoriale cambia l'architettura della mappa. Il costo è generare i
raster una volta e un file più pesante — accettabile perché servito
statico e scaricato solo a mappa aperta, lazy come il blocco C.

## 2. Catena di produzione (una tantum, per estratto)

Prerequisiti: `tilemaker` o un estratto Protomaps già costruito;
`pmtiles` CLI (Go, binario singolo); per la via raster un renderer
headless. La via più semplice oggi:

```bash
# 1. estratto vettoriale dell'area da un build Protomaps (gratuito):
pmtiles extract https://build.protomaps.com/YYYYMMDD.pmtiles \
    italia_z14.pmtiles --bbox=6.6,35.4,18.6,47.1 --maxzoom=14

# 2. resa raster con lo stile "light" (una volta, in locale):
#    protomaps offre `pmtiles serve` + uno script di render via
#    maplibre-gl headless; in alternativa lo stile light di
#    versatiles/shortbread. Output: directory z/x/y.png
#    [dettaglio da fissare alla prova: lo strumento di render cambia
#     rapidamente, verificare lo stato dell'arte al momento]

# 3. impacchettare i raster in PMTiles:
pmtiles convert tiles_dir/ base_light_italia.pmtiles
```

Se al momento dell'esecuzione la via raster risultasse macchinosa, il
piano B è vettoriale + `protomaps-leaflet` **solo per il fondo** (il
nostro layer dati resta sul canvas sopra): più JS, zero rendering
nostro.

## 3. Zoom e dimensioni — la scelta che governa il peso

Il pannello usa i tile solo come *contesto*: strade e isolati, non POI.
La mappa lavora fra z11 (città intera) e z16 (isolato); l'atlante
regionale scende a z8.

Stima raster (PNG ~25–40 KB/tile ai nostri zoom, area urbanizzata):

| copertura | z8–14 | z8–15 | z8–16 |
|---|---|---|---|
| ER + Brescia (~25.000 km²) | ~150–300 MB | ~0,5–1 GB | ~2–4 GB |
| Italia intera | ~1,5–3 GB | ~5–10 GB | ~20–40 GB |

Decisioni conseguenti:

- **v1.1: ER + Brescia, z8–15**, un file ~0,5–1 GB su Pages (limite
  per file 25 MiB su Pages! → **va su R2**, vedi §4). A z16 il pannello
  mostra il tile z15 ingrandito 2×: per un fondo di contesto è
  accettabile, e lo facciamo già oggi quando un tile manca.
- **Tutte le regioni**: stesso file logico, un PMTiles *per regione*
  (`base_light_{regione}.pmtiles`), caricato secondo il comune attivo —
  coerente con l'organizzazione per regione di geodata e AVQ, e il
  passaggio a nuove regioni non ripubblica nulla di esistente.
- I tile *dati* (quote, punti) restano generati dal pannello: PMTiles è
  solo il fondo.

## 4. Dove sta il file

Cloudflare **Pages** ha un limite di 25 MiB per singolo file: il
PMTiles non ci sta. Opzioni, in ordine di preferenza:

1. **Cloudflare R2** con dominio pubblico (`tiles.animarium…`): range
   requests nativi, egress gratuito verso Cloudflare, ~0,015 $/GB/mese
   di storage — un file da 1 GB costa centesimi. Il viewer resta su
   Pages, il fondo su R2: due origini statiche, zero servizi.
2. GitHub Releases come CDN di fatto (file fino a 2 GiB, range ok):
   gratuito, ma URL meno controllabile e fuori dal binding Cloudflare.
3. Zenodo per l'archiviazione del file con DOI (non per il serving:
   niente CORS/range garantiti) — complementare, non alternativo.

## 5. Modifiche al pannello (piccole per costruzione)

```js
// in testa, una volta:
import { PMTiles } from "https://cdn.jsdelivr.net/npm/pmtiles@3/+esm";
const FONDO_PM = new PMTiles("https://tiles…/base_light_emilia.pmtiles");

// urlTile() sostituita da una get async:
async function tilePM(z, i, j) {
  const t = await FONDO_PM.getZxy(z, i, j);      // ArrayBuffer PNG
  ...createImageBitmap(new Blob([t.data]))...
}
```

La cache (`cacheTile`) e `disegnaFondo` restano; il selettore `fondo`
guadagna la voce `pmtiles` che diventa il nuovo default, e OSM/CARTO
restano opt-in di confronto o spariscono. L'attribuzione sul canvas
diventa «© OpenStreetMap contributors, tiles Protomaps» (obbligo
CC-BY/ODbL della sorgente: resta, va tenuta).

## 6. Registro e binding

Il PMTiles è un **derivato registrabile**: voce nel registro con
`derivato_da` (build Protomaps del giorno X, bbox, zoom, stile),
impronta SHA-256, licenza ODbL per i dati OSM sottostanti + licenza
dello stile. Entra nella tabella di binding del report dalla v1.1 come
ogni altro artefatto. `ATTRIBUZIONI.md` guadagna la riga OSM/Protomaps.

## 7. Ordine di esecuzione, quando si farà

1. Prova su un bbox piccolo (Castenaso) per fissare lo strumento di
   render (§2 punto 2) e il peso reale per km².
2. Estratto ER+Brescia z8–15; misura; R2; patch al pannello; deploy.
3. Voce di registro + attribuzioni + riga nel report (IV.1 e binding).
4. Le altre regioni: solo §2 ripetuto per bbox, un file per regione.

Stima: mezza giornata il punto 1–2 la prima volta; un'ora per regione a
regime.
