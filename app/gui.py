from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .engine import DownloadEngine


class App(tk.Tk):
    """Stable Tk/ttk GUI.

    This version deliberately does not use CustomTkinter. The previous EXE
    crashed inside CustomTkinter during startup with `CTkLabel object is not
    callable`; using the standard Tk stack removes that dependency entirely.
    """

    BG = "#17191d"
    PANEL = "#202329"
    PANEL_2 = "#262a31"
    TEXT = "#f2f4f7"
    MUTED = "#9aa4b2"
    ACCENT = "#2f89e8"
    ACCENT_HOVER = "#3d97f0"
    SUCCESS = "#55c27a"
    ERROR = "#f06b6b"
    BORDER = "#343943"

    def __init__(self):
        super().__init__()
        self.title("Dota 2 Asset Studio 2.1")
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.configure(bg=self.BG)

        self.base_dir = (
            Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parents[1]
        )

        self.vars = {k: tk.StringVar(value="0") for k in ["total", "downloaded", "skipped", "manual", "failed"]}
        self.type_var = tk.StringVar(value="heroes")
        self.size_var = tk.StringVar(value="Original")
        self.processing_var = tk.StringVar(value="Original")
        self.custom_var = tk.StringVar(value="512")
        self.list_var = tk.StringVar(value="")
        self.state_var = tk.StringVar(value="Ready")
        self.running = False

        self._setup_styles()
        self._build()
        self._type_changed()
        self._load_default()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Root.TFrame", background=self.BG)
        style.configure("Panel.TFrame", background=self.PANEL)
        style.configure("Panel2.TFrame", background=self.PANEL_2)
        style.configure("Title.TLabel", background=self.BG, foreground=self.TEXT, font=("Segoe UI", 28, "bold"))
        style.configure("Subtitle.TLabel", background=self.BG, foreground=self.MUTED, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=self.PANEL, foreground=self.TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=self.PANEL, foreground=self.MUTED, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=self.PANEL_2, foreground=self.TEXT, font=("Segoe UI", 9))
        style.configure("Value.TLabel", background=self.PANEL_2, foreground=self.TEXT, font=("Segoe UI", 22, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(14, 9), background=self.PANEL_2, foreground=self.TEXT)
        style.map("TButton", background=[("active", self.BORDER)])
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(18, 10), background=self.ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", self.ACCENT_HOVER), ("disabled", "#344152")])
        style.configure("TCombobox", fieldbackground=self.PANEL_2, background=self.PANEL_2, foreground=self.TEXT, arrowcolor=self.TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", self.PANEL_2)], foreground=[("readonly", self.TEXT)])
        style.configure("TEntry", fieldbackground=self.PANEL_2, foreground=self.TEXT, insertcolor=self.TEXT)
        style.configure("Horizontal.TProgressbar", troughcolor=self.PANEL_2, background=self.ACCENT, bordercolor=self.PANEL_2, lightcolor=self.ACCENT, darkcolor=self.ACCENT)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ttk.Frame(self, style="Root.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 10))
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="DOTA 2 ASSET STUDIO", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="Heroes • Neutral Creeps • Items", style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(header, textvariable=self.state_var, style="Subtitle.TLabel").grid(row=0, column=1, rowspan=2, sticky="e")

        controls = ttk.Frame(self, style="Panel.TFrame")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=8)
        controls.grid_columnconfigure(3, weight=1)

        ttk.Label(controls, text="Asset type", style="Panel.TLabel").grid(row=0, column=0, padx=(16, 8), pady=(16, 8), sticky="w")
        self.type_combo = ttk.Combobox(controls, textvariable=self.type_var, state="readonly", values=["heroes", "neutral_creeps", "items"], width=18)
        self.type_combo.grid(row=0, column=1, padx=6, pady=(16, 8), sticky="w")
        self.type_combo.bind("<<ComboboxSelected>>", lambda _: self._type_changed())

        ttk.Label(controls, text="List file", style="Panel.TLabel").grid(row=0, column=2, padx=(16, 8), pady=(16, 8), sticky="w")
        self.path_entry = ttk.Entry(controls, textvariable=self.list_var)
        self.path_entry.grid(row=0, column=3, padx=6, pady=(16, 8), sticky="ew")
        self.browse_btn = ttk.Button(controls, text="Browse", command=self._browse)
        self.browse_btn.grid(row=0, column=4, padx=6, pady=(16, 8))
        self.start_btn = ttk.Button(controls, text="START DOWNLOAD", style="Accent.TButton", command=self._start)
        self.start_btn.grid(row=0, column=5, padx=(6, 16), pady=(16, 8))

        ttk.Label(controls, text="Size", style="Panel.TLabel").grid(row=1, column=0, padx=(16, 8), pady=(6, 16), sticky="w")
        self.size_combo = ttk.Combobox(controls, textvariable=self.size_var, state="readonly", values=["Original", "256x256", "512x512", "1024x1024", "Custom"], width=18)
        self.size_combo.grid(row=1, column=1, padx=6, pady=(6, 16), sticky="w")
        ttk.Label(controls, text="Processing", style="Panel.TLabel").grid(row=1, column=2, padx=(16, 8), pady=(6, 16), sticky="w")
        self.processing_combo = ttk.Combobox(controls, textvariable=self.processing_var, state="readonly", values=["Original", "Contain"], width=18)
        self.processing_combo.grid(row=1, column=3, padx=6, pady=(6, 16), sticky="w")
        ttk.Label(controls, text="Custom px", style="Panel.TLabel").grid(row=1, column=4, padx=6, pady=(6, 16), sticky="e")
        self.custom_entry = ttk.Entry(controls, textvariable=self.custom_var, width=9)
        self.custom_entry.grid(row=1, column=5, padx=(6, 16), pady=(6, 16), sticky="w")

        self.refresh_btn = ttk.Button(controls, text="UPDATE DATABASES", command=self._refresh)
        self.refresh_btn.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 14), sticky="w")
        ttk.Label(controls, text="Liquipedia API is used for the live catalog; no HTML page scraping.", style="Muted.TLabel").grid(row=2, column=2, columnspan=4, padx=8, pady=(0, 14), sticky="w")

        body = ttk.Frame(self, style="Root.TFrame")
        body.grid(row=2, column=0, sticky="nsew", padx=18, pady=8)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(1, weight=1)

        stats = ttk.Frame(body, style="Panel.TFrame")
        stats.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for i, (label, key) in enumerate([("TOTAL", "total"), ("DOWNLOADED", "downloaded"), ("SKIPPED", "skipped"), ("MANUAL", "manual"), ("FAILED", "failed")]):
            stats.grid_columnconfigure(i, weight=1)
            card = ttk.Frame(stats, style="Panel2.TFrame")
            card.grid(row=0, column=i, padx=5, pady=6, sticky="ew")
            ttk.Label(card, text=label, style="Card.TLabel").pack(pady=(8, 1))
            ttk.Label(card, textvariable=self.vars[key], style="Value.TLabel").pack(pady=(0, 8))

        left = ttk.Frame(body, style="Panel.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(1, weight=1); left.grid_columnconfigure(0, weight=1)
        ttk.Label(left, text="ASSETS", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 7))
        self.listbox = tk.Text(left, bg="#111318", fg=self.TEXT, insertbackground=self.TEXT, relief="flat", bd=0, font=("Consolas", 10), wrap="none")
        self.listbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        right = ttk.Frame(body, style="Panel.TFrame")
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1); right.grid_columnconfigure(0, weight=1)
        ttk.Label(right, text="LOG", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 7))
        self.logbox = tk.Text(right, bg="#111318", fg=self.TEXT, insertbackground=self.TEXT, relief="flat", bd=0, font=("Segoe UI", 9), wrap="word")
        self.logbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        footer = ttk.Frame(self, style="Root.TFrame")
        footer.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        footer.grid_columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(footer, style="Horizontal.TProgressbar", maximum=100)
        self.progress.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        self.pct = ttk.Label(footer, text="0/0", style="Subtitle.TLabel")
        self.pct.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.output_btn = ttk.Button(footer, text="OPEN OUTPUT FOLDER", command=self._open_output)
        self.output_btn.grid(row=0, column=1, rowspan=2, sticky="e")

    def _load_default(self):
        p = self.base_dir / f"{self.type_var.get()}.txt"
        if p.exists():
            self.list_var.set(str(p))
            self._append(f"Found {p.name}")

    def _type_changed(self):
        if self.running:
            return
        p = self.base_dir / f"{self.type_var.get()}.txt"
        if p.exists():
            self.list_var.set(str(p))
        else:
            self.list_var.set("")

    def _browse(self):
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            self.list_var.set(p)

    def _append(self, text):
        self.after(0, self._append_now, text)

    def _append_now(self, text):
        self.logbox.insert("end", text + "\n")
        self.logbox.see("end")

    def _set_status(self, text):
        self.after(0, self.state_var.set, text)

    def _progress(self, i, n, stats):
        def update():
            self.progress["value"] = 100 * i / max(1, n)
            self.pct.configure(text=f"{i}/{n}")
            for key in self.vars:
                self.vars[key].set(str(getattr(stats, key)))
        self.after(0, update)

    def _render_list(self, names):
        def update():
            self.listbox.delete("1.0", "end")
            self.listbox.insert("end", "\n".join(names))
        self.after(0, update)

    def _set_controls(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.start_btn.configure(state=state)
        self.refresh_btn.configure(state=state)
        self.browse_btn.configure(state=state)
        self.type_combo.configure(state="readonly" if enabled else "disabled")
        self.size_combo.configure(state="readonly" if enabled else "disabled")
        self.processing_combo.configure(state="readonly" if enabled else "disabled")
        self.custom_entry.configure(state=state)

    def _start(self):
        if self.running:
            return
        path = Path(self.list_var.get().strip())
        if not path.exists():
            messagebox.showerror("Dota 2 Asset Studio", "List file not found.")
            return
        self._run(False)

    def _refresh(self):
        if self.running:
            return
        self._run(True)

    def _run(self, refresh_only: bool):
        if not refresh_only:
            try:
                custom = int(self.custom_var.get() or "512")
                if custom < 16 or custom > 8192:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Dota 2 Asset Studio", "Custom px must be an integer from 16 to 8192.")
                return

        self.running = True
        self._set_controls(False)
        self._set_status("Working…")
        self.logbox.delete("1.0", "end")
        self.listbox.delete("1.0", "end")

        def work():
            try:
                engine = DownloadEngine(self.base_dir, self._append, self._progress, self._set_status)
                if refresh_only:
                    engine.refresh()
                    self._append("Databases updated successfully.")
                    self._set_status("Completed")
                    return

                from .text_io import read_names
                names = read_names(Path(self.list_var.get()))
                if not names:
                    raise RuntimeError("The selected list is empty.")
                self._render_list(names)

                custom = int(self.custom_var.get() or "512")
                stats = engine.download(
                    self.type_var.get(),
                    Path(self.list_var.get()),
                    self.size_var.get(),
                    custom,
                    force_refresh=True,
                )
                self._append(
                    f"Completed: {stats.downloaded} downloaded | "
                    f"{stats.skipped} skipped | {stats.manual} manual | {stats.failed} failed"
                )
                self._set_status("Completed")
            except Exception as exc:
                self._append(f"ERROR: {exc}")
                self._set_status("Error")
                self.after(0, lambda: messagebox.showerror("Dota 2 Asset Studio", str(exc)))
            finally:
                self.running = False
                self.after(0, lambda: self._set_controls(True))

        threading.Thread(target=work, daemon=True).start()

    def _open_output(self):
        p = self.base_dir / "output" / self.type_var.get()
        p.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(p)
        except OSError as exc:
            messagebox.showerror("Dota 2 Asset Studio", f"Could not open folder:\n{exc}")

    def _on_close(self):
        if self.running:
            if not messagebox.askyesno("Dota 2 Asset Studio", "A download is still running. Close the application?"):
                return
        self.destroy()
