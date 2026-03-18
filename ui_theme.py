import tkinter as tk
from tkinter import ttk

WINDOW_BG = '#f5f7fb'
CARD_BG = '#ffffff'
ACCENT = '#2563eb'
ACCENT_HOVER = '#1d4ed8'
TEXT_PRIMARY = '#111827'
TEXT_SECONDARY = '#5b6473'
BORDER = '#d8deea'
SUCCESS = '#15803d'
WARNING = '#c2410c'
SURFACE = '#eef2ff'


def apply_modern_theme(root):
    style = ttk.Style(root)
    available_themes = set(style.theme_names())
    if 'vista' in available_themes:
        style.theme_use('vista')
    elif 'clam' in available_themes:
        style.theme_use('clam')

    root.configure(bg=WINDOW_BG)

    style.configure('.', font=('Segoe UI', 10))
    style.configure('App.TFrame', background=WINDOW_BG)
    style.configure('Surface.TFrame', background=SURFACE)
    style.configure('Card.TFrame', background=CARD_BG, relief='flat')
    style.configure('CardTitle.TLabel', background=CARD_BG, foreground=TEXT_PRIMARY, font=('Segoe UI Semibold', 11))
    style.configure('HeroTitle.TLabel', background=WINDOW_BG, foreground=TEXT_PRIMARY, font=('Segoe UI Semibold', 24))
    style.configure('HeroBody.TLabel', background=WINDOW_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 10))
    style.configure('SectionTitle.TLabel', background=WINDOW_BG, foreground=TEXT_PRIMARY, font=('Segoe UI Semibold', 12))
    style.configure('Body.TLabel', background=WINDOW_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 10))
    style.configure('CardBody.TLabel', background=CARD_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 10))
    style.configure('Muted.TLabel', background=WINDOW_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 9))
    style.configure('Status.TLabel', background=SURFACE, foreground=ACCENT, font=('Segoe UI Semibold', 10), padding=(12, 7))
    style.configure('Primary.TButton', font=('Segoe UI Semibold', 10), padding=(18, 12))
    style.map('Primary.TButton', background=[('active', ACCENT_HOVER), ('!disabled', ACCENT)])
    style.configure('Secondary.TButton', font=('Segoe UI', 10), padding=(16, 10))
    style.configure('Toolbar.TButton', font=('Segoe UI Semibold', 10), padding=(16, 10))
    style.configure('Modern.TLabelframe', background=WINDOW_BG, borderwidth=0)
    style.configure('Modern.TLabelframe.Label', background=WINDOW_BG, foreground=TEXT_PRIMARY, font=('Segoe UI Semibold', 12))
    style.configure('Modern.Vertical.TScrollbar', gripcount=0, arrowsize=12)

    return style


def create_card(parent, padding=20):
    card = tk.Frame(
        parent,
        bg=CARD_BG,
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER,
        padx=padding,
        pady=padding,
    )
    return card


def configure_text_widget(widget, *, readonly=False):
    widget.configure(
        bg=CARD_BG,
        fg=TEXT_PRIMARY,
        insertbackground=ACCENT,
        relief='flat',
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER,
        font=('Segoe UI', 10),
        padx=16,
        pady=16,
        spacing1=2,
        spacing3=2,
    )
    if readonly:
        widget.configure(state=tk.DISABLED)


def bind_responsive_wrap(widget, container=None, *, padding=0, min_wrap=160):
    target = container or widget
    state = {'wraplength': None}

    def update(event=None):
        if not widget.winfo_exists() or not target.winfo_exists():
            return

        width = event.width if event is not None and getattr(event, 'width', 0) else target.winfo_width()
        if width <= 1:
            return

        wraplength = max(min_wrap, width - padding)
        if wraplength == state['wraplength']:
            return

        widget.configure(wraplength=wraplength)
        state['wraplength'] = wraplength

    target.bind('<Configure>', update, add='+')
    target.after_idle(update)
    return widget


def bind_responsive_layout(container, *, threshold, compact_layout, wide_layout):
    state = {'compact': None}

    def update(event=None):
        if not container.winfo_exists():
            return

        width = event.width if event is not None and getattr(event, 'width', 0) else container.winfo_width()
        if width <= 1:
            return

        compact = width < threshold
        if compact == state['compact']:
            return

        state['compact'] = compact
        if compact:
            compact_layout()
        else:
            wide_layout()

    container.bind('<Configure>', update, add='+')
    container.after_idle(update)
    return container
