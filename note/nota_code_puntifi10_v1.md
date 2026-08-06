# Le code di `PUNTIFI10` — quanti agenti distinti si possono davvero fare

**v1 — 6 agosto 2026**

Serve a decidere se un esperimento di taratura sul modello di SIVE si
possa rifare con individui veri invece che con personas costruite, e da
quale comune conviene partire.

La risposta è sì, e il comune giusto **non** è quello che si sceglierebbe
per dimensione.

---

## 1. La domanda

Il disegno di SIVE-Montelago funziona così: si sceglie un valore latente
di fiducia, si genera una storia che lo codifica senza nominarlo,
l'agente riceve solo la storia, e la batteria ricava un valore osservato.
Se l'osservato torna al latente, lo strumento è tarato.

Con una popolazione GSP il latente non si sceglie più: è `PUNTIFI10` del
donatore AVQ, cioè un dato. Il che è meglio per la validità esterna, ma
apre due dubbi pratici:

- **le code esistono?** Una scala di fiducia potrebbe concentrarsi al
  centro, e senza casi estremi la taratura non si misura;
- **quanti agenti DISTINTI ci sono davvero?** Non quanti individui, ma
  quanti vettori AVQ diversi: due agenti con lo stesso vettore non sono
  evidenza indipendente, sono la stessa risposta con nomi diversi.

La seconda è la domanda che conta.

---

## 2. La distribuzione

Parma, 93.173 occupati con `PUNTIFI10` valorizzato:

| valore | individui | quota | |
|---|---|---|---|
| 0 | 8.708 | 9,35% | ███████████ |
| 1 | 3.099 | 3,33% | ███ |
| 2 | 4.366 | 4,69% | █████ |
| 3 | 4.009 | 4,30% | █████ |
| 4 | 6.270 | 6,73% | ████████ |
| 5 | 14.555 | 15,62% | ██████████████████ |
| 6 | 17.111 | 18,36% | ██████████████████████ |
| 7 | 15.460 | 16,59% | ███████████████████ |
| 8 | 11.901 | 12,77% | ███████████████ |
| 9 | 3.776 | 4,05% | ████ |
| 10 | 3.918 | 4,21% | █████ |

**Le code ci sono e sono grosse**: 17,4% sotto 3, 21,0% sopra 7. Il picco
a zero — quasi un decimo del totale — è la firma tipica delle scale di
fiducia istituzionale, dove chi non si fida sceglie l'estremo invece di
graduare.

Non serve stratificare per avere abbastanza casi.

---

## 3. Undici comuni, e la sorpresa

| comune | occupati | donatori | coda bassa | don. | coda alta | don. |
|---|---|---|---|---|---|---|
| **Brescia** | 88.425 | **6.681** | 18,2% | **1.137** | 19,2% | **1.326** |
| Bologna | 184.827 | 4.005 | 17,3% | 649 | 20,9% | 878 |
| Parma | 93.173 | 3.906 | 17,4% | 640 | 21,0% | 852 |
| Modena | 84.439 | 3.913 | 17,5% | 635 | 20,8% | 856 |
| Reggio Emilia | 80.170 | 3.861 | 17,6% | 634 | 21,0% | 833 |
| Ravenna | 68.487 | 3.830 | 17,3% | 629 | 21,1% | 833 |
| Rimini | 63.531 | 3.885 | 17,2% | 632 | 21,1% | 851 |
| Ferrara | 56.942 | 3.831 | 17,3% | 626 | 21,0% | 823 |
| Forlì | 52.819 | 3.784 | 17,5% | 628 | 21,4% | 820 |
| Piacenza | 46.182 | 3.748 | 17,5% | 623 | 21,1% | 807 |
| Castenaso | 7.706 | 2.670 | 16,8% | 456 | 21,5% | 564 |

### Le quote sono identiche ovunque

17,2–18,2% nella coda bassa, 19,2–21,5% nell'alta, su comuni che vanno da
7.706 a 184.827 occupati.

Non è un fatto sui comuni: **è un fatto sul pool di donatori**. La
distribuzione di `PUNTIFI10` viene dall'hot-deck, condizionato sulla
regione, quindi undici comuni la replicano quasi identica. Le differenze
residue vengono dalla composizione demografica, che sposta i pesi delle
celle di condizionamento.

