"""
build_sezioni.py — estrae le sezioni di censimento 2023 di un comune dal file
regionale ISTAT, con validazione e cache.

Sostituisce l'estrazione manuale con cui sono stati prodotti
brescia_sezioni_2023.csv e bologna_sezioni_2023.csv:

    d = pd.read_excel(<file regionale>)
    d[d.PROCOM == <procom>].to_csv(...)

Aggiunge: cache Parquet del file regionale (il caricamento xlsx costa ~40 s
e da una regione si estraggono piu' comuni), profilo dei livelli ASC
effettivamente popolati, controlli di annidamento e di coerenza dei totali.

Nota sui livelli ASC:
    il tracciato ISTAT definisce COM_ASC1/2/3 come sub-aree amministrative
    "ove presenti". La disponibilita' varia per comune: Bologna pubblica piu'
    di un livello (ASC1 = 6 quartieri, ASC2 = 18 zone), Parma soltanto il
    primo (ASC2 e ASC3 valgono 0). Brescia (33) e Modena (4) sono registrati
    sul solo ASC1. Lo script riporta esplicitamente quali livelli sono
    utilizzabili, perche' e' questo a determinare il valore ammesso di
    --level in build_zona_tables.py.

Uso:
    python build_sezioni.py 034027                      # Parma
    python build_sezioni.py 037006 --out bologna_sezioni_2023.csv
    python build_sezioni.py 017029 --file R03_Lombardia_2023_sezioni.xlsx
    python build_sezioni.py 034027 --dry-run            # solo diagnostica
"""

import argparse
import os
import sys
import time

import pandas as pd

import gsp.common as G

SUBMUN = G.SUBMUN
DATA_DIR = os.path.join(SUBMUN, "Dati_regionali_2023")
CACHE_DIR = os.path.join(SUBMUN, ".cache")

ASC_COLS = ["COM_ASC1", "COM_ASC2", "COM_ASC3"]
KEY_COLS = ["CODREG", "REGIONE", "CODPRO", "PROVINCIA", "CODCOM",
            "COMUNE", "PROCOM", "SEZ21_ID"]





