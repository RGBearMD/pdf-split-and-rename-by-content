import os
import re
from tkinterdnd2 import TkinterDnD, DND_FILES
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from pypdf import PdfReader, PdfWriter


# =========================
# ESTRAZIONE TESTO
# =========================
def estrai_testo(pdf_path):
    reader = PdfReader(pdf_path)
    testo = ""

    for page in reader.pages:
        t = page.extract_text()
        if t:
            testo += t + "\n"

    return testo

# =========================
# PARSER GENERICO
# =========================
def estrai_campi(testo, rules=None):

    campi = {}
    righe = [r.strip() for r in testo.split("\n") if r.strip()]

    if rules is None:
        rules = {}

    # =========================
    # REGEX BASE GENERICA
    # =========================

    for r in righe:

        m = re.match(r"(.+?)\.{2,}\s*(.+)$", r)
        if m:
            campi[m.group(1).lower()] = m.group(2)
            continue

        m = re.match(r"(.{4,}?)\s{2,}(.+)$", r)
        if m:
            campi[m.group(1).lower()] = m.group(2)

    # =========================
    # REGOLE UTENTE
    # =========================

    for key, keywords in rules.items():

        for kw in keywords:

            m = re.search(rf"{re.escape(kw)}\s*[:\-]?\s*(.+)", testo, re.IGNORECASE)

            if m:

                campi[key] = m.group(1).strip()
                break

    return campi


# =========================
# SPLIT PDF
# =========================
def split_pdf(path, out_dir):

    reader = PdfReader(path)
    base = os.path.splitext(os.path.basename(path))[0]

    files = []

    for i, page in enumerate(reader.pages, start=1):

        writer = PdfWriter()
        writer.add_page(page)

        out = os.path.join(out_dir, f"{base}_page_{i}.pdf")

        with open(out, "wb") as f:
            writer.write(f)

        files.append(out)

    return files


# =========================
# CLEAN NOME FILE
# =========================
def clean(x):
    x = re.sub(r'\s+', ' ', str(x)).strip()
    return re.sub(r'[\\/:*?"<>|]', '-', x)


