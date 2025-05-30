import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from math import radians, cos, sin, asin, sqrt

from list_kml_positions import parse_kml

# 거리 계산을 위한 haversine 함수 (단위: 미터)
def haversine(lon1, lat1, lon2, lat2):
    R = 6371e3
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

# 이동경로.txt 파싱
def parse_path_txt(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 헤더 건너뜀
        for row in reader:
            # 최소 6개 컬럼(순서, 장소, 경도, 위도, 도착알림, 출발알림)이 있어야 함
            if len(row) < 6:
                continue
            place = row[1]
            lon = float(row[2])
            lat = float(row[3])
            arrive_alert = row[4].replace(".", ":").strip()
            depart_alert = row[5].replace(".", ":").strip()
            entries.append({
                "place": place,
                "lon": lon,
                "lat": lat,
                "arrive_alert": arrive_alert,
                "depart_alert": depart_alert,
            })
    return entries

# KML 위치 정보를 장소 기준으로 그룹화
def group_positions(entries, kml_positions, radius=300):
    groups = {e["place"]: [] for e in entries}
    for dt, lat, lon in kml_positions:
        for e in entries:
            dist = haversine(lon, lat, e["lon"], e["lat"])
            if dist <= radius:
                groups[e["place"]].append((dt, lat, lon))
    return groups

# 장소 이름만 추출 (주소 부분 제거)
def short_place(name: str) -> str:
    if "(" in name:
        return name.split("(")[0].strip()
    return name.strip()

class RealRouteGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real Route Viewer")
        self.geometry("1600x800")
        self._create_widgets()

    def _create_widgets(self):
        # 상단 파일 선택 영역
        top = ttk.Frame(self)
        top.pack(fill=tk.X, pady=5)

        self.txt_var = tk.StringVar()
        self.kml_var = tk.StringVar()

        ttk.Button(top, text="이동경로.txt", command=self.select_txt).grid(row=0, column=0, padx=5)
        ttk.Entry(top, textvariable=self.txt_var, width=60).grid(row=0, column=1, padx=5)

        ttk.Button(top, text="Tracking.kml", command=self.select_kml).grid(row=1, column=0, padx=5)
        ttk.Entry(top, textvariable=self.kml_var, width=60).grid(row=1, column=1, padx=5)

        ttk.Button(top, text="불러오기", command=self.load).grid(row=2, column=0, columnspan=2, pady=5)

        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        # 왼쪽 요약 테이블
        left_frame = ttk.Labelframe(body, text="history_real_route_summury")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns1 = ("place", "arrive", "depart", "alert", "diff", "result")
        self.tree_summary = ttk.Treeview(left_frame, columns=columns1, show="headings")
        self.tree_summary.heading("place", text="장소")
        self.tree_summary.heading("arrive", text="도착시간")
        self.tree_summary.heading("depart", text="출발 시간")
        self.tree_summary.heading("alert", text="도착알림 시간")
        self.tree_summary.heading("diff", text="diff 도착-알림")
        self.tree_summary.heading("result", text="결과_도착비교")
        self.tree_summary.pack(fill=tk.BOTH, expand=True)

        # 오른쪽 상세 테이블
        right_frame = ttk.Labelframe(body, text="history_real_route")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns2 = ("place", "time", "lat", "lon")
        self.tree_detail = ttk.Treeview(right_frame, columns=columns2, show="headings")
        self.tree_detail.heading("place", text="장소")
        self.tree_detail.heading("time", text="시간")
        self.tree_detail.heading("lat", text="위도")
        self.tree_detail.heading("lon", text="경도")
        self.tree_detail.pack(fill=tk.BOTH, expand=True)

    def select_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path:
            self.txt_var.set(path)

    def select_kml(self):
        path = filedialog.askopenfilename(filetypes=[("KML", "*.kml")])
        if path:
            self.kml_var.set(path)

    def load(self):
        txt = self.txt_var.get()
        kml = self.kml_var.get()
        if not txt or not kml:
            messagebox.showerror("오류", "파일을 선택하세요")
            return

        try:
            entries = parse_path_txt(txt)
            kml_positions = parse_kml(kml)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return

        groups = group_positions(entries, kml_positions)

        for item in self.tree_summary.get_children():
            self.tree_summary.delete(item)
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)

        # 상세 정보 출력
        for e in entries:
            place = e["place"]
            rows = groups.get(place, [])
            for dt, lat, lon in rows:
                self.tree_detail.insert("", tk.END, values=[short_place(place), dt.strftime("%H:%M:%S"), f"{lat:.6f}", f"{lon:.6f}"])

        # 요약 정보 출력
        summary_rows = []
        for e in entries:
            place = e["place"]
            rows = groups.get(place, [])
            if rows:
                arrive_dt = rows[0][0]
                depart_dt = rows[-1][0]
                arrive_str = arrive_dt.strftime("%H:%M:%S")
                depart_str = depart_dt.strftime("%H:%M:%S")
                alert_str = e.get("arrive_alert", "")

                diff_display = ""
                result = ""
                if alert_str and alert_str != "-":
                    try:
                        h, m = map(int, alert_str.split(":")[:2])
                        alert_dt = arrive_dt.replace(hour=h, minute=m, second=0, microsecond=0)
                        diff_min = (alert_dt - arrive_dt).total_seconds() / 60
                        diff_display = f"{diff_min:.1f}"
                        result = "Pass" if 0 <= diff_min <= 2 else "Fail"
                    except ValueError:
                        result = "Fail"
                else:
                    result = "Fail"

                summary_rows.append((arrive_dt, short_place(place), arrive_str, depart_str, alert_str, diff_display, result))

        summary_rows.sort(key=lambda x: x[0])
        for _, p, a, d, alert, diff, res in summary_rows:
            self.tree_summary.insert("", tk.END, values=[p, a, d, alert, diff, res])


def main():
    app = RealRouteGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
