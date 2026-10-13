"""Genera i grafici HTML di Connessioni fragili a partire dal CSV del questionario.

Uso: python3 -I gen.py <csv> <cartella_output>
Nei file finisce solo la percentuale per ogni opzione, mai i conteggi.
Un file viene riscritto solo se i dati sono cambiati: la data di aggiornamento
indica quindi l'ultima volta in cui le percentuali si sono mosse.
"""
import csv, json, re, sys, collections, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

CSV, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
TEMPLATE = (pathlib.Path(__file__).parent / "template.html").read_text(encoding="utf-8")

rows = list(csv.reader(open(CSV, encoding="utf-8")))
H, DATA = rows[0], rows[1:]

# Controllo di sicurezza: se le colonne del modulo cambiano posizione, meglio fermarsi
# che pubblicare grafici sbagliati.
EXPECT = {
    5: "Quando sei online senti", 6: "filtri", 7: "Guardando ciò che altre", 8: "Quanto ti preoccupa il giudizio",
    9: "Hai mai cancellato", 10: "controllare like", 11: "giudicato/a o escluso/a", 12: "litigio o conflitto",
    13: "Quanto ti ha fatto stare male", 15: "subire prese in giro", 17: "Ne hai parlato con un adulto",
    19: "vedere online insulti", 20: "come hai reagito", 21: "sentire meglio", 22: "sotto pressione",
    23: "Conosci qualcuno", 24: "diffusi senza il tuo permesso", 25: "profilo falso", 26: "sapresti cosa fare",
    27: "segnalare o denunciare", 28: "Cosa ti ha frenato", 29: "a chi ti capita di rivolgerti",
    30: "rischi legati a internet", 31: "adulti di riferimento conoscono", 32: "a scuola",
    33: "Dormire male", 34: "Andare a dormire più tardi", 35: "ansia o pressione", 36: "irritabile",
    37: "giù di morale",
}
for i, frag in EXPECT.items():
    if i >= len(H) or frag.lower() not in H[i].lower():
        sys.exit(f"Colonna {i} inattesa: mi aspettavo '{frag}', trovo '{H[i] if i < len(H) else '(assente)'}'")

NR = "Preferisco non rispondere"

# Colori
S1, S2, S3, S4, S5 = "#F5DFE0", "#E8AEB0", "#D0777A", "#9E2024", "#5E1215"
GRAY, NO, NO2, NRC = "#5F6466", "#CDD0D1", "#A3A8AA", "#E6E8E9"
DARK, WHITE = "#1F2223", "#FFFFFF"


def col(i, where=None):
    return [r[i].strip() for r in DATA if len(r) > i and r[i].strip() and (where is None or where(r))]


def pcts(vals, keys, merge=None):
    merge = merge or {}
    c = collections.Counter(merge.get(v, v) for v in vals)
    unknown = set(c) - set(keys)
    if unknown:  # risposta mai vista: la segnalo e la escludo dal calcolo
        print("  attenzione, risposte non previste escluse:", unknown, file=sys.stderr)
    tot = sum(c[k] for k in keys)
    return [round(100 * c[k] / tot, 2) for k in keys]


def legend(*items):
    return [{"key": k, "color": c, "ink": i} for k, c, i in items]


FREQ_KEYS = ["Mai", "Raramente", "Qualche volta", "Spesso", "Molto spesso", NR]
FREQ = legend(("Mai", S1, DARK), ("Raramente", S2, DARK), ("Qualche volta", S3, DARK),
              ("Spesso", S4, WHITE), ("Molto spesso", S5, WHITE), ("Non risponde", NRC, DARK))
SCALE_KEYS = ["1", "2", "3", "4", "5"]
SCALE = legend(("1 · per niente", S1, DARK), ("2", S2, DARK), ("3", S3, DARK),
               ("4", S4, WHITE), ("5 · moltissimo", S5, WHITE))
