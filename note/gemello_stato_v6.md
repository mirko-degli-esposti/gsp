# Gemello identico: stato dopo il passo 5 (campione S, R2a, R3)

*v6, 10/10/2026. **Sostituisce `gemello_stato_v5.md`** (ora in `storico/`).
Rispetto alla v5, aggiunge il passo 5 al livello 0: il campione S, R2a
(IPF a seme) e R3 (Fay–Herriot), confrontati con R0 e R1. Fissa anche le
covariate di R3, approvate da Mirko prima dei risultati.*

*Aree intermedie, scale dello z, passo 4 per area e correzione su q13
restano come nella v5 (`storico/gemello_stato_v5.md`). Tutto riguarda
Modena 036023, livello 0 (verità = popolazione GSP: inverse crime).*

*Etichette: **misurato** = c'è un log; **dichiarato** = viene dal codice o
da una fonte; **aperto** = non deciso o non misurato.*

---

## 0. Commit e provenienza

- gemello `8222bda`: campione, R2a, R3, metrica comune sulle quote, script
  del passo 5.
- gemello `0ecb29c`: script di analisi.
- La corsa è stata fatta con gemello `8222bda` e gsp `c017961`. Il manifest
  dice «+sporco» solo perché `script/analisi_passo5.py`, non ancora
  tracciato e non usato dalla corsa, era nell'albero.
- Comandi: `python script/passo5_campione.py config/livello0.yaml
  --paralleli 7` (1.988 s), poi `python script/analisi_passo5.py`.
- Uscite in `gemello/risultati/passo5/036023/`: `quote.csv`,
  `r3_stime.csv.gz`, `r2_info.csv`, `decisioni.csv`, `analisi_*.csv`,
  `analisi.txt`.

## 1. Disegno (*dichiarato*)

- **S.** Bernoulli delle unità di T: nuclei interi, e individui in
  convivenza come unità a sé. φ ∈ {0,1%, 0,5%, 1%, 2%, 5%}, B = 20 repliche
  per φ, peso 1/φ. A φ = 1% ci sono circa 870 nuclei e 1.850 individui.
- **R2a.** I-proiezione del seme (conteggi di S × 1/φ, più δ su ogni cella
  ammessa) sugli **stessi vincoli e sullo stesso supporto di R1**. È lo
  stesso budget d'informazione: cambia solo la prior (§2.4 della nota).
  - Si calcola con IPF a blocchi con complemento, alla tolleranza 5e-4. I
    vincoli derivati da `cs_build` sono coerenti solo fino a circa 2,7e-4,
    e R1 stesso si ferma a 4,3e-4.
  - Poi lo stesso campionamento e gli stessi anelli 3–4 di R1.
  - δ principale 10⁻³ (in conteggi pesati); sensibilità con δ ∈ {10⁻⁶,
    0,5} a φ = 1%.
  - Le IPF convergono in 1.500–3.500 iterazioni. KL(R2a‖p\*_R1) va da 1,39
    nat (φ = 0,1%) a 0,44 nat (φ = 5%): il seme sparso concentra la massa
    sulle celle campionate.
- **R2b** (calibrazione dei nuclei, IPU) **non è implementato** (*aperto*).
- **R3.** Fay–Herriot per area intermedia (87 aree), un modello per
  domanda. Covariate fissate prima dei risultati (`fay_herriot.py`): quote
  0–14, 65+, 75+ e stranieri; ampiezza media delle famiglie e quota di
  famiglie di una persona (da Π per area); quote di zona di laureati,
  occupati 15–64 e non nativi (dal cs di Π).
  - ψ_i = θ̄(1−θ̄)/n_eff, con n_eff in nuclei; σ_u² stimata per REML.
  - EBLUP, stima sintetica dove n = 0, troncamento in [0, 1].
  - MSE Prasad–Rao senza g3.
  - q12, che è una tabella comunale, usa la stima diretta.
  - Per le decisioni la quota θ̂ si moltiplica per una base di Π: over 75
    per q41; per q42 i bambini 0–4, proxy pubblico dei nuclei con figli
    sotto i 3 anni.
- **Metrica comune** (`metriche.confronta_quote`): errore relativo pesato
  sulle quote per area, Σ N|θ̂ − α| / Σ N α. Vale per tutti i metodi,
  anche per R3, che non produce una popolazione.

## 2. Risultati (*misurato*, medie sulle repliche, scala di area)

**Errore relativo pesato sulle quote:**

| domanda | ord. | R0 | R1 | R2a 0,1% | R2a 1% | R2a 5% | R3 0,1% | R3 1% | R3 5% |
|---|---|---|---|---|---|---|---|---|---|
| q11 laureati 25–64 | 1 | 0,233 | 0,043 | 0,098 | 0,052 | 0,045 | 0,417 | 0,120 | 0,057 |
| q12 istr. × cond. | 1 | 0,864 | 0,022 | 0,244 | 0,137 | 0,055 | 0,542 | 0,172 | 0,077 |
| q13 occupati 25–64 | 1 | 0,325 | 0,017 | 0,021 | 0,018 | 0,017 | 0,150 | 0,042 | 0,022 |
| q14 coniugate occupate | 1 | 0,369 | 0,081 | 0,342 | 0,146 | 0,095 | 0,705 | 0,207 | 0,109 |
| q15 vedovi 75+ | 1 | 0,804 | 0,080 | 0,366 | 0,153 | 0,093 | 0,708 | 0,262 | 0,120 |
| q21 over 75 soli | 2 | 0,176 | 0,105 | 0,173 | 0,123 | 0,106 | 0,844 | 0,281 | 0,140 |
| q22 stranieri ≤ media in cerca | 2 | 0,673 | 0,354 | 0,755 | 0,747 | 0,391 | 2,904 | 0,865 | 0,430 |
| q23 laureate occupate | 2 | 0,620 | 0,083 | 0,364 | 0,131 | 0,094 | 0,738 | 0,239 | 0,112 |
| q31 figlio < 3, due occupati | 3 | 0,471 | 0,238 | 0,249 | 0,240 | 0,244 | 0,821 | 0,660 | 0,317 |
| q32 monoparentali in cerca | 3 | 1,453 | 0,898 | 0,995 | 0,946 | 0,927 | 1,212 | 1,626 | 1,048 |
| q33 over 80 senza 18–64 | 3 | 0,088 | 0,083 | 0,090 | 0,084 | 0,081 | 0,282 | 0,217 | 0,101 |
| q34 coppie laureate | 3 | 0,223 | 0,189 | 0,259 | 0,190 | 0,186 | 1,336 | 0,482 | 0,238 |