# =========================
# APP
# =========================
class App:

    def __init__(self, root):
        
        root.grid_columnconfigure(0, weight=1)

        self.root = root
        self.root.title("RGBear PDF Split & Rename by Content v1.4")

        self.files = []
        self.campi = {}
        self.scelta = []

        self.font = ("Segoe UI", 10)
        self.font_small = ("Segoe UI", 9)
        self.font_title = ("Segoe UI", 11, "bold")
        self.bg = "#f5f6f8"
        self.card = "#ffffff"
        self.accent = "#2f80ed"
        self.text = "#1f1f1f"

        root.configure(bg=self.bg)

        # ================= LAYOUT =================
        
        # ========================= ISTRUZIONI PER PARSER =========================
        tk.Label(root, text="Istruzioni parser (una per riga):").pack()

        self.rules_box = tk.Text(root, height=6, font=("Segoe UI", 10))
        self.rules_box.pack(fill="x", padx=10)

        self.rules_box.insert("1.0",
        """
        ean = ean
        codice articolo = sku|item code|codice articolo
        marchio = brand|marchio
        prodotto = prodotto|product name
        peso = weight|peso
        """)

        # ================= TITOLO =================

        title = tk.Label(
            root,
            text="RGBear PDF Split & Rename by Content v1.4",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg,
            fg=self.text
        )
        title.pack(pady=10)

        # ================= ISTRUZIONI =================

        info = tk.Label(
            root,
            text=
            "1) Carica o trascina il PDF\n"
            "2) Seleziona i campi da usare nel nome del file e clicca su aggiungi (max 2)\n"
            "3) Premi il pulsante in basso per eseguire\n\n",
            justify="left",
            font=("Segoe UI", 11),
            bg="white",
            fg=self.text,
            relief="solid",
            padx=10,
            pady=8
        )
        info.pack(pady=5, ipadx=10)

        """
        main = tk.Frame(root)
        main.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(main, width=220, bg="#2b2b2b")
        self.sidebar.pack(side="left", fill="y")

        self.center = tk.Frame(main)
        self.center.pack(side="right", fill="both", expand=True)
        """

        # ================= SIDEBAR =================
        """
        tk.Label(
            self.sidebar,
            text="RGBear Tools",
            fg="white",
            bg="#2b2b2b",
            font=self.font_title
        ).pack(pady=10)

        tk.Button(
            self.sidebar,
            text="📂 Carica PDF",
            font=self.font_small,
            command=self.select_files
        ).pack(fill="x", padx=10, pady=5)

        tk.Button(
            self.sidebar,
            text="🔎 Analizza",
            font=self.font_small,
            command=self.analyze
        ).pack(fill="x", padx=10, pady=5)

        tk.Button(
            self.sidebar,
            text="🚀 Esegui",
            font=self.font_small,
            command=self.execute
        ).pack(fill="x", padx=10, pady=5)
        """



        # ================= DROP =================
        self.drop_label = tk.Label(
            root,
            text="📥 Trascina qui il PDF\noppure clicca per selezionarlo",
            font=("Segoe UI", 11),
            bg="white",
            fg=self.accent,
            cursor="hand2",
            relief="solid",
            padx=10,
            pady=20
        )
        self.drop_label.pack(fill="x", padx=10, pady=10)

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)
        self.drop_label.bind("<Button-1>", lambda e: self.select_files())

        self.label = tk.Label(root, text="Nessun file selezionato", font=("Segoe UI", 10))
        self.label.pack(pady=5)

        # ================= LISTBOX =================
        self.listbox = tk.Listbox(
            root,
            width=100,
            height=10,
            font=("Segoe UI", 10),
            bg="white",
            fg=self.text,
            highlightthickness=1,
            selectbackground=self.accent
        )
        self.listbox.pack(padx=10, pady=10)

        # ================= CONTROL =================
        btn = tk.Frame(root)
        btn.pack(pady=5)

        tk.Button(btn, text="➕ Aggiungi", font=("Segoe UI", 10), command=self.add).pack(side="left", padx=5)
        tk.Button(btn, text="❌ Rimuovi", font=("Segoe UI", 10), command=self.remove).pack(side="left", padx=5)
        tk.Button(btn, text="🔄 Reset", font=("Segoe UI", 10), command=self.reset).pack(side="left", padx=5)


        # ================= ORDER =================
        self.order = tk.StringVar()
        self.order.set("Ordine: (nessuno)")

        tk.Label(
            root,
            textvariable=self.order,
            fg=self.accent,
            bg=self.bg,
            font=("Segoe UI", 12, "bold")
        ).pack(pady=5)

        # ================= PROGRESS =================
        self.progress = ttk.Progressbar(
            root,
            orient="horizontal",
            mode="determinate"
        )
        self.progress.pack(fill="x", padx=10, pady=10)

        # ================= BUTTONS =================

        style_btn = {
            "font": ("Segoe UI", 11),
            "bg": self.accent,
            "fg": "white",
            "activebackground": "#1f6fd1",
            "activeforeground": "white",
            "bd": 0,
            "padx": 10,
            "pady": 5
        }

        tk.Button(root, text="🚀 GO SPLIT AND RENAME", command=self.execute, **style_btn).pack(pady=3)

