# Nota per la Part III — ritrattazione della spiegazione di sd(z)

**29 agosto 2026.** Emersa scrivendo §4 del paper Animarium, verificando
quale solver abbia prodotto la flotta al tag `report-v1.0`.

---

## Cosa dice oggi la Part III

Nel commento alla tabella dei z-score per comune:

> The z-scores are not independent draws — the sampler is a Gibbs chain,
> and sd(z) above 1 measures the variance inflation due to its
> autocorrelation. Nine municipalities sit between 0.98 and 1.16.
> Bologna stands out at 1.391, with |z|max = 36 on a cell of expectation
> 1.0 (widowed men aged 15–24 in one zone): the largest state space of
> the fleet (18 zones, K9C) mixes least, and the inflation concentrates
> on near-empty cells while cells with expectation above ~100 stay
> within |z| ≲ 4.

## Perché è sbagliata

`fit_cs.py` non campiona con una catena. Il campionamento è **diretto**
sullo spazio enumerato:

```
389:        sample = all_tuples[idx]
```

`--sweeps` compare **solo** dentro `gibbs.fit(...)` (riga 345), cioè è un
parametro del solver PCD, che è **opt-in** (`--gibbs`) e nella riga di
produzione di `rigenera.sh` è disattivato (`--no-gibbs`). Le righe
374–382 calcolano `KL(exact‖gibbs)` e `KL(gibbs‖exact)`: il ramo Gibbs
esiste per **confrontare**, non per produrre.

Il collaudo lo conferma indipendentemente: Milano K9C «esatto, MRE =
4,24·10⁻⁴ in 54 s», Mantova K6C «esatto, 0,17 s».

Quindi: **fit esatto sul duale + estrazioni i.i.d.** Non esiste
autocorrelazione da inflazionare, e la spiegazione va ritirata.

## Cosa resta vero, e cosa diventa aperto

**Vero, e da riformulare in positivo.** Con estrazioni indipendenti
sd(z) ≈ 1 è *ciò che la teoria predice*: i nove comuni fra 0,98 e 1,16
non sono un'anomalia da giustificare ma una **verifica che passa**. La
frase va girata: da scusa a conferma.

**Aperto: Bologna a 1,391**, con |z|max = 36 su una cella di attesa 1,0.
Va marcato `aperto`, non spiegato. Ipotesi da testare, in ordine:

1. **Celle rare.** Su un supporto con molte celle di attesa ≪ 1 la
   normale non approssima la binomiale: lo z non è uno z, e la coda si
   allunga. Bologna ha lo spazio più grande e quindi più celle quasi
   vuote. *Test:* ricalcolare sd(z) escludendo le celle con attesa < 5,
   o < 10, e vedere se converge a 1 su tutti i comuni. Se sì, la
   spiegazione è questa e costa una riga.
2. **Vincolo sul totale.** N è fissato (non Poisson), quindi le celle
   non sono binomiali indipendenti: c'è una correlazione negativa
   indotta, che *riduce* la varianza — direzione sbagliata per spiegare
   1,391, ma va escluso esplicitamente.
3. **Non-indipendenza dei vincoli.** I margini si sovrappongono; l'errore
   per cella non è una statistica indipendente per cella. Da valutare se
   l'effetto scala con la sovrapposizione del constraint set (Bologna
   K9C 18 zone è il più fitto).

Il test (1) è quello decisivo e costa poco: si fa sui file al tag,
senza rigenerare.

## Cosa cambia nei documenti

| dove | azione |
|---|---|
| Part III, commento ai z-score | riscrivere: sd(z)≈1 come verifica che passa; Bologna `aperto` con le tre ipotesi |
| Part III, registro delle ritrattazioni | aggiungere la voce: spiegazione Gibbs ritirata, meccanismo dichiarato |
| Part I / riferimento §5 | verificare che non dicano «fit PCD» per la flotta |
| paper §4 anello 1 | **fatto** (v0.2): fit esatto + i.i.d., PCD come ramo di confronto e frontiera di scala |
| paper §6 | riscrivere la frase «the largest state space of the fleet mixes least» — cade con la ritrattazione |

## Guadagno collaterale

Se il fit è esatto a 1e-8, il 4·10⁻⁴ **non è errore di modello ma rumore
di campionamento**. Questo rende l'argomento del pavimento in §6 più
forte, non più debole: si misura un errore quasi interamente di
campionamento su un fit che sui vincoli è praticamente esatto — ed è la
ragione per cui il MRE non dipende da |X|.
