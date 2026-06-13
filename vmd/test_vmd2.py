import subprocess

VMD_CMD = 'vmd'

def wait_for_prompt(proc, prompt=b'vmd > '):
    """Read stdout until the VMD prompt appears."""
    buf = b''
    while not buf.endswith(prompt):
        ch = proc.stdout.read(1)
        if not ch:
            break
        buf += ch
    return buf.decode(errors='replace')

def send_cmd(proc, cmd: str):
    proc.stdin.write((cmd + '\n').encode())
    proc.stdin.flush()
    return wait_for_prompt(proc)

print("Launching VMD...")
proc = subprocess.Popen(
    [VMD_CMD, "-dispdev", "text"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
)

# Wait for VMD to be ready
wait_for_prompt(proc)
print("VMD ready.")

# Example: print VMD version
out = send_cmd(proc, 'vmdinfo version')
print(out)

# Quit VMD cleanly
send_cmd(proc, 'quit')
proc.wait()
print("VMD exited.")