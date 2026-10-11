"""gsp.banco — il banco di prova: corse sperimentali della catena, isolate.

    python -m gsp.banco nuovo 040007 --etichetta senza_Z3 --senza Z3
    python -m gsp.banco lancia 040007_senza_Z3_20261011a
    python -m gsp.banco elenca
    python -m gsp.banco replica 040007_senza_Z3_20261011a

PERCHE' ESISTE. Le popolazioni in data/comuni/ sono quelle citate dal
report e non si toccano. Ogni esperimento -- togliere un blocco, cambiare
un seme, accorpare categorie -- ha bisogno di una cartella propria, di un
manifesto che dica che cosa e' cambiato rispetto alla produzione e di un
esito che permetta di rifarlo byte per byte. Qui sta tutto questo e
nient'altro: il banco lancia gli script esistenti della catena, nello
stesso ordine e con gli stessi flag di rigenera.sh, puntandoli a una
cartella isolata tramite GSP_COMUNI_DIR.

L'UNITA' E' L'ESPERIMENTO: un file esperimento.yaml (vedi `manifesto`)
con le manopole dichiarate come DIFFERENZE dalla produzione, e un blocco
`esito` che scrive solo il runner. Una corsa finita non si sovrascrive:
si fa una corsa nuova.

DOVE SCRIVE. GSP_BANCO_DIR (default ~/progetti/laboratorio), mai dentro
il repo: il runner rifiuta di partire altrimenti.

Il disegno e le decisioni stanno in note/laboratorio_design_vNN.md.
"""
import os

RADICE = os.path.expanduser(os.environ.get("GSP_BANCO_DIR",
                                           "~/progetti/laboratorio"))
CORSE = os.path.join(RADICE, "corse")
