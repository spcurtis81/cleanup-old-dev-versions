#!/usr/bin/env python3
"""Install the Sunday 10:00 LaunchAgent for the current macOS user."""
import os
import plistlib
import shutil
import subprocess
from pathlib import Path

source = Path(__file__).resolve().parent
folder = Path.home() / 'Library/Application Support/MacMaintenance'
agent = Path.home() / 'Library/LaunchAgents/com.ste.mac-maintenance.plist'
domain = 'gui/' + str(os.getuid())
label = 'com.ste.mac-maintenance'

def run(*args):
    subprocess.run(args, check=True)

if os.getuid() == 0:
    raise SystemExit('Run as your logged-in user, without sudo.')
for name in ['cleanup-old-dev-versions.py', 'run-weekly-cleanup.zsh']:
    if not (source / name).is_file():
        raise SystemExit('Missing installation file: ' + name)
loaded = subprocess.run(['/bin/launchctl', 'print', domain + '/' + label], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
if loaded:
    raise SystemExit('Job is already loaded. Disable/unload it using the README before reinstalling.')
folder.mkdir(parents=True, exist_ok=True, mode=0o700)
agent.parent.mkdir(parents=True, exist_ok=True)
for name in ['cleanup-old-dev-versions.py', 'run-weekly-cleanup.zsh']:
    shutil.copyfile(source / name, folder / name)
    (folder / name).chmod(0o700)
config = {
    'Label': label,
    'ProgramArguments': ['/bin/zsh', str(folder / 'run-weekly-cleanup.zsh')],
    'StartCalendarInterval': {'Weekday': 0, 'Hour': 10, 'Minute': 0},
    'ProcessType': 'Background',
    'EnvironmentVariables': {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'},
    'RunAtLoad': False,
}
agent.write_bytes(plistlib.dumps(config))
agent.chmod(0o644)
run('/usr/bin/plutil', '-lint', str(agent))
run('/bin/launchctl', 'enable', domain + '/' + label)
run('/bin/launchctl', 'bootstrap', domain, str(agent))
print('Installed: Sundays at 10:00, local time. No cleanup was run during installation.')
print('Logs:', folder / 'cleanup.log')
