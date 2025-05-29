import csv
import tkinter as tk
from tkinter import filedialog, scrolledtext
from math import radians, cos, sin, asin, sqrt

from datetime import datetime

from list_kml_positions import parse_kml


def haversine(lon1, lat1, lon2, lat2):
    R = 6371e3
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def load_places(path):
    places = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) < 4:
                continue
            name_full = row[1]
            name = name_full.split("(")[0].strip()
            lon = float(row[2])
            lat = float(row[3])
            places.append({"name": name, "lon": lon, "lat": lat})
    return places


def group_positions_by_place(positions, places, radius=300):
    result = {p["name"]: [] for p in places}
    for dt, lat, lon in positions:
        for p in places:
            d = haversine(lon, lat, p["lon"], p["lat"])
            if d <= radius:
                result[p["name"]].append((dt, lat, lon))
    # remove empty
    return {k: v for k, v in result.items() if v}


def summarize_places(grouped):
    summary = []
    for name, entries in grouped.items():
        entries.sort(key=lambda x: x[0])
        arrive = entries[0][0]
        depart = entries[-1][0]
        summary.append((name, arrive, depart))
    summary.sort(key=lambda x: x[1])
    return summary


class Viewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KML 위치 정보 보기")
        self.geometry("1000x600")
        self._create_widgets()

    def _create_widgets(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, pady=5)

        self.kml_var = tk.StringVar()
        self.txt_var = tk.StringVar()

        tk.Button(top, text="KML 파일", command=self.select_kml).pack(side=tk.LEFT, padx=5)
        tk.Entry(top, textvariable=self.kml_var, width=50).pack(side=tk.LEFT, padx=5)

        tk.Button(top, text="이동경로.txt", command=self.select_txt).pack(side=tk.LEFT, padx=5)
        tk.Entry(top, textvariable=self.txt_var, width=50).pack(side=tk.LEFT, padx=5)

        tk.Button(top, text="불러오기", command=self.load).pack(side=tk.LEFT, padx=5)

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.left_text = scrolledtext.ScrolledText(paned)
        self.right_text = scrolledtext.ScrolledText(paned)

        paned.add(self.left_text)
        paned.add(self.right_text)

    def select_kml(self):
        path = filedialog.askopenfilename(filetypes=[("KML", "*.kml"), ("All", "*")])
        if path:
            self.kml_var.set(path)

    def select_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*")])
        if path:
            self.txt_var.set(path)

    def load(self):
        kml_path = self.kml_var.get()
        txt_path = self.txt_var.get()
        if not kml_path or not txt_path:
            return
        positions = parse_kml(kml_path)
        places = load_places(txt_path)
        grouped = group_positions_by_place(positions, places)
        summary = summarize_places(grouped)
        self.display_summary(summary)
        self.display_grouped(grouped)

    def display_summary(self, summary):
        self.left_text.delete("1.0", tk.END)
        for name, arrive, depart in summary:
            line = f"{name}\t{arrive.strftime('%Y-%m-%d %H:%M:%S')}\t{depart.strftime('%Y-%m-%d %H:%M:%S')}\n"
            self.left_text.insert(tk.END, line)

    def display_grouped(self, grouped):
        self.right_text.delete("1.0", tk.END)
        for name, entries in grouped.items():
            self.right_text.insert(tk.END, f"[{name}]\n")
            for dt, lat, lon in sorted(entries, key=lambda x: x[0]):
                line = f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} {lat:.6f}, {lon:.6f}\n"
                self.right_text.insert(tk.END, line)
            self.right_text.insert(tk.END, "\n")


def main():
    app = Viewer()
    app.mainloop()


if __name__ == "__main__":
    main()
