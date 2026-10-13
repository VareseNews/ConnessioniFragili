# Connessioni fragili: grafici

Grafici interattivi tratti dal questionario *Connessioni fragili* sulla vita online dei ragazzi, preparati per essere incorporati negli articoli di VareseNews (larghezza 600 px).

La pagina [`index.html`](index.html) mostra l'anteprima di tutti i grafici e, per ognuno, il codice da incorporare già pronto da copiare.

## Contenuto

| File | Tema |
|---|---|
| `grafici/01-percezione-di-se.html` | Come ci si vede online: like, confronto, filtri, giudizio |
| `grafici/02-conflitti-cyberbullismo.html` | Conflitti, prese in giro e insulti, reazioni |
| `grafici/03-intimita-privacy.html` | Pressioni, contenuti diffusi, profili falsi, segnalazioni |
| `grafici/04-adulti-scuola.html` | A chi ci si rivolge, famiglia, adulti, scuola |
| `grafici/05-benessere.html` | Sonno, ansia, umore negli ultimi tre mesi |
| `grafici/06-wordcloud-adulti.html` | Wordcloud: cosa diresti agli adulti |
| `grafici/07-wordcloud-telefono.html` | Wordcloud: cosa racconterebbe il telefono |
| `script/` | Generatori dei grafici (Python + template HTML) e download dal foglio |
| `.github/workflows/aggiorna-grafici.yml` | Aggiornamento automatico ogni ora |

Ogni grafico è un unico file HTML: CSS e JavaScript sono dentro il file. Dall'esterno vengono caricati solo i font (Google Fonts) e, per le wordcloud, la libreria `d3-cloud` da jsdelivr.

## Pubblicazione su GitHub Pages

1. Carica il contenuto di questa cartella nel repository.
2. Su GitHub: **Settings → Pages → Build and deployment**, scegli *Deploy from a branch*, branch `main`, cartella `/ (root)`.
3. Dopo un paio di minuti il sito è online su `https://<utente>.github.io/<repository>/`.

Il file vuoto `.nojekyll` dice a GitHub Pages di servire i file così come sono, senza elaborarli.

## Come incorporare un grafico

Apri `index.html` dal sito pubblicato e copia il codice sotto il grafico che ti serve: gli indirizzi sono già quelli giusti. Il codice ha questa forma:

```html
<iframe src="https://<utente>.github.io/<repository>/grafici/01-percezione-di-se.html"
        title="Come ci si vede online" width="100%" height="830" scrolling="no" loading="lazy"
        style="border:0;width:100%;max-width:600px;display:block;margin:0 auto;"></iframe>
<script>/* adatta l'altezza dell'iframe al contenuto */</script>
```

L'altezza di partenza basta a mostrare tutto il grafico anche su smartphone. Lo script accorcia l'iframe quando c'è più spazio, per esempio da computer. Se il CMS rimuove lo script, il grafico si vede comunque per intero, con un po' di spazio bianco in fondo sugli schermi larghi.

## Aggiornamento automatico

Ogni ora, al minuto 7, il workflow `.github/workflows/aggiorna-grafici.yml`:

1. scarica le risposte dal foglio Google, che resta **privato**, usando un account di servizio;
2. rigenera i 7 grafici con `script/gen.py` e `script/wc.py`;
3. fa il commit solo se le percentuali sono cambiate. GitHub Pages pubblica la nuova versione in un paio di minuti.

Ogni grafico riporta in nota la data e l'ora dell'ultimo aggiornamento dei dati. Il CSV con le risposte resta nella cartella temporanea della macchina di GitHub e viene cancellato a fine lavoro: non entra mai nel repository.

Il workflow si può lanciare anche a mano: tab **Actions → Aggiorna grafici → Run workflow**. Parte da solo anche quando modifichi i file in `script/`.

### Configurazione (una volta sola)

**A. Crea l'account di servizio su Google Cloud**

