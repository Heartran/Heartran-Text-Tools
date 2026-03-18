import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import subprocess
import os
import sys
import tempfile
import atexit
import time
import threading
import shutil
from pathlib import Path

from ui_theme import (
    ACCENT,
    ACCENT_HOVER,
    CARD_BG,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WINDOW_BG,
    apply_modern_theme,
    bind_responsive_layout,
    bind_responsive_wrap,
    create_card,
    configure_text_widget,
)

try:
    from PIL import ImageGrab, Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    pytesseract = None
    HAS_PYTESSERACT = False

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

TESSERACT_DIR = BASE_DIR / 'redist' / 'tesseract-5.5.1'
TESSERACT_EXE_NAME = 'tesseract.exe' if os.name == 'nt' else 'tesseract'
TESSERACT_EXE = TESSERACT_DIR / TESSERACT_EXE_NAME
HAS_TESSERACT_CMD = False

if HAS_PYTESSERACT:
    candidate_paths = []
    if TESSERACT_EXE.exists():
        candidate_paths.append(TESSERACT_EXE)

    env_keys = ("TESSERACT_PATH", "TESSERACT_HOME", "TESSERACT_EXE", "TESSERACT_EXE_PATH")
    for key in env_keys:
        value = os.environ.get(key)
        if not value:
            continue
        env_path = Path(value)
        if env_path.is_dir():
            env_path = env_path / TESSERACT_EXE_NAME
        if env_path.exists():
            candidate_paths.append(env_path)

    program_files = os.environ.get("PROGRAMFILES")
    if program_files:
        pf_path = Path(program_files) / "Tesseract-OCR" / TESSERACT_EXE_NAME
        if pf_path.exists():
            candidate_paths.append(pf_path)

    program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
    if program_files_x86:
        pf86_path = Path(program_files_x86) / "Tesseract-OCR" / TESSERACT_EXE_NAME
        if pf86_path.exists():
            candidate_paths.append(pf86_path)

    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        la_path = Path(localappdata) / "Programs" / "Tesseract-OCR" / TESSERACT_EXE_NAME
        if la_path.exists():
            candidate_paths.append(la_path)

    unique_cmds = []
    for path_cmd in candidate_paths:
        cmd_str = str(path_cmd)
        if cmd_str not in unique_cmds:
            unique_cmds.append(cmd_str)

    tess_cmd_candidate = None
    if unique_cmds:
        tess_cmd_candidate = unique_cmds[0]
    else:
        fallback_cmd = shutil.which('tesseract')
        if fallback_cmd:
            tess_cmd_candidate = fallback_cmd

    if tess_cmd_candidate:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd_candidate
        HAS_TESSERACT_CMD = True

HAS_WIN32 = os.name == 'nt'


class ToolLock:
    """Class to handle tool locking to prevent multiple instances"""
    _instance = None
    _locks = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolLock, cls).__new__(cls)
            cls._temp_dir = tempfile.gettempdir()
            atexit.register(cls.cleanup)
        return cls._instance

    @classmethod
    def is_locked(cls, tool_name):
        """Check if a tool is already running"""
        lock_file = os.path.join(cls._temp_dir, f"heartran_{tool_name}.lock")
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as file_handle:
                    pid = int(file_handle.read().strip())
                try:
                    os.kill(pid, 0)
                    return True
                except (ProcessLookupError, PermissionError):
                    os.unlink(lock_file)
                    return False
            except (ValueError, PermissionError):
                return False
        return False

    @classmethod
    def acquire_lock(cls, tool_name):
        """Acquire a lock for a tool"""
        if cls.is_locked(tool_name):
            return False

        lock_file = os.path.join(cls._temp_dir, f"heartran_{tool_name}.lock")
        try:
            with open(lock_file, 'w') as file_handle:
                file_handle.write(str(os.getpid()))
            cls._locks[tool_name] = lock_file
            return True
        except (IOError, OSError):
            return False

    @classmethod
    def release_lock(cls, tool_name):
        """Release a lock for a tool"""
        lock_file = os.path.join(cls._temp_dir, f"heartran_{tool_name}.lock")
        try:
            if os.path.exists(lock_file):
                os.unlink(lock_file)
            if tool_name in cls._locks:
                del cls._locks[tool_name]
        except (IOError, OSError):
            pass

    @classmethod
    def cleanup(cls):
        """Clean up all locks on exit"""
        for tool_name in list(cls._locks.keys()):
            cls.release_lock(tool_name)


class TextToolsLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Heartran Text Tools")
        self.root.geometry("1040x700")
        self.root.minsize(940, 640)
        self.style = apply_modern_theme(self.root)
        self.status_var = tk.StringVar(value="Pronto")
        self.quick_hint_var = tk.StringVar(value="Scegli uno strumento per iniziare.")

        try:
            self.root.iconbitmap(self.resource_path("icon.ico"))
        except Exception:
            pass

        self.setup_ui()

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def setup_ui(self):
        shell = ttk.Frame(self.root, style='App.TFrame', padding=24)
        shell.pack(fill=tk.BOTH, expand=True)

        hero = ttk.Frame(shell, style='App.TFrame')
        hero.pack(fill=tk.X, pady=(0, 20))
        hero.columnconfigure(0, weight=1)

        title_block = ttk.Frame(hero, style='App.TFrame')
        title_block.grid(row=0, column=0, sticky='ew')

        ttk.Label(title_block, text="Heartran Text Tools", style='HeroTitle.TLabel').pack(anchor='w')
        hero_body = ttk.Label(
            title_block,
            text=(
                "Una dashboard ispirata a Windows 11 per trasformare il testo negli appunti, "
                "gestire i tool e usare l'OCR con un'esperienza più pulita e leggibile."
            ),
            style='HeroBody.TLabel',
            wraplength=620,
            justify=tk.LEFT,
        )
        hero_body.pack(anchor='w', fill=tk.X, pady=(8, 0))
        bind_responsive_wrap(hero_body, title_block, padding=20, min_wrap=260)

        status_chip = tk.Label(
            hero,
            textvariable=self.status_var,
            bg=SURFACE,
            fg=ACCENT,
            font=('Segoe UI Semibold', 10),
            padx=16,
            pady=10,
        )
        status_chip.grid(row=1, column=0, sticky='e', pady=(12, 0))

        top_grid = ttk.Frame(shell, style='App.TFrame')
        top_grid.pack(fill=tk.BOTH, expand=True)
        top_grid.columnconfigure(0, weight=3)
        top_grid.columnconfigure(1, weight=2)
        top_grid.rowconfigure(0, weight=1)

        tools_card = create_card(top_grid, padding=22)
        self._build_tools_card(tools_card)

        side_panel = ttk.Frame(top_grid, style='App.TFrame')
        side_panel.columnconfigure(0, weight=1)
        side_panel.rowconfigure(0, weight=1)
        side_panel.rowconfigure(1, weight=1)

        overview_card = create_card(side_panel, padding=22)
        self._build_overview_card(overview_card)
        overview_card.grid(row=0, column=0, sticky='nsew', pady=(0, 12))

        activity_card = create_card(side_panel, padding=22)
        self._build_activity_card(activity_card)
        activity_card.grid(row=1, column=0, sticky='nsew')

        def apply_compact_top_grid():
            tools_card.grid_forget()
            side_panel.grid_forget()
            top_grid.columnconfigure(0, weight=1)
            top_grid.columnconfigure(1, weight=0)
            top_grid.rowconfigure(0, weight=3)
            top_grid.rowconfigure(1, weight=2)
            tools_card.grid(row=0, column=0, sticky='nsew', pady=(0, 12))
            side_panel.grid(row=1, column=0, sticky='nsew')

        def apply_wide_top_grid():
            tools_card.grid_forget()
            side_panel.grid_forget()
            top_grid.columnconfigure(0, weight=3)
            top_grid.columnconfigure(1, weight=2)
            top_grid.rowconfigure(0, weight=1)
            top_grid.rowconfigure(1, weight=0)
            tools_card.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
            side_panel.grid(row=0, column=1, sticky='nsew')

        bind_responsive_layout(
            top_grid,
            threshold=980,
            compact_layout=apply_compact_top_grid,
            wide_layout=apply_wide_top_grid,
        )

    def _build_tools_card(self, parent):
        tk.Label(parent, text="Strumenti", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 18)).pack(anchor='w')
        tools_body = tk.Label(
            parent,
            text="Accesso rapido ai tre flussi principali con card arrotondate, gerarchia visiva chiara e stato sempre visibile.",
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=('Segoe UI', 10),
            wraplength=520,
            justify=tk.LEFT,
        )
        tools_body.pack(anchor='w', fill=tk.X, pady=(6, 18))
        bind_responsive_wrap(tools_body, parent, padding=44, min_wrap=240)

        cards = [
            {
                'emoji': '✍️',
                'title': 'Maiuscole intelligenti',
                'description': 'Converte i nomi negli appunti in formato leggibile e coerente.',
                'cta': 'Apri tool',
                'command': self.launch_capitalize_tool,
                'hint': 'Tool nomi pronto per essere aperto.',
            },
            {
                'emoji': '⬆️',
                'title': 'MAIUSCOLO totale',
                'description': 'Trasforma il contenuto copiato in maiuscolo in tempo reale.',
                'cta': 'Avvia monitor',
                'command': self.launch_uppercase_tool,
                'hint': 'Monitor clipboard maiuscolo in apertura.',
            },
            {
                'emoji': '🖼️',
                'title': 'OCR dagli appunti',
                'description': 'Estrae testo dalle immagini già copiate senza uscire dalla dashboard.',
                'cta': 'Esegui OCR',
                'command': self.launch_ocr_tool,
                'hint': 'Analisi OCR avviata dagli appunti.',
            },
        ]

        for item in cards:
            self._build_tool_row(parent, item)

    def _build_tool_row(self, parent, item):
        row = tk.Frame(parent, bg='#f8faff', highlightthickness=1, highlightbackground='#e4eaf5', padx=18, pady=18)
        row.pack(fill=tk.X, pady=8)
        row.grid_columnconfigure(1, weight=1)

        icon = tk.Label(row, text=item['emoji'], bg='#e8f0ff', fg=ACCENT, font=('Segoe UI Emoji', 18), width=3, pady=8)
        icon.grid(row=0, column=0, sticky='nw', padx=(0, 14))

        content = tk.Frame(row, bg='#f8faff')
        content.grid(row=0, column=1, sticky='nsew')

        tk.Label(content, text=item['title'], bg='#f8faff', fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 12)).pack(anchor='w', fill=tk.X)
        description = tk.Label(
            content,
            text=item['description'],
            bg='#f8faff',
            fg=TEXT_SECONDARY,
            font=('Segoe UI', 10),
            wraplength=420,
            justify=tk.LEFT,
        )
        description.pack(anchor='w', fill=tk.X, pady=(5, 0))
        bind_responsive_wrap(description, content, padding=8, min_wrap=180)

        action = tk.Button(
            row,
            text=item['cta'],
            command=lambda i=item: self._run_action(i['command'], i['hint']),
            bg=ACCENT,
            fg='white',
            activebackground=ACCENT_HOVER,
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=18,
            pady=10,
            cursor='hand2',
            font=('Segoe UI Semibold', 10),
        )

        def apply_compact_row():
            action.grid_forget()
            icon.grid_configure(row=0, column=0, rowspan=2, padx=(0, 14), pady=(2, 0))
            content.grid_configure(row=0, column=1, columnspan=2, sticky='ew')
            action.grid(row=1, column=1, columnspan=2, sticky='w', pady=(14, 0))

        def apply_wide_row():
            action.grid_forget()
            icon.grid_configure(row=0, column=0, rowspan=1, padx=(0, 14), pady=0)
            content.grid_configure(row=0, column=1, columnspan=1, sticky='nsew')
            action.grid(row=0, column=2, sticky='e')

        bind_responsive_layout(
            row,
            threshold=640,
            compact_layout=apply_compact_row,
            wide_layout=apply_wide_row,
        )

    def _build_overview_card(self, parent):
        tk.Label(parent, text="Panoramica", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 16)).pack(anchor='w')
        overview_body = tk.Label(
            parent,
            text="Il layout segue i principi Windows 11: spaziatura generosa, superfici chiare e CTA ben evidenziate.",
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=('Segoe UI', 10),
            wraplength=280,
            justify=tk.LEFT,
        )
        overview_body.pack(anchor='w', fill=tk.X, pady=(8, 16))
        bind_responsive_wrap(overview_body, parent, padding=44, min_wrap=180)

        for label, value in (
            ('Clipboard tools', '2 monitor live'),
            ('OCR', '1 workflow integrato'),
            ('Compatibilità', 'Python / PyInstaller'),
        ):
            strip = tk.Frame(parent, bg='#f8faff', padx=14, pady=12)
            strip.pack(fill=tk.X, pady=5)
            tk.Label(strip, text=label, bg='#f8faff', fg=TEXT_SECONDARY, font=('Segoe UI', 9)).pack(anchor='w')
            tk.Label(strip, text=value, bg='#f8faff', fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 11)).pack(anchor='w', pady=(3, 0))
        return parent

    def _build_activity_card(self, parent):
        tk.Label(parent, text="Attività", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 16)).pack(anchor='w')
        activity_hint = tk.Label(
            parent,
            textvariable=self.quick_hint_var,
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=('Segoe UI', 10),
            wraplength=280,
            justify=tk.LEFT,
        )
        activity_hint.pack(anchor='w', fill=tk.X, pady=(8, 16))
        bind_responsive_wrap(activity_hint, parent, padding=44, min_wrap=180)

        self.activity_log = tk.Text(parent, height=8, wrap='word')
        configure_text_widget(self.activity_log)
        self.activity_log.pack(fill=tk.BOTH, expand=True)
        self._append_activity("Interfaccia aggiornata con una dashboard moderna in stile Windows 11.")
        self._append_activity("Usa le azioni rapide per aprire i tool o avviare l'OCR dagli appunti.")
        return parent

    def _append_activity(self, message):
        self.activity_log.insert(tk.END, f"• {message}\n")
        self.activity_log.see(tk.END)

    def _run_action(self, command, hint):
        self.quick_hint_var.set(hint)
        self._append_activity(hint)
        command()

    def launch_tool(self, script_name):
        tool_name = os.path.splitext(script_name)[0]

        if ToolLock().is_locked(tool_name):
            messagebox.showinfo(
                "Strumento già in esecuzione",
                f"Lo strumento '{tool_name}' è già in esecuzione.\nChiudi l'istanza esistente prima di aprirne una nuova."
            )
            self.status_var.set(f"{tool_name} già in esecuzione")
            return

        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
            if os.path.exists(script_path):
                if not ToolLock().acquire_lock(tool_name):
                    messagebox.showerror("Errore", f"Impossibile acquisire il lock per {tool_name}")
                    self.status_var.set("Errore di avvio")
                    return

                self.status_var.set(f"Avvio di {script_name}...")
                self.root.update()
                python = sys.executable

                def cleanup_and_launch():
                    try:
                        process = subprocess.Popen([python, script_path])
                        time.sleep(1)
                        if process.poll() is not None:
                            ToolLock().release_lock(tool_name)
                        else:
                            def monitor_process():
                                process.wait()
                                ToolLock().release_lock(tool_name)

                            threading.Thread(target=monitor_process, daemon=True).start()

                        self.root.after(0, lambda: self.status_var.set(f"{script_name} avviato con successo"))
                    except Exception as exc:
                        ToolLock().release_lock(tool_name)
                        self.root.after(0, lambda: messagebox.showerror("Errore", f"Impossibile avviare lo strumento: {exc}"))
                        self.root.after(0, lambda: self.status_var.set("Errore durante l'avvio dello strumento"))

                threading.Thread(target=cleanup_and_launch, daemon=True).start()
            else:
                messagebox.showerror("Errore", f"File non trovato: {script_name}")
                self.status_var.set("Errore: file non trovato")

        except Exception as exc:
            ToolLock().release_lock(tool_name)
            messagebox.showerror("Errore", f"Impossibile avviare lo strumento: {exc}")
            self.status_var.set("Errore durante l'avvio dello strumento")

    def launch_capitalize_tool(self):
        self.launch_tool("capitolAllText.py")

    def launch_uppercase_tool(self):
        self.launch_tool("upperAllText.py")

    def launch_ocr_tool(self):
        self.perform_ocr_from_clipboard()

    def perform_ocr_from_clipboard(self):
        if not HAS_PIL:
            messagebox.showerror("Dipendenza mancante", "La funzione OCR richiede il pacchetto Pillow.")
            self.status_var.set("OCR non disponibile (Pillow mancante)")
            return

        if not HAS_PYTESSERACT:
            messagebox.showerror("Dipendenza mancante", "La funzione OCR richiede il pacchetto pytesseract e il motore Tesseract.")
            self.status_var.set("OCR non disponibile (pytesseract mancante)")
            return

        if not HAS_TESSERACT_CMD:
            messagebox.showerror("Tesseract non configurato", "Motore Tesseract non trovato nella cartella 'redist\\tesseract-5.5.1', in Program Files/Tesseract-OCR o nel PATH di sistema.")
            self.status_var.set("OCR non disponibile (Tesseract mancante)")
            return

        self.status_var.set("Analisi OCR in corso...")
        self.quick_hint_var.set("Analisi in esecuzione: controlla la finestra del risultato al termine.")
        self.root.update_idletasks()

        def worker():
            try:
                clipboard_data = ImageGrab.grabclipboard()
            except Exception as exc:
                self.root.after(0, lambda: self._handle_ocr_failure(f"Impossibile accedere agli appunti: {exc}"))
                return

            image = None
            if isinstance(clipboard_data, Image.Image):
                image = clipboard_data
            elif isinstance(clipboard_data, list):
                for item in clipboard_data:
                    if isinstance(item, str) and os.path.exists(item):
                        try:
                            with Image.open(item) as img_file:
                                image = img_file.convert('RGB')
                            break
                        except Exception:
                            continue

            if image is None:
                self.root.after(0, self._handle_no_image)
                return

            if image.mode not in ("RGB", "RGBA", "L"):
                image = image.convert('RGB')

            try:
                text_result = pytesseract.image_to_string(image)
            except getattr(pytesseract, 'TesseractNotFoundError', Exception):
                self.root.after(0, lambda: self._handle_ocr_failure("Tesseract OCR non trovato. Controllare 'redist\\tesseract-5.5.1', Program Files/Tesseract-OCR o il PATH di sistema."))
                return
            except Exception as exc:
                self.root.after(0, lambda: self._handle_ocr_failure(f"Errore durante l'elaborazione OCR: {exc}"))
                return

            self.root.after(0, lambda: self._show_ocr_result_window(text_result))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_no_image(self):
        messagebox.showinfo("Nessuna immagine rilevata", "Gli appunti non contengono un'immagine supportata.")
        self.status_var.set("Nessuna immagine negli appunti")

    def _handle_ocr_failure(self, error_message):
        messagebox.showerror("Errore OCR", error_message)
        self.status_var.set("Errore durante l'OCR")

    def _show_ocr_result_window(self, extracted_text):
        self.status_var.set("OCR completato")
        self.quick_hint_var.set("Risultato OCR pronto: puoi copiarlo o ritoccarlo nella finestra dedicata.")
        self._append_activity("OCR completato con apertura del pannello risultato.")

        window = tk.Toplevel(self.root)
        window.title("Risultato OCR dagli appunti")
        window.geometry("760x560")
        window.minsize(620, 460)
        window.configure(bg=WINDOW_BG)
        window.transient(self.root)

        container = ttk.Frame(window, style='App.TFrame', padding=24)
        container.pack(fill=tk.BOTH, expand=True)

        header = create_card(container, padding=20)
        header.pack(fill=tk.X, pady=(0, 16))
        tk.Label(header, text="Testo estratto", bg=CARD_BG, fg=TEXT_PRIMARY, font=('Segoe UI Semibold', 18)).pack(anchor='w')
        header_body = tk.Label(header, text="Controlla il contenuto, apporta modifiche se necessario e copialo negli appunti con un click.", bg=CARD_BG, fg=TEXT_SECONDARY, font=('Segoe UI', 10), wraplength=600, justify=tk.LEFT)
        header_body.pack(anchor='w', fill=tk.X, pady=(6, 0))
        bind_responsive_wrap(header_body, header, padding=40, min_wrap=220)

        editor_card = create_card(container, padding=0)
        editor_card.pack(fill=tk.BOTH, expand=True, pady=(0, 16))

        text_area = ScrolledText(editor_card, wrap=tk.WORD, font=('Segoe UI', 10))
        configure_text_widget(text_area)
        text_area.pack(fill=tk.BOTH, expand=True)
        cleaned_text = extracted_text.strip() if extracted_text else ''
        text_area.insert('1.0', cleaned_text)
        text_area.focus_set()

        button_row = ttk.Frame(container, style='App.TFrame')
        button_row.pack(fill=tk.X)

        def copy_to_clipboard():
            content = text_area.get('1.0', tk.END).strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.status_var.set("Testo OCR copiato negli appunti")
            self._append_activity("Testo OCR copiato negli appunti.")

        copy_button = tk.Button(button_row, text="Copia negli appunti", command=copy_to_clipboard, bg=ACCENT, fg='white', activebackground=ACCENT_HOVER, activeforeground='white', relief='flat', bd=0, padx=18, pady=10, cursor='hand2', font=('Segoe UI Semibold', 10))
        close_button = ttk.Button(button_row, text="Chiudi", command=window.destroy, style='Secondary.TButton')

        def apply_compact_button_row():
            copy_button.pack_forget()
            close_button.pack_forget()
            copy_button.pack(fill=tk.X)
            close_button.pack(fill=tk.X, pady=(10, 0))

        def apply_wide_button_row():
            copy_button.pack_forget()
            close_button.pack_forget()
            copy_button.pack(side=tk.LEFT)
            close_button.pack(side=tk.RIGHT)

        bind_responsive_layout(
            button_row,
            threshold=480,
            compact_layout=apply_compact_button_row,
            wide_layout=apply_wide_button_row,
        )


def main():
    root = tk.Tk()

    if HAS_WIN32:
        try:
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(ico_path):
                root.iconbitmap(default=ico_path)
        except Exception as exc:
            print(f"Could not set window icon: {exc}")

    app = TextToolsLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
