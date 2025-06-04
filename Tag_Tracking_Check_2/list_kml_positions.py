import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

NS = {
    'kml': 'http://www.opengis.net/kml/2.2'
}


def parse_kml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    positions = []
    for placemark in root.findall('.//kml:Placemark', NS):
        when_elem = placemark.find('.//kml:TimeStamp/kml:when', NS)
        coord_elem = placemark.find('.//kml:Point/kml:coordinates', NS)

        if when_elem is None or coord_elem is None:
            continue

        try:
            dt_utc = datetime.fromisoformat(when_elem.text.replace('Z', '+00:00'))
        except ValueError:
            continue

        dt_kst = dt_utc.astimezone(KST)
        coord_text = coord_elem.text.strip()
        lon, lat = map(float, coord_text.split(',')[:2])
        positions.append((dt_kst, lat, lon))

    positions.sort(key=lambda x: x[0])
    return positions


def main():
    if len(sys.argv) < 2:
        print('사용법: python list_kml_positions.py <파일.kml>')
        return

    path = sys.argv[1]
    try:
        positions = parse_kml(path)
    except FileNotFoundError:
        print('파일을 찾을 수 없습니다:', path)
        return
    except ET.ParseError as e:
        print('KML 파싱 오류:', e)
        return

    for dt, lat, lon in positions:
        print(dt.strftime('%Y-%m-%d %H:%M:%S'), f'{lat:.6f}', f'{lon:.6f}')


if __name__ == '__main__':
    main()