(Tabella completa con 0,5% e 2% in `analisi_errore.csv`.)

**φ\*** è il φ minimo a cui un metodo a campione ha errore medio ≤ R1:
- **R2a:** 2% per q31 e q33, 5% per q34; mai, fino al 5%, per le domande di
  ordine 1–2 e per q32;
- **R3:** mai, per nessuna domanda.

**Criteri del §11.5 della nota:**
- **(a) R2a con S ⊂ T non batte R1 in modo significativo: soddisfatto.**
  Su 60 combinazioni domanda × φ, in 0 casi la differenza è sotto −2 errori
  standard. R2a converge a R1 al crescere di φ: q13 è già alla pari a
  0,1%, perché è nello span; q12 è la più lenta.
- **(b) R3 a φ = 5% entro il suo MSE nominale: soddisfatto.** La copertura
  dell'intervallo al 95% va da 0,92 a 0,96, e la media di err²/MSE da 0,88
  a 1,20. A φ basso l'MSE è conservativo (err²/MSE 0,5–0,8). L'eccezione
  sono le domande rare: q32 ha copertura 0,05–0,82 fino al 2%, e q22 e q31
  scendono a 0,57 e 0,35 a 0,1%, dove il modello degenera (θ̄ quasi 0, poche
  aree campionate).

**Sensibilità a δ (R2a, φ = 1%).** È piccola: δ = 0,5 aiuta solo sulle
celle rare (q12 da 0,137 a 0,112; q22 da 0,747 a 0,571), con differenze
≤ 0,02 altrove.

**Decisioni per area (regret medio):**
- **q41 (over 75 soli):** R1 0,027–0,056; R2a si avvicina a R1 a 5%
  (0,028–0,047); R3 a 5% 0,048–0,069; R0 0,050–0,092.
- **q42 (prima infanzia):** è dominata dal rumore per tutti (regret
  0,16–0,31).

Un dettaglio curioso su q42: lo Spearman di R3 a φ = 0,1% è 0,48, sopra R1
(0,38). A φ così basso R3 è quasi costante, e la graduatoria la dà la base
pubblica, cioè i bambini 0–4 per area. **Una proxy pubblica semplice
ordina le aree per q42 meglio di tutte le ricostruzioni.** È da tenere
presente nella discussione delle decisioni.

## 3. Lettura

1. **Al livello 0 non esiste un φ\* per le domande di ordine 1–2.** È
   quello che il disegno prevede: la verità è MaxEnt (inverse crime),
   quindi R1 ha già tutta l'informazione e S aggiunge solo rumore. I φ\* che
   contano si misurano ai livelli 1 e 2, dove la verità ha struttura fuori
   vincolo (ipotesi H3 e H4). Il livello 0 fissa le curve di riferimento:
   quanto rumore costa ricostruire da un campione quando non c'è niente da
   imparare.
2. **R2a batte nettamente R3 a parità di φ** su quasi tutte le domande, a
   tutti i φ. R2a usa i vincoli della popolazione intera, R3 solo
   covariate d'area. A φ = 5% R3 si avvicina (q11 0,057 contro 0,045; q13
   0,022 contro 0,017).
3. **Le domande di nucleo** (q31, q33, q34) sono le uniche dove R2a
   raggiunge R1, dal 2% in su. Coerente con la v5: lì R1 non ha vantaggio
   d'informazione, perché l'anello 4 è comune a tutti.
4. **Fay–Herriot è ben calibrato** dove non degenera. Le stime sono quasi
   sintetiche (σ_u² spesso 0): il guadagno su una stima diretta viene dalle
   covariate di Π.

## 4. Prossimi passi

1. **Livello 1a** con g1 (principale), poi g2 e g4, su Modena. Si inclina
   p\* lungo g a vincoli fissi, si genera T_θ (anelli 1+3+4), e si ripetono
   R0, R1, R2a e R3 per alcuni θ. Pendenze previste θ·Cov(h_⊥, g_⊥) contro
   misurate. Qui φ\* diventa informativo.
2. R2b (IPU sui nuclei), se serve per le domande di ordine 3.
3. Variante «indagine da un'altra città» (§7.3 della nota).

## 5. Aperto (cumulativo)

- Rigenerare gli anelli 3+4 della flotta con l'età corretta (release).
- Regole `IMPOSSIBILI` per background × origine, con refit.
- Età singola condizionata allo stato civile, e coniugati di 15 anni.
- Causa del disallineamento dei nuclei di produzione di Modena.
- R2b non implementato.
- MSE di R3 senza g3, e comportamento a φ molto basso sulle domande rare.
