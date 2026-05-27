import os
import re
import json
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from pypdf import PdfReader, PdfWriter

# FILE LOCALE PER SALVARE I PROFILI
PROFILES_FILE = "profili_parser.json"

DEFAULT_PROFILES = {
    "Rilevamento Automatico": {
        "is_auto": True
    },
    "Schede Barilla": {
        "is_auto": False,
        "keyword_identificazione": "barilla g. e r. fratelli",
        "campo_1_nome": "Codice EAN",
        "campo_1_ancora": "codice ean",
        "campo_2_nome": "Marchio",
        "campo_2_ancora": "marchio"
    },
    "Esselunga Specifiche": {
        "is_auto": False,
        "keyword_identificazione": "esselunga s.p.a.",
        "campo_1_nome": "Articolo",
        "campo_1_ancora": "cod. articolo",
        "campo_2_nome": "TMC",
        "campo_2_ancora": "termine minimo di conservazione"
    }
}

# ==========================================
# MOTORE DI PARSING (DIETRO LE QUINTE)
# ==========================================
def estrai_testo_pagina(pdf_path, numero_pagina=0):
    try:
        reader = PdfReader(pdf_path)
        if numero_pagina < len(reader.pages):
            return reader.pages[numero_pagina].extract_text() or ""
    except Exception:
        return ""
    return ""

def estrai_valore_da_ancora(testo, ancora):
    if not ancora or not testo:
        return ""
    
    # Genera dinamicamente la regex basandosi sull'ancora testuale dell'utente
    pattern = rf"(?i){re.escape(ancora)}\s*[:\-–=]?\s*(.+)"
    match = re.search(pattern, testo)
    if match:
        # Prende la prima riga trovata
        valore = match.group(1).split("\n")[0].strip()
        
        # 🌟 RIMOZIONE DEI PUNTINI DI SEPARAZIONE
        # Rimuove sequenze di 2 o più puntini (es. '....') ed eventuali spazi all'inizio o alla fine
        valore = re.sub(r"^\s*\.{2,}\s*", "", valore)
        valore = re.sub(r"\s*\.{2,}\s*$", "", valore)
        
        return valore.strip()
    return ""

def clean_filename(name):
    name = re.sub(r'\s+', ' ', str(name)).strip()
    return re.sub(r'[\\/:*?"<>|]', '-', name)

