"""Carta d'identità delle 12 zone ASC1 di Cesena: P1 e sezioni dal
censuario 2023, centroidi dalle geometrie 2021. Due aggregazioni
indipendenti sulla stessa chiave COM_ASC1: se le zone non coincidono
fra le due fonti, lo dice l'outer join, non un silenzio."""
import geopandas as gpd
import pandas as pd
import gsp.common as G

# --- lato censuario: P1 e n. sezioni per zona
sez = pd.read_csv("data/submun/cesena_sezioni_2023.csv")
cens = (sez.groupby("COM_ASC1")
           .agg(P1=("P1", "sum"), n_sez=("P1", "size")))

# --- lato geometrie: centroidi per zona
s = gpd.read_file(G.path_shp("emilia_romagna"))
s = s[s.PRO_COM == G.procom("040007")]
geo = s.dissolve(by="COM_ASC1")
cent = geo.geometry.centroid
geo = pd.DataFrame({"x": cent.x.round(0), "y": cent.y.round(0)},
                   index=geo.index)

# --- incontro sulla chiave, outer: le divergenze devono vedersi
t = cens.join(geo, how="outer").sort_values("P1", ascending=False)
print(t.to_string())
print(f"\nP1 totale: {int(t['P1'].sum()):,}  (atteso 96.066)")
print(f"zone censuario: {cens.shape[0]}  zone geometrie: {geo.shape[0]}")