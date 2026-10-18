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

# 3. CSS for the switch
rep('</style>\n\n<div class="app">',
    "  .leaflet-bar.maptype a { width: auto; min-width: 64px; padding: 0 8px; height: 36px; line-height: 36px; font-size: 12px; font-weight: 600; }\n"
    "  .leaflet-bar.maptype a.on { background: var(--accent); color: var(--accent-fg); }\n"
    '</style>\n\n<div class="app">')

# 4. tiles + switch + automatic fallback
JS = r"""// real map tiles (GitHub Pages copy only): Street map = OSM tiles; Offline map = the embedded basemap
const TKEY = 'romeFlyerMapType';
const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors' });
let mapType = 'street', tileOk = 0, tileBad = 0, tileAuto = false;
try { if (localStorage.getItem(TKEY) === 'offline') mapType = 'offline'; } catch (e) {}
const mtBtns = {};
function setMapType(m, save) {
  mapType = m;
  const street = m === 'street';
  street ? tiles.addTo(map) : tiles.remove();
  for (const p of ['basemap', 'labels']) map.getPane(p).style.display = street ? 'none' : '';
  for (const k in mtBtns) mtBtns[k].classList.toggle('on', k === m);
  if (save) { try { localStorage.setItem(TKEY, m); } catch (e) {} }
}
const MapTypeCtl = L.Control.extend({ options: { position: 'topleft' }, onAdd() {
  const d = L.DomUtil.create('div', 'leaflet-bar maptype');
  for (const [k, name] of [['street', 'Street map'], ['offline', 'Offline map']]) {
    const a = mtBtns[k] = L.DomUtil.create('a', '', d);
    a.href = '#'; a.textContent = name; a.setAttribute('role', 'button');
    L.DomEvent.on(a, 'click', ev => { L.DomEvent.preventDefault(ev); setMapType(k, true); });
  }
  L.DomEvent.disableClickPropagation(d);
  return d; } });
new MapTypeCtl().addTo(map);
tiles.on('tileload', () => { tileOk++; });
tiles.on('tileerror', () => {
  tileBad++;
  if (!tileOk && tileBad >= 6 && mapType === 'street' && !tileAuto) {
    tileAuto = true; setMapType('offline', false);
    say('Street map tiles could not load: showing the offline map.');
  }
});
setMapType(mapType, false);
"""
rep("};\nrender();\n</script>", "};\n" + JS + "render();\n</script>")
open(D + 'pages/index.html', 'w', encoding='utf-8', newline='').write(t)
print('ok', len(t))
