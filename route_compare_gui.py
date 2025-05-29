import csv
import os
import webbrowser
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt

import show_kml_path

RADIUS_M = 150


def parse_path_txt(path):
    """이동경로 텍스트 파일을 읽어 도착 시간이 있는 항목만 반환"""
    entries = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 6:
                continue
            arrive = row[4].strip()
            if not arrive or arrive == "-":
                continue
            order = int(row[0])
            place = row[1].split("(")[0].strip()
            lon = float(row[2])
            lat = float(row[3])
            arrive = arrive.replace(".", ":")
            entries.append(
                {
                    "order": order,
                    "place": place,
                    "lon": lon,
                    "lat": lat,
                    "arrive": arrive,
                }
            )
    return entries


KST = timezone(timedelta(hours=9))


def parse_kml(path):
    """KML 파일에서 시각과 좌표를 읽어 서울 시간대로 변환합니다."""
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    tree = ET.parse(path)
    root = tree.getroot()
    points = []
    for pm in root.findall(".//kml:Placemark", ns):
        time_elem = pm.find(".//kml:when", ns)
        coord_elem = pm.find(".//kml:Point/kml:coordinates", ns)
        if time_elem is None or coord_elem is None:
            continue
        coord_text = coord_elem.text.strip().split()[0]
        lon, lat = map(float, coord_text.split(",")[:2])
        t = datetime.fromisoformat(time_elem.text.replace("Z", "+00:00")).astimezone(KST)
        points.append({"time": t, "lon": lon, "lat": lat})
    points.sort(key=lambda x: x["time"])
    return points


def haversine(lon1, lat1, lon2, lat2):
    R = 6371e3
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def find_first_within_radius(lon, lat, points, radius=RADIUS_M):
    """주어진 위치에서 radius 미터 이내 처음 기록된 포인트를 반환"""
    nearest = None
    min_dist = None
    for p in points:
        d = haversine(lon, lat, p["lon"], p["lat"])
        if d <= radius:
            return d, p["time"], p["lon"], p["lat"]
        if min_dist is None or d < min_dist:
            min_dist = d
            nearest = p
    if nearest is None:
        return None, None, None, None
    return min_dist, nearest["time"], nearest["lon"], nearest["lat"]


class RouteCompareGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("이동 경로 비교")
        self.geometry("800x600")
        self._create_widgets()

    def _create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=5)

        self.txt_var = tk.StringVar()
        self.kml_var = tk.StringVar()

        ttk.Button(top, text="이동경로.txt", command=self.select_txt).grid(row=0, column=0, padx=5)
        ttk.Entry(top, textvariable=self.txt_var, width=60).grid(row=0, column=1, padx=5)

        ttk.Button(top, text="Tracking.kml", command=self.select_kml).grid(row=1, column=0, padx=5)
        ttk.Entry(top, textvariable=self.kml_var, width=60).grid(row=1, column=1, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="비교", command=self.compare).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="지도 보기", command=self.show_map).pack(side=tk.LEFT, padx=5)

        columns = ("place", "arrive", "t_place", "t_time", "dist")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("place", text="이동 장소")
        self.tree.heading("arrive", text="도착시간")
        self.tree.heading("t_place", text="Tracking 위치")
        self.tree.heading("t_time", text="Tracking 도착 시간")
        self.tree.heading("dist", text="거리 차이(m)")
        self.tree.pack(fill=tk.BOTH, expand=True)

    def show_map(self):
        path = self.kml_var.get()
        if not path:
            messagebox.showerror("오류", "KML 파일을 선택하세요")
            return
        try:
            html = show_kml_path.generate_html(path)
            webbrowser.open(os.path.abspath(html))
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def select_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path:
            self.txt_var.set(path)

    def select_kml(self):
        path = filedialog.askopenfilename(filetypes=[("KML", "*.kml")])
        if path:
            self.kml_var.set(path)

    def compare(self):
        txt = self.txt_var.get()
        kml = self.kml_var.get()
        if not txt or not kml:
            messagebox.showerror("오류", "파일을 선택하세요")
            return
        try:
            path_entries = parse_path_txt(txt)
            kml_points = parse_kml(kml)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        for entry in path_entries:
            dist, t_time, t_lon, t_lat = find_first_within_radius(entry["lon"], entry["lat"], kml_points)
            if t_time is None:
                t_str = ""
                pos = ""
                dist_str = ""
            else:
                t_str = t_time.strftime("%Y-%m-%d %H:%M:%S")
                pos = f"{t_lat:.5f}, {t_lon:.5f}"
                dist_str = f"{dist:.1f}"
            self.tree.insert(
                "",
                tk.END,
                values=(
                    entry["place"],
                    entry["arrive"],
                    pos,
                    t_str,
                    dist_str,
                ),
            )


def main():
    app = RouteCompareGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