def load_regionale(xlsx_path: str) -> pd.DataFrame:
    """Carica il file regionale, usando una cache Parquet se disponibile."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(xlsx_path))[0]
    cache = os.path.join(CACHE_DIR, base + ".parquet")

    if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(xlsx_path):
        t = time.time()
        d = pd.read_parquet(cache)
        print(f"[load] cache: {os.path.basename(cache)} "
              f"({d.shape[0]:,}x{d.shape[1]}, {time.time()-t:.1f}s)")
        return d

    print(f"[load] leggo {os.path.basename(xlsx_path)} (~40 s, poi in cache)")
    t = time.time()
    d = pd.read_excel(xlsx_path)
    print(f"[load] {d.shape[0]:,} righe x {d.shape[1]} colonne ({time.time()-t:.0f}s)")
    try:
        d.to_parquet(cache, index=False)
        print(f"[load] cache scritta: {cache}")
    except Exception as exc:                      # pyarrow assente, disco pieno...
        print(f"[load] cache non scritta ({exc})")
    return d


def profila_asc(sez: pd.DataFrame) -> list[str]:
    """Riporta quali livelli ASC sono popolati; ritorna quelli utilizzabili."""
    validi = []
    print("\n[asc] livelli sub-comunali:")
    for col in ASC_COLS:
        if col not in sez.columns:
            print(f"  {col}: colonna assente")
            continue
        v = pd.to_numeric(sez[col], errors="coerce").fillna(0).astype("int64")
        nz = int((v != 0).sum())
        n_dist = int(v[v != 0].nunique())
        if nz == 0:
            print(f"  {col}: NON DISPONIBILE (tutti zero)")
        elif nz < len(sez):
            print(f"  {col}: PARZIALE — {n_dist} zone, ma {len(sez)-nz} "
                  f"sezioni su {len(sez)} senza codice")
            validi.append(col)
        else:
            print(f"  {col}: {n_dist} zone, tutte le sezioni codificate")
            validi.append(col)
    if not validi:
        print("  !! nessun livello ASC utilizzabile: il comune non e' "
              "articolabile in zone")
    return validi

def check_speciali(sez: pd.DataFrame) -> None:
    """Sezioni speciali (convivenze): codici 888888/999999 nel SEZ21_ID."""
    sp = sez["SEZ21_ID"].astype(str).str.contains("888888|999999", na=False)
    if not sp.any():
        print("\n[spec] nessuna sezione speciale 888888/999999")
        return
    s = sez[sp]
    print(f"\n[spec] {len(s)} sezioni speciali (convivenze), "
          f"P1 = {int(s['P1'].sum()):,} ({s['P1'].sum()/sez['P1'].sum():.2%} del comune)")
    for _, r in s.iterrows():
        tot = int(r["P1"])
        if tot == 0:
            print(f"  {r['SEZ21_ID']}  P1=0 (sezione speciale vuota)")
            continue
        m, f = int(r["P2"]), int(r["P3"])
        st = int(r["ST1"]) if "ST1" in s.columns else 0
        zone = "  ".join(f"{c[-4:]}={r[c]}" for c in ASC_COLS
                         if c in s.columns and r[c] != 0)
        print(f"  {r['SEZ21_ID']}  {zone}  P1={tot:,}  "
              f"M/F={m}/{f}  stranieri={st} ({st/tot:.0%})")

    print("  nota: profilo demografico anomalo (caserme, studentati, RSA, "
          "centri di accoglienza). Mantenute nel file; la scelta se "
          "escluderle a valle deve essere la stessa per tutti i comuni.")


def valida(sez: pd.DataFrame, validi: list[str]) -> None:
    """Controlli su totali, annidamento gerarchico e sezioni vuote."""
    pop = int(sez["P1"].sum())
    print(f"\n[val] popolazione P1 = {pop:,} su {len(sez):,} sezioni")

    n_vuote = int((sez["P1"] == 0).sum())
    if n_vuote:
        print(f"[val] {n_vuote} sezioni con P1 = 0 (non residenziali): "
              f"mantenute nel file, da filtrare a valle se serve")

    # coerenza P1 = P2 + P3
    scarto = int((sez["P1"] - sez["P2"] - sez["P3"]).abs().sum())
    print(f"[val] P1 - (P2+P3): scarto totale {scarto} "
          f"({'ok' if scarto == 0 else 'ANOMALIA'})")
    
    if "ST1" in sez.columns:
        st = int(sez["ST1"].sum())
        print(f"[val] ST1 stranieri = {st:,} ({st/pop:.1%} della popolazione)")


    for col in validi:
        g = sez.groupby(col)["P1"].agg(["size", "sum"])
        print(f"\n[val] {col}: {len(g)} zone | "
              f"pop min {g['sum'].min():,} max {g['sum'].max():,} | "
              f"somma {g['sum'].sum():,} "
              f"({'ok' if g['sum'].sum() == pop else 'ANOMALIA'})")

    # annidamento: ogni zona di livello fine deve stare in una sola zona grossa
    for fine, grossa in [("COM_ASC2", "COM_ASC1"), ("COM_ASC3", "COM_ASC2")]:
        if fine in validi and grossa in validi:
            n = sez.groupby(fine)[grossa].nunique()
            rotti = n[n > 1]
            if len(rotti):
                print(f"[val] !! {fine} -> {grossa}: {len(rotti)} zone "
                      f"appartengono a piu' zone superiori: {list(rotti.index)[:5]}")
            else:
                print(f"[val] {fine} -> {grossa}: annidamento coerente")


def main(comune, file_arg, regione_arg, out_arg, dry_run):
    if len(comune) != 6 or not comune.isdigit():
        sys.exit("Il codice comune deve avere sei cifre (es. 034027).")
    procom = G.procom(comune)
    info = G.COMUNI.get(comune, {})

    if file_arg:
        xlsx = file_arg if os.path.isabs(file_arg) else os.path.join(DATA_DIR, file_arg)
    elif regione_arg:                       # override: codice regione ISTAT
        if regione_arg not in G.REGIONE_FILE:
            sys.exit(f"Codice regione {regione_arg} sconosciuto.")
        xlsx = os.path.join(DATA_DIR, G.REGIONE_FILE[regione_arg])
    elif info:
        xlsx = G.path_regionale_xlsx(info["regione"])
    else:
        sys.exit(f"Comune {comune} non nel registro di gsp_common.py: "
                 f"indicare --regione <codice ISTAT> oppure --file <xlsx>.")

    if not os.path.exists(xlsx):
        sys.exit(f"File regionale assente: {xlsx}\n"
                 f"  estrarlo da Dati_regionali_2023.zip in {SUBMUN}")

    d = load_regionale(xlsx)

    mancanti = [c for c in KEY_COLS + ["P1", "P2", "P3"] if c not in d.columns]
    if mancanti:
        sys.exit(f"Colonne attese assenti nel file regionale: {mancanti}")

    # ---- filtro del comune ----
    sez = d[pd.to_numeric(d["PROCOM"], errors="coerce") == procom].copy()
    if sez.empty:
        disp = sorted(d["COMUNE"].dropna().unique())[:10]
        sys.exit(f"PROCOM {procom} assente in {os.path.basename(xlsx)}.\n"
                 f"  Regione sbagliata? Comuni presenti (primi 10): {disp}")

    nome = str(sez["COMUNE"].iloc[0])
    print(f"\n[com] {nome} (PROCOM {procom}) — {len(sez):,} sezioni")
    print(f"[com] {sez['REGIONE'].iloc[0]} / {sez['PROVINCIA'].iloc[0]}")
    if info.get("nome") and info["nome"].lower() != nome.lower():
        print(f"[com] !! atteso '{info['nome']}', trovato '{nome}': "
              f"verificare il codice comune")

    validi = profila_asc(sez)
    check_speciali(sez)
    valida(sez, validi)

    # ---- livello zonale: dal registro, non da default ----
    liv = None
    atteso = None
    if info and info.get("livello"):
        liv = G.livello_col(comune)
        atteso = info["livelli"][info["livello"]]["n"]

    if liv is None:
        print(f"\n[out] livello non fissato nel registro per {comune}.")
        print(f"[out] livelli disponibili: {', '.join(validi) or 'nessuno'}")
        print(f"[out] scegliere guardando pop/zona qui sopra e aggiungerlo "
              f"a COMUNI in gsp_common.py prima di procedere a valle")
    elif liv not in validi:
        sys.exit(f"\n[out] il registro chiede {liv}, ma per {nome} i livelli "
                 f"disponibili sono {validi}")
    else:
        nz = int(sez.loc[sez[liv] != 0, liv].nunique())
        print(f"\n[out] livello zonale: {liv} — {nz} zone")
        if atteso and nz != atteso:
            sys.exit(f"[out] !! attese {atteso} zone, trovate {nz}: "
                     f"il file regionale e' cambiato, verificare prima di procedere")
        
        
        # nessuna colonna derivata: il livello effettivo lo sceglie
        # build_zona_tables.py dal proprio registro. Qui solo verifica.

    if dry_run:
        print("\n[dry-run] nessun file scritto")
        return

    out_name = out_arg or (f"{info['slug']}_sezioni_{G.ANNO_SEZIONI}.csv"
                           if info else
                           f"{nome.lower().replace(' ', '_')}_sezioni_"
                           f"{G.ANNO_SEZIONI}.csv")
    out = os.path.join(SUBMUN, out_name)
    if os.path.exists(out):
        sys.exit(f"{out} esiste gia': rimuoverlo o usare --out")
    sez.to_csv(out, index=False)                  # virgola, come bologna_*.csv
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Estrae le sezioni di censimento 2023 di un comune "
                    "dal file regionale ISTAT.")
    ap.add_argument("comune", help="codice ISTAT a sei cifre (es. 034027)")
    ap.add_argument("--file", help="file regionale xlsx (override del registro)")
    ap.add_argument("--regione", type=int,
                    help="codice regione ISTAT, se il comune non e' nel registro")
    ap.add_argument("--out", help="nome del CSV di output [<comune>_sezioni_2023.csv]")
    ap.add_argument("--dry-run", action="store_true",
                    help="esegue solo diagnostica e validazione")
    x = ap.parse_args()
    main(x.comune, x.file, x.regione, x.out, x.dry_run)
