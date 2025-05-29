import re
from typing import List, Dict
import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText


def parse_fc_events(path: str) -> List[Dict[str, str]]:
    events = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        capturing = False
        package = None
        timestamp = None
        cause = None
        event_lines = []
        for line in f:
            if 'beginning of crash' in line.lower():
                capturing = True
                package = None
                timestamp = None
                cause = None
                event_lines = [line.strip()]
                continue
            if capturing:
                event_lines.append(line.strip())
                if not timestamp:
                    m = re.match(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                    if m:
                        timestamp = m.group(1)
                if 'Cmdline:' in line:
                    package = line.split('Cmdline:')[1].strip()
                if 'Cause:' in line:
                    cause = line.split('Cause:')[1].strip()
                if line.strip() == '':
                    events.append({
                        'timestamp': timestamp or '',
                        'package': package or '',
                        'cause': cause or '',
                        'details': '\n'.join(event_lines)
                    })
                    capturing = False
        if capturing:
            events.append({
                'timestamp': timestamp or '',
                'package': package or '',
                'cause': cause or '',
                'details': '\n'.join(event_lines)
            })
    return events


def parse_anr_events(path: str) -> List[Dict[str, str]]:
    events = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'ServiceANR' in line:
                m = re.match(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                ts = m.group(1) if m else ''
                pm = re.search(r'UFZ : ([\w\.]+)', line)
                pkg = pm.group(1) if pm else ''
                rm = re.search(r'reason: ([^\s]+)', line)
                reason = rm.group(1) if rm else ''
                events.append({'timestamp': ts, 'package': pkg, 'reason': reason, 'line': line.strip()})
            elif 'exitType: ANR' in line:
                m = re.match(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                ts = m.group(1) if m else ''
                events.append({'timestamp': ts, 'package': '', 'reason': 'exitType: ANR', 'line': line.strip()})
    return events


def analyze_file(path: str) -> str:
    fc_events = parse_fc_events(path)
    anr_events = parse_anr_events(path)
    lines = []
    lines.append('=== App F/C Events ===')
    if not fc_events:
        lines.append('F/C 이벤트 없음')
    for i, e in enumerate(fc_events, 1):
        cause = f", 원인: {e['cause']}" if e['cause'] else ''
        lines.append(f"[{i}] 시각: {e['timestamp']} 패키지: {e['package']}{cause}")
    lines.append('\n=== ANR Events ===')
    if not anr_events:
        lines.append('ANR 이벤트 없음')
    for i, e in enumerate(anr_events, 1):
        pkg = f" 패키지: {e['package']}" if e['package'] else ''
        reason = f", 원인: {e['reason']}" if e['reason'] else ''
        lines.append(f"[{i}] 시각: {e['timestamp']}{pkg}{reason}")
    return '\n'.join(lines)


def open_file():
    filepath = filedialog.askopenfilename(title='dumpstate 파일 선택', filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')])
    if not filepath:
        return
    result = analyze_file(filepath)
    output.delete('1.0', tk.END)
    output.insert(tk.END, result)


root = tk.Tk()
root.title('Dumpstate Analyzer')

open_btn = tk.Button(root, text='덤프 파일 열기', command=open_file)
open_btn.pack(padx=10, pady=10)

output = ScrolledText(root, width=100, height=30)
output.pack(padx=10, pady=10, fill='both', expand=True)

root.mainloop()
