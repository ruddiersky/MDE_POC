import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
import webbrowser

import show_kml_path


def parse_path_txt(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 6:
                continue
            order = int(row[0])
            place = row[1]
            lon = float(row[2])
            lat = float(row[3])
            arrive = row[4].replace('.', ':').strip()
            if arrive == "-" or not arrive:
                continue
            depart = row[5].replace('.', ':').strip()
            entries.append({
                "order": order,
                "place": place,
                "lon": lon,
                "lat": lat,
                "arrive": arrive,
                "depart": depart,
            })
    return entries


def parse_kml(path):
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    tree = ET.parse(path)
    root = tree.getroot()
    points = []
    for pm in root.findall(".//kml:Placemark", ns):
        time_elem = pm.find(".//kml:when", ns)
        coord_elem = pm.find(".//kml:Point/kml:coordinates", ns)
        if time_elem is not None and coord_elem is not None:
            coord_text = coord_elem.text.strip().split()[0]
            lon, lat = map(float, coord_text.split(",")[:2])
            t = datetime.strptime(time_elem.text, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=9)
            points.append({"time": t, "lon": lon, "lat": lat})
    return points


def haversine(lon1, lat1, lon2, lat2):
    R = 6371e3
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def find_nearest(lon, lat, points):
    min_dist = None
    nearest_time = None
    nearest_point = None
    for p in points:
        d = haversine(lon, lat, p["lon"], p["lat"])
        if min_dist is None or d < min_dist:
            min_dist = d
            nearest_time = p["time"]
            nearest_point = (p["lon"], p["lat"])
    return min_dist, nearest_time, nearest_point


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

        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="비교", command=self.compare).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="지도 보기", command=self.show_map).pack(side=tk.LEFT)

        columns = ("place", "arrive", "track_pos", "track_time", "dist")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("place", text="이동 장소")
        self.tree.heading("arrive", text="도착시간")
        self.tree.heading("track_pos", text="Tracking 도착 위치")
        self.tree.heading("track_time", text="Tracking 도착 시간")
        self.tree.heading("dist", text="거리 차이(m)")
        self.tree.pack(fill=tk.BOTH, expand=True)

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

        for i in self.tree.get_children():
            self.tree.delete(i)

        for entry in path_entries:
            dist, t, pos = find_nearest(entry["lon"], entry["lat"], kml_points)
            if t is None:
                continue
            track_pos = f"{pos[1]:.6f}, {pos[0]:.6f}"
            self.tree.insert(
                "",
                tk.END,
                values=[
                    entry["place"],
                    entry["arrive"],
                    track_pos,
                    t.strftime("%H:%M:%S"),
                    f"{dist:.1f}",
                ],
            )

    def show_map(self):
        kml = self.kml_var.get()
        if not kml:
            messagebox.showerror("오류", "KML 파일을 선택하세요")
            return
        coords = show_kml_path.parse_kml(kml)
        out_file = os.path.abspath("path.html")
        show_kml_path.generate_html(coords, out_file)
        webbrowser.open(f"file://{out_file}")


def main():
    app = RouteCompareGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
