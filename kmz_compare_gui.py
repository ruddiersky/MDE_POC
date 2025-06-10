import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt
import webbrowser


def haversine(lon1, lat1, lon2, lat2):
    """두 지점 사이의 거리를 미터 단위로 계산"""
    R = 6371e3
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def parse_kml_text(text):
    """KML 문자열에서 좌표 리스트 추출"""
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    root = ET.fromstring(text)
    coords = []
    for elem in root.findall('.//kml:LineString/kml:coordinates', ns):
        if elem.text:
            for part in elem.text.strip().split():
                pieces = part.split(',')
                if len(pieces) >= 2:
                    lon, lat = map(float, pieces[:2])
                    coords.append((lat, lon))
    return coords


def load_path(path):
    """KMZ 또는 KML 파일에서 좌표 리스트 로드"""
    ext = os.path.splitext(path)[1].lower()
    if ext == '.kmz':
        with zipfile.ZipFile(path, 'r') as zf:
            kml_name = next((n for n in zf.namelist() if n.lower().endswith('.kml')), None)
            if not kml_name:
                raise ValueError('KMZ 파일에 KML이 없습니다')
            text = zf.read(kml_name).decode('utf-8')
    else:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    return parse_kml_text(text)


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>Route Compare</title>
<style>#map { height: 600px; }</style>
<script src='https://maps.googleapis.com/maps/api/js?key=&callback=initMap' async defer></script>
<script>
var basePath = {base};
var testSegments = {segments};
function initMap() {
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 14,
        center: basePath[0]
    });
    var basePolyline = new google.maps.Polyline({
        path: basePath,
        strokeColor: '#0000ff',
        strokeOpacity: 1.0,
        strokeWeight: 2
    });
    basePolyline.setMap(map);
    testSegments.forEach(function(seg) {
        var poly = new google.maps.Polyline({
            path: seg.coords,
            strokeColor: seg.color,
            strokeOpacity: 1.0,
            strokeWeight: 2
        });
        poly.setMap(map);
    });
}
</script>
</head>
<body>
<div id='map'></div>
</body>
</html>"""


def generate_html(base_coords, test_coords, mask, out_file='compare.html'):
    segments = []
    for coord, is_far in zip(test_coords, mask):
        color = '#ff0000' if is_far else '#00aa00'
        if not segments or segments[-1]['color'] != color:
            segments.append({'color': color, 'coords': []})
        segments[-1]['coords'].append({'lat': coord[0], 'lng': coord[1]})
    base = [{'lat': c[0], 'lng': c[1]} for c in base_coords]
    html = HTML_TEMPLATE.format(base=base, segments=segments)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return out_file


class CompareGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('KMZ 비교')
        self.geometry('600x400')
        self._create_widgets()

    def _create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=5)

        self.base_var = tk.StringVar()
        self.test_var = tk.StringVar()

        ttk.Button(top, text='A 파일 선택', command=self.select_base).grid(row=0, column=0, padx=5)
        ttk.Entry(top, textvariable=self.base_var, width=50).grid(row=0, column=1, padx=5)

        ttk.Button(top, text='B 파일 선택', command=self.select_test).grid(row=1, column=0, padx=5)
        ttk.Entry(top, textvariable=self.test_var, width=50).grid(row=1, column=1, padx=5)

        ttk.Button(top, text='비교', command=self.compare).grid(row=2, column=0, columnspan=2, pady=5)

        columns = ('file', 'role')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.tree.heading('file', text='파일명')
        self.tree.heading('role', text='역할')
        self.tree.pack(fill=tk.BOTH, expand=True)

    def select_base(self):
        path = filedialog.askopenfilename(filetypes=[('KML/KMZ', '*.kml *.kmz')])
        if path:
            self.base_var.set(path)

    def select_test(self):
        path = filedialog.askopenfilename(filetypes=[('KML/KMZ', '*.kml *.kmz')])
        if path:
            self.test_var.set(path)

    def compare(self):
        base_path = self.base_var.get()
        test_path = self.test_var.get()
        if not base_path or not test_path:
            messagebox.showerror('오류', '두 파일을 선택하세요')
            return
        try:
            base_coords = load_path(base_path)
            test_coords = load_path(test_path)
        except Exception as e:
            messagebox.showerror('오류', str(e))
            return

        n = min(len(base_coords), len(test_coords))
        mask = []
        for i in range(n):
            b = base_coords[i]
            t = test_coords[i]
            d = haversine(b[1], b[0], t[1], t[0])
            mask.append(d > 150)

        out_file = os.path.abspath('compare.html')
        generate_html(base_coords[:n], test_coords[:n], mask, out_file)
        webbrowser.open(f'file://{out_file}')

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.insert('', tk.END, values=[os.path.basename(base_path), '기준파일'])
        self.tree.insert('', tk.END, values=[os.path.basename(test_path), '시험파일'])


def main():
    app = CompareGUI()
    app.mainloop()


if __name__ == '__main__':
    main()
