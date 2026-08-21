# Verifica fuori-campione della link function — 36 celle, T=0,3

Predizioni L1-L3 e trappola del clipping: docstring dello script.


## claude-haiku-4.5  (celle: 36; quota tutte le repliche)

- celle sature (quota 0 o 1): 24/36 — il clipping lavora li'
- eps 0.02:  a -0.63  b 3.64  R² 0.89
- eps 0.05:  a -0.45  b 2.84  R² 0.87
- fase 2 (tecnici, T=1,0): a -1.28  b 3.04  R² 0.88  ->  L1 (b piu' ripida al freddo): **NO**

## deepseek-chat  (celle: 36; quota tutte le repliche)

- celle sature (quota 0 o 1): 15/36 — il clipping lavora li'
- eps 0.02:  a +0.28  b 3.52  R² 0.96
- eps 0.05:  a +0.19  b 2.81  R² 0.95
- fase 2 (tecnici, T=1,0): a +0.68  b 1.67  R² 0.61  ->  L1 (b piu' ripida al freddo): regge a entrambi gli eps

## gpt-4o-mini  (celle: 36; quota r0+r2 per il primacy)

- celle sature (quota 0 o 1): 10/36 — il clipping lavora li'
- eps 0.02:  a -5.78  b 8.24  R² 0.73
- eps 0.05:  a -4.68  b 6.72  R² 0.67
- fase 2: non identificabile; qui si stampa e non si interpreta

## Verdetti

- L2 (a_Haiku < a_DeepSeek): -0.63 vs +0.28 -> regge
- claude-haiku-4.5 · L1: NO
- claude-haiku-4.5 · L3: regge
- deepseek-chat · L1: regge
- deepseek-chat · L3: regge

Se L1-L3 reggono, (a,b) e' del MODELLO — con b funzione della temperatura — e la link function e' promossa da descrizione dei tecnici a proprieta' dello strumento. Se cadono, era locale, e la nota lo dice.