YN_KEYS = ["Sì", "No", NR]
YN = legend(("Sì", S4, WHITE), ("No", NO, DARK), ("Non risponde", NRC, DARK))
YNS_KEYS = ["Sì", "Non so", "No", NR]
YNS = legend(("Sì", S4, WHITE), ("Non so", GRAY, WHITE), ("No", NO, DARK), ("Non risponde", NRC, DARK))
M3_KEYS = ["Mai", "Qualche volta", "Spesso", NR]
M3 = legend(("Mai", S1, DARK), ("Qualche volta", S3, DARK), ("Spesso", S4, WHITE), ("Non risponde", NRC, DARK))


def stack(i, keys, q, where=None, merge=None):
    return {"q": q, "p": pcts(col(i, where), keys, merge)}


def options(i, keys, merge=None):
    """Scelta multipla: percentuale di chi ha risposto alla domanda che ha scelto ogni opzione."""
    merge = merge or {}
    vals = col(i)
    c = collections.Counter()
    for v in vals:
        chosen = set()
        for o in v.split("\n"):
            o = o.strip()
            m = merge.get(o, o)
            for x in (m if isinstance(m, list) else [m]):
                chosen.add(x if x in keys or x == NR else "Altro")
        c.update(chosen)
    items = [{"label": k, "p": round(100 * c[k] / len(vals), 2)} for k in keys]
    items.sort(key=lambda d: -d["p"])
    if c["Altro"]:
        items.append({"label": "Altro", "p": round(100 * c["Altro"] / len(vals), 2)})
    return items


def share(i, ok, where=None):
    vals = col(i, where)
    return round(100 * sum(v in ok for v in vals) / len(vals), 2)


MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
_now = datetime.now(ZoneInfo("Europe/Rome"))
UPDATED = f"Dati aggiornati al {_now.day} {MESI[_now.month - 1]} {_now.year}, ore {_now:%H:%M}."


def old_spec(path):
    try:
        return json.loads(re.search(r"const SPEC = (\{.*?\});\n", path.read_text(encoding="utf-8"), re.S).group(1))
    except (OSError, AttributeError, ValueError):
        return None


def page(fname, title, blocks, note):
    spec = {"blocks": blocks, "note": note}
    path = OUT / fname
    prev = old_spec(path)
    if prev and template_unchanged(path, title) and {k: v for k, v in prev.items() if k != "updated"} == spec:
        print("invariato", fname)
        return
    spec["updated"] = UPDATED
    html = TEMPLATE.replace("{{TITLE}}", title).replace("{{SPEC}}", json.dumps(spec, ensure_ascii=False, indent=1))
    path.write_text(html, encoding="utf-8")
    print("scritto", fname)


def template_unchanged(path, title):
    """Vero se il file è stato generato con il template attuale (a parte i dati)."""
    current = re.sub(r"const SPEC = \{.*?\};\n", "", path.read_text(encoding="utf-8"), flags=re.S)
    fresh = re.sub(r"const SPEC = \{\{SPEC\}\};\n", "", TEMPLATE.replace("{{TITLE}}", title))
    return current == fresh


NOTE = "Fonte: questionario Connessioni fragili. Percentuali su chi ha risposto alla singola domanda."
NOTE_MULTI = NOTE + " Per le domande a scelta multipla il totale supera 100."

# 01 — Percezione di sé
page("01-percezione-di-se.html", "Come ci si vede online", [
    {"type": "hero", "p": share(9, {"Sì"}),
     "text": "ha cancellato o modificato qualcosa che aveva pubblicato per paura del giudizio degli altri"},
    {"type": "stack", "title": "Quanto spesso capita di…", "legend": FREQ, "rows": [
        stack(10, FREQ_KEYS, "Controllare like, visualizzazioni o commenti dopo aver pubblicato qualcosa"),
        stack(7, FREQ_KEYS, "Pensare che la vita degli altri, vista sui social, sia migliore della propria"),
        stack(6, FREQ_KEYS, "Usare filtri o strumenti per modificare il proprio aspetto in una foto"),
    ]},
    {"type": "stack", "title": "Da 1 (per niente) a 5 (moltissimo)…", "legend": SCALE, "rows": [
        stack(8, SCALE_KEYS, "Quanto preoccupa il giudizio degli altri su ciò che si pubblica, commenta o condivide"),
        stack(5, SCALE_KEYS, "Quanto ci si sente diversi online rispetto a quando si è con le persone dal vivo"),
    ]},
], NOTE)