1. Vai su <https://console.cloud.google.com>, accedi con il tuo account Google e crea un nuovo progetto (per esempio `connessioni-fragili`).
2. Nel menu **API e servizi → Libreria**, cerca **Google Sheets API** e premi **Abilita**.
3. Vai in **IAM e amministrazione → Account di servizio → Crea account di servizio**. Dagli un nome (per esempio `grafici`) e salta i passaggi sui ruoli: non servono.
4. Apri l'account appena creato, scheda **Chiavi → Aggiungi chiave → Crea nuova chiave → JSON**. Il browser scarica un file `.json`: è la chiave, trattala come una password.
5. Copia l'indirizzo email dell'account di servizio, quello che finisce con `.iam.gserviceaccount.com`.

**B. Condividi il foglio con l'account di servizio**

6. Apri il foglio delle risposte → **Condividi**, incolla l'email del punto 5, scegli **Visualizzatore** e togli la spunta da "Invia notifica".
7. Già che ci sei, riporta l'**Accesso generale** a **Con limitazioni**: il link pubblico non serve più.

**C. Aggiungi i segreti su GitHub**

8. Nel repository: **Settings → Secrets and variables → Actions → New repository secret**. Crea questi tre segreti:

| Nome | Valore |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT` | tutto il contenuto del file `.json` del punto 4 (aprilo con TextEdit, seleziona tutto, copia e incolla) |
| `SHEET_ID` | l'ID del foglio, cioè la parte dell'indirizzo tra `/d/` e `/edit` |
| `SHEET_GID` | il numero della scheda delle risposte, quello dopo `gid=` nell'indirizzo |

9. **Settings → Actions → General → Workflow permissions**: seleziona **Read and write permissions** e salva.
10. Vai nel tab **Actions**, apri **Aggiorna grafici** e premi **Run workflow**. Se diventa verde, è tutto a posto.
11. Cancella il file `.json` dal computer: d'ora in poi la chiave vive solo nei segreti di GitHub.

### Se il workflow fallisce

Apri il run in rosso nel tab **Actions** e leggi il messaggio:

- **Manca la variabile…** → manca un segreto oppure ha il nome sbagliato (punto 8);
- **Accesso negato (403)** → il foglio non è condiviso con l'account di servizio (punto 6), oppure la Google Sheets API non è attiva (punto 2);
- **Foglio non trovato (404)** o **Nessuna scheda con gid…** → controlla `SHEET_ID` e `SHEET_GID`;
- **Colonna … inattesa** → nel modulo sono state aggiunte, tolte o spostate delle domande. I grafici restano all'ultima versione corretta finché non si aggiornano gli script.

Quando un run fallisce GitHub ti manda una mail, e i grafici pubblicati restano quelli dell'ultimo aggiornamento riuscito.

## Dati e privacy

Le risposte vengono da studenti tra i 15 e i 20 anni, in buona parte minorenni. Per questo:

- il foglio resta privato: lo legge solo l'account di servizio, con permesso di sola lettura;
- nei file pubblicati ci sono **solo percentuali aggregate**, mai conteggi o risposte individuali;
- nelle wordcloud compaiono solo parole presenti in almeno tre risposte diverse. Siccome le parole nuove entrano senza revisione, lo script scarta anche i probabili nomi propri (parole scritte quasi sempre con la maiuscola a metà frase) e le parolacce. Conviene comunque dare un'occhiata alle wordcloud ogni tanto;
- il repository non contiene mai i dati grezzi né la chiave: `.gitignore` esclude i file `.csv`, `.xlsx` e `.json`.

## Rigenerare i grafici a mano

Se vuoi provare una modifica prima di pubblicarla, scarica il foglio come CSV in una cartella **fuori** dal repository e lancia:

```bash
python3 -I script/gen.py /percorso/risposte.csv grafici
python3 -I script/wc.py /percorso/risposte.csv grafici
```

Lo stile (colori, font, dimensioni) è nei due template, `script/template.html` e `script/wc_template.html`. I testi e la scelta delle domande sono in `gen.py` e `wc.py`. Questi due script richiedono solo Python 3; `fetch.py`, che scarica il foglio, ha bisogno anche di `google-auth` e `requests`. Gli script leggono le colonne in base alla loro posizione e controllano che le intestazioni corrispondano: se cambia la struttura del modulo, vanno aggiornati.
