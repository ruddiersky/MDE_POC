import sys
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from math import radians, sin, cos, sqrt, asin

KST = timezone(timedelta(hours=9))

# Namespace definitions for parsing KML
NS = {
    'kml': 'http://www.opengis.net/kml/2.2'
}


def haversine(lon1, lat1, lon2, lat2):
    """두 지점 간 거리를 미터 단위로 반환합니다."""
    R = 6371e3
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


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
            # Skip invalid timestamp format
            continue

        dt_kst = dt_utc.astimezone(KST)
        coord_text = coord_elem.text.strip()
        lon, lat = map(float, coord_text.split(',')[:2])
        positions.append((dt_kst, lat, lon))

    positions.sort(key=lambda x: x[0])
    return positions


def parse_locations(file_path):
    """이동경로.txt 파일에서 장소와 좌표를 추출합니다."""
    locations = []
    with open(file_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                name = row['장소 이름']
                lon = float(row['longitude'])
                lat = float(row['latitude'])
            except (KeyError, ValueError):
                continue
            locations.append({'name': name, 'lon': lon, 'lat': lat})
    return locations


def group_by_location(positions, locations, radius=300):
    """장소별로 반경 내 위치 정보를 묶어 반환합니다."""
    groups = {loc['name']: [] for loc in locations}
    for dt, lat, lon in positions:
        for loc in locations:
            dist = haversine(lon, lat, loc['lon'], loc['lat'])
            if dist <= radius:
                groups[loc['name']].append((dt, lat, lon))
    return groups


def main():
    if len(sys.argv) < 2:
        print('사용법: python list_kml_positions.py <파일.kml> [이동경로.txt]')
        return

    kml_path = sys.argv[1]
    loc_path = sys.argv[2] if len(sys.argv) > 2 else '이동경로.txt'
    try:
        positions = parse_kml(kml_path)
    except FileNotFoundError:
        print('파일을 찾을 수 없습니다:', kml_path)
        return
    except ET.ParseError as e:
        print('KML 파싱 오류:', e)
        return

    try:
        locations = parse_locations(loc_path)
    except FileNotFoundError:
        print('장소 파일을 찾을 수 없습니다:', loc_path)
        locations = []

    if locations:
        groups = group_by_location(positions, locations)
        for loc in locations:
            name = loc['name']
            print(f'[{name}]')
            items = groups.get(name, [])
            if not items:
                print('  해당 위치 정보 없음')
            else:
                for dt, lat, lon in items:
                    print(dt.strftime('%Y-%m-%d %H:%M:%S'), f'{lat:.6f}', f'{lon:.6f}')
            print()
    else:
        for dt, lat, lon in positions:
            print(dt.strftime('%Y-%m-%d %H:%M:%S'), f'{lat:.6f}', f'{lon:.6f}')


if __name__ == '__main__':
    main()