# 02 — Conflitti e cyberbullismo
REACT = ["Non ho fatto niente", "Ho segnalato il contenuto o il profilo",
         "Ho cercato di difendere o sostenere la persona", "Ne ho parlato con amici o coetanei",
         "Ho partecipato o reagito per scherzo", "Ne ho parlato con un insegnante o un altro adulto"]
page("02-conflitti-cyberbullismo.html", "Conflitti e cyberbullismo", [
    {"type": "hero", "p": share(19, {"Spesso", "Qualche volta", "Una volta"}),
     "text": "ha visto online insulti, prese in giro, esclusioni o contenuti offensivi rivolti a un’altra persona"},
    {"type": "stack", "title": "Online ti è mai capitato di…", "legend": YN, "rows": [
        stack(12, YN_KEYS, "Vivere un litigio o un conflitto importante nato o cresciuto online"),
        stack(11, YN_KEYS, "Sentirti giudicato/a o escluso/a per qualcosa successo online"),
        stack(15, YN_KEYS, "Subire prese in giro, esclusione, insulti o la diffusione di contenuti senza consenso"),
    ]},
    {"type": "stack", "title": "Chi ha subito prese in giro o insulti online…", "legend": YN, "rows": [
        stack(17, YN_KEYS, "Ne ha parlato con un adulto?"),
    ]},
    {"type": "stack", "title": "Chi ha vissuto un litigio importante online…", "legend": SCALE, "rows": [
        stack(13, SCALE_KEYS, "Quanto è stato male, da 1 (per niente) a 5 (moltissimo)"),
    ]},
    {"type": "options", "title": "Davanti a offese rivolte ad altri, come si è reagito",
     "items": options(20, REACT, merge={
         "Ne ho parlato con adulti e amici": ["Ne ho parlato con un insegnante o un altro adulto", "Ne ho parlato con amici o coetanei"],
         "non conoscevo la persona ma ho comunque parlato con un adulto": "Ne ho parlato con un insegnante o un altro adulto",
     })},
], NOTE_MULTI)

# 03 — Intimità, privacy, identità
FRENO = ["Non sapevo se fosse abbastanza grave", "Pensavo che non sarebbe servito",
         "Non volevo coinvolgere genitori, scuola o altri adulti", "Non sapevo come fare",
         "Avevo paura delle conseguenze", "Mi vergognavo", "Avevo paura di non essere creduto/a"]
KNOW_KEYS = ["Sì, penso di saperlo", "Più o meno", "No", "Non ci ho mai pensato"]
KNOW = legend(("Sì", S4, WHITE), ("Più o meno", S2, DARK), ("No", NO, DARK), ("Non ci ho mai pensato", GRAY, WHITE))
page("03-intimita-privacy.html", "Intimità, privacy e identità", [
    {"type": "hero", "p": share(22, {"Sì"}),
     "text": "ha subito pressioni per inviare foto, video o messaggi intimi che non voleva inviare"},
    {"type": "stack", "title": "Ti è mai capitato…", "legend": YNS, "rows": [
        stack(23, YNS_KEYS, "Di conoscere qualcuno che ha subito pressioni per inviare contenuti intimi"),
        stack(24, YNS_KEYS, "Che tue foto, video o messaggi privati siano stati diffusi senza il tuo permesso"),
        stack(25, YNS_KEYS, "Di trovare un profilo falso a tuo nome o un uso della tua identità online"),
        stack(27, YNS_KEYS, "Di pensare di segnalare o denunciare qualcosa successo online, ma poi non farlo"),
    ]},
    {"type": "options", "title": "Cosa ha frenato chi non ha segnalato", "items": options(28, FRENO)},
    {"type": "stack", "title": "Se un contenuto online ti danneggiasse, sapresti cosa fare per farlo rimuovere o chiedere aiuto?",
     "legend": KNOW, "rows": [
        stack(26, KNOW_KEYS, "", merge={"Sì, lo sapevo": "Sì, penso di saperlo"}),
    ]},
], NOTE_MULTI)

