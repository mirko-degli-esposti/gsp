"""
build_zona_tables.py — dalle sezioni di censimento alle tabelle per quartiere.

Input:  ~/progetti/gsp/data/submun/brescia_sezioni_2023.csv  (da R03 Lombardia,
        filtro PROCOM=17029; 1822 sezioni, 33 quartieri in COM_ASC1)
Output: ~/progetti/gsp/data/comuni/017029/zona_2023/
    z1_zona_sesso_eta5.csv        zona x sesso x classi quinquennali
    z2_zona_sesso_macroeta_citt.csv  zona x sesso x (0-14/15-64/65+) x ITL/FRG
    z3_zona_sesso_istruzione.csv  zona x sesso x istruzione (5 livelli)
    z4_zona_sesso_occup.csv       zona x sesso x occupato/non_occupato (15-64)
    zona_nomi.csv                 codice ASC -> nome quartiere

Decisioni (sessione 19/7/2026):
  - sezione fittizia 888888x (549 persone senza fissa dimora) TENUTA nel
    quartiere assegnato da ISTAT (17029004): coerenza contabile con i totali
    ufficiali (opzione a); variante di esclusione rimandata all'analisi Caffaro
  - riferimento temporale: censimento 31-12-2023 == anagrafe 1/1/2024 (K7C
    con --anno 2024); identita' verificata alla persona (198.259)

I margini comunali dei blocchi Z verranno imposti in cs_build via
P(zona | margine) x conteggi comunali (consistenza esatta per costruzione);
qui si misurano gli scarti grezzi come audit.
"""

import os
import sys
import pandas as pd

SEZ_CSV = os.path.expanduser("~/progetti/gsp/data/submun/brescia_sezioni_2023.csv")
OUT_DIR = os.path.expanduser("~/progetti/gsp/data/comuni/017029/zona_2023")
COM_DIR = os.path.expanduser("~/progetti/gsp/data/comuni/017029")

ASC_NOMI = {
 '17029001':'Brescia Antica','17029002':'Borgo Trento','17029003':'Porta Milano',
 '17029004':'Centro Storico Nord','17029005':'Chiusure','17029006':'Don Bosco',
 '17029007':'Fiumicello','17029008':'Folzano','17029009':'Fornaci','17029010':'Lamarmora',
 '17029011':'Mompiano','17029012':'Porta Cremona','17029013':'Buffalora','17029014':'Porta Venezia',
 '17029015':'Villaggio Prealpino','17029016':'Caionvico','17029017':'S. Bartolomeo',
 '17029018':'S. Eufemia','17029019':'S. Polo Case','17029020':'Chiesanuova',
 '17029021':'Urago','17029022':'Casazza','17029023':'Villaggio Badia','17029024':'Villaggio Sereno',
 '17029025':'Villaggio Violino','17029026':'Primo Maggio','17029027':'Centro Storico Sud',
 '17029028':'S. Eustacchio','17029029':'S. Rocchino','17029030':'Crocifissa Di Rosa',
 '17029031':'S. Polo Cimabue','17029032':'San Polino','17029033':'S. Polo Parco'}

# ---- mapping colonne tracciato -> variabili tidy --------------------------
ETA5 = ["Y0-4", "Y5-9", "Y10-14", "Y15-19", "Y20-24", "Y25-29", "Y30-34",
        "Y35-39", "Y40-44", "Y45-49", "Y50-54", "Y55-59", "Y60-64",
        "Y65-69", "Y70-74", "Y_GE75"]
COLS_ETA_M = [f"P{i}" for i in range(30, 46)]   # maschi quinquennali
COLS_ETA_F = [f"P{i}" for i in range(67, 83)]   # femmine quinquennali

EDU5 = ["nessun_titolo", "elementare", "media", "diploma", "terziario"]
COLS_EDU_M = [f"P{i}" for i in range(91, 96)]
COLS_EDU_F = [f"P{i}" for i in range(96, 101)]

MACROETA = ["Y0-14", "Y15-64", "Y_GE65"]
COLS_IT_M, COLS_IT_F = ["IT4", "IT5", "IT6"], ["IT7", "IT8", "IT9"]
COLS_ST_M, COLS_ST_F = ["ST25", "ST26", "ST27"], ["ST28", "ST29", "ST30"]


