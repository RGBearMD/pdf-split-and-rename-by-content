import os
import re
from tkinterdnd2 import TkinterDnD, DND_FILES
import tkinter as tk
from tkinter import filedialog, messagebox
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
# PARSER
# =========================
def estrai_campi(testo):

    campi = {}
    righe = [r.strip() for r in testo.split("\n") if r.strip()]

    for r in righe:

        m = re.match(r"(.+?)\.{2,}\s*(.+)$", r)
        if m:
            campi[m.group(1).lower()] = m.group(2)
            continue

        m = re.match(r"(.{5,}?)\s{2,}(.+)$", r)
        if m:
            campi[m.group(1).lower()] = m.group(2)

    m = re.search(r'(RAN\d+)', testo)
    if m:
        campi["codice articolo / article item"] = m.group(1)

    return campi


# =========================
# SPLIT
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
# CLEAN
# =========================
def clean(x):
    x = re.sub(r'\s+', ' ', str(x)).strip()
    return re.sub(r'[\\/:*?"<>|]', '-', x)


# =========================
# APP
# =========================
class App:

    def __init__(self, root):

        self.root = root
        self.root.title("PDF Rename Tool - Datasheet")

        self.files = []
        self.campi = {}
        self.scelta = []

        # ================= UX HEADER =================
        info = tk.Label(
            root,
            text=
            "ISTRUZIONI:\n"
            "1) Seleziona un PDF contenente più pagine\n"
            "2) Premi ANALIZZA per vedere i campi disponibili\n"
            "3) Seleziona i campi per il nome file (max 2). Clicca su aggiungi ogni volta che selezioni un campo\n"
            "4) L'ordine di selezione lo vedi in basso e determina il nome finale",
            justify="left",
            fg="blue"
        )
        info.pack(pady=10)

        # ================= FILE BUTTON =================
        tk.Button(root, text="📂 Seleziona PDF", command=self.select_files).pack(pady=5)

        # ================= ANALYZE =================
        tk.Button(root, text="🔎 Analizza PDF", command=self.analyze).pack(pady=5)

        self.label = tk.Label(root, text="Nessun file selezionato")
        self.drop_label = tk.Label(
            root,
            text="📥 Trascina qui i PDF",
            fg="gray",
            relief="solid",
            height=4
        )
        self.drop_label.pack(fill="both", padx=10, pady=10)

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)
        self.label.pack(pady=5)

        # ================= LISTBOX =================
        self.listbox = tk.Listbox(root, width=110, height=18)
        self.listbox.pack()

        # ================= CONTROL BUTTONS =================
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="➕ Aggiungi campo", command=self.add).pack(side="left")
        tk.Button(btn_frame, text="❌ Rimuovi ultimo", command=self.remove).pack(side="left")
        tk.Button(btn_frame, text="🔄 Reset", command=self.reset).pack(side="left")
        tk.Button(btn_frame, text="🚀 ESEGUI", command=self.execute).pack(side="left")

        # ordine visuale
        self.order = tk.StringVar()
        self.order.set("Ordine: (nessuno)")

        tk.Label(root, textvariable=self.order, fg="green").pack(pady=5)

    # ================= FILE =================
    def select_files(self):

        self.files = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])

        self.label.config(text=f"{len(self.files)} file selezionati")

    # ================= ANALYZE =================
    def analyze(self):

        if not self.files:
            messagebox.showwarning("Errore", "Seleziona prima i PDF")
            return

        testo = estrai_testo(self.files[0])
        self.campi = estrai_campi(testo)

        self.listbox.delete(0, tk.END)

        for k, v in self.campi.items():
            preview = str(v)[:80]
            self.listbox.insert(tk.END, f"{k} → {preview}")

    # ================= ADD FIELD =================
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

    # ================= ORDER UI =================
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

        for file in self.files:

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

                i = 1
                while os.path.exists(out):
                    out = os.path.join(out_dir, f"{' - '.join(valori)}_{i}.pdf")
                    i += 1

                os.rename(p, out)

        messagebox.showinfo("OK", "Operazione completata!")

    #=========================DRAG & DROP=========================
    def on_drop(self, event):

        files = self.root.tk.splitlist(event.data)

        pdfs = [f for f in files if f.lower().endswith(".pdf")]

        self.files = pdfs

        self.label.config(text=f"{len(pdfs)} file caricati (drag & drop)")


# ================= RUN =================
if __name__ == "__main__":

    root = TkinterDnD.Tk()
    App(root)
    root.mainloop()