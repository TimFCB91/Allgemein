#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator fuer die Gran-Canaria-Rundreise-Karte.

Aus einer einzigen Ortsliste werden drei Dateien erzeugt:
  - gran-canaria-rundreise.kml      -> Import in Google My Maps / Google Earth
  - gran-canaria-rundreise.csv      -> Import in Google My Maps (Farbe nach Etappe)
  - gran-canaria-karte-vorschau.html-> lokale Vorschau (Leaflet/OpenStreetMap)

Alle Koordinaten in WGS84 (Dezimalgrad). West = negativ.
Aufruf:  python3 build_map.py
"""

import csv
import json
from html import escape as html_escape

# ---------------------------------------------------------------------------
# Kategorien (Etappen + Sonderkategorien). Reihenfolge = Reihenfolge der Tour.
#   color    -> Hex-Farbe fuer die HTML-Vorschau
#   kml_icon -> Icon-URL fuer die KML-Darstellung
# ---------------------------------------------------------------------------
CATEGORIES = {
    "sueden":     {"label": "Etappe 1 · Süden",          "tag": "Tag 1–2",   "color": "#E53935",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png"},
    "fataga":     {"label": "Etappe 2 · Fataga-Tal",     "tag": "Tag 3",     "color": "#FB8C00",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"},
    "berge":      {"label": "Etappe 3 · Bergland",       "tag": "Tag 4",     "color": "#43A047",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png"},
    "westen":     {"label": "Etappe 4 · Westküste (GC-200)", "tag": "Tag 5", "color": "#1E88E5",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png"},
    "norden":     {"label": "Etappe 5 · Norden",         "tag": "Tag 6",     "color": "#8E24AA",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/purple-pushpin.png"},
    "laspalmas":  {"label": "Etappe 6 · Las Palmas",     "tag": "Tag 7",     "color": "#D81B60",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/pink-pushpin.png"},
    "extras":     {"label": "Optional · 8–10 Tage",      "tag": "optional",  "color": "#00897B",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/ltblu-pushpin.png"},
    "unterkunft": {"label": "Unterkünfte",               "tag": "—",         "color": "#5D4037",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/shapes/lodging.png"},
    "kulinarik":  {"label": "Kulinarik",                 "tag": "—",         "color": "#C0A800",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/shapes/dining.png"},
}

# ---------------------------------------------------------------------------
# Orte:  (Name, Breitengrad, Längengrad, Kategorie-Key, Beschreibung)
# ---------------------------------------------------------------------------
PLACES = [
    # --- Etappe 1: Süden -------------------------------------------------
    ("Dünen von Maspalomas", 27.7392, -15.5847, "sueden",
     "Echte Wüste am Meer. Am schönsten früh morgens oder kurz vor Sonnenuntergang – lange Schatten, kaum Leute."),
    ("Faro de Maspalomas", 27.7314, -15.5997, "sueden",
     "Alter Leuchtturm am Südzipfel. Schöner Spot für den ersten Sonnenuntergang."),
    ("Playa del Inglés", 27.7516, -15.5716, "sueden",
     "Großer Strand zum entspannten Ankommen."),
    ("Puerto de Mogán", 27.8156, -15.7656, "sueden",
     "Hübscher Hafenort. Startpunkt für Bootstouren – mit Glück Delfine."),
    ("Puerto Rico", 27.7894, -15.7106, "sueden",
     "Ferienort mit Hafen, ebenfalls Ausgangspunkt für Bootstouren."),

    # --- Etappe 2: Fataga-Tal -------------------------------------------
    ("Mirador de la Degollada de las Yeguas", 27.8193, -15.5793, "fataga",
     "Aussichtspunkt über die Schlucht, der „Grand Canyon von Gran Canaria“. Erster großer Blick auf der Auffahrt."),
    ("Arteara (Palmenhain & Necrópolis)", 27.8347, -15.5856, "fataga",
     "Ausgedehnter Palmenhain im Barranco de Fataga, dazu eine alte Ureinwohner-Nekropole."),
    ("Fataga", 27.8506, -15.5836, "fataga",
     "Hübsches weißes Bergdorf im „Tal der tausend Palmen“. Gute erste Mittagspause."),

    # --- Etappe 3: Bergland / Dach der Insel ----------------------------
    ("Roque Nublo", 27.9686, -15.6153, "berge",
     "67 m hoher Felsmonolith auf ~1.800 m – Wahrzeichen der Insel. Bei klarer Sicht im Westen der Teide."),
    ("Zubringer/Parkplatz La Goleta (GC-600)", 27.9742, -15.6110, "berge",
     "Klassischer Startpunkt der Roque-Nublo-Wanderung (30–45 Min). ACHTUNG Stand 2025/26: Parkplatz für "
     "Privat-Pkw gesperrt – Zugang nur mit Online-Reservierung (grancanariasenderos.com) und Zubringerbus "
     "ab Cruz de los Llanos / Tejeda."),
    ("Pico de las Nieves", 27.9617, -15.5703, "berge",
     "Mit ~1.949 m der höchste Aussichtspunkt der Insel."),
    ("Tejeda", 27.9956, -15.6147, "berge",
     "Weißes Bergdorf, eines der schönsten Spaniens. Hier den Bienmesabe probieren."),
    ("Parador Cruz de Tejeda", 28.0086, -15.6011, "berge",
     "Berghotel an der Cruz de Tejeda. Optionale Bergnacht mit Sonnenaufgang über dem Wolkenmeer."),

    # --- Etappe 4: Westküste (GC-200) -----------------------------------
    ("Mirador del Balcón", 28.0194, -15.7853, "westen",
     "In den Fels gehauene Plattform hoch über dem Atlantik – Höhepunkt der GC-200 („Drachenstraße“). "
     "Bei gutem Wetter Blick zum Teide."),
    ("Agaete", 28.0989, -15.7006, "westen",
     "Tor zum grünen Agaete-Tal, in dem sogar Kaffee wächst (Café de Agaete)."),
    ("Puerto de las Nieves", 28.1033, -15.7089, "westen",
     "Fischerort mit frischem Fisch am Paseo de los Poetas. Fähre nach Teneriffa."),
    ("Piscinas naturales Las Salinas", 28.1063, -15.7106, "westen",
     "Mehrere durch Lava verbundene Meerwasser-Naturbecken, ~10 Min zu Fuß vom Puerto de las Nieves."),

    # --- Etappe 5: Norden -----------------------------------------------
    ("Gáldar – Cueva Pintada", 28.1456, -15.6536, "norden",
     "Unter einer Bananenplantage ausgegrabene Ureinwohner-Siedlung mit originalen Wandmalereien. "
     "Museum, montags oft geschlossen – vorab planen."),
    ("Arucas – Iglesia de San Juan Bautista", 28.1190, -15.5237, "norden",
     "Mächtige Kirche aus dunklem Vulkanstein, im Volksmund „Kathedrale von Arucas“."),
    ("Destilería Arehucas", 28.1158, -15.5249, "norden",
     "Älteste Rumfabrik der Kanaren. Führung durch die Reifekeller, Verkostung von Rum und Ron Miel. "
     "Meist nur vormittags."),
    ("Teror", 28.0606, -15.5478, "norden",
     "Wallfahrtsort mit Holzbalkonen, Sonntagsmarkt und streichfähigem Chorizo de Teror."),

    # --- Etappe 6: Las Palmas -------------------------------------------
    ("Catedral de Santa Ana (Vegueta)", 28.0989, -15.4157, "laspalmas",
     "Kathedrale in der kolonialen Altstadt; vom Turm toller Blick über die Dächer."),
    ("Casa de Colón", 28.1003, -15.4154, "laspalmas",
     "Museum zu Christoph Kolumbus mitten in Vegueta."),
    ("Museo Canario", 28.0982, -15.4159, "laspalmas",
     "Mumien und Funde der Ureinwohner – ordnet Bergland und Gáldar erst richtig ein."),
    ("Playa de las Canteras", 28.1397, -15.4339, "laspalmas",
     "Einer der schönsten Stadtstrände Europas. Promenade zum Sonnenuntergang."),
    ("Mercado del Puerto", 28.1362, -15.4286, "laspalmas",
     "Markthalle mit Tapas – idealer Ausklang des Trips."),

    # --- Unterkünfte -----------------------------------------------------
    ("Lopesan Costa Meloneras", 27.7445, -15.6042, "unterkunft",
     "Empfehlung erste Hälfte (Süden): Strandnähe, Pool, Dünen vor der Tür."),
    ("Hotel Cordial Plaza Mayor de Santa Ana", 28.0993, -15.4149, "unterkunft",
     "Empfehlung zweite Hälfte: mitten in Vegueta, kurze Wege zu Kathedrale, Strand und Tapas."),

    # --- Optional (8–10 Tage) -------------------------------------------
    ("Playa de Amadores", 27.7822, -15.7253, "extras",
     "Geschützte Bucht mit ruhigem Wasser – idealer Strandtag zu Beginn."),
    ("Anfi del Mar", 27.7836, -15.6967, "extras",
     "Bucht mit türkisem, ruhigem Wasser. Strandtag."),
    ("Roque Bentayga", 27.9772, -15.6378, "extras",
     "Heiliger Felsen der Ureinwohner. Schöne Wanderung als zweiter Bergtag."),
    ("Artenara", 28.0214, -15.6494, "extras",
     "Höchstgelegenes Dorf der Insel mit Höhlenhäusern, umgeben von Pinienwäldern."),
    ("Barranco de Guayadeque", 27.9081, -15.4661, "extras",
     "Schlucht mit bewohnten Höhlen und Restaurants direkt im Fels."),
    ("Agüimes", 27.9061, -15.4467, "extras",
     "Hübsche, gepflegte Altstadt im Osten – gut kombinierbar mit Guayadeque."),

    # --- Kulinarik (nur Orte ohne eigenen Pin oben) ----------------------
    ("Santa María de Guía", 28.1408, -15.6314, "kulinarik",
     "Heimat des Queso de Flor – Käse, gelabt mit den Blüten der wilden Distel."),
]


def xml_text(value):
    """Minimales XML-Escaping fuer KML-Attribute/Elemente."""
    return (value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_kml():
    """KML mit einem Ordner pro Kategorie (in Google Earth = eigene Ebenen)."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "  <Document>",
        "    <name>Gran Canaria Rundreise (7–10 Tage)</name>",
        "    <description>Alle Orte aus dem Blog-Beitrag, sortiert nach Etappen.</description>",
    ]

    # Styles je Kategorie
    for key, cat in CATEGORIES.items():
        lines += [
            f'    <Style id="{key}">',
            "      <IconStyle>",
            "        <scale>1.1</scale>",
            f"        <Icon><href>{cat['kml_icon']}</href></Icon>",
            "      </IconStyle>",
            "    </Style>",
        ]

    # Ein Ordner pro Kategorie
    for key, cat in CATEGORIES.items():
        members = [p for p in PLACES if p[3] == key]
        if not members:
            continue
        lines += [
            "    <Folder>",
            f"      <name>{xml_text(cat['label'])}</name>",
        ]
        for name, lat, lng, _key, desc in members:
            cdata = f"<b>{html_escape(cat['label'])} · {html_escape(cat['tag'])}</b><br/>{html_escape(desc)}"
            lines += [
                "      <Placemark>",
                f"        <name>{xml_text(name)}</name>",
                f"        <description><![CDATA[{cdata}]]></description>",
                f"        <styleUrl>#{key}</styleUrl>",
                f"        <Point><coordinates>{lng:.6f},{lat:.6f},0</coordinates></Point>",
                "      </Placemark>",
            ]
        lines.append("    </Folder>")

    lines += ["  </Document>", "</kml>", ""]
    return "\n".join(lines)