# 04 — Adulti e scuola
WHO = ["Ad amici o coetanei", "Ai miei genitori o agli adulti che si occupano di me",
       "A un fratello, una sorella o un altro familiare", "A nessuno",
       "A strumenti di intelligenza artificiale o chatbot", "A uno psicologo o altro professionista",
       "A un insegnante o educatore", "A servizi o numeri di aiuto"]
WHO_LABEL = {"Ai miei genitori o agli adulti che si occupano di me": "Ai genitori o agli adulti che si occupano di loro"}
FAM_KEYS = ["Sì, in modo approfondito", "Sì, ma solo a grandi linee", "No", "Non ricordo", NR]
FAM = legend(("Sì, in modo approfondito", S4, WHITE), ("Sì, ma solo a grandi linee", S2, DARK),
             ("No", NO, DARK), ("Non ricordo", GRAY, WHITE), ("Non risponde", NRC, DARK))
SCH_KEYS = ["Sì, vorrei che se ne parlasse di più", "No, per me se ne parla già abbastanza",
            "No, non ne sento il bisogno", "Non saprei"]
SCH = legend(("Sì, vorrei parlarne di più", S4, WHITE), ("No, se ne parla già abbastanza", NO, DARK),
             ("No, non ne sento il bisogno", NO2, DARK), ("Non saprei", GRAY, WHITE))
who = options(29, WHO, merge={"Non mi rivolgo a nessuno": "A nessuno", "nessuno": "A nessuno", "Mie amiche": "Ad amici o coetanei"})
for it in who:
    it["label"] = WHO_LABEL.get(it["label"], it["label"])
page("04-adulti-scuola.html", "Adulti e scuola", [
    {"type": "hero", "p": share(31, {"1", "2"}),
     "text": "sente che gli adulti di riferimento conoscono e capiscono poco o per niente la sua vita online"},
    {"type": "options", "title": "A chi ci si rivolge quando qualcosa online preoccupa", "items": who},
    {"type": "stack", "title": "In famiglia si è parlato dei rischi di internet, social e smartphone?", "legend": FAM, "rows": [
        stack(30, FAM_KEYS, ""),
    ]},
    {"type": "stack", "title": "Quanto gli adulti conoscono e capiscono la vita online, da 1 (per niente) a 5 (moltissimo)",
     "legend": SCALE, "rows": [stack(31, SCALE_KEYS, "")]},
    {"type": "stack", "title": "A scuola si dovrebbe parlare di più di social e internet?", "legend": SCH, "rows": [
        stack(32, SCH_KEYS, ""),
    ]},
], NOTE_MULTI)

# 05 — Benessere
WELL = [(34, "Andare a dormire più tardi del previsto per continuare a usare telefono o social"),
        (35, "Sentire ansia o pressione per dover rispondere subito a messaggi o notifiche"),
        (37, "Sentirsi giù di morale dopo aver usato i social"),
        (36, "Sentirsi irritabili, agitati o a disagio senza telefono o social per diverse ore"),
        (33, "Dormire male per qualcosa successo sul telefono o sui social")]
page("05-benessere.html", "Telefono e benessere", [
    {"type": "hero", "p": share(34, {"Spesso", "Qualche volta"}),
     "text": "negli ultimi tre mesi ha fatto più tardi di quanto volesse, almeno qualche volta, per continuare a usare il telefono o i social"},
    {"type": "stack", "title": "Negli ultimi tre mesi è capitato di…", "legend": M3,
     "rows": [stack(i, M3_KEYS, q) for i, q in WELL]},
    {"type": "stack", "title": "E quanto spesso qualcosa vissuto online ha fatto sentire meglio, meno soli o più sostenuti?",
     "legend": FREQ, "rows": [stack(21, FREQ_KEYS, "")]},
], NOTE)
