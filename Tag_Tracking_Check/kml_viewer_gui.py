import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from list_kml_positions import parse_kml


class KMLViewer:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title('KML 위치 보기')

        self.open_btn = tk.Button(master, text='KML 파일 선택', command=self.open_file)
        self.open_btn.pack(pady=5)

        self.text = scrolledtext.ScrolledText(master, width=60, height=20)
        self.text.pack(fill=tk.BOTH, expand=True)

    def open_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[('KML 파일', '*.kml'), ('모든 파일', '*')])
        if not path:
            return
        try:
            positions = parse_kml(path)
        except Exception as e:
            messagebox.showerror('오류', f'파일을 읽을 수 없습니다:\n{e}')
            return
        self.text.delete('1.0', tk.END)
        for dt, lat, lon in positions:
            line = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {lat:.6f} {lon:.6f}\n"
            self.text.insert(tk.END, line)


def main() -> None:
    root = tk.Tk()
    KMLViewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()
