"""Wordcloud delle risposte aperte. Uso: python3 -I wc.py <csv> <cartella_output>

Per ogni parola si salva solo la quota di risposte che la contengono (%).
Si tengono solo parole presenti in almeno MIN_DOCS risposte, per non esporre espressioni rare.
Con l'aggiornamento automatico entrano parole nuove senza revisione, quindi si scartano anche
i probabili nomi propri (scritti quasi sempre con la maiuscola a metà frase) e le parolacce.
Un file viene riscritto solo se le parole o le percentuali cambiano.
"""
import csv, json, re, sys, collections, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

CSV, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
TEMPLATE = (pathlib.Path(__file__).parent / "wc_template.html").read_text(encoding="utf-8")
rows = list(csv.reader(open(CSV, encoding="utf-8")))
H, DATA = rows[0], rows[1:]

EXPECT = {39: "Se potessi dire agli adulti", 40: "Se il tuo telefono potesse"}
for i, frag in EXPECT.items():
    if i >= len(H) or frag.lower() not in H[i].lower():
        sys.exit(f"Colonna {i} inattesa: mi aspettavo '{frag}', trovo '{H[i] if i < len(H) else '(assente)'}'")

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

BLOCK = set("""
cazzo cazzi cazzata cazzate merda merde culo stronzo stronza stronzi stronze puttana puttane troia troie
vaffanculo fanculo coglione coglioni cogliona figa fica minchia fottere fottuto fottuta porco porca dio madonna
frocio froci ricchione negro negri zoccola zoccole bastardo bastarda bastardi mongoloide ritardato ritardata
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


def proper_nouns(answers):
    """Parole scritte con la maiuscola a metà frase in più di metà delle occorrenze: probabili nomi."""
    caps, tot = collections.Counter(), collections.Counter()
    for a in answers:
        for m in re.finditer(r"[A-Za-zÀ-ÿ]+", a.replace("’", "'")):
            w = MERGE.get(m.group().lower(), m.group().lower())
            tot[w] += 1
            before = a[:m.start()].rstrip()
            if m.group()[0].isupper() and before and before[-1] not in ".!?:\"«(\n":
                caps[w] += 1
    return {w for w in tot if caps[w] * 2 > tot[w]}


MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
_now = datetime.now(ZoneInfo("Europe/Rome"))
UPDATED = f"Dati aggiornati al {_now.day} {MESI[_now.month - 1]} {_now.year}, ore {_now:%H:%M}."
SPEC_RE = re.compile(r"const SPEC = \{.*?\};\n", re.S)


def unchanged(path, title, spec):
    try:
        text = path.read_text(encoding="utf-8")
        prev = json.loads(SPEC_RE.search(text).group()[len("const SPEC = "):-2])
    except (OSError, AttributeError, ValueError):
        return False
    same_template = SPEC_RE.sub("", text) == TEMPLATE.replace("{{TITLE}}", title).replace("const SPEC = {{SPEC}};\n", "")
    return same_template and {k: v for k, v in prev.items() if k != "updated"} == spec


def cloud(i, fname, title, sub):
    answers = [r[i].strip() for r in DATA if len(r) > i and r[i].strip()]
    skip = STOP | BLOCK | EXTRA.get(i, set()) | proper_nouns(answers)
    df = collections.Counter()
    for a in answers:
        df.update({w for w in words(a) if w not in skip})
    top = sorted(((w, n) for w, n in df.items() if n >= MIN_DOCS), key=lambda x: (-x[1], x[0]))[:MAX_WORDS]
    spec = {"title": title, "sub": sub,
            "words": [{"t": w, "p": round(100 * n / len(answers), 2)} for w, n in top],
            "note": "Fonte: questionario Connessioni fragili. Sono esclusi articoli, preposizioni e altre parole d’uso comune, "
                    "e le parole presenti in meno di tre risposte."}
    path = OUT / fname
    if unchanged(path, title, spec):
        print("invariato", fname)
        return
    spec["updated"] = UPDATED
    html = TEMPLATE.replace("{{TITLE}}", title).replace("{{SPEC}}", json.dumps(spec, ensure_ascii=False, indent=1))
    path.write_text(html, encoding="utf-8")
    print("scritto", fname, len(top), "parole:", ", ".join(w for w, _ in top))


cloud(39, "06-wordcloud-adulti.html",
      "Se potessi dire agli adulti una cosa sulla vita online dei ragazzi, cosa vorresti che capissero?",
      "Le parole più usate nelle risposte: più è grande, più spesso compare")
cloud(40, "07-wordcloud-telefono.html",
      "Se il tuo telefono potesse raccontare agli adulti una cosa della tua vita digitale che loro non sanno, cosa racconterebbe?",
      "Le parole più usate nelle risposte: più è grande, più spesso compare")
