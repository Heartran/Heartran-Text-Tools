# Heartran Text Tools

Raccolta di utility desktop Windows-oriented per trasformare rapidamente il testo negli appunti, con una dashboard Tkinter moderna e un flusso OCR integrato.

## Panoramica

Il progetto include tre strumenti principali:

- **Maiuscole intelligenti**: monitora gli appunti e applica una capitalizzazione più adatta a nomi propri e testi simili.
- **MAIUSCOLO totale**: converte automaticamente in maiuscolo il testo copiato.
- **OCR dagli appunti**: estrae testo da immagini presenti negli appunti tramite Tesseract.

L'interfaccia principale è `textTools-gui.py`, che avvia i tool secondari e gestisce il workflow OCR in un'unica dashboard.

## Struttura del progetto

- `textTools-gui.py` — launcher principale con dashboard, lock dei tool e OCR dagli appunti.
- `capitolAllText.py` — monitor clipboard per maiuscole intelligenti.
- `upperAllText.py` — monitor clipboard per conversione automatica in maiuscolo.
- `ui_theme.py` — tema grafico condiviso per le finestre Tkinter.
- `requirements.txt` — dipendenze runtime.
- `redist/tesseract-5.5.1` — runtime Tesseract opzionale incluso nel bundle, se presente.

## Requisiti

- **Python 3.10+** consigliato.
- **Windows** come piattaforma target principale.
- Dipendenze Python elencate in `requirements.txt`:
  - `pyperclip`
  - `psutil`
  - `pywin32` (solo Windows)
  - `pytesseract`
  - `Pillow`

## Installazione

### 1. Crea un ambiente virtuale

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Installa le dipendenze

```powershell
pip install -r requirements.txt
```

## Avvio rapido

### Dashboard principale

```powershell
python textTools-gui.py
```

### Tool singoli

```powershell
python capitolAllText.py
python upperAllText.py
```

## Funzionalità principali

### 1. Dashboard unificata

La finestra principale offre:

- accesso rapido ai tre flussi principali;
- stato operativo sempre visibile;
- log attività interno;
- prevenzione di istanze duplicate dei tool tramite file di lock temporanei.

### 2. Maiuscole intelligenti

Il tool `capitolAllText.py`:

- osserva il contenuto degli appunti;
- converte parole e nomi in title case “intelligente”;
- gestisce particelle come `di`, `de`, `van`, `von`, `del`, ecc.;
- mantiene casi come prefissi con apostrofo (`D'`, `L'`) e nomi composti con trattino.

### 3. Conversione in MAIUSCOLO

Il tool `upperAllText.py`:

- monitora continuamente gli appunti;
- converte il testo in maiuscolo quando necessario;
- mostra anteprima, stato e metadati dell'ultimo contenuto elaborato.

### 4. OCR dagli appunti

La dashboard può leggere immagini dagli appunti e passare il contenuto a Tesseract per estrarre testo modificabile e ricopiabile.

## Configurazione OCR

Per usare l'OCR servono:

- `Pillow`
- `pytesseract`
- un binario Tesseract disponibile in uno dei seguenti modi:
  - `redist/tesseract-5.5.1`
  - una directory indicata dalle variabili d'ambiente `TESSERACT_PATH`, `TESSERACT_HOME`, `TESSERACT_EXE` oppure `TESSERACT_EXE_PATH`
  - `Program Files\Tesseract-OCR`
  - `Program Files (x86)\Tesseract-OCR`
  - `%LOCALAPPDATA%\Programs\Tesseract-OCR`
  - `PATH` di sistema

Se il motore OCR o le dipendenze non sono disponibili, l'app mostra un messaggio di errore esplicito.

## Note d'uso

- I monitor clipboard lavorano in tempo reale e possono essere messi in pausa dalla rispettiva finestra.
- Il progetto è progettato principalmente per Windows, inclusi `pywin32` e i metadati del processo/finestra attiva.
- In contesti PyInstaller, `textTools-gui.py` supporta anche il caricamento delle risorse tramite `sys._MEIPASS`.

## Validazione manuale consigliata

Dato che il repository non include una suite di test automatizzati, è consigliato verificare manualmente:

- apertura della dashboard;
- lancio dei tool secondari dalla GUI;
- monitoraggio e conversione del testo negli appunti;
- pausa/ripresa dei monitor;
- OCR con un'immagine valida negli appunti;
- comportamento di fallback quando Tesseract o le dipendenze OCR mancano.

## Licenza

Verificare con il proprietario del repository la licenza applicabile prima della distribuzione pubblica del progetto o dei binari.
