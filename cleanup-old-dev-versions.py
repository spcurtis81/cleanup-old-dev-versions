#!/usr/bin/env python3
"""Preview by default. Pass --apply to remove superseded program versions only."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()

def run(command):
    subprocess.run(command, check=True)

# Use Apple's version comparison, not alphabetical ordering of beta build numbers.
# This removes older builds of the same runtime identifier, not old major OS versions.
print('Simulator runtime cleanup', flush=True)
command = ['xcrun', 'simctl', 'runtime', 'delete', '--outdated']
if not args.apply:
    command.append('--dry-run')
devices = subprocess.run(['xcrun', 'simctl', 'list', 'devices', '--json'], capture_output=True, text=True, check=True, timeout=60)
booted = any(d.get('state') == 'Booted' for group in json.loads(devices.stdout)['devices'].values() for d in group)
if booted and args.apply:
    print('Simulator is running; skip runtime cleanup this week.')
    result = subprocess.CompletedProcess(command, 0, '', '')
else:
    preview = subprocess.run(command + ([] if not args.apply else ['--dry-run']), capture_output=True, text=True, timeout=120) if args.apply else None
    if preview and preview.returncode not in (0, 2):
        raise SystemExit('Runtime preview failed; refusing cleanup: ' + preview.stderr)
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if args.apply and result.returncode == 0 and preview and 'Would delete' in preview.stdout:
        print('CLEANUP_CHANGED: Superseded simulator runtime removal requested.', flush=True)
print(result.stdout, end='')
print(result.stderr, end='')
if result.returncode and not (result.returncode == 2 and 'No matching images found to delete' in result.stdout + result.stderr):
    raise SystemExit(result.returncode)

base = Path.home() / 'Library/Application Support/Cursor/User/globalStorage/anysphere.cursor-agent-worker/agent-cli/.local/share/cursor-agent/versions'
launcher = base.parent.parent.parent / 'bin/cursor-agent'
if not base.is_dir():
    raise SystemExit('Cursor version directory not found; nothing removed.')
current = launcher.resolve(strict=True).parent
if current.parent != base or not (current / 'index.js').is_file():
    raise SystemExit('Unrecognised Cursor layout; refusing removal.')
# Process arguments may contain credentials. Keep them in memory and never log them.
commands = subprocess.check_output(['/bin/ps', '-axo', 'command'], text=True, timeout=30)
active = set(re.findall(re.escape(str(base)) + r'/([^/\s]+)/', commands))
keep = active | {current.name}
candidates = []
for path in sorted(base.iterdir()):
    if path.is_symlink() or not path.is_dir() or not re.fullmatch(r'\d{4}\.\d{2}\.\d{2}-[a-f0-9]+', path.name):
        raise SystemExit('Unexpected version entry; refusing removal: ' + path.name)
    if not (path / 'cursor-agent').is_file() or not (path / 'index.js').is_file():
        raise SystemExit('Unrecognised version contents; refusing removal: ' + path.name)
    if path.name in keep:
        print('Keep Cursor agent:', path.name)
    else:
        candidates.append(path)
for path in candidates:
    # Recheck the launcher and active process paths immediately before each removal.
    if args.apply:
        now = subprocess.check_output(['/bin/ps', '-axo', 'command'], text=True, timeout=30)
        if launcher.resolve(strict=True).parent == path or str(path) + '/' in now:
            print('Keep newly active Cursor agent:', path.name)
            continue
        shutil.rmtree(path)
    print('Removed' if args.apply else 'Would remove', 'Cursor agent:', path.name)
print('Chat databases, workspace state, projects and simulator device data are outside this cleanup.')
run(['df', '-h', '/'])
