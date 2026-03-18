import pyperclip
import time
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import win32gui
import win32process
import psutil

from ui_theme import ACCENT, ACCENT_HOVER, CARD_BG, SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, apply_modern_theme, create_card, configure_text_widget

running = True


def get_active_window_title():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except Exception:
        return "Unknown"


def update_clipboard_content(textbox, metadata_label, status_label):
    global running
    last_text = ""
    last_metadata = ""
    snapshot_metadata = ""

    while True:
        if running:
            current_text = pyperclip.paste()
            print(f"[DEBUG] Current clipboard content: '{current_text}'")

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

            if current_text != last_text and current_text != current_text.upper():
                print("[DEBUG] Text is not uppercase and differs from last_text. Converting to uppercase.")
                status_label.config(text="Conversione in corso", fg='#b45309')
                upper_text = current_text.upper()
                pyperclip.copy(upper_text)
                print(f"[DEBUG] Converted text to uppercase and copied to clipboard: '{upper_text}'")
                last_text = upper_text
                last_metadata = snapshot_metadata
                status_label.config(text="Convertito", fg=SUCCESS)
            else:
                print("[DEBUG] No conversion needed. Updating last_text.")
                last_text = current_text
                if current_text == current_text.upper():
                    status_label.config(text="Convertito", fg=SUCCESS)
                else:
                    status_label.config(text="Non convertito", fg='#b91c1c')

            textbox.config(state=tk.NORMAL)
            textbox.delete(1.0, tk.END)
            textbox.insert(tk.END, last_text)
            textbox.config(state=tk.DISABLED)

            if snapshot_metadata:
                metadata_label.config(text=last_metadata)

        time.sleep(0.5)


def toggle_running(toggle_button, pill):
    global running
    running = not running
    print(f"[DEBUG] Clipboard monitoring {'resumed' if running else 'paused'}.")
    if running:
        toggle_button.config(text="Metti in pausa")
        pill.config(text="Monitor attivo", bg='#dcfce7', fg=SUCCESS)
    else:
        toggle_button.config(text="Riprendi monitor")
        pill.config(text="Monitor in pausa", bg='#fef3c7', fg='#b45309')


def main():
    root = tk.Tk()
    root.title("Monitor Clipboard - MAIUSCOLO")
    root.geometry("920x640")
    root.minsize(820, 560)
    apply_modern_theme(root)

    shell = ttk.Frame(root, style='App.TFrame', padding=24)
    shell.pack(fill=tk.BOTH, expand=True)

    header = ttk.Frame(shell, style='App.TFrame')
    header.pack(fill=tk.X, pady=(0, 16))
    ttk.Label(header, text="MAIUSCOLO automatico", style='HeroTitle.TLabel').pack(anchor='w')
    ttk.Label(header, text="Una finestra più moderna per seguire il testo appena convertito, lo stato del monitor e i metadati del contenuto copiato.", style='HeroBody.TLabel', wraplength=700, justify=tk.LEFT).pack(anchor='w', pady=(8, 0))

    pill = tk.Label(header, text="Monitor attivo", bg='#dcfce7', fg=SUCCESS, font=('Segoe UI Semibold', 10), padx=14, pady=8)
    pill.pack(anchor='e', pady=(10, 0))

    preview_card = create_card(shell, padding=20)
    preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
    tk.Label(preview_card, text="Anteprima live", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 16)).pack(anchor='w')
    tk.Label(preview_card, text="Il testo mostrato qui sotto viene aggiornato in tempo reale non appena il monitor rileva un nuovo contenuto negli appunti.", bg=CARD_BG, fg=TEXT_SECONDARY, font=('Segoe UI', 10), wraplength=760, justify=tk.LEFT).pack(anchor='w', pady=(6, 14))

    textbox = tk.Text(preview_card, wrap='word', height=12)
    configure_text_widget(textbox, readonly=True)
    textbox.pack(fill=tk.BOTH, expand=True)

    bottom_row = ttk.Frame(shell, style='App.TFrame')
    bottom_row.pack(fill=tk.BOTH, expand=False)
    bottom_row.columnconfigure(0, weight=3)
    bottom_row.columnconfigure(1, weight=2)

    metadata_card = create_card(bottom_row, padding=20)
    metadata_card.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
    tk.Label(metadata_card, text="Dettagli clipboard", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 15)).pack(anchor='w')
    metadata_label = tk.Label(metadata_card, text="Provenienza: Unknown\nData e ora: --\nFormato: --\nDimensione: --", bg=CARD_BG, fg=TEXT_SECONDARY, font=('Segoe UI', 10), justify='left', anchor='w')
    metadata_label.pack(anchor='w', pady=(10, 0), fill=tk.X)

    actions_card = create_card(bottom_row, padding=20)
    actions_card.grid(row=0, column=1, sticky='nsew')
    tk.Label(actions_card, text="Controlli", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 15)).pack(anchor='w')
    status_label = tk.Label(actions_card, text="Non convertito", bg=CARD_BG, fg='#b91c1c', font=('Segoe UI Semibold', 11), anchor='w')
    status_label.pack(anchor='w', pady=(10, 16), fill=tk.X)

    toggle_button = tk.Button(actions_card, text="Metti in pausa", command=lambda: toggle_running(toggle_button, pill), bg=ACCENT, fg='white', activebackground=ACCENT_HOVER, activeforeground='white', relief='flat', bd=0, padx=18, pady=10, cursor='hand2', font=('Segoe UI Semibold', 10))
    toggle_button.pack(anchor='w')

    threading.Thread(target=update_clipboard_content, args=(textbox, metadata_label, status_label), daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()
