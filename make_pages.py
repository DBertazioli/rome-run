#!/usr/bin/env python3
"""Regenerate pages/index.html from rome-flyer-run.html: PWA metas + real OSM tiles (Street / Offline switch).
Run: python3 -I make_pages.py   (every replacement must match exactly once)"""
import os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
t = open(D + 'rome-flyer-run.html', encoding='utf-8', newline='').read()

def rep(old, new):
    global t
    assert t.count(old) == 1, (t.count(old), old[:70])
    t = t.replace(old, new)

# 1. PWA metas
vp = '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
rep(vp, vp + '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-title" content="Rome Run"><meta name="theme-color" content="#005088">')

# 2. embedded basemap + its labels get their own panes (so Street mode can hide them); metro stays in the overlay canvas
rep("const B = BASEMAP, cv = L.canvas({ padding: 0.3 });",
    "map.createPane('basemap').style.zIndex = 300; map.createPane('labels').style.zIndex = 590;\n"
    "const B = BASEMAP, cv = L.canvas({ padding: 0.3 }), cvb = L.canvas({ pane: 'basemap', padding: 0.3 });")
rep("L.polygon(rings, { renderer: cv,", "L.polygon(rings, { renderer: cvb,")
rep("L.polyline(B.river, { renderer: cv,", "L.polyline(B.river, { renderer: cvb,")
rep("casing: L.polyline(B.roads[cls], { renderer: cv,", "casing: L.polyline(B.roads[cls], { renderer: cvb,")
rep("fill: L.polyline(B.roads[cls], { renderer: cv,", "fill: L.polyline(B.roads[cls], { renderer: cvb,")
rep("L.marker([lat, lon], { interactive: false, keyboard: false,", "L.marker([lat, lon], { pane: 'labels', interactive: false, keyboard: false,")

# 4. tiles + automatic fallback (no visible switch: the user always uses the street map)
JS = r"""// real map tiles (GitHub Pages copy only): OSM tiles; the embedded basemap shows only if the tiles cannot load
const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors' });
let mapType = 'street', tileOk = 0, tileBad = 0, tileAuto = false;
function setMapType(m) {
  mapType = m;
  const street = m === 'street';
  street ? tiles.addTo(map) : tiles.remove();
  for (const p of ['basemap', 'labels']) map.getPane(p).style.display = street ? 'none' : '';
}
tiles.on('tileload', () => { tileOk++; });
tiles.on('tileerror', () => {
  tileBad++;
  if (!tileOk && tileBad >= 6 && mapType === 'street' && !tileAuto) {
    tileAuto = true; setMapType('offline');
    say('Street map tiles could not load: showing the offline map.');
  }
});
setMapType(mapType);
"""
rep("};\nrender();\n</script>", "};\n" + JS + "render();\n</script>")
open(D + 'pages/index.html', 'w', encoding='utf-8', newline='').write(t)
print('ok', len(t))
