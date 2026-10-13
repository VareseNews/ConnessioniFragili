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
| `script/` | Generatori dei grafici (Python + template HTML) |

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

## Dati e privacy

Le risposte vengono da studenti tra i 15 e i 20 anni, in buona parte minorenni. Per questo:

- nei file pubblicati ci sono **solo percentuali aggregate**, mai conteggi o risposte individuali;
- nelle wordcloud compaiono solo parole presenti in almeno tre risposte diverse;
- il CSV del questionario **non fa parte del repository**: `.gitignore` esclude i file `.csv` e `.xlsx`.

## Rigenerare i grafici

Se cambiano i dati o lo stile, scarica il foglio come CSV in una cartella **fuori** dal repository e lancia:

```bash
python3 -I script/gen.py /percorso/risposte.csv grafici
python3 -I script/wc.py /percorso/risposte.csv grafici
```

Lo stile (colori, font, dimensioni) è nei due template, `script/template.html` e `script/wc_template.html`. I testi e la scelta delle domande sono in `gen.py` e `wc.py`. Gli script richiedono solo Python 3, senza librerie esterne. Leggono le colonne in base alla loro posizione, quindi se cambia la struttura del foglio vanno aggiornati.