def melt_block(g, cols, labels, sex, extra: dict):
    rows = []
    for zona, sub in g:
        vals = sub[cols].sum()
        for c, lab in zip(cols, labels):
            rows.append({"zona": str(zona), "sesso": sex, **extra,
                         "cat": lab, "count": float(vals[c])})
    return rows


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    b = pd.read_csv(SEZ_CSV)
    b["COM_ASC1"] = b["COM_ASC1"].astype(int).astype(str)
    g = list(b.groupby("COM_ASC1"))
    assert len(g) == 33, f"attesi 33 quartieri, trovati {len(g)}"

    # nomi
    nomi = pd.DataFrame([{"zona": k, "nome": v} for k, v in ASC_NOMI.items()])
    nomi.to_csv(os.path.join(OUT_DIR, "zona_nomi.csv"), index=False)

    # ---- Z1: zona x sesso x eta5 -----------------------------------------
    z1 = pd.DataFrame(
        melt_block(g, COLS_ETA_M, ETA5, "M", {}) +
        melt_block(g, COLS_ETA_F, ETA5, "F", {})
    ).rename(columns={"cat": "eta5"})
    z1.to_csv(os.path.join(OUT_DIR, "z1_zona_sesso_eta5.csv"), index=False)

    # ---- Z2: zona x sesso x macroeta x cittadinanza ----------------------
    rows = (melt_block(g, COLS_IT_M, MACROETA, "M", {"cittadinanza": "ITL"}) +
            melt_block(g, COLS_IT_F, MACROETA, "F", {"cittadinanza": "ITL"}) +
            melt_block(g, COLS_ST_M, MACROETA, "M", {"cittadinanza": "FRG"}) +
            melt_block(g, COLS_ST_F, MACROETA, "F", {"cittadinanza": "FRG"}))
    z2 = pd.DataFrame(rows).rename(columns={"cat": "macroeta"})
    z2.to_csv(os.path.join(OUT_DIR, "z2_zona_sesso_macroeta_citt.csv"), index=False)

    # ---- Z3: zona x sesso x istruzione5 (universo 9+) --------------------
    z3 = pd.DataFrame(
        melt_block(g, COLS_EDU_M, EDU5, "M", {}) +
        melt_block(g, COLS_EDU_F, EDU5, "F", {})
    ).rename(columns={"cat": "istruzione5"})
    z3.to_csv(os.path.join(OUT_DIR, "z3_zona_sesso_istruzione.csv"), index=False)

    # ---- Z4: zona x sesso x occupato/non_occupato (universo 15-64) -------
    rows = []
    for zona, sub in g:
        pop_m = float(sub[["IT5", "ST26"]].sum().sum())   # 15-64 M (ita+stran)
        pop_f = float(sub[["IT8", "ST29"]].sum().sum())
        occ_m, occ_f = float(sub["P102"].sum()), float(sub["P103"].sum())
        rows += [
            {"zona": str(zona), "sesso": "M", "occup": "occupato", "count": occ_m},
            {"zona": str(zona), "sesso": "M", "occup": "non_occupato",
             "count": max(pop_m - occ_m, 0.0)},
            {"zona": str(zona), "sesso": "F", "occup": "occupato", "count": occ_f},
            {"zona": str(zona), "sesso": "F", "occup": "non_occupato",
             "count": max(pop_f - occ_f, 0.0)},
        ]
    z4 = pd.DataFrame(rows)
    z4.to_csv(os.path.join(OUT_DIR, "z4_zona_sesso_occup.csv"), index=False)

    # ---- Z6: zona x background (EM1-6, senza sesso) ----------------------
    EM_MAP = {"EM1": "italiano_nativo", "EM2": "italiano_rientrato",
              "EM3": "naturalizzato_g2", "EM4": "naturalizzato_immigrato",
              "EM5": "straniero_g2", "EM6": "straniero_immigrato"}
    rows = []
    for zona, sub in g:
        for em, bg in EM_MAP.items():
            rows.append({"zona": str(zona), "background": bg,
                         "count": float(sub[em].sum())})
    z6 = pd.DataFrame(rows)
    z6.to_csv(os.path.join(OUT_DIR, "z6_zona_background.csv"), index=False)
    print(f"[audit] Z6 totale: {z6['count'].sum():,.0f} (atteso 198.259)")

    # ---- audit margini vs tavole comunali 2023 ---------------------------
    print(f"[zona] 33 quartieri | Z1 {len(z1)} righe | Z2 {len(z2)} | "
          f"Z3 {len(z3)} | Z4 {len(z4)}")
    print(f"[audit] Z1 totale: {z1['count'].sum():,.0f} (atteso 198.259)")
    print(f"[audit] Z2 totale: {z2['count'].sum():,.0f} | "
          f"FRG: {z2[z2.cittadinanza=='FRG']['count'].sum():,.0f} (atteso 37.478)")
    print(f"[audit] Z3 totale (9+): {z3['count'].sum():,.0f} (atteso 184.715)")
    print(f"[audit] Z4 totale (15-64): {z4['count'].sum():,.0f} | "
          f"occupati: {z4[z4.occup=='occupato']['count'].sum():,.0f}")

    # confronto con censimento comunale 2023 (stesse fonti, granularita' diverse)
    s = pd.read_csv(f"{COM_DIR}/cens_sesso_eta_cittadinanza_decoded.csv")
    s23 = s[(s["TIME_PERIOD"] == 2023)
            & (s["AGE_NOCLASS"].astype(str).str.fullmatch(r"Y\d+|Y_GE\d+"))
            & (s["GENDER"].isin(["M", "F"]))]
    for cit_sez, cit_com, lbl in [(None, "TOTAL", "totale"),
                                  ("FRG", "FRGAPO", "stranieri")]:
        sez_v = (z2 if cit_sez else z1)
        sez_tot = (sez_v[sez_v["cittadinanza"] == "FRG"]["count"].sum()
                   if cit_sez else z1["count"].sum())
        com_tot = s23[s23["CITIZENSHIP"] == cit_com]["OBS_VALUE"].sum()
        print(f"[audit] {lbl}: sezioni {sez_tot:,.0f} vs comunale 2023 "
              f"{com_tot:,.1f} (scarto {sez_tot-com_tot:+,.1f})")

    # top-5 quartieri per quota stranieri (sanity qualitativa)
    q = z2.groupby(["zona", "cittadinanza"])["count"].sum().unstack()
    q["quota_frg"] = q["FRG"] / (q["FRG"] + q["ITL"])
    q = q.join(nomi.set_index("zona")).sort_values("quota_frg", ascending=False)
    print("\n[sanity] top-5 quartieri per quota stranieri:")
    print(q.head(5)[["nome", "quota_frg"]].round(3).to_string())
    print(f"\n[done] tabelle in {OUT_DIR}")


if __name__ == "__main__":
    main()
