"""Scarica le risposte dal foglio Google privato e le salva in un CSV temporaneo.

Uso: python3 fetch.py <file_csv_di_destinazione>

Variabili d'ambiente (in GitHub sono i segreti del repository):
  GOOGLE_SERVICE_ACCOUNT  contenuto completo del file JSON della chiave dell'account di servizio
  SHEET_ID                ID del foglio (la parte dell'indirizzo tra /d/ e /edit)
  SHEET_GID               numero della scheda (quello dopo gid= nell'indirizzo)

Il foglio va condiviso, come Visualizzatore, con l'indirizzo email dell'account di servizio.
Il CSV contiene le risposte individuali: non va mai salvato dentro il repository.
"""
import csv, json, os, sys
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

API = "https://sheets.googleapis.com/v4/spreadsheets"


def env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"Manca la variabile {name}: va aggiunta tra i segreti del repository.")
    return value


def get(session, url, **params):
    r = session.get(url, params=params, timeout=60)
    if r.status_code == 403:
        sys.exit("Accesso negato (403): il foglio è condiviso con l'email dell'account di servizio? "
                 "La Google Sheets API è attiva nel progetto Google Cloud?\n" + r.text[:500])
    if r.status_code == 404:
        sys.exit("Foglio non trovato (404): controlla il segreto SHEET_ID.\n" + r.text[:500])
    r.raise_for_status()
    return r.json()


def main(dest):
    info = json.loads(env("GOOGLE_SERVICE_ACCOUNT"))
    sheet_id, gid = env("SHEET_ID"), int(env("SHEET_GID"))
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    session = AuthorizedSession(creds)

    meta = get(session, f"{API}/{sheet_id}", fields="sheets.properties(sheetId,title)")
    titles = {s["properties"]["sheetId"]: s["properties"]["title"] for s in meta.get("sheets", [])}
    if gid not in titles:
        sys.exit(f"Nessuna scheda con gid {gid}. Schede trovate: {titles}")
    rng = "'" + titles[gid].replace("'", "''") + "'"

    values = get(session, f"{API}/{sheet_id}/values/{quote(rng)}",
                 valueRenderOption="FORMATTED_VALUE").get("values", [])
    if len(values) < 2:
        sys.exit("Il foglio sembra vuoto: interrompo per non pubblicare grafici senza dati.")

    # L'API omette le celle vuote in fondo alle righe: le riallineo all'intestazione
    width = len(values[0])
    with open(dest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for row in values:
            w.writerow(row + [""] * (width - len(row)))
    print(f"Scaricate {len(values) - 1} risposte dalla scheda '{titles[gid]}'.")


if __name__ == "__main__":
    main(sys.argv[1])
