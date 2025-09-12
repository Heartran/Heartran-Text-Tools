import pyperclip
import time
import threading
import tkinter as tk
from tkinter import StringVar
from tkinter import ttk
from datetime import datetime
import win32gui
import win32process
import psutil
import re
import sys

# Variabile di controllo per mettere in pausa o riavviare il controllo degli appunti
running = True

# Particelle da mantenere minuscole (se NON sono la prima parola/frammento)
PARTICELLE = {
    "di", "de", "del", "della", "dello", "delle", "dei", "degli",
    "da", "van", "von", "der", "den", "dos", "das", "du",
    "le", "la", "lo"
}
# Forme con apostrofo da NON forzare minuscole (es: D'Angelo, L'Amato)
APOSTROFO_KEEP_CASE = ("d'", "l'")

def get_active_window_title():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except Exception as e:
        return "Unknown"

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
    if not text.strip():
        return text
        
    def repl(match):
        word = match.group(0)
        # Determina se è "prima parola" rispetto all'inizio della riga
        start = match.start()
        prev_nl = text.rfind("\n", 0, start)
        row_start = 0 if prev_nl == -1 else prev_nl + 1
        is_first = text[row_start:start].strip() == ""
        return smart_title_word(word, is_first)

    # Sostituisce sequenze di lettere (inclusi accenti)
    pattern = re.compile(r'[\w\u00C0-\u017F\-\']+', re.UNICODE)
    result = pattern.sub(repl, text)
    return result

def update_clipboard_content(textbox, metadata_label, status_label):
    global running
    last_text = ""
    last_metadata = ""
    snapshot_metadata = ""
    
    while True:
        if running:
            # Legge il contenuto degli appunti
            current_text = pyperclip.paste()
            print(f"[DEBUG] Current clipboard content: '{current_text}'")
            
            # Ottiene i metadati dell'appunto
            if current_text != last_text:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                source_app = get_active_window_title()
                text_size = len(current_text.encode('utf-8'))
                text_format = "Testo" if isinstance(current_text, str) else "Sconosciuto"
                snapshot_metadata = (
                    f"Provenienza: {source_app}\n"
                    f"Data e ora: {current_time}\n"
                    f"Formato: {text_format}\n"
                    f"Dimensione: {text_size} byte"
                )
            
            # Controlla se il testo è cambiato e ha bisogno di essere convertito
            if current_text != last_text and current_text != smart_title_name(current_text):
                print(f"[DEBUG] Text needs title case conversion.")
                # Aggiorna lo stato
                status_label.config(text="🔄 Conversione in corso")
                # Converte il testo in title case
                converted_text = smart_title_name(current_text)
                # Salva il testo convertito negli appunti
                pyperclip.copy(converted_text)
                print(f"[DEBUG] Converted text to title case and copied to clipboard: '{converted_text}'")
                # Aggiorna l'ultimo testo
                last_text = converted_text
                last_metadata = snapshot_metadata
                # Aggiorna lo stato
                status_label.config(text="✅ Convertito")
            else:
                print(f"[DEBUG] No conversion needed. Updating last_text.")
                # Aggiorna l'ultimo testo per evitare riconversioni inutili
                last_text = current_text
                # Aggiorna lo stato
                if current_text == smart_title_name(current_text):
                    status_label.config(text="✅ Convertito")
                else:
                    status_label.config(text="❌ Non convertito")
            
            # Aggiorna il contenuto della textbox nella finestra
            textbox.config(state=tk.NORMAL)
            textbox.delete(1.0, tk.END)
            textbox.insert(tk.END, last_text)
            textbox.config(state=tk.DISABLED)
            
            # Aggiorna il contenuto dell'etichetta dei metadati solo se c'è stato un cambiamento
            if snapshot_metadata:
                metadata_label.config(text=last_metadata)
        
        # Aspetta un attimo per evitare un utilizzo eccessivo della CPU
        time.sleep(0.5)

def toggle_running(toggle_button):
    global running
    running = not running
    print(f"[DEBUG] Clipboard monitoring {'resumed' if running else 'paused'}.")
    # Aggiorna il testo del pulsante con l'emoji play/pause
    if running:
        toggle_button.config(text="⏯️ Pausa Monitoraggio")
    else:
        toggle_button.config(text="⏯️ Riprendi Monitoraggio")

def main():
    # Verifica se pyperclip è installato
    try:
        import pyperclip
    except ImportError:
        print("Errore: pyperclip non è installato. Installalo con: pip install pyperclip")
        sys.exit(1)
    
    # Creazione della finestra principale
    root = tk.Tk()
    root.title("Converti Nomi in Maiuscolo Intelligente")
    root.geometry("600x500")
    
    # Frame principale con padding
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Etichetta per lo stato
    status_label = ttk.Label(main_frame, text="✅ Pronto", font=('Arial', 10, 'bold'))
    status_label.pack(pady=5, anchor='w')
    
    # Etichetta per i metadati
    metadata_label = ttk.Label(main_frame, text="Nessun contenuto recente", justify=tk.LEFT)
    metadata_label.pack(pady=5, anchor='w')
    
    # Etichetta per il testo convertito
    ttk.Label(main_frame, text="Testo convertito:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 0))
    
    # Area di testo per mostrare il contenuto convertito
    text_display = tk.Text(main_frame, wrap=tk.WORD, height=15, padx=5, pady=5)
    text_display.pack(fill=tk.BOTH, expand=True, pady=5)
    text_display.config(state=tk.DISABLED)  # Disabilita la modifica
    
    # Barra di scorrimento
    scrollbar = ttk.Scrollbar(text_display)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_display.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=text_display.yview)
    
    # Pulsante per mettere in pausa/riprendere il monitoraggio
    toggle_button = ttk.Button(
        main_frame, 
        text="⏯️ Pausa Monitoraggio",
        command=lambda: toggle_running(toggle_button)
    )
    toggle_button.pack(pady=10)
    
    # Avvia il thread per il monitoraggio degli appunti
    clipboard_thread = threading.Thread(
        target=update_clipboard_content,
        args=(text_display, metadata_label, status_label),
        daemon=True
    )
    clipboard_thread.start()
    
    # Gestione della chiusura della finestra
    def on_closing():
        global running
        running = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Avvia il loop principale dell'interfaccia
    root.mainloop()

if __name__ == "__main__":
    main()
