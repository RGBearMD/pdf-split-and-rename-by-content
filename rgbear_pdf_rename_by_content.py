import os
import re
import json
import locale
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
from pypdf import PdfReader, PdfWriter

PROFILES_FILE = "profili_parser.json"

# ==========================================
# DIZIONARIO DELLE TRADUZIONI (IT / EN)
# ==========================================
LANGUAGES = {
    "it": {
        "title": "RGBear PDF Smart Split & Rename v1.0",
        "tab_process": "🚀 Elaborazione File",
        "tab_config": "⚙️ Configura Profili Dati",
        "guide_title": " 📋 GUIDA RAPIDA: COME ESTRARRE LE PAGINE E RINOMINARLE ",
        "guide_text": """1. Trascina qui sotto o seleziona il file PDF dal computer.
2. Vai nella scheda "Configura profili dati", inserisci i testi di riferimento che vuoi utilizzare per rinominare il file e salva il profilo.
3. Torna in questa scheda ("Elaborazione file") e seleziona il profilo salvato dal menu a tendina.
4. Controlla nella tabella se il nuovo nome del file simulato è corretto, quindi procedi cliccando il pulsante in basso "ESEGUI".""",
        "profile_lbl": "Profilo Layout PDF:",
        "auto_detect": "Rilevamento Automatico",
        "drop_lbl": "📥 TRASCINA QUI I PDF DA ELABORARE oppure clicca per selezionarli dal computer",
        "preview_lbl": "Anteprima dati estratti e simulazione ridenominazione:",
        "col_orig": "File Originale",
        "col_prof": "Profilo Rilevato",
        "col_c1": "Dato Campo 1",
        "col_c2": "Dato Campo 2",
        "col_new": "Nuovo Nome File Generato (Simulazione)",
        "btn_run": "🚀 ESEGUI SPLIT E RIDENOMINAZIONE",
        "config_title": "🛠️ Configura nuovo profilo dati senza codice",
        "prof_name": "Nome del Profilo (es. Nome Fornitore):",
        "prof_kw": "Parola chiave per riconoscerlo nel PDF (es. Ragione Sociale o P.IVA scritta nel file):",
        "c1_name": "Nome Campo 1 (es. EAN o SKU):",
        "c1_anc": "Testo fisso vicino al valore (Ancora): (es. 'Codice EAN' o 'Cod. Articolo')",
        "c2_name": "Nome Campo 2 (es. Peso o Marchio):",
        "c2_anc": "Testo fisso vicino al valore (Ancora): (es. 'Peso Netto' o 'Brand:')",
        "btn_save": "💾 Salva questo Profilo Dati",
        "warn_missing_title": "Campi Mancanti",
        "warn_missing_txt": "Il nome del profilo, la parola chiave identificativa e l'ancora del Campo 1 sono obbligatori.",
        "success_save": "Profilo '{name}' registrato correttamente!",
        "error_save": "Impossibile salvare il profilo su disco: ",
        "warn_drag": "Trascina o seleziona prima dei file PDF.",
        "warn_drag_title": "Attenzione",
        "not_recognized": "Non riconosciuto",
        "unknown": "Sconosciuto",
        "missing_data_sim": "[Profilo o Dati Mancanti: Non verrà diviso]",
        "error_process": "Impossibile elaborare il file ",
        "success_process": "Elaborazione terminata con successo!\nI file sono stati salvati in:\n{dir}"
    },
    "en": {
        "title": "RGBear PDF Smart Split & Rename v1.0",
        "tab_process": "🚀 Process Files",
        "tab_config": "⚙️ Configure Data Profiles",
        "guide_title": " 📋 QUICK GUIDE: HOW TO EXTRACT PAGES AND RENAME THEM ",
        "guide_text": """1. Drag and drop your PDF file below or click to select it from your computer.
2. Go to the "Configure Data Profiles" tab, insert the reference keywords you want to use for renaming, and save the profile.
3. Return to this tab ("Process Files") and select the saved profile from the dropdown menu.
4. Check the table to ensure the simulated new filename is correct, then click "RUN" at the bottom.""",
        "profile_lbl": "PDF Layout Profile:",
        "auto_detect": "Automatic Detection",
        "drop_lbl": "📥 DRAG & DROP YOUR PDF FILES HERE\nor click to browse from your computer",
        "preview_lbl": "Extracted data preview and filename simulation:",
        "col_orig": "Original File",
        "col_prof": "Detected Profile",
        "col_c1": "Field 1 Value",
        "col_c2": "Field 2 Value",
        "col_new": "Simulated New Filename",
        "btn_run": "🚀 RUN SPLIT AND RENAME",
        "config_title": "🛠️ Configure New Data Profile Without Code",
        "prof_name": "Profile Name (e.g., Supplier Name):",
        "prof_kw": "Keyword to identify this profile inside the PDF (e.g., Company Name or VAT number inside the text):",
        "c1_name": "Field 1 Name (e.g., EAN or SKU):",
        "c1_anc": "Fixed text next to the value (Anchor): (e.g., 'EAN Code' or 'Item Code:')",
        "c2_name": "Field 2 Name (e.g., Weight or Brand):",
        "c2_anc": "Fixed text next to the value (Anchor): (e.g., 'Net Weight' or 'Brand Name:')",
        "btn_save": "💾 Save This Data Profile",
        "warn_missing_title": "Missing Fields",
        "warn_missing_txt": "Profile name, identification keyword, and Field 1 anchor are mandatory.",
        "success_save": "Profile '{name}' successfully saved!",
        "error_save": "Could not save profile to disk: ",
        "warn_drag": "Please drag or select PDF files first.",
        "warn_drag_title": "Warning",
        "not_recognized": "Not Recognized",
        "unknown": "Unknown",
        "missing_data_sim": "[Missing Profile/Data: Will not split]",
        "error_process": "Could not process file ",
        "success_process": "Processing completed successfully!\nFiles saved in:\n{dir}"
    }
}

