📖 RGBear PDF Split & Rename

Benvenuto in RGBear PDF Split & Rename.

Il software divide documenti PDF multipagina in file singoli e assegna automaticamente a ciascuna pagina un nome basato sulle informazioni estratte dal contenuto.

L’obiettivo è semplice: ridurre il lavoro manuale a pochi clic.

🚀 Funzionalità principali
📄 Lettura automatica di PDF multipagina
✂️ Split automatico per pagina
🧠 Estrazione intelligente dei dati dal testo
🏷️ Rinominazione automatica dei file
📦 Supporto drag & drop
📊 Anteprima campi estratti prima dell’elaborazione
🔁 Gestione automatica di nomi duplicati


Utilizzo (Workflow quotidiano)

Per elaborare i PDF basta seguire 3 passaggi:

1. Carica i file
Trascina uno o più PDF nell’area dedicata oppure usa il pulsante di selezione.

2. Analizza il contenuto
Il programma estrae automaticamente il testo e mostra i campi rilevati (es. Codice Articolo, EAN, Marchio).

3. Scegli i campi per il nome file
Seleziona fino a 2 campi tra quelli disponibili.
L’ordine di selezione determina il nome finale del file.

4. Avvia l’elaborazione
Clicca su ESEGUI per:

Dividere il PDF in pagine
Rinominare automaticamente i file

I file vengono salvati nella stessa cartella del PDF originale.

🧩 Parser intelligente (come funziona)

Il sistema di estrazione dati non è legato a un fornitore specifico.

Funziona così:

analizza il testo del PDF riga per riga
riconosce pattern comuni come:
Etichetta ..... Valore
Etichetta: Valore
strutture a colonne
applica anche alcune regole generiche (es. codici alfanumerici, EAN, ecc.)
Esempi di campi rilevati automaticamente:
Codice Articolo → 8102
TMC → 30 gg
Codice EAN → 8000889100695
Marchio → RGBear
⚙️ Configurazione (opzionale avanzata)

Il parser è progettato per essere generico, ma può essere esteso in futuro con:

regole personalizzabili per PDF diversi
“ancore testuali” (es. parole chiave prima del valore)
profili per fornitori specifici

Questa funzione è pensata per utenti avanzati o ambienti aziendali con formati PDF ricorrenti.

💡 Note importanti
Se un valore non viene trovato, la pagina viene comunque salvata con nome provvisorio
I duplicati vengono automaticamente numerati (_1, _2, ecc.)
Il sistema ignora spazi, puntini e formattazioni irregolari
Funziona con PDF testuali e (parzialmente) con PDF scannerizzati

🎯 Obiettivo del progetto
Ridurre il lavoro manuale nella gestione di documenti e schede tecniche, rendendo il processo:

veloce
automatico
replicabile
scalabile
🧑‍💻

Sviluppato da RGBear
🌐 https://rgbear.it
💻 https://github.com/RGBearMD/pdf-split-and-rename-by-content