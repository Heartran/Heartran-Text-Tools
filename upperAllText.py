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
import os

# Variabile di controllo per mettere in pausa o riavviare il controllo degli appunti
running = True

def get_active_window_title():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except Exception as e:
        return "Unknown"

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
            
            # Controlla se il testo attuale non è tutto in maiuscolo e è diverso dall'ultimo testo convertito
            if current_text != last_text and current_text != current_text.upper():
                print(f"[DEBUG] Text is not uppercase and differs from last_text. Converting to uppercase.")
                # Aggiorna lo stato
                status_label.config(text="❌ Conversione in corso")
                # Converte il testo in maiuscolo
                upper_text = current_text.upper()
                # Salva il testo convertito negli appunti
                pyperclip.copy(upper_text)
                print(f"[DEBUG] Converted text to uppercase and copied to clipboard: '{upper_text}'")
                # Aggiorna l'ultimo testo
                last_text = upper_text
                last_metadata = snapshot_metadata
                # Aggiorna lo stato
                status_label.config(text="✅ Convertito")
            else:
                print(f"[DEBUG] No conversion needed. Updating last_text.")
                # Aggiorna l'ultimo testo per evitare riconversioni inutili
                last_text = current_text
                # Aggiorna lo stato
                if current_text == current_text.upper():
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
    # Creazione della finestra principale
    root = tk.Tk()
    root.title("Clipboard Monitor")
    root.geometry("800x500")
    root.minsize(800, 500)
    root.maxsize(1000, 700)
    
    # Creazione della textbox per mostrare l'ultimo appunto copiato
    textbox = tk.Text(root, wrap='word', height=10, state=tk.DISABLED)
    textbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
    
    # Creazione dell'etichetta per mostrare i metadati dell'ultimo appunto copiato
    metadata_label = tk.Label(root, text="Provenienza: Unknown\nData e ora: ", anchor="w", justify="left")
    metadata_label.pack(pady=5, padx=20, fill=tk.X)
    
    # Creazione dell'etichetta per mostrare lo stato dell'ultimo appunto copiato
    status_label = tk.Label(root, text="❌ Non convertito", anchor="w", justify="left")
    status_label.pack(pady=5, padx=20, fill=tk.X)
    
    # Creazione del pulsante per mettere in pausa o riavviare il controllo degli appunti
    toggle_button = ttk.Button(root, text="⏯️", command=lambda: toggle_running(toggle_button))
    toggle_button.pack(pady=10, side="bottom")
    toggle_button.config(width=25)  # Imposta una larghezza maggiore per rendere il pulsante più grande e visibile
    
    # Avvio del thread per monitorare gli appunti
    threading.Thread(target=update_clipboard_content, args=(textbox, metadata_label, status_label), daemon=True).start()
    
    # Avvio della finestra principale
    root.mainloop()

if __name__ == "__main__":
    main()
