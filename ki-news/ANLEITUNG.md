# KI-News einpflegen: Anleitung für Claude

Diese Anleitung ist für eine Claude-Session gedacht, die den Auftrag bekommt, die KI-News aus dem Repo-Postfach in die Website tim-schoster.onepage.me einzupflegen. Sie ist selbsterklärend, damit auch eine Session ohne Vorwissen sie abarbeiten kann.

## Woher die News kommen

Ein n8n-Workflow ("KI-News Scanner tim-schoster.de") legt nach jedem Lauf mit neuen Einträgen eine Datei ab unter:

```
ki-news/inbox/JJJJ-MM-TT-HHMM.json   (Branch: claude/freelancer-portfolio-onepage-z9ohoh)
```

Format je Datei:

```json
{
  "lauf": "2026-07-05T20:00:00.000Z",
  "eintraege": [
    { "tag": "KI-Modelle", "date": "5. Juli 2026", "title": "…", "text": "…", "source": "https://…" }
  ]
}
```

## Verarbeitung, Schritt für Schritt

1. Alle Dateien in `ki-news/inbox/` lesen, die jünger als 72 Stunden sind (Dateiname trägt den Zeitstempel). Ältere ignorieren.
2. Onepage-MCP nutzen. Vor Schreib-Calls die Skills `react-components` und `sites-pages` per `onepage_skill_get` laden.
3. Ziel-IDs:
   - site_id: `d9695000-c09e-4ae9-b274-771ea6b805c5`
   - KI-News-Seite (page_id): `7690bbe4-1b00-4263-9e03-6ceba003fa5e`, News-Feed-Komponente (react_app_id): `6a47d2da7ba118ad564d2917`, Feld: `items` (Array-Control in package.json, Felder je Eintrag: `tag`, `date`, `title`, `text`, `source`)
   - Startseite (page_id): `09b7686b-8187-4768-8be0-5632baecb50a`, News-Anriss-Komponente (react_app_id): `6a47c9a984ce2e7dcfb746c4`, Feld: `items` (Felder: `tag`, `title`, `text`, `source`, OHNE date)
4. **Dubletten-Schutz (wichtig, macht alles idempotent):** Einen Eintrag nur einfügen, wenn sein `source`-Link noch NICHT in den `items` der News-Feed-Komponente steht. Bereits vorhandene Einträge unverändert lassen.
5. **Qualitäts-Gate:** Einträge überspringen, bei denen ein Feld fehlt oder in `title`/`text` ein Gedankenstrich (– oder —) vorkommt. Übersprungene im Abschlussbericht nennen.
6. Einfügen: Neue Einträge VORNE in das `items`-Array der News-Feed-Komponente (neueste zuerst, innerhalb eines Laufs Reihenfolge der Datei beibehalten). Danach Liste auf maximal 8 Einträge kürzen (älteste fliegen raus). `sourcePrefix` und `note` unverändert lassen.
7. Startseiten-Anriss: Die 3 neuesten Einträge aus der (aktualisierten) News-Feed-Liste in den Anriss spiegeln (ohne `date`-Feld).
8. Vor der ersten Änderung je Seite einmal `save_page_version` aufrufen. Danach beide Seiten mit `publish_page` veröffentlichen.
9. Verarbeitete Inbox-Dateien per GitHub-MCP nach `ki-news/verarbeitet/` verschieben (Datei dort anlegen, Original löschen). Wenn das nicht möglich ist: einfach liegen lassen, der Dubletten-Schutz aus Schritt 4 verhindert Doppel-Einträge.

## Grenzen

- Nur die zwei genannten Komponenten und Seiten anfassen, nichts anderes an der Website ändern.
- Keine Texte umformulieren, die Einträge sind final redigiert. Nichts erfinden.
- Interne Kennungen (IDs, Workflow-Namen, Tokens) niemals in Website-Inhalte schreiben.
- Kurzen Abschlussbericht geben: eingefügt / übersprungen (mit Grund) / entfernte alte Einträge.
