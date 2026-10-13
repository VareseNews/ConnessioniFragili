"""Wordcloud delle risposte aperte. Uso: python3 -I wc.py <csv> <cartella_output>

Per ogni parola si salva solo la quota di risposte che la contengono (%).
Si tengono solo parole presenti in almeno MIN_DOCS risposte, per non esporre espressioni rare.
"""
import csv, json, re, sys, collections, pathlib

CSV, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
TEMPLATE = (pathlib.Path(__file__).parent / "wc_template.html").read_text(encoding="utf-8")
rows = list(csv.reader(open(CSV, encoding="utf-8")))
DATA = rows[1:]

MIN_DOCS, MAX_WORDS = 3, 70

STOP = set("""
a ad al allo ai agli all alla alle dal dallo dai dagli dall dalla dalle del dello dei degli dell della delle
di da in con su per tra fra nel nello nei negli nell nella nelle sul sullo sui sugli sull sulla sulle col coi
il lo la i gli le l un uno una un' e ed o od ma se che chi cui non né ne ci vi si mi ti lo li la le
io tu lui lei noi voi loro me te sé sè esso essa essi esse mio mia miei mie tuo tua tuoi tue suo sua suoi sue
nostro nostra nostri nostre vostro vostra vostri vostre proprio propria propri proprie
questo questa questi queste quello quella quelli quelle quel quei quegli ciò cio
sono sei è e' siamo siete era erano sia siano sarebbe sarebbero sta stanno sto stai stiamo stato stata stati state
ho hai ha abbiamo avete hanno avere avrebbe avrebbero abbia aver essere fare fatto fatta far fa faccio fanno
può puo possono posso poter potere potrebbe possa devono dovrebbero deve bisogna vuol
più piu meno molto molta molti molte tanto tanta tanti tante troppo troppa poco poca pochi
anche ancora già gia sempre mai spesso volte volta ogni tutto tutta tutti tutte altro altra altri altre
come dove quando perché perchè perche quindi però pero invece oppure anzi cosi così poi ora qui qua lì li
solo soltanto magari forse proprio davvero veramente comunque soprattutto almeno nemmeno neanche neppure
cosa cose qualcosa qualcuno ogni uno alcuni alcune certi certe tipo modo parte esempio senso
dire detto vorrei vorrebbe capissero capire dovrebbe penso pensano credo secondo
racconterebbe racconterebbero direbbe potesse farebbe
ormai maggior direi viene vengono semplicemente abbastanza probabilmente quasi prima preferisco rispondere trovo tengo posto grazie
sono sto stai sta già oltre tra senza dietro davanti dentro fuori sopra sotto
ecc etc cioè cioe quale quali quanto quanta quanti quante tale tali stesso stessa stessi stesse
""".split())

EXTRA = {
    39: {"adulti"},          # ripete la domanda
    40: {"telefono", "sanno"},  # ripetono la domanda
}
MERGE = {"bho": "boh", "passione": "passioni", "problema": "problemi", "reali": "reale",
         "amicizia": "amicizie", "negativa": "negativo", "negative": "negativo", "negativi": "negativo",
         "ragazzo": "ragazzi", "persona": "persone", "cellulari": "cellulare", "schermi": "schermo"}


def words(text):
    text = text.lower().replace("’", "'")
    for t in re.findall(r"[a-zàèéìòù]+", text):
        t = MERGE.get(t, t)
        if len(t) > 2:
            yield t


def cloud(i, fname, title, sub):
    answers = [r[i].strip() for r in DATA if r[i].strip()]
    df = collections.Counter()
    for a in answers:
        df.update({w for w in words(a) if w not in STOP and w not in EXTRA.get(i, set())})
    top = [(w, n) for w, n in df.most_common() if n >= MIN_DOCS][:MAX_WORDS]
    spec = {"title": title, "sub": sub,
            "words": [{"t": w, "p": round(100 * n / len(answers), 2)} for w, n in top],
            "note": "Fonte: questionario Connessioni fragili. Sono escluse articoli, preposizioni e altre parole d’uso comune, "
                    "e le parole presenti in meno di tre risposte."}
    html = TEMPLATE.replace("{{TITLE}}", title).replace("{{SPEC}}", json.dumps(spec, ensure_ascii=False, indent=1))
    (OUT / fname).write_text(html, encoding="utf-8")
    print("scritto", fname, len(top), "parole:", ", ".join(w for w, _ in top))


cloud(39, "06-wordcloud-adulti.html",
      "Se potessi dire agli adulti una cosa sulla vita online dei ragazzi, cosa vorresti che capissero?",
      "Le parole più usate nelle risposte: più è grande, più spesso compare")
cloud(40, "07-wordcloud-telefono.html",
      "Se il tuo telefono potesse raccontare agli adulti una cosa della tua vita digitale che loro non sanno, cosa racconterebbe?",
      "Le parole più usate nelle risposte: più è grande, più spesso compare")
