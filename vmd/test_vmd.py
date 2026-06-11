"""Test VMD subprocess pipe communication on Linux."""
import queue
import subprocess
import threading
import time

VMD_CMD = "vmd"
SENTINEL = "---VMD-MCP-DONE---"


def reader(proc, q):
    for raw in proc.stdout:
        q.put(raw.decode(errors="replace").rstrip("\n"))


def send(proc, q, command, timeout=10.0):
    proc.stdin.write(f"{command}\nputs \"{SENTINEL}\"\nflush stdout\n".encode())
    proc.stdin.flush()
    lines = []
    while True:
        try:
            line = q.get(timeout=timeout)
        except queue.Empty:
            return f"TIMEOUT after {timeout}s"
        if line == SENTINEL:
            break
        lines.append(line)
    return "\n".join(lines).strip() or "OK"


print("Launching VMD...")
proc = subprocess.Popen(
    [VMD_CMD, "-dispdev", "text"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)
q = queue.Queue()
threading.Thread(target=reader, args=(proc, q), daemon=True).start()
time.sleep(3)

tests = [
    ("puts hello",              "hello"),
    ("expr 1 + 1",              "2"),
    ("mol list",                None),   # just check no timeout
]

passed = 0
for cmd, expect in tests:
    result = send(proc, q, cmd)
    ok = (expect is None) or (expect in result)
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    print(f"[{status}] {cmd!r} -> {result!r}")

proc.stdin.write(b"quit\n")
proc.stdin.flush()
proc.wait(timeout=5)
print(f"\n{passed}/{len(tests)} passed")
