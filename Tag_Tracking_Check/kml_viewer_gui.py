import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
NS = {
    'kml': 'http://www.opengis.net/kml/2.2'
}


def parse_kml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    positions = []
    for pm in root.findall('.//kml:Placemark', NS):
        when_elem = pm.find('.//kml:TimeStamp/kml:when', NS)
        coord_elem = pm.find('.//kml:Point/kml:coordinates', NS)
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


class KMLViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('KML 위치 정보')
        self.geometry('500x400')
        self._create_widgets()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=5)
        open_btn = ttk.Button(toolbar, text='파일 선택', command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=5)
        self.text = tk.Text(self, wrap=tk.NONE)
        self.text.pack(fill=tk.BOTH, expand=True)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[('KML 파일', '*.kml'), ('모든 파일', '*.*')])
        if not path:
            return
        try:
            positions = parse_kml(path)
        except Exception as e:
            messagebox.showerror('오류', str(e))
            return
        self.text.delete('1.0', tk.END)
        for dt, lat, lon in positions:
            line = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {lat:.6f} {lon:.6f}\n"
            self.text.insert(tk.END, line)


def main():
    app = KMLViewer()
    app.mainloop()


if __name__ == '__main__':
    main()
