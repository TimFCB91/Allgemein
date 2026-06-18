# Gran Canaria Rundreise – Karte für den Blogbeitrag

Hier liegen alle Orte aus dem Beitrag als fertige Karte zum Importieren in **Google My Maps**
und zum Einbetten ins Blog.

## Dateien

| Datei | Wofür |
|---|---|
| `gran-canaria-rundreise.csv` | **Empfohlen** für My Maps – farbige Pins nach Etappe |
| `gran-canaria-rundreise.kml` | Alternative – schon vorsortiert/gestylt (auch für Google Earth) |
| `gran-canaria-karte-vorschau.html` | Lokale Vorschau im Browser (zum Prüfen, ohne Google) |
| `gran-canaria-karte-vorschau.png` | Statisches Vorschaubild |
| `build_map.py` | Generator – erzeugt die drei oberen Dateien aus einer Ortsliste |

Enthalten sind **35 Orte** in 9 Kategorien: die 6 Etappen, die optionalen 8–10-Tage-Stopps,
die Unterkünfte und ein Kulinarik-Punkt.

---

## Weg 1 (empfohlen): CSV → Google My Maps mit Farbe je Etappe

1. Öffne **[mymaps.google.com](https://www.google.com/mymaps)** → **„Neue Karte erstellen"**.
2. In der Ebene auf **„Importieren"** klicken und `gran-canaria-rundreise.csv` hochladen.
3. **Positionsspalten** wählen: `Latitude` und `Longitude` ankreuzen → Weiter.
4. **Titelspalte** wählen: `Name` → Fertig. Alle 35 Pins erscheinen.
5. Farben nach Etappe: bei der Ebene auf **„Einzelne Stile"** klicken →
   **„Gruppieren nach" = `Kategorie`** wählen. Jede Etappe bekommt automatisch eine eigene Farbe.
   Optional darunter **„Beschriftungen einstellen" = `Name`**, dann stehen die Namen an den Pins.
6. Oben den Kartentitel setzen, z. B. *„Gran Canaria Rundreise – 7 bis 10 Tage"*.

Die Spalte `Beschreibung` (mein Kurztext je Ort) und `Tag` erscheinen automatisch im
Pin-Popup, wenn man einen Punkt anklickt.

> Hinweis: Beim CSV-Import landet alles in **einer** Ebene; die Farben trennen die Etappen.
> Möchtest du die Etappen einzeln ein-/ausblendbar haben, importiere die CSV mehrfach und
> filtere je Ebene nach `Kategorie` – oder nimm die KML (Weg 2).

## Weg 2 (Alternative): KML importieren

`gran-canaria-rundreise.kml` ist bereits in **Ordner pro Etappe** gegliedert und mit Icons
gestylt. In My Maps: **„Importieren"** → KML hochladen. In **Google Earth** öffnet sich die
Karte direkt mit allen Ebenen.

---

## Karte ins Blog einbetten

1. In My Maps oben rechts auf **„Teilen"**. Stelle die Karte auf
   **„Jeder, der über den Link verfügt"** bzw. öffentlich – sonst lässt sie sich nicht einbetten.
2. Auf das **Menü (drei Punkte)** neben dem Kartentitel → **„Karte in meine Website einbetten"**.
3. Den angezeigten `<iframe>`-Code kopieren und im Blog in einen **HTML-Block** einfügen.

Vorschlag für die Platzierung im Beitrag: direkt nach dem Abschnitt
**„Das Wichtigste auf einen Blick"** oder am Anfang von **„Gran Canaria Rundreise: Wo übernachten?"**.
Beispiel-Snippet (iframe ersetzen):

```html
<figure>
  <iframe src="HIER_DEINEN_MYMAPS_EINBETTUNGSLINK"
          width="100%" height="480" style="border:0;border-radius:8px"
          loading="lazy" allowfullscreen></iframe>
  <figcaption>Alle Orte der Route auf einen Blick – farbig nach Etappe.</figcaption>
</figure>
```

---

## Vorschau ohne Google

`gran-canaria-karte-vorschau.html` einfach im Browser öffnen (Doppelklick). Interaktive
OpenStreetMap-Karte mit allen Pins, Etappen-Umschalter und Legende – gut zum Gegenprüfen,
bevor du importierst. Diese HTML-Karte kannst du theoretisch auch direkt einbetten, falls dein
Blog eigenes JavaScript erlaubt (WordPress.com z. B. nicht; dann ist die My-Maps-iframe der Weg).

## Orte ändern / ergänzen

Die Ortsliste steht zentral in `build_map.py` (Liste `PLACES`). Ort ändern/ergänzen, dann:

```bash
python3 build_map.py
```

Das schreibt KML, CSV und HTML neu.

---

## Wichtig: Roque Nublo – Beitragstext bitte prüfen

Seit **Februar 2025** ist der Zugang zum Roque Nublo reguliert: Der alte Parkplatz an der
**Degollada de La Goleta** ist für Privat-Pkw **dauerhaft gesperrt**. Nötig sind jetzt eine
**kostenlose Online-Reservierung** (QR-Code über `grancanariasenderos.com`, begrenzte Plätze pro
Stunde) plus ein **Zubringerbus** ab Cruz de los Llanos bzw. Tejeda.

Dein Satz „Vom Parkplatz La Goleta an der GC-600 bist du in etwa 30 bis 45 Minuten oben" trifft
so nicht mehr zu. Der Pin in der Karte enthält bereits einen entsprechenden Hinweis – im
Beitragstext solltest du die Stelle aber ebenfalls anpassen (Reservierung + Bus erwähnen).
Bitte vor Veröffentlichung den aktuellen Stand auf der offiziellen Seite gegenprüfen,
solche Regelungen ändern sich.

## Hinweis zu den Koordinaten

Alle Koordinaten sind sorgfältig gesetzt (Aussichtspunkte, Wanderstart und Westküste zusätzlich
per Recherche verifiziert), Stadt-Pins zeigen auf den Ortskern. In My Maps lässt sich jeder Pin
per Drag & Drop noch fein verschieben, falls du einen Punkt exakt auf ein Gebäude setzen willst.
