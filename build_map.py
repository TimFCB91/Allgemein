#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator fuer die Gran-Canaria-Rundreise-Karte.

Aus einer einzigen Ortsliste werden erzeugt:
  - gran-canaria-rundreise.kml          -> Komplett-Datei: Route + alle Pins (1 Import)
  - gran-canaria-rundreise.csv          -> My-Maps-Import, Farbe nach Etappe
  - gran-canaria-karte-vorschau.html    -> lokale Vorschau (Leaflet/OpenStreetMap)
  - my-maps-ebenen/*.kml                -> je Etappe + Route eine Datei (schaltbare Ebenen)
  - gran-canaria-my-maps-ebenen.zip     -> die Einzeldateien gebuendelt

Alle Koordinaten in WGS84 (Dezimalgrad). West = negativ.
Aufruf:  python3 build_map.py
"""

import csv
import json
import os
import zipfile
from html import escape as html_escape

# ---------------------------------------------------------------------------
# Kategorien (Etappen + Sonderkategorien). Reihenfolge = Reihenfolge der Tour.
#   color    -> Hex-Farbe (HTML-Vorschau + Linien-/Icon-Faerbung)
#   kml_icon -> Icon-URL fuer die KML-Darstellung
#   slug     -> Dateiname-Baustein fuer die Einzel-Ebenen
# ---------------------------------------------------------------------------
CATEGORIES = {
    "sueden":     {"label": "Etappe 1 · Süden",          "tag": "Tag 1–2",   "color": "#E53935",
                   "slug": "01-sueden",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png"},
    "fataga":     {"label": "Etappe 2 · Fataga-Tal",     "tag": "Tag 3",     "color": "#FB8C00",
                   "slug": "02-fataga",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"},
    "berge":      {"label": "Etappe 3 · Bergland",       "tag": "Tag 4",     "color": "#43A047",
                   "slug": "03-bergland",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png"},
    "westen":     {"label": "Etappe 4 · Westküste (GC-200)", "tag": "Tag 5", "color": "#1E88E5",
                   "slug": "04-westkueste",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png"},
    "norden":     {"label": "Etappe 5 · Norden",         "tag": "Tag 6",     "color": "#8E24AA",
                   "slug": "05-norden",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/purple-pushpin.png"},
    "laspalmas":  {"label": "Etappe 6 · Las Palmas",     "tag": "Tag 7",     "color": "#D81B60",
                   "slug": "06-las-palmas",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/pink-pushpin.png"},
    "extras":     {"label": "Optional · 8–10 Tage",      "tag": "optional",  "color": "#00897B",
                   "slug": "07-optional",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/pushpin/ltblu-pushpin.png"},
    "unterkunft": {"label": "Unterkünfte",               "tag": "—",         "color": "#5D4037",
                   "slug": "08-unterkuenfte",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/shapes/lodging.png"},
    "kulinarik":  {"label": "Kulinarik",                 "tag": "—",         "color": "#C0A800",
                   "slug": "09-kulinarik",
                   "kml_icon": "https://maps.google.com/mapfiles/kml/shapes/dining.png"},
}

# Stil der Routenlinie
ROUTE = {
    "name": "Route (Süden → Berge → Westen → Norden → Las Palmas)",
    "color": "#37474F",
    "slug": "00-route",
    # Wegpunkte in Reisereihenfolge (Name nur zur Orientierung im Code)
    "points": [
        (27.7392, -15.5847, "Maspalomas"),
        (27.8193, -15.5793, "Degollada de las Yeguas"),
        (27.8506, -15.5836, "Fataga"),
        (27.9686, -15.6153, "Roque Nublo"),
        (27.9956, -15.6147, "Tejeda"),
        (28.0086, -15.6011, "Cruz de Tejeda"),
        (28.0194, -15.7853, "Mirador del Balcón"),
        (28.0989, -15.7006, "Agaete"),
        (28.1456, -15.6536, "Gáldar"),
        (28.1190, -15.5237, "Arucas"),
        (28.0606, -15.5478, "Teror"),
        (28.0989, -15.4157, "Las Palmas / Vegueta"),
    ],
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


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def xml_text(value):
    """Minimales XML-Escaping fuer KML-Elemente."""
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hex_to_kml(hex_color, alpha="ff"):
    """#RRGGBB -> KML-Farbe aabbggrr."""
    r, g, b = hex_color[1:3], hex_color[3:5], hex_color[5:7]
    return (alpha + b + g + r).lower()


def placemark_xml(name, lat, lng, cat, indent="      "):
    """Ein <Placemark> fuer einen Ort (inkl. Popup-Text)."""
    cdata = f"<b>{html_escape(cat['label'])} · {html_escape(cat['tag'])}</b><br/>{html_escape(name_desc(name))}"
    return "\n".join([
        f"{indent}<Placemark>",
        f"{indent}  <name>{xml_text(name)}</name>",
        f"{indent}  <description><![CDATA[{cdata}]]></description>",
        f"{indent}  <styleUrl>#{cat['_key']}</styleUrl>",
        f"{indent}  <Point><coordinates>{lng:.6f},{lat:.6f},0</coordinates></Point>",
        f"{indent}</Placemark>",
    ])


# Schneller Zugriff Name -> Beschreibung
_DESC = {p[0]: p[4] for p in PLACES}
def name_desc(name):
    return _DESC.get(name, "")


def style_xml(key, cat, indent="    "):
    return "\n".join([
        f'{indent}<Style id="{key}">',
        f"{indent}  <IconStyle><scale>1.1</scale><Icon><href>{cat['kml_icon']}</href></Icon></IconStyle>",
        f"{indent}</Style>",
    ])


def route_style_xml(indent="    "):
    return "\n".join([
        f'{indent}<Style id="route">',
        f"{indent}  <LineStyle><color>{hex_to_kml(ROUTE['color'])}</color><width>4</width></LineStyle>",
        f"{indent}</Style>",
    ])


def route_placemark_xml(indent="    "):
    coords = " ".join(f"{lng:.6f},{lat:.6f},0" for lat, lng, _n in ROUTE["points"])
    return "\n".join([
        f"{indent}<Placemark>",
        f"{indent}  <name>{xml_text(ROUTE['name'])}</name>",
        f"{indent}  <styleUrl>#route</styleUrl>",
        f"{indent}  <LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString>",
        f"{indent}</Placemark>",
    ])


# ---------------------------------------------------------------------------
# KML – Komplett-Datei (Route + alle Etappen, je Etappe ein Ordner)
# ---------------------------------------------------------------------------
def build_kml():
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "  <Document>",
        "    <name>Gran Canaria Rundreise (7–10 Tage)</name>",
        "    <description>Route und alle Orte aus dem Blog-Beitrag, sortiert nach Etappen.</description>",
        route_style_xml(),
    ]
    for key, cat in CATEGORIES.items():
        lines.append(style_xml(key, cat))

    # Route-Ordner zuerst
    lines += [
        "    <Folder>",
        f"      <name>{xml_text(ROUTE['name'])}</name>",
        route_placemark_xml("      "),
        "    </Folder>",
    ]

    # Ein Ordner pro Kategorie
    for key, cat in CATEGORIES.items():
        members = [p for p in PLACES if p[3] == key]
        if not members:
            continue
        cat_full = dict(cat, _key=key)
        lines += ["    <Folder>", f"      <name>{xml_text(cat['label'])}</name>"]
        for name, lat, lng, _key, _desc in members:
            lines.append(placemark_xml(name, lat, lng, cat_full))
        lines.append("    </Folder>")

    lines += ["  </Document>", "</kml>", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# KML – Einzeldateien (eine pro Etappe + eine fuer die Route) = schaltbare Ebenen
# ---------------------------------------------------------------------------
def build_category_kml(key):
    cat = CATEGORIES[key]
    cat_full = dict(cat, _key=key)
    members = [p for p in PLACES if p[3] == key]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "  <Document>",
        f"    <name>{xml_text(cat['label'])}</name>",
        style_xml(key, cat, "    "),
    ]
    for name, lat, lng, _key, _desc in members:
        lines.append(placemark_xml(name, lat, lng, cat_full, "    "))
    lines += ["  </Document>", "</kml>", ""]
    return "\n".join(lines)


def build_route_kml():
    return "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "  <Document>",
        f"    <name>{xml_text(ROUTE['name'])}</name>",
        route_style_xml("    "),
        route_placemark_xml("    "),
        "  </Document>",
        "</kml>",
        "",
    ])


def build_layer_files(outdir="my-maps-ebenen"):
    os.makedirs(outdir, exist_ok=True)
    written = []
    route_path = os.path.join(outdir, ROUTE["slug"] + ".kml")
    with open(route_path, "w", encoding="utf-8") as fh:
        fh.write(build_route_kml())
    written.append(route_path)
    for key, cat in CATEGORIES.items():
        path = os.path.join(outdir, cat["slug"] + ".kml")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build_category_kml(key))
        written.append(path)
    # Buendeln
    zip_path = "gran-canaria-my-maps-ebenen.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in written:
            zf.write(path, os.path.basename(path))
    return written, zip_path


# ---------------------------------------------------------------------------
# CSV (Farbe nach Kategorie via "Gruppieren nach")
# ---------------------------------------------------------------------------
def build_csv(path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Name", "Kategorie", "Tag", "Beschreibung", "Latitude", "Longitude"])
        for name, lat, lng, key, desc in PLACES:
            cat = CATEGORIES[key]
            writer.writerow([name, cat["label"], cat["tag"], desc, f"{lat:.6f}", f"{lng:.6f}"])


# ---------------------------------------------------------------------------
# HTML-Vorschau (Leaflet/OpenStreetMap) inkl. Routenlinie
# ---------------------------------------------------------------------------
def build_html():
    cats_js = json.dumps(CATEGORIES, ensure_ascii=False)
    places_js = json.dumps(
        [{"name": n, "lat": la, "lng": lo, "cat": k, "desc": d} for (n, la, lo, k, d) in PLACES],
        ensure_ascii=False,
    )
    route_js = json.dumps({"name": ROUTE["name"], "color": ROUTE["color"],
                           "points": [[la, lo] for (la, lo, _n) in ROUTE["points"]]},
                          ensure_ascii=False)

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
  const ROUTE = __ROUTE__;

  const map = L.map('map');
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, attribution: '&copy; OpenStreetMap-Mitwirkende'
  }).addTo(map);

  // Routenlinie
  const routeLayer = L.layerGroup().addTo(map);
  L.polyline(ROUTE.points, {color: ROUTE.color, weight: 4, opacity: 0.85}).addTo(routeLayer);

  const groups = {};
  Object.keys(CATEGORIES).forEach(k => { groups[k] = L.layerGroup().addTo(map); });

  const bounds = [];
  PLACES.forEach(p => {
    const cat = CATEGORIES[p.cat];
    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 8, color: '#333', weight: 1, fillColor: cat.color, fillOpacity: 0.95
    });
    marker.bindPopup('<b>' + p.name + '</b><br/>' +
      '<span class="cat" style="background:' + cat.color + '">' + cat.label + ' · ' + cat.tag + '</span><br/>' + p.desc);
    marker.bindTooltip(p.name, {direction:'top', offset:[0,-6]});
    marker.addTo(groups[p.cat]);
    bounds.push([p.lat, p.lng]);
  });
  map.fitBounds(bounds, {padding:[30,30]});

  const overlays = {};
  overlays['<span class="dot" style="background:' + ROUTE.color + '"></span><b>Route</b>'] = routeLayer;
  Object.keys(CATEGORIES).forEach(k => {
    const c = CATEGORIES[k];
    overlays['<span class="dot" style="background:' + c.color + '"></span>' + c.label] = groups[k];
  });
  L.control.layers(null, overlays, {collapsed:false}).addTo(map);

  const legend = L.control({position:'bottomleft'});
  legend.onAdd = function(){
    const div = L.DomUtil.create('div','legend');
    let html = '<b>Gran Canaria Rundreise</b>';
    html += '<div><span class="dot" style="background:' + ROUTE.color + '"></span>Route</div>';
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
    return (template.replace("__CATS__", cats_js)
                    .replace("__PLACES__", places_js)
                    .replace("__ROUTE__", route_js))


def main():
    with open("gran-canaria-rundreise.kml", "w", encoding="utf-8") as fh:
        fh.write(build_kml())
    build_csv("gran-canaria-rundreise.csv")
    with open("gran-canaria-karte-vorschau.html", "w", encoding="utf-8") as fh:
        fh.write(build_html())
    layer_files, zip_path = build_layer_files()

    print(f"OK: {len(PLACES)} Orte in {len(CATEGORIES)} Kategorien + Route.")
    print("  -> gran-canaria-rundreise.kml (Komplett)")
    print("  -> gran-canaria-rundreise.csv")
    print("  -> gran-canaria-karte-vorschau.html")
    print(f"  -> {len(layer_files)} Einzel-Ebenen in my-maps-ebenen/")
    print(f"  -> {zip_path}")


if __name__ == "__main__":
    main()
