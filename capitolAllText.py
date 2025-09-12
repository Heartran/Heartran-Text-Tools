# fix_nomi_clipboard.py
# Trasforma il testo negli appunti in "Title Case" per nomi/cognomi
# e rimette il risultato negli appunti (Windows/macOS/Linux).
# Uso: copia -> python fix_nomi_clipboard.py -> incolla

import re
import sys
try:
    import pyperclip
except ImportError:
    print("Devi installare pyperclip:  pip install pyperclip")
    sys.exit(1)

# Particelle da mantenere minuscole (se NON sono la prima parola/frammento)
PARTICELLE = {
    "di", "de", "del", "della", "dello", "delle", "dei", "degli",
    "da", "van", "von", "der", "den", "dos", "das", "du",
    "le", "la", "lo"
}
# Forme con apostrofo da NON forzare minuscole (es: D'Angelo, L'Amato)
APOSTROFO_KEEP_CASE = ("d'", "l'")

def smart_title_word(word: str, is_first: bool) -> str:
    """
    Converte una singola parola in Title Case con regole per nomi:
    - tiene minuscole le particelle (di, de, van...) se non sono la prima parola
    - gestisce apostrofi italiani (D'Angelo, L'Amato)
    - gestisce parti con trattino (Es: Jean-Luc -> Jean-Luc)
    - fix per 'McDonald' (da Mcdonald)
    """
    if not word:
        return word

    # Se contiene trattini, elabora ogni parte
    if "-" in word:
        parts = word.split("-")
        parts = [smart_title_word(p, is_first and i == 0) for i, p in enumerate(parts)]
        return "-".join(parts)

    w = word.lower()

    # Se è una particella e non è la prima parola -> minuscolo
    if (not is_first) and (w in PARTICELLE):
        return w

    # Apostrofo: se è tipo d'/l' mantieni D'/L' + parte dopo con iniziale maiuscola
    for pref in APOSTROFO_KEEP_CASE:
        if w.startswith(pref):
            after = w[len(pref):]
            # Esempio: d'angelo -> D' + Angelo
            return pref[0].upper() + pref[1:] + after.capitalize()

    # Title case standard
    w = w.capitalize()

    # Fix 'Mc' -> McDonald
    if w.startswith("Mc") and len(w) > 2:
        w = "Mc" + w[2:].capitalize()

    return w

def smart_title_name(text: str) -> str:
    """
    Applica smart_title_word a tutte le parole preservando spazi multipli
    e nuove righe. Funziona bene su blocchi di testo (elenco di nomi).
    """
    def repl(match):
        word = match.group(0)
        # Determina se è "prima parola" rispetto all'inizio della riga
        # Guardiamo il testo prima della parola fino al precedente newline.
        start = match.start()
        prev_nl = text.rfind("\n", 0, start)
        row_start = 0 if prev_nl == -1 else prev_nl + 1
        is_first = text[row_start:start].strip() == ""
        return smart_title_word(word, is_first)

    # Sostituisce solo sequenze alfanumeriche con lettere (comprende accenti)
    # Mantiene spazi, punteggiatura e
