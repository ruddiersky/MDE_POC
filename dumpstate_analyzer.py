import re
import sys
from typing import List, Dict


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
                rm = re.search(r'reason:\s*(\S+)', line)
                reason = rm.group(1) if rm else ''
                events.append({'timestamp': ts, 'package': pkg, 'reason': reason, 'line': line.strip()})
            elif 'exitType: ANR' in line:
                m = re.match(r'(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                ts = m.group(1) if m else ''
                events.append({'timestamp': ts, 'package': '', 'reason': '', 'line': line.strip()})
    return events


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'dumpstate.txt'
    fc_events = parse_fc_events(path)
    anr_events = parse_anr_events(path)

    print('=== App F/C Events ===')
    if not fc_events:
        print('No F/C events found')
    for i, e in enumerate(fc_events, 1):
        cause = f" Cause: {e['cause']}" if e.get('cause') else ''
        print(f"[{i}] Time: {e['timestamp']} Package: {e['package']}{cause}")

    print('\n=== ANR Events ===')
    if not anr_events:
        print('No ANR events found')
    for i, e in enumerate(anr_events, 1):
        pkg = f" Package: {e['package']}" if e['package'] else ''
        reason = f" Reason: {e['reason']}" if e.get('reason') else ''
        print(f"[{i}] Time: {e['timestamp']}{pkg}{reason}")


if __name__ == '__main__':
    main()
