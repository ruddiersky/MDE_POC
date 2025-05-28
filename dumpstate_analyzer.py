import re
import sys
from typing import List, Dict


def parse_fc_events(path: str) -> List[Dict[str, str]]:
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        capturing = False
        package = None
        timestamp = None
        reason = None
        event_lines = []
        for line in f:
            lower = line.lower()
            if "beginning of crash" in lower:
                capturing = True
                package = None
                timestamp = None
                reason = None
                event_lines = [line.rstrip()]
                continue

            if capturing:
                # If another log section starts, end the current crash block
                if line.startswith("--------- ") and "beginning of crash" not in lower:
                    events.append(
                        {
                            "timestamp": timestamp or "",
                            "package": package or "",
                            "reason": reason or "",
                            "details": "\n".join(event_lines),
                        }
                    )
                    capturing = False
                    # Do not process this line as part of the crash
                    continue

                event_lines.append(line.rstrip())

                if timestamp is None:
                    m = re.match(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", line)
                    if m:
                        timestamp = m.group(1)

                if "Cmdline:" in line:
                    package = line.split("Cmdline:")[1].strip()

                if "Cause:" in line:
                    reason = line.split("Cause:", 1)[1].strip()

        if capturing:
            events.append(
                {
                    "timestamp": timestamp or "",
                    "package": package or "",
                    "reason": reason or "",
                    "details": "\n".join(event_lines),
                }
            )
    return events


def parse_anr_events(path: str) -> List[Dict[str, str]]:
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "ServiceANR" in line:
                ts_match = re.match(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", line)
                ts = ts_match.group(1) if ts_match else ""
                pkg_match = re.search(r"UFZ : ([\w\.]+)", line)
                pkg = pkg_match.group(1) if pkg_match else ""
                reason_match = re.search(r"reason:\s*(\S+)", line)
                reason = reason_match.group(1) if reason_match else "ServiceANR"
                events.append({"timestamp": ts, "package": pkg, "reason": reason, "line": line.strip()})
            elif "exitType: ANR" in line:
                ts_match = re.match(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)", line)
                ts = ts_match.group(1) if ts_match else ""
                events.append({"timestamp": ts, "package": "", "reason": "ANR", "line": line.strip()})
    return events


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'dumpstate.txt'
    fc_events = parse_fc_events(path)
    anr_events = parse_anr_events(path)

    print('=== App F/C Events ===')
    if not fc_events:
        print('No F/C events found')
    for i, e in enumerate(fc_events, 1):
        reason = f" Reason: {e['reason']}" if e.get('reason') else ''
        print(f"[{i}] Time: {e['timestamp']} Package: {e['package']}{reason}")

    print('\n=== ANR Events ===')
    if not anr_events:
        print('No ANR events found')
    for i, e in enumerate(anr_events, 1):
        pkg = f" Package: {e['package']}" if e['package'] else ''
        reason = f" Reason: {e['reason']}" if e.get('reason') else ''
        print(f"[{i}] Time: {e['timestamp']}{pkg}{reason}")


if __name__ == '__main__':
    main()
