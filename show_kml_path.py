import sys
import xml.etree.ElementTree as ET

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>KML Path</title>
    <style>#map {{ height: 600px; }}</style>
    <script src='https://maps.googleapis.com/maps/api/js?key=&callback=initMap' async defer></script>
    <script>
    var coords = {coords};
    function initMap() {{
        var path = coords.map(function(c) {{ return {{lat: c[0], lng: c[1]}}; }});
        var map = new google.maps.Map(document.getElementById('map'), {{
            zoom: 14,
            center: path[0]
        }});
        var poly = new google.maps.Polyline({{
            path: path,
            strokeColor: '#FF0000',
            strokeOpacity: 1.0,
            strokeWeight: 2
        }});
        poly.setMap(map);
    }}
    </script>
</head>
<body>
<div id='map'></div>
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


def generate_html(coords, out_file='path.html'):
    html = HTML_TEMPLATE.format(coords=coords)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return out_file


def main():
    if len(sys.argv) < 2:
        print('Usage: python show_kml_path.py path_to_file.kml')
        return
    path = sys.argv[1]
    coords = parse_kml(path)
    if not coords:
        print('No coordinates found in', path)
        return
    out_file = generate_html(coords)
    print('HTML 파일이 생성되었습니다:', out_file)

if __name__ == '__main__':
    main()
