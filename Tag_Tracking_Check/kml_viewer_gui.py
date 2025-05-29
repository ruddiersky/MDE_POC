import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from math import radians, cos, sin, asin, sqrt

from list_kml_positions import parse_kml


def haversine(lon1, lat1, lon2, lat2):
    """Return distance in meters between two coordinates."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371000 * c


def parse_places(path):
    places = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 4:
                continue
            name = row[1].split("(")[0].strip()
            lon = float(row[2])
            lat = float(row[3])
            places.append({"name": name, "lon": lon, "lat": lat})
    return places


def group_positions(places, positions, radius=300):
    groups = {p["name"]: [] for p in places}
    for dt, lat, lon in positions:
        for p in places:
            d = haversine(lon, lat, p["lon"], p["lat"])
            if d <= radius:
                groups[p["name"]].append((dt, lat, lon))
    return {k: v for k, v in groups.items() if v}


def summarize(groups):
    summary = []
    for name, pos_list in groups.items():
        pos_list.sort(key=lambda x: x[0])
        arrive = pos_list[0][0]
        depart = pos_list[-1][0]
        summary.append((name, arrive, depart))
    summary.sort(key=lambda x: x[1])
    return summary


class KMLViewerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KML 위치 정보")
        self.geometry("900x600")
        self._create_widgets()

    def _create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=5)

        self.txt_var = tk.StringVar()
        self.kml_var = tk.StringVar()

        ttk.Button(top, text="이동경로.txt", command=self.select_txt).pack(side=tk.LEFT, padx=5)
        ttk.Entry(top, textvariable=self.txt_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Tracking.kml", command=self.select_kml).pack(side=tk.LEFT, padx=5)
        ttk.Entry(top, textvariable=self.kml_var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="실행", command=self.process).pack(side=tk.LEFT, padx=5)

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right = ttk.Frame(body)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        columns = ("place", "arrive", "depart")
        self.tree = ttk.Treeview(left, columns=columns, show="headings")
        self.tree.heading("place", text="장소")
        self.tree.heading("arrive", text="도착시간")
        self.tree.heading("depart", text="출발 시간")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(right)
        scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def select_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path:
            self.txt_var.set(path)

    def select_kml(self):
        path = filedialog.askopenfilename(filetypes=[("KML", "*.kml")])
        if path:
            self.kml_var.set(path)

    def process(self):
        txt = self.txt_var.get()
        kml = self.kml_var.get()
        if not txt or not kml:
            messagebox.showerror("오류", "파일을 선택하세요")
            return
        try:
            places = parse_places(txt)
            positions = parse_kml(kml)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return

        groups = group_positions(places, positions)
        summary = summarize(groups)

        for item in self.tree.get_children():
            self.tree.delete(item)
        for name, arrive, depart in summary:
            self.tree.insert("", tk.END, values=(name, arrive.strftime("%Y-%m-%d %H:%M:%S"), depart.strftime("%Y-%m-%d %H:%M:%S")))

        self.text.delete("1.0", tk.END)
        for name, pos_list in groups.items():
            self.text.insert(tk.END, f"[{name}]\n")
            for dt, lat, lon in sorted(pos_list, key=lambda x: x[0]):
                self.text.insert(tk.END, f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {lat:.6f}, {lon:.6f}\n")
            self.text.insert(tk.END, "\n")


def main():
    app = KMLViewerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()