# ================= CREDITS & FOOTER =================
        import webbrowser

        # Colore di default dei link e colore quando ci passi sopra (hover)
        link_color = "#555555"
        link_hover_color = self.accent  # Usa l'azzurro della tua app (#2f80ed)

        def on_enter(e):
            e.widget.config(fg=link_hover_color, font=("Segoe UI", 9, "underline"))

        def on_leave(e):
            e.widget.config(fg=link_color, font=("Segoe UI", 9))

        def open_site(event):
            webbrowser.open("https://rgbear.it")

        def open_git(event):
            webbrowser.open("https://github.com/RGBearMD/pdf-split-and-rename-by-content")

        # Unico barozzo/footer in fondo
        footer_bg = "#e9edf5"
        footer = tk.Frame(root, bg=footer_bg, padx=15, pady=8)
        footer.pack(side="bottom", fill="x")

        # Testo dei credits (allineato a sinistra)
        credits_lbl = tk.Label(
            footer,
            text="© RGBear di Massimo D'Ambrogio",
            font=("Segoe UI", 9),
            bg=footer_bg,
            fg="#444"
        )
        credits_lbl.pack(side="left")

        # Separatore grafico | prima dei link
        sep = tk.Label(footer, text=" | ", font=("Segoe UI", 9), bg=footer_bg, fg="#aaa")
        sep.pack(side="left")

        # Link GitHub (allineato a sinistra dopo il separatore)
        git_lbl = tk.Label(
            footer,
            text="GitHub",
            fg=link_color,
            bg=footer_bg,
            cursor="hand2",
            font=("Segoe UI", 9)
        )
        git_lbl.pack(side="left", padx=5)
        git_lbl.bind("<Button-1>", open_git)
        git_lbl.bind("<Enter>", on_enter)
        git_lbl.bind("<Leave>", on_leave)

        # Link Sito Web
        site_lbl = tk.Label(
            footer,
            text="rgbear.it",
            fg=link_color,
            bg=footer_bg,
            cursor="hand2",
            font=("Segoe UI", 9)
        )
        site_lbl.pack(side="left", padx=5)
        site_lbl.bind("<Button-1>", open_site)
        site_lbl.bind("<Enter>", on_enter)
        site_lbl.bind("<Leave>", on_leave)

    # ================= FILE =================
    def select_files(self):

        self.files = filedialog.askopenfilenames(
            filetypes=[("PDF", "*.pdf")]
        )

        if not self.files:
            return

        self.label.config(
            text=f"{len(self.files)} file selezionati"
        )

        # ANALISI AUTOMATICA
        self.analyze()

    # ================= DROP =================
    def on_drop(self, event):

        files = self.root.tk.splitlist(event.data)

        self.files = [
            f for f in files
            if f.lower().endswith(".pdf")
        ]

        if not self.files:
            return

        self.label.config(
            text=f"{len(self.files)} file caricati"
        )

        # ANALISI AUTOMATICA
        self.analyze()

    # ================= ANALYZE =================
    def analyze(self):

        if not self.files:
            messagebox.showwarning("Errore", "Seleziona PDF")
            return

        testo = estrai_testo(self.files[0])

        # =========================
        # REGOLE UTENTE
        # =========================
        rules = self.parse_rules()

        # =========================
        # PARSER
        # =========================
        self.campi = estrai_campi(testo, rules)

        self.listbox.delete(0, tk.END)

        for k, v in self.campi.items():
            self.listbox.insert(tk.END, f"{k} → {str(v)[:80]}")

    # ================= ADD =================
    def add(self):

        sel = self.listbox.curselection()
        if not sel:
            return

        if len(self.scelta) >= 2:
            messagebox.showwarning("Limite", "Max 2 campi")
            return

        key = list(self.campi.keys())[sel[0]]

        if key not in self.scelta:
            self.scelta.append(key)

        self.update_order()

    # ================= REMOVE =================
    def remove(self):
        if self.scelta:
            self.scelta.pop()
            self.update_order()

    # ================= RESET =================
    def reset(self):
        self.scelta = []
        self.update_order()

    # ================= ORDER =================
    def update_order(self):
        if self.scelta:
            self.order.set("Ordine: " + " → ".join(self.scelta))
        else:
            self.order.set("Ordine: (nessuno)")

    # ================= EXECUTE =================
    def execute(self):

        if not self.files:
            messagebox.showwarning("Errore", "Seleziona PDF")
            return

        if not self.scelta:
            messagebox.showwarning("Errore", "Seleziona campi")
            return

        out_dir = os.path.dirname(self.files[0])

        total = len(self.files)
        self.progress["maximum"] = total
        self.progress["value"] = 0

        for i, file in enumerate(self.files):

            pages = split_pdf(file, out_dir)

            for p in pages:

                testo = estrai_testo(p)
                campi = estrai_campi(testo)

                valori = []

                for s in self.scelta:
                    v = campi.get(s)
                    if v:
                        valori.append(clean(v))

                if not valori:
                    continue

                name = " - ".join(valori) + ".pdf"
                out = os.path.join(out_dir, name)

                j = 1
                while os.path.exists(out):
                    out = os.path.join(out_dir, f"{' - '.join(valori)}_{j}.pdf")
                    j += 1

                os.rename(p, out)

            self.progress["value"] = i + 1
            self.root.update_idletasks()

        messagebox.showinfo("OK", "Operazione completata!")

#======================== Leggi regole personalizzate parser ========================
    def parse_rules(self):

        rules = {}

        raw = self.rules_box.get("1.0", tk.END).strip().split("\n")

        for r in raw:

            if "=" not in r:
                continue

            key, values = r.split("=", 1)

            key = key.strip().lower()
            values = [v.strip() for v in values.split("|") if v.strip()]

            rules[key] = values

        return rules

# ================= RUN =================
if __name__ == "__main__":

    # Inizializziamo l'istanza UNICA di TkinterDnD
    root = TkinterDnD.Tk()
    root.title("RGBear PDF Split & Rename by Content v1.4")
    
    # Gestione dell'icona (se il file non esiste, evita che il programma crashi)
    if os.path.exists("pdf-spliterenamebycontent256.ico"):
        root.iconbitmap("pdf-spliterenamebycontent256.ico")
    
    # Impostiamo una geometria sufficiente per mostrare tutto, credits inclusi
    root.geometry("900x850")
    root.minsize(900, 800)
    
    # Permettiamo il ridimensionamento verticale se l'utente ha schermi piccoli
    root.resizable(False, True) 

    # Avviamo l'applicazione
    App(root)
    root.mainloop()