# ==========================================
# APPLICAZIONE PRINCIPALE
# ==========================================
class RGBearApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RGBear PDF Smart Split & Rename by content v3.0")
        self.root.geometry("1000x850")
        self.root.minsize(950, 750)
        
        self.accent = "#2f80ed"
        self.bg_color = "#f5f6f8"
        self.root.configure(bg=self.bg_color)
        
        self.caricati_files = []
        self.profili = self.carica_profili()
        
        # Struttura a Schede (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_elaborazione = ttk.Frame(self.notebook)
        self.tab_configurazione = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_elaborazione, text="🚀 Elaborazione File")
        self.notebook.add(self.tab_configurazione, text="⚙️ Configura Profili Layout")
        
        self.build_tab_elaborazione()
        self.build_tab_configurazione()
        self.build_footer()

    # ==========================================
    # TAB 1: OPERATIVO (INTERFACCIA SECTOR BUSINESS)
    # ==========================================
    def build_tab_elaborazione(self):
        # Top Panel: Selezione Profilo
        top_frame = tk.Frame(self.tab_elaborazione, pady=10, bg="#ffffff", relief="groove", bd=1)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(top_frame, text="Profilo Layout PDF:", font=("Segoe UI", 11, "bold"), bg="#ffffff").pack(side="left", padx=10)
        
        self.combo_profili = ttk.Combobox(top_frame, values=list(self.profili.keys()), font=("Segoe UI", 10), state="readonly", width=30)
        self.combo_profili.set("Rilevamento Automatico")
        self.combo_profili.pack(side="left", padx=5)
        self.combo_profili.bind("<<ComboboxSelected>>", lambda e: self.ricarica_anteprima_tabella())

        # Area Drag and Drop
        self.drop_label = tk.Label(
            self.tab_elaborazione,
            text="📥 TRASCINA QUI I PDF DA ELABORARE\noppure clicca per selezionarli dal computer",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff", fg=self.accent,
            relief="solid", bd=1, cursor="hand2", pady=30,
            highlightbackground="#cccccc", highlightthickness=1 # Crea un bordino sottile grigio stile web
        )
        self.drop_label.pack(fill="x", padx=10, pady=10)
        
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.handle_drop)
        self.drop_label.bind("<Button-1>", lambda e: self.sfoglia_files())

        # Tabella Anteprima Risultati (Stile Excel)
        lbl_anteprima = tk.Label(self.tab_elaborazione, text="Anteprima dati estratti e simulazione ridenominazione:", font=("Segoe UI", 10, "italic"))
        lbl_anteprima.pack(anchor="w", padx=10, pady=(10, 0))

        frame_table = tk.Frame(self.tab_elaborazione)
        frame_table.pack(fill="both", expand=True, padx=10, pady=5)

        colonne = ("originale", "profilo", "campo1", "campo2", "nuovo_nome")
        self.tree = ttk.Treeview(frame_table, columns=colonne, show="headings")
        
        self.tree.heading("originale", text="File Originale")
        self.tree.heading("profilo", text="Profilo Rilevato")
        self.tree.heading("campo1", text="Dato Campo 1")
        self.tree.heading("campo2", text="Dato Campo 2")
        self.tree.heading("nuovo_nome", text="Nuovo Nome File Generato (Simulazione)")
        
        self.tree.column("originale", width=200, anchor="w")
        self.tree.column("profilo", width=130, anchor="center")
        self.tree.column("campo1", width=120, anchor="center")
        self.tree.column("campo2", width=120, anchor="center")
        self.tree.column("nuovo_nome", width=300, anchor="w")
        
        scroll_y = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Progress bar e Bottone di Avvio
        self.progress = ttk.Progressbar(self.tab_elaborazione, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        self.btn_run = tk.Button(
            self.tab_elaborazione, text="🚀 ESEGUI SPLIT E RIDENOMINAZIONE",
            font=("Segoe UI", 12, "bold"), bg=self.accent, fg="white",
            activebackground="#1f6fd1", activeforeground="white", bd=0, pady=10, command=self.esegui_elaborazione
        )
        self.btn_run.pack(fill="x", padx=10, pady=10)

    # ==========================================
    # TAB 2: CONFIGURAZIONE PANNELLO NO-CODE
    # ==========================================
    def build_tab_configurazione(self):
        container = tk.Frame(self.tab_configurazione, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="🛠️ Configura nuovo layout fornitore senza codice", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Input Nome Profilo
        tk.Label(container, text="Nome del Profilo (es. Nome Fornitore):", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_prof_name = ttk.Entry(container, width=40)
        self.entry_prof_name.grid(row=1, column=1, sticky="w", pady=5, padx=10)

        # Input Parola chiave identificazione
        tk.Label(container, text="Parola chiave per riconoscerlo nel PDF\n(es. Ragione Sociale o P.IVA scritta nel file):", font=("Segoe UI", 10), justify="left").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_prof_key = ttk.Entry(container, width=40)
        self.entry_prof_key.grid(row=2, column=1, sticky="w", pady=5, padx=10)

        # Separatore visivo
        ttk.Separator(container, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)

        # Configurazione CAMPO 1
        tk.Label(container, text="Nome Campo 1 (es. EAN o SKU):", font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w", pady=5)
        self.entry_c1_nome = ttk.Entry(container, width=40)
        self.entry_c1_nome.grid(row=4, column=1, sticky="w", pady=5, padx=10)

        tk.Label(container, text="Testo fisso vicino al valore (Ancora):\n(es. 'Codice EAN' o 'Cod. Articolo')", font=("Segoe UI", 9, "italic"), justify="left").grid(row=5, column=0, sticky="w", pady=5)
        self.entry_c1_ancora = ttk.Entry(container, width=40)
        self.entry_c1_ancora.grid(row=5, column=1, sticky="w", pady=5, padx=10)

        # Separatore visivo 2
        ttk.Separator(container, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=15)

        # Configurazione CAMPO 2
        tk.Label(container, text="Nome Campo 2 (es. Peso o Marchio):", font=("Segoe UI", 10)).grid(row=7, column=0, sticky="w", pady=5)
        self.entry_c2_nome = ttk.Entry(container, width=40)
        self.entry_c2_nome.grid(row=7, column=1, sticky="w", pady=5, padx=10)

        tk.Label(container, text="Testo fisso vicino al valore (Ancora):\n(es. 'Peso Netto' o 'Brand:')", font=("Segoe UI", 9, "italic"), justify="left").grid(row=8, column=0, sticky="w", pady=5)
        self.entry_c2_ancora = ttk.Entry(container, width=40)
        self.entry_c2_ancora.grid(row=8, column=1, sticky="w", pady=5, padx=10)

        # Bottone di salvataggio
        btn_salva = tk.Button(
            container, text="💾 Salva questo Profilo di Layout",
            font=("Segoe UI", 11, "bold"), bg="#27ae60", fg="white",
            activebackground="#219653", activeforeground="white", bd=0, padx=20, pady=8, command=self.salva_nuovo_profilo
        )
        btn_salva.grid(row=9, column=0, columnspan=2, pady=25)

    # ==========================================
    # LOGICA DI BUSINESS ED ELABORAZIONE
    # ==========================================
    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.caricati_files = [f for f in files if f.lower().endswith(".pdf")]
        self.ricarica_anteprima_tabella()

    def sfoglia_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Documenti PDF", "*.pdf")])
        if files:
            self.caricati_files = list(files)
            self.ricarica_anteprima_tabella()

    def ricarica_anteprima_tabella(self):
        self.tree.delete(*self.tree.get_children())
        profilo_scelto = self.combo_profili.get()
        
        for path in self.caricati_files:
            nome_file = os.path.basename(path)
            testo_anteprima = estrai_testo_pagina(path, 0) # Legge solo pag 1 per velocità in anteprima
            
            profilo_effettivo = profilo_scelto
            
            # Logica Auto-Detection dei template se impostato su automatico
            if profilo_scelto == "Rilevamento Automatico":
                profilo_effettivo = "Non riconosciuto"
                for p_name, p_data in self.profili.items():
                    if p_data.get("is_auto"): continue
                    kw = p_data.get("keyword_identificazione", "").lower()
                    if kw and kw in testo_anteprima.lower():
                        profilo_effettivo = p_name
                        break
            
            # Estrazione valori basata sul profilo finale decretato
            val1, val2 = "", ""
            if profilo_effettivo in self.profili:
                profiling_data = self.profili[profilo_effettivo]
                if profiling_data:
                    if not profiling_data.get("is_auto"):
                        val1 = estrai_valore_da_ancora(testo_anteprima, profiling_data.get("campo_1_ancora", ""))
                        val2 = estrai_valore_da_ancora(testo_anteprima, profiling_data.get("campo_2_ancora", ""))
            
            # Fallback se non trova i valori o il profilo è sconosciuto
            mostra_v1 = val1 if val1 else "N.D."
            mostra_v2 = val2 if val2 else "N.D."
            
            # Generazione Nome di Simulazione
            if val1 or val2:
                pezzi = [clean_filename(v) for v in [val1, val2] if v]
                nuovo_nome_simulato = " - ".join(pezzi) + "_pag_X.pdf"
            else:
                nuovo_nome_simulato = "[Profilo o Dati Mancanti: Non verrà diviso]"
                
            self.tree.insert("", "end", values=(nome_file, profilo_effettivo, mostra_v1, mostra_v2, nuovo_nome_simulato))

    def esegui_elaborazione(self):
        if not self.caricati_files:
            messagebox.showwarning("Attenzione", "Trascina o seleziona prima dei file PDF.")
            return
            
        profilo_scelto = self.combo_profili.get()
        out_dir = os.path.dirname(self.caricati_files[0])
        
        self.progress["maximum"] = len(self.caricati_files)
        self.progress["value"] = 0
        
        file_processati = 0
        
        for path in self.caricati_files:
            try:
                reader = PdfReader(path)
                base_orig = os.path.splitext(os.path.basename(path))[0]
                
                for idx, page in enumerate(reader.pages):
                    testo_pag = page.extract_text() or ""
                    
                    # Rilevamento automatico per singola pagina (gestisce file misti!)
                    profilo_effettivo = profilo_scelto
                    if profilo_scelto == "Rilevamento Automatico":
                        profilo_effettivo = "Sconosciuto"
                        for p_name, p_data in self.profili.items():
                            if p_data.get("is_auto"): continue
                            kw = p_data.get("keyword_identificazione", "").lower()
                            if kw and kw in testo_pag.lower():
                                profilo_effettivo = p_name
                                break
                    
                    val1, val2 = "", ""
                    if profilo_effettivo in self.profili and not self.profili[profilo_effettivo].get("is_auto"):
                        p_data = self.profili[profilo_effettivo]
                        val1 = estrai_valore_da_ancora(testo_pag, p_data.get("campo_1_ancora", ""))
                        val2 = estrai_valore_da_ancora(testo_pag, p_data.get("campo_2_ancora", ""))
                    
                    # Creazione file splittato effettivo
                    writer = PdfWriter()
                    writer.add_page(page)
                    
                    if val1 or val2:
                        nomi_puliti = [clean_filename(v) for v in [val1, val2] if v]
                        nuovo_nome = " - ".join(nomi_puliti) + ".pdf"
                    else:
                        # Fallback se non trova i criteri di ridenominazione
                        nuovo_nome = f"{base_orig}_pagina_{idx+1}.pdf"
                        
                    final_path = os.path.join(out_dir, nuovo_nome)
                    
                    # Evita sovrascrittura di file omonimi
                    contatore = 1
                    while os.path.exists(final_path):
                        nome_senza_ext = os.path.splitext(nuovo_nome)[0]
                        final_path = os.path.join(out_dir, f"{nome_senza_ext}_{contatore}.pdf")
                        contatore += 1
                        
                    with open(final_path, "wb") as f_out:
                        writer.write(f_out)
                        
                file_processati += 1
                self.progress["value"] = file_processati
                self.root.update_idletasks()
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile elaborare il file {os.path.basename(path)}: {str(e)}")
                
        messagebox.showinfo("Successo", f"Elaborazione terminata con successo!\nI file sono stati salvati in:\n{out_dir}")
        self.caricati_files = []
        self.tree.delete(*self.tree.get_children())
        self.progress["value"] = 0

    # ==========================================
    # GESTIONE DEI PROFILI (PERSISTENZA JSON)
    # ==========================================
    def carica_profili(self):
        if os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return DEFAULT_PROFILES.copy()
        return DEFAULT_PROFILES.copy()

    def salva_nuovo_profilo(self):
        name = self.entry_prof_name.get().strip()
        kw = self.entry_prof_key.get().strip()
        c1_n = self.entry_c1_nome.get().strip()
        c1_a = self.entry_c1_ancora.get().strip()
        c2_n = self.entry_c2_nome.get().strip()
        c2_a = self.entry_c2_ancora.get().strip()
        
        if not name or not kw or not c1_a:
            messagebox.showwarning("Campi Mancanti", "Il nome del profilo, la parola chiave identificativa e l'ancora del Campo 1 sono obbligatori.")
            return
            
        self.profili[name] = {
            "is_auto": False,
            "keyword_identificazione": kw,
            "campo_1_nome": c1_n if c1_n else "Campo 1",
            "campo_1_ancora": c1_a,
            "campo_2_nome": c2_n if c2_n else "Campo 2",
            "campo_2_ancora": c2_a
        }
        
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profili, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Salvato", f"Profilo '{name}' registrato correttamente!")
            
            # Pulisci form e aggiorna combobox
            self.entry_prof_name.delete(0, tk.END)
            self.entry_prof_key.delete(0, tk.END)
            self.entry_c1_nome.delete(0, tk.END)
            self.entry_c1_ancora.delete(0, tk.END)
            self.entry_c2_nome.delete(0, tk.END)
            self.entry_c2_ancora.delete(0, tk.END)
            
            self.combo_profili["values"] = list(self.profili.keys())
            self.notebook.select(self.tab_elaborazione) # Riporta alla scheda operativa
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare il profilo su disco: {str(e)}")

    # ==========================================
    # FOOTER & CREDITS MIGLIORATI
    # ==========================================
    def build_footer(self):
        link_color = "#555555"
        link_hover_color = self.accent

        def on_enter(e):
            e.widget.config(fg=link_hover_color, font=("Segoe UI", 9, "underline"))

        def on_leave(e):
            e.widget.config(fg=link_color, font=("Segoe UI", 9))

        footer_bg = "#e9edf5"
        footer = tk.Frame(self.root, bg=footer_bg, padx=15, pady=8)
        footer.pack(side="bottom", fill="x")

        credits_lbl = tk.Label(footer, text="© RGBear di Massimo D'Ambrogio", font=("Segoe UI", 9), bg=footer_bg, fg="#444")
        credits_lbl.pack(side="left")

        sep = tk.Label(footer, text=" | ", font=("Segoe UI", 9), bg=footer_bg, fg="#aaa")
        sep.pack(side="left")

        git_lbl = tk.Label(footer, text="GitHub", fg=link_color, bg=footer_bg, cursor="hand2", font=("Segoe UI", 9))
        git_lbl.pack(side="left", padx=5)
        git_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/RGBearMD/pdf-split-and-rename-by-content"))
        git_lbl.bind("<Enter>", on_enter)
        git_lbl.bind("<Leave>", on_leave)

        site_lbl = tk.Label(footer, text="rgbear.it", fg=link_color, bg=footer_bg, cursor="hand2", font=("Segoe UI", 9))
        site_lbl.pack(side="left", padx=5)
        site_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://rgbear.it"))
        site_lbl.bind("<Enter>", on_enter)
        site_lbl.bind("<Leave>", on_leave)

# ==========================================
# AVVIO APPLICAZIONE
# ==========================================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    root.title("RGBear PDF Split & Rename by Content")
    
    if os.path.exists("pdf-spliterenamebycontent256.ico"):
        root.iconbitmap("pdf-spliterenamebycontent256.ico")
        
    root.geometry("1000x820")
    root.resizable(True, True) 
    
    RGBearApp(root)
    root.mainloop()