def build_csv(path):
    """CSV fuer den My-Maps-Import; in My Maps spaeter 'nach Kategorie gruppieren'."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Name", "Kategorie", "Tag", "Beschreibung", "Latitude", "Longitude"])
        for name, lat, lng, key, desc in PLACES:
            cat = CATEGORIES[key]
            writer.writerow([name, cat["label"], cat["tag"], desc, f"{lat:.6f}", f"{lng:.6f}"])


def build_html():
    """Eigenstaendige Leaflet-Vorschau (OpenStreetMap-Kacheln)."""
    cats_js = json.dumps(CATEGORIES, ensure_ascii=False)
    places_js = json.dumps(
        [{"name": n, "lat": la, "lng": lo, "cat": k, "desc": d} for (n, la, lo, k, d) in PLACES],
        ensure_ascii=False,
    )

    template = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gran Canaria Rundreise – Karte</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,Arial,sans-serif}
  #map{height:100%}
  .legend{background:#fff;padding:10px 12px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.3);line-height:1.6;font-size:13px}
  .legend b{display:block;margin-bottom:4px}
  .dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:middle;border:1px solid rgba(0,0,0,.35)}
  .leaflet-popup-content{font-size:13px;line-height:1.45}
  .leaflet-popup-content .cat{display:inline-block;font-size:11px;color:#fff;padding:1px 7px;border-radius:10px;margin:3px 0}
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  const CATEGORIES = __CATS__;
  const PLACES = __PLACES__;

  const map = L.map('map');
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap-Mitwirkende'
  }).addTo(map);

  const groups = {};
  Object.keys(CATEGORIES).forEach(k => { groups[k] = L.layerGroup().addTo(map); });

  const bounds = [];
  PLACES.forEach(p => {
    const cat = CATEGORIES[p.cat];
    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 8, color: '#333', weight: 1, fillColor: cat.color, fillOpacity: 0.95
    });
    marker.bindPopup(
      '<b>' + p.name + '</b><br/>' +
      '<span class="cat" style="background:' + cat.color + '">' + cat.label + ' · ' + cat.tag + '</span><br/>' +
      p.desc
    );
    marker.bindTooltip(p.name, {direction:'top', offset:[0,-6]});
    marker.addTo(groups[p.cat]);
    bounds.push([p.lat, p.lng]);
  });
  map.fitBounds(bounds, {padding:[30,30]});

  // Ebenen-Umschalter (Etappen ein-/ausblenden)
  const overlays = {};
  Object.keys(CATEGORIES).forEach(k => {
    const c = CATEGORIES[k];
    overlays['<span class="dot" style="background:' + c.color + '"></span>' + c.label] = groups[k];
  });
  L.control.layers(null, overlays, {collapsed:false}).addTo(map);

  // Legende
  const legend = L.control({position:'bottomleft'});
  legend.onAdd = function(){
    const div = L.DomUtil.create('div','legend');
    let html = '<b>Gran Canaria Rundreise</b>';
    Object.keys(CATEGORIES).forEach(k => {
      const c = CATEGORIES[k];
      html += '<div><span class="dot" style="background:' + c.color + '"></span>' + c.label + '</div>';
    });
    div.innerHTML = html;
    return div;
  };
  legend.addTo(map);
</script>
</body>
</html>
"""
    return template.replace("__CATS__", cats_js).replace("__PLACES__", places_js)


def main():
    with open("gran-canaria-rundreise.kml", "w", encoding="utf-8") as fh:
        fh.write(build_kml())
    build_csv("gran-canaria-rundreise.csv")
    with open("gran-canaria-karte-vorschau.html", "w", encoding="utf-8") as fh:
        fh.write(build_html())
    print(f"OK: {len(PLACES)} Orte in {len(CATEGORIES)} Kategorien geschrieben.")
    print("  -> gran-canaria-rundreise.kml")
    print("  -> gran-canaria-rundreise.csv")
    print("  -> gran-canaria-karte-vorschau.html")


if __name__ == "__main__":
    main()