# ==========================================
# PARSING ENGINE
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
    
    pattern = rf"(?i){re.escape(ancora)}\s*[:\-–=]?\s*(.+)"
    match = re.search(pattern, testo)
    if match:
        valore = match.group(1).split("\n")[0].strip()
        valore = re.sub(r"^\s*\.{2,}\s*", "", valore)
        valore = re.sub(r"\s*\.{2,}\s*$", "", valore)
        return valore.strip()
    return ""

def clean_filename(name):
    # Sostituisce spazi multipli o tabulazioni con un singolo spazio
    name = re.sub(r'\s+', ' ', str(name)).strip()
    # Sostituisce i caratteri vietati nei sistemi operativi con un trattino
    return re.sub(r'[\\/:*?"<>|]', '-', name)

# ==========================================
# MAIN APPLICATION
# ==========================================
class RGBearApp:
    def __init__(self, root):
        self.root = root
        
        try:
            sys_lang = locale.getdefaultlocale()[0][:2].lower()
            self.current_lang = "it" if sys_lang == "it" else "en"
        except Exception:
            self.current_lang = "en"
            
        self.accent = "#2f80ed"
        self.bg_color = "#f5f6f8"
        self.root.configure(bg=self.bg_color)
        
        self.caricati_files = []
        self.profili = self.carica_profili()
        
        self.setup_ui_widgets()
        self.aggiorna_lingua_interfaccia()

    def setup_ui_widgets(self):
        lang_frame = tk.Frame(self.root, bg=self.bg_color)
        lang_frame.pack(anchor="e", padx=15, pady=2)
        
        tk.Label(lang_frame, text="Language / Lingua:", font=("Segoe UI", 9), bg=self.bg_color, fg="#555").pack(side="left", padx=5)
        self.combo_lang = ttk.Combobox(lang_frame, values=["Italiano", "English"], font=("Segoe UI", 9), state="readonly", width=10)
        self.combo_lang.set("Italiano" if self.current_lang == "it" else "English")
        self.combo_lang.pack(side="left")
        self.combo_lang.bind("<<ComboboxSelected>>", self.cambio_lingua_manuale)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_elaborazione = ttk.Frame(self.notebook)
        self.tab_configurazione = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_elaborazione, text="")
        self.notebook.add(self.tab_configurazione, text="")
        
        # --- BUILD TAB 1 ---
        self.info_frame = tk.LabelFrame(self.tab_elaborazione, font=("Segoe UI", 10, "bold"), bg="#fdfefe", fg=self.accent, bd=1, relief="solid")
        self.info_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.lbl_istruzioni = tk.Label(self.info_frame, font=("Segoe UI", 10), bg="#fdfefe", fg="#333333", justify="left", anchor="w", padx=10, pady=8)
        self.lbl_istruzioni.pack(fill="x")

        self.top_frame = tk.Frame(self.tab_elaborazione, pady=10, bg="#ffffff", relief="groove", bd=1)
        self.top_frame.pack(fill="x", padx=10, pady=5)
        
        self.lbl_prof_sel = tk.Label(self.top_frame, font=("Segoe UI", 10, "bold"), bg="#ffffff")
        self.lbl_prof_sel.pack(side="left", padx=10)
        
        self.combo_profili = ttk.Combobox(self.top_frame, font=("Segoe UI", 10), state="readonly", width=30)
        self.combo_profili.pack(side="left", padx=5)
        self.combo_profili.bind("<<ComboboxSelected>>", lambda e: self.ricarica_anteprima_tabella())

        self.drop_label = tk.Label(self.tab_elaborazione, font=("Segoe UI", 11, "bold"), bg="#ffffff", fg=self.accent, relief="groove", bd=2, cursor="hand2", pady=25)
        self.drop_label.pack(fill="x", padx=10, pady=5)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.handle_drop)
        self.drop_label.bind("<Button-1>", lambda e: self.sfoglia_files())

        self.lbl_anteprima = tk.Label(self.tab_elaborazione, font=("Segoe UI", 10, "italic"))
        self.lbl_anteprima.pack(anchor="w", padx=10, pady=(5, 0))

        frame_table = tk.Frame(self.tab_elaborazione)
        frame_table.pack(fill="both", expand=True, padx=10, pady=5)

        colonne = ("originale", "profilo", "campo1", "campo2", "nuovo_nome")
        self.tree = ttk.Treeview(frame_table, columns=colonne, show="headings")
        
        scroll_y = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.progress = ttk.Progressbar(self.tab_elaborazione, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        self.btn_run = tk.Button(self.tab_elaborazione, font=("Segoe UI", 12, "bold"), bg=self.accent, fg="white", activebackground="#1f6fd1", activeforeground="white", bd=0, pady=10, command=self.esegui_elaborazione)
        self.btn_run.pack(fill="x", padx=10, pady=10)

        # --- BUILD TAB 2 ---
        self.container_config = tk.Frame(self.tab_configurazione, padx=20, pady=20)
        self.container_config.pack(fill="both", expand=True)

        self.lbl_conf_title = tk.Label(self.container_config, font=("Segoe UI", 14, "bold"))
        self.lbl_conf_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        self.lbl_p_name = tk.Label(self.container_config, font=("Segoe UI", 10, "bold"))
        self.lbl_p_name.grid(row=1, column=0, sticky="w", pady=5)
        self.entry_prof_name = ttk.Entry(self.container_config, width=40)
        self.entry_prof_name.grid(row=1, column=1, sticky="w", pady=5, padx=10)

        self.lbl_p_kw = tk.Label(self.container_config, font=("Segoe UI", 10), justify="left")
        self.lbl_p_kw.grid(row=2, column=0, sticky="w", pady=5)
        self.entry_prof_key = ttk.Entry(self.container_config, width=40)
        self.entry_prof_key.grid(row=2, column=1, sticky="w", pady=5, padx=10)

        ttk.Separator(self.container_config, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=15)

        self.lbl_c1_n = tk.Label(self.container_config, font=("Segoe UI", 10))
        self.lbl_c1_n.grid(row=4, column=0, sticky="w", pady=5)
        self.entry_c1_nome = ttk.Entry(self.container_config, width=40)
        self.entry_c1_nome.grid(row=4, column=1, sticky="w", pady=5, padx=10)

        self.lbl_c1_a = tk.Label(self.container_config, font=("Segoe UI", 9, "italic"), justify="left")
        self.lbl_c1_a.grid(row=5, column=0, sticky="w", pady=5)
        self.entry_c1_ancora = ttk.Entry(self.container_config, width=40)
        self.entry_c1_ancora.grid(row=5, column=1, sticky="w", pady=5, padx=10)

        ttk.Separator(self.container_config, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=15)

        self.lbl_c2_n = tk.Label(self.container_config, font=("Segoe UI", 10))
        self.lbl_c2_n.grid(row=7, column=0, sticky="w", pady=5)
        self.entry_c2_nome = ttk.Entry(self.container_config, width=40)
        self.entry_c2_nome.grid(row=7, column=1, sticky="w", pady=5, padx=10)

        self.lbl_c2_a = tk.Label(self.container_config, font=("Segoe UI", 9, "italic"), justify="left")
        self.lbl_c2_a.grid(row=8, column=0, sticky="w", pady=5)
        self.entry_c2_ancora = ttk.Entry(self.container_config, width=40)
        self.entry_c2_ancora.grid(row=8, column=1, sticky="w", pady=5, padx=10)

        self.btn_salva = tk.Button(self.container_config, font=("Segoe UI", 11, "bold"), bg="#27ae60", fg="white", activebackground="#219653", activeforeground="white", bd=0, padx=20, pady=8, command=self.salva_nuovo_profilo)
        self.btn_salva.grid(row=9, column=0, columnspan=2, pady=25)

        self.build_footer()

    def aggiorna_lingua_interfaccia(self):
        ln = LANGUAGES[self.current_lang]
        self.root.title(ln["title"])
        self.notebook.tab(0, text=ln["tab_process"])
        self.notebook.tab(1, text=ln["tab_config"])
        
        self.info_frame.config(text=ln["guide_title"])
        self.lbl_istruzioni.config(text=ln["guide_text"])
        self.lbl_prof_sel.config(text=ln["profile_lbl"])
        self.drop_label.config(text=ln["drop_lbl"])
        self.lbl_anteprima.config(text=ln["preview_lbl"])
        self.btn_run.config(text=ln["btn_run"])
        
        self.tree.heading("originale", text=ln["col_orig"])
        self.tree.heading("profilo", text=ln["col_prof"])
        self.tree.heading("campo1", text=ln["col_c1"])
        self.tree.heading("campo2", text=ln["col_c2"])
        self.tree.heading("nuovo_nome", text=ln["col_new"])
        
        self.lbl_conf_title.config(text=ln["config_title"])
        self.lbl_p_name.config(text=ln["prof_name"])
        self.lbl_p_kw.config(text=ln["prof_kw"])
        self.lbl_c1_n.config(text=ln["c1_name"])
        self.lbl_c1_a.config(text=ln["c1_anc"])
        self.lbl_c2_n.config(text=ln["c2_name"])
        self.lbl_c2_a.config(text=ln["c2_anc"])
        self.btn_salva.config(text=ln["btn_save"])
        
        vecchio_valore = self.combo_profili.get()
        lista_chiavi = list(self.profili.keys())
        
        if "Automatic Detection" in lista_chiavi: self.profili[ln["auto_detect"]] = self.profili.pop("Automatic Detection")
        if "Rilevamento Automatico" in lista_chiavi: self.profili[ln["auto_detect"]] = self.profili.pop("Rilevamento Automatico")
            
        self.combo_profili["values"] = list(self.profili.keys())
        
        if vecchio_valore in ["Rilevamento Automatico", "Automatic Detection", ""]:
            self.combo_profili.set(ln["auto_detect"])
        else:
            self.combo_profili.set(vecchio_valore)
            
        self.ricarica_anteprima_tabella()

    def cambio_lingua_manuale(self, event):
        scelta = self.combo_lang.get()
        self.current_lang = "it" if scelta == "Italiano" else "en"
        self.aggiorna_lingua_interfaccia()

    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        self.caricati_files = [f for f in files if f.lower().endswith(".pdf")]
        self.ricarica_anteprima_tabella()

    def sfoglia_files(self):
        ftype = "PDF Documents" if self.current_lang == "en" else "Documenti PDF"
        files = filedialog.askopenfilenames(filetypes=[(ftype, "*.pdf")])
        if files:
            self.caricati_files = list(files)
            self.ricarica_anteprima_tabella()

    def ricarica_anteprima_tabella(self):
        self.tree.delete(*self.tree.get_children())
        ln = LANGUAGES[self.current_lang]
        profilo_scelto = self.combo_profili.get()
        
        for path in self.caricati_files:
            nome_file = os.path.basename(path)
            testo_anteprima = estrai_testo_pagina(path, 0)
            profilo_effettivo = profilo_scelto
            
            if profilo_scelto in ["Rilevamento Automatico", "Automatic Detection"]:
                profilo_effettivo = ln["not_recognized"]
                for p_name, p_data in self.profili.items():
                    if p_data.get("is_auto"): continue
                    kw = p_data.get("keyword_identificazione", "").lower()
                    if kw and kw in testo_anteprima.lower():
                        profilo_effettivo = p_name
                        break
            
            val1, val2 = "", ""
            if profilo_effettivo in self.profili:
                profiling_data = self.profili[profilo_effettivo]
                if profiling_data and not profiling_data.get("is_auto"):
                    val1 = estrai_valore_da_ancora(testo_anteprima, profiling_data.get("campo_1_ancora", ""))
                    val2 = estrai_valore_da_ancora(testo_anteprima, profiling_data.get("campo_2_ancora", ""))
            
            mostra_v1 = val1 if val1 else "N.D." if self.current_lang == "it" else "N.A."
            mostra_v2 = val2 if val2 else "N.D." if self.current_lang == "it" else "N.A."
            
            if val1 or val2:
                pezzi = [clean_filename(v) for v in [val1, val2] if v]
                nuovo_nome_simulato = " - ".join(pezzi) + f"_{'pag' if self.current_lang == 'it' else 'page'}_X.pdf"
            else:
                nuovo_nome_simulato = ln["missing_data_sim"]
                
            self.tree.insert("", "end", values=(nome_file, profilo_effettivo, mostra_v1, mostra_v2, nuovo_nome_simulato))

    def esegui_elaborazione(self):
        ln = LANGUAGES[self.current_lang]
        if not self.caricati_files:
            messagebox.showwarning(ln["warn_missing_title"], ln["warn_drag"])
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
                    profilo_effettivo = profilo_scelto
                    
                    if profilo_scelto in ["Rilevamento Automatico", "Automatic Detection"]:
                        profilo_effettivo = ln["unknown"]
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
                    
                    writer = PdfWriter()
                    writer.add_page(page)
                    
                    if val1 or val2:
                        nomi_puliti = [clean_filename(v) for v in [val1, val2] if v]
                        nuovo_nome = " - ".join(nomi_puliti) + ".pdf"
                    else:
                        suff = "pagina" if self.current_lang == "it" else "page"
                        nuovo_nome = f"{base_orig}_{suff}_{idx+1}.pdf"
                        
                    final_path = os.path.join(out_dir, nuovo_nome)
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
                messagebox.showerror("Error", f"{ln['error_process']}{os.path.basename(path)}: {str(e)}")
                
        messagebox.showinfo("Success / Successo", ln["success_process"].format(dir=out_dir))
        self.caricati_files = []
        self.tree.delete(*self.tree.get_children())
        self.progress["value"] = 0

    # ==========================================
    # PERSISTENZA PROFILI CON DATI DI ESEMPIO GENERATI DI DEFAULT
    # ==========================================
    def carica_profili(self):
        ln = LANGUAGES[self.current_lang]
        
        # Struttura dati di esempio standard richiesta dall'utente (senza brand reali)
        def_auto_key = ln["auto_detect"]
        default_data = {
            def_auto_key: {
                "is_auto": True
            },
            "Schede Esempio Brand1": {
                "is_auto": False,
                "keyword_identificazione": "Nome marchio esempio1",
                "campo_1_nome": "Codice EAN",
                "campo_1_ancora": "codice ean",
                "campo_2_nome": "Marchio",
                "campo_2_ancora": "marchio"
            },
            "Schede Esempio Brand2": {
                "is_auto": False,
                "keyword_identificazione": "Nome marchio esempio2",
                "campo_1_nome": "Articolo",
                "campo_1_ancora": "cod. articolo",
                "campo_2_nome": "TMC",
                "campo_2_ancora": "termine minimo di conservazione"
            }
        }

        # Se il file JSON non esiste, lo crea salvando i dati di esempio iniziali
        if not os.path.exists(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, indent=4, ensure_ascii=False)
                return default_data
            except Exception:
                return default_data

        # Se esiste già, carica semplicemente i dati presenti
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                caricati = json.load(f)
                # Assicuriamoci che la chiave di rilevamento automatico ci sia sempre
                if def_auto_key not in caricati and "Automatic Detection" not in caricati and "Rilevamento Automatico" not in caricati:
                    caricati[def_auto_key] = {"is_auto": True}
                return caricati
        except Exception:
            return default_data

    def salva_nuovo_profilo(self):
        ln = LANGUAGES[self.current_lang]
        name = self.entry_prof_name.get().strip()
        kw = self.entry_prof_key.get().strip()
        c1_n = self.entry_c1_nome.get().strip()
        c1_a = self.entry_c1_ancora.get().strip()
        c2_n = self.entry_c2_nome.get().strip()
        c2_a = self.entry_c2_ancora.get().strip()
        
        if not name or not kw or not c1_a:
            messagebox.showwarning(ln["warn_missing_title"], ln["warn_missing_txt"])
            return
            
        self.profili[name] = {
            "is_auto": False,
            "keyword_identificazione": kw,
            "campo_1_nome": c1_n if c1_n else "Field 1",
            "campo_1_ancora": c1_a,
            "campo_2_nome": c2_n if c2_n else "Field 2",
            "campo_2_ancora": c2_a
        }
        
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profili, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Saved / Salvato", ln["success_save"].format(name=name))
            
            self.entry_prof_name.delete(0, tk.END)
            self.entry_prof_key.delete(0, tk.END)
            self.entry_c1_nome.delete(0, tk.END)
            self.entry_c1_ancora.delete(0, tk.END)
            self.entry_c2_nome.delete(0, tk.END)
            self.entry_c2_ancora.delete(0, tk.END)
            
            self.combo_profili["values"] = list(self.profili.keys())
            self.notebook.select(self.tab_elaborazione)
        except Exception as e:
            messagebox.showerror("Error", f"{ln['error_save']}{str(e)}")

    def build_footer(self):
        footer_bg = "#e9edf5"
        footer = tk.Frame(self.root, bg=footer_bg, padx=15, pady=8)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="© RGBear by Massimo D'Ambrogio", font=("Segoe UI", 9), bg=footer_bg, fg="#444").pack(side="left")
        
        site_lbl = tk.Label(footer, text=" | rgbear.it", fg="#555", bg=footer_bg, cursor="hand2", font=("Segoe UI", 9))
        site_lbl.pack(side="left", padx=5)
        site_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://rgbear.it"))

# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    root.geometry("1000x880")
    root.resizable(True, True) 
    
    if os.path.exists("pdf-spliterenamebycontent256.ico"):
        root.iconbitmap("pdf-spliterenamebycontent256.ico")
        
    RGBearApp(root)
    root.mainloop()