È lo stesso fenomeno del tier 0 per il paese di cittadinanza, su un altro
asse: **la geografia degli attributi AVQ si ferma alla regione**, e una
mappa della fiducia per quartiere mostra la composizione demografica del
quartiere, non un'informazione locale.

### Brescia ha il doppio dei donatori

1.137 e 1.326 contro i ~630 e ~840 degli emiliani. Il rapporto è **1,77**,
che è esattamente il rapporto fra i due pool: 8.111 donatori lombardi
contro 4.629 emiliani.

> **Per un esperimento con agenti, il comune migliore è Brescia — non
> Bologna.** Bologna ha il doppio degli occupati e *meno* donatori
> distinti nelle code: 649 contro 1.137. Il numero che conta non è
> quanti individui ci sono ma quante risposte diverse esistono, e quella
> è una proprietà del pool regionale.

È un criterio di scelta che nessuno cercherebbe guardando la dimensione
dei comuni.

---

## 4. Cosa questo significa per il disegno

**Un esperimento a 120 agenti è largamente sostenibile.** Anche a
Castenaso, il comune più piccolo, la coda bassa ha 456 donatori distinti:
quaranta agenti con fiducia 0-2 sarebbero quaranta vettori AVQ diversi
con probabilità quasi certa.

**Ma la scala non è libera.** A 1.000 agenti stratificati sulle code, a
Parma si pescherebbe da 640 donatori: alcune coppie condividerebbero il
vettore. A Brescia il limite è quasi il doppio.

> Il tetto di un esperimento non è la popolazione sintetica ma il **pool
> di donatori nella cella che si sta campionando**. Con la
> stratificazione il tetto scende ancora, perché ogni strato attinge a un
> sottoinsieme.

**E la replica va misurata, non assunta.** Un campione stratificato di N
agenti va accompagnato dal conteggio dei `donor_id` distinti: se fossero
meno di N, alcuni agenti sono la stessa persona con un altro nome, e la
varianza osservata sottostima quella vera.

---

## 5. La cosa che peggiora, non migliora

Gli attributi derivati — nome, titolo di studio dettagliato, settore,
posizione professionale — rendono due agenti con lo stesso vettore AVQ
**molto meno simili in superficie**. Uno è «Maria Bruni, laurea in
medicina, dipendente nella sanità», l'altro «Anna Ferri, diploma tecnico,
lavoratrice in proprio nel commercio».

Dove conta, però, sono identici: stesse ventitré risposte, stesse
correlazioni, stesso contributo a una statistica.

> **La diversità apparente cresce mentre quella reale resta la stessa**,
> e questo rende più difficile accorgersi che due agenti non sono
> evidenza indipendente. È un peggioramento del problema, non un
> miglioramento.

Da cui la regola operativa: in qualunque campagna, riportare i
**`donor_id` distinti** accanto al numero di agenti. È una riga di codice
e toglie l'illusione.

---

## 6. Lo script

```python
import pandas as pd, glob

righe = []
for f in sorted(glob.glob(
        "data/comuni/*/constraints_2024/popolazione_K[6-9]C_avq_full.csv")):
    c = f.split("/")[2]
    d = pd.read_csv(f, usecols=["PUNTIFI10", "condizione", "donor_id"],
                    low_memory=False)
    v = pd.to_numeric(d.PUNTIFI10, errors="coerce")
    o = d[(d.condizione == "occupato") & v.notna()]
    vo = pd.to_numeric(o.PUNTIFI10, errors="coerce")
    r = {"comune": c, "occupati": len(o), "donatori": o.donor_id.nunique()}
    for lo, hi, et in ((0, 2, "bassa"), (3, 7, "centro"), (8, 10, "alta")):
        s = o[vo.between(lo, hi)]
        r[f"n_{et}"] = len(s)
        r[f"don_{et}"] = s.donor_id.nunique()
    righe.append(r)
print(pd.DataFrame(righe).to_string(index=False))
```

Vale per qualunque variabile AVQ cambiando il nome della colonna: la
domanda «quanti agenti distinti posso fare» si ripropone identica per
`FIDMED`, `AMBIENTE` o qualunque altra.

---

## Riferimenti

| | |
|---|---|
| lo strato donatori | `note/GSP_popolazioni_full_riferimento_v22.md` §13 |
| n_eff di Kish per variabile | idem §13.3 |
| gli attributi derivati | idem §2.4 · `note/nota_biografia_v1.md` §6 |
| la diversità apparente | `note/design_animarium_v13.md` §14 |
