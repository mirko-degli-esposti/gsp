# Confronto T=0,3 vs T=1,0 — soli tecnici (P1-P3)


## claude-haiku-4.5

- parsing T=1,0: pulito {'prob_universita': 1.0, 'situazione': 1.0} · None 0.0%
- dispersione prob entro agente: 1.21 (T03) -> 4.43 (T10) · scelta identica su tutte le repliche: 87.5% -> 71.5%
- **P1**: credenza (prob media T03) 40.0% · quota T03 7.6% (scarto 32.3%) · quota T10 11.5% (scarto 28.5%) -> **MIGRA** (P1 regge)
- **P2** posizione presentata (ciclo completo, attesa 25% se indifferente): p0=19.8%  p1=25.3%  p2=30.2%  p3=24.7%
  ITS quando primo 0.0% vs altrove 0.0%
- **P3** per cella (n=12): scarto medio 28.5%, max 35.3% (tecnico·diploma·M·straniero) -> oltre (P3 no)
  celle estreme: tecnico·diploma·M·straniero: quota 0% vs cred 35% · tecnico·laurea+·F·ita: quota 38% vs cred 58%

## deepseek-chat

- parsing T=1,0: pulito {'prob_universita': 1.0, 'situazione': 0.99} · None 0.0%
- dispersione prob entro agente: 7.19 (T03) -> 17.02 (T10) · scelta identica su tutte le repliche: 66.7% -> 46.5%
- **P1**: credenza (prob media T03) 49.3% · quota T03 56.2% (scarto 7.0%) · quota T10 63.2% (scarto 13.9%) -> **non migra** (P1 no)
- **P2** posizione presentata (ciclo completo, attesa 25% se indifferente): p0=22.7%  p1=28.1%  p2=27.6%  p3=21.5%
  ITS quando primo 2.1% vs altrove 0.5%
- **P3** per cella (n=12): scarto medio 13.9%, max 36.0% (tecnico·diploma·M·ita) -> oltre (P3 no)
  celle estreme: tecnico·bassa·M·straniero: quota 46% vs cred 46% · tecnico·diploma·M·ita: quota 88% vs cred 52%

## gpt-4o-mini

- parsing T=1,0: pulito {'prob_universita': 1.0, 'situazione': 0.938} · None 0.3%
- dispersione prob entro agente: 0.56 (T03) -> 2.58 (T10) · scelta identica su tutte le repliche: 5.6% -> 11.1%
- **P1**: credenza (prob media T03) 70.4% · quota T03 56.2% (scarto 14.1%) · quota T10 63.1% (scarto 7.3%) -> **MIGRA** (P1 regge)
- **P2** posizione presentata (ciclo completo, attesa 25% se indifferente): p0=50.5%  p1=21.5%  p2=21.3%  p3=6.6%
  ITS quando primo 84.0% vs altrove 0.2%
- **P3** per cella (n=12): scarto medio 12.2%, max 32.5% (tecnico·bassa·M·ita) -> oltre (P3 no)
  celle estreme: tecnico·bassa·M·ita: quota 38% vs cred 70% · tecnico·laurea+·F·ita: quota 85% vs cred 70%

## Verdetti

- claude-haiku-4.5 · P1: regge
- claude-haiku-4.5 · P2: NO
- claude-haiku-4.5 · P3: NO
- deepseek-chat · P1: NO
- deepseek-chat · P2: NO
- deepseek-chat · P3: NO
- gpt-4o-mini · P1: regge
- gpt-4o-mini · P2: regge
- gpt-4o-mini · P3: NO

Lettura d'insieme: P1 vera per tutti = la scomposizione credenza/argmax e' dimostrata; P1 vera solo per alcuni = la regola di decisione e' essa stessa idiosincratica anche nella sua sensibilita' alla temperatura — che sarebbe il finding.
