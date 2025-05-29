import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from dumpstate_analyzer import parse_fc_events, parse_anr_events


class DumpstateGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dumpstate Analyzer")
        self.geometry("700x500")

        self._create_widgets()

    def _create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=5)

        open_btn = ttk.Button(toolbar, text="파일 선택", command=self.open_file)
        open_btn.pack(side=tk.LEFT, padx=5)

        self.text = tk.Text(self, wrap=tk.NONE)
        self.text.pack(fill=tk.BOTH, expand=True)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not path:
            return
        try:
            fc_events = parse_fc_events(path)
            anr_events = parse_anr_events(path)
        except Exception as e:
            messagebox.showerror("오류", str(e))
            return

        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, "=== App F/C Events ===\n")
        if not fc_events:
            self.text.insert(tk.END, "No F/C events found\n")
        for i, e in enumerate(fc_events, 1):
            cause = f" Cause: {e['cause']}" if e.get('cause') else ''
            self.text.insert(tk.END, f"[{i}] Time: {e['timestamp']} Package: {e['package']}{cause}\n")

        self.text.insert(tk.END, "\n=== ANR Events ===\n")
        if not anr_events:
            self.text.insert(tk.END, "No ANR events found\n")
        for i, e in enumerate(anr_events, 1):
            pkg = f" Package: {e['package']}" if e['package'] else ''
            reason = f" Reason: {e['reason']}" if e.get('reason') else ''
            self.text.insert(tk.END, f"[{i}] Time: {e['timestamp']}{pkg}{reason}\n")

def main():
    app = DumpstateGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
