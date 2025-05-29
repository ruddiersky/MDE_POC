import sys
import xml.etree.ElementTree as ET

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>KML Path</title>
<link rel='stylesheet' href='https://unpkg.com/leaflet@1.7.1/dist/leaflet.css'>
<script src='https://unpkg.com/leaflet@1.7.1/dist/leaflet.js'></script>
<style>
#map {{ height: 600px; }}
</style>
</head>
<body>
<div id='map'></div>
<script>
var coords = {coords};
var map = L.map('map');
map.fitBounds(coords);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
}}).addTo(map);
L.polyline(coords, {{color: 'red'}}).addTo(map);
</script>
</body>
</html>"""


def parse_kml(filename):
    ns = {
        'kml': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2'
    }
    tree = ET.parse(filename)
    root = tree.getroot()
    for folder in root.findall('.//kml:Folder', ns):
        name_elem = folder.find('kml:name', ns)
        if name_elem is not None and name_elem.text.strip() == 'course':
            coord_elem = folder.find('.//kml:LineString/kml:coordinates', ns)
            if coord_elem is None:
                continue
            coords = []
            for part in coord_elem.text.strip().split():
                pieces = part.split(',')
                if len(pieces) >= 2:
                    lon, lat = float(pieces[0]), float(pieces[1])
                    coords.append([lat, lon])
            return coords
    return []


def main():
    if len(sys.argv) < 2:
        print('Usage: python show_kml_path.py path_to_file.kml')
        return
    path = sys.argv[1]
    coords = parse_kml(path)
    if not coords:
        print('No coordinates found in', path)
        return
    html = HTML_TEMPLATE.format(coords=coords)
    out_file = 'path.html'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print('HTML 파일이 생성되었습니다:', out_file)

if __name__ == '__main__':
    main()
