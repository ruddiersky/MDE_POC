import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from Tag_Tracking_Check.list_kml_positions import (
    parse_kml,
    parse_locations,
    group_by_location,
)


class KMLViewerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KML 위치 보기")
        self.geometry("700x500")

        top = tk.Frame(self)
        top.pack(pady=10)

        self.kml_path = tk.StringVar()
        self.loc_path = tk.StringVar()

        tk.Button(top, text="KML 파일 선택", command=self.select_kml).grid(row=0, column=0, padx=5)
        tk.Entry(top, textvariable=self.kml_path, width=50).grid(row=0, column=1)

        tk.Button(top, text="이동경로.txt 선택", command=self.select_loc).grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(top, textvariable=self.loc_path, width=50).grid(row=1, column=1)

        tk.Button(self, text="실행", command=self.run).pack(pady=5)

        self.text = scrolledtext.ScrolledText(self)
        self.text.pack(expand=True, fill="both", padx=5, pady=5)

    def select_kml(self):
        path = filedialog.askopenfilename(filetypes=[("KML files", "*.kml")])
        if path:
            self.kml_path.set(path)

    def select_loc(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.loc_path.set(path)

    def run(self):
        kml_path = self.kml_path.get()
        if not kml_path:
            messagebox.showerror("오류", "KML 파일을 선택하세요.")
            return
        loc_path = self.loc_path.get() or "이동경로.txt"
        try:
            positions = parse_kml(kml_path)
        except Exception as e:
            messagebox.showerror("오류", f"KML 읽기 실패: {e}")
            return
        try:
            locations = parse_locations(loc_path)
        except FileNotFoundError:
            locations = []
        output = []
        if locations:
            groups = group_by_location(positions, locations)
            for loc in locations:
                name = loc["name"]
                output.append(f"[{name}]")
                items = groups.get(name, [])
                if not items:
                    output.append("  해당 위치 정보 없음")
                else:
                    for dt, lat, lon in items:
                        output.append(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {lat:.6f} {lon:.6f}")
                output.append("")
        else:
            for dt, lat, lon in positions:
                output.append(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {lat:.6f} {lon:.6f}")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, "\n".join(output))


if __name__ == "__main__":
    app = KMLViewerGUI()
    app.mainloop()