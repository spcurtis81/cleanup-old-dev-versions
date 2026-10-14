# Cleanup Old Dev Versions

A small macOS maintenance script that clears superseded Xcode simulator builds and unused Cursor agent executables. Preview changes first, run cleanup manually, or install a weekly job with notifications.

## What it cleans

- **Xcode simulator runtimes:** uses Apple's `xcrun simctl runtime delete --outdated` command to remove older builds of the same runtime identifier. It skips runtime cleanup when any simulator is booted.
- **Cursor agent executables:** removes historical versions from Cursor's bundled agent directory, retaining the launcher-selected version and any version referenced by a running process.

The script does not target chats, workspace databases, projects, Xcode archives, AI models or simulator device data. Old agent executables are rollback copies; removing them means reinstalling if you later need one.

It validates the expected Cursor directory layout before deleting anything. Unknown entries cause it to stop. Xcode cleanup happens first, so a later Cursor error does not undo simulator removal.

## Requirements

- macOS with a logged-in desktop user.
- Xcode installed and selected as the active developer directory, with its initial setup completed.
- Python 3 (the examples use `/usr/bin/python3`, available with the development tools on the tested Mac).
- Cursor's bundled agent installed at `~/Library/Application Support/Cursor/User/globalStorage/anysphere.cursor-agent-worker/agent-cli/.local/share/cursor-agent/versions` for Cursor cleanup.

No third-party Python packages are required. Run as your normal user, without `sudo`.

If `xcrun` cannot find `simctl`, select the correct Xcode installation in **Xcode → Settings → Locations → Command Line Tools**. The script targets the bundled Cursor agent, not a separately installed agent under `~/.local/share`.

## Download and preview

```sh
git clone https://github.com/spcurtis81/cleanup-old-dev-versions.git
cd cleanup-old-dev-versions
/usr/bin/python3 cleanup-old-dev-versions.py
```

The default is a preview: no versions are deleted. Review any reported candidates before applying them.

## Run cleanup manually

```sh
/usr/bin/python3 cleanup-old-dev-versions.py --apply
```

This permanently deletes eligible program versions. The script also prints current disk free space. Simulator removal is asynchronous and may finish shortly after the command returns.

## Install the weekly job

After reviewing the preview, run:

```sh
/usr/bin/python3 install-weekly-job.py
```

The installer copies the script and runner to `~/Library/Application Support/MacMaintenance` and loads a user LaunchAgent at `~/Library/LaunchAgents/com.ste.mac-maintenance.plist`. Installation itself does not run cleanup.

The job runs **every Sunday at 10:00 in the Mac's local timezone**, while you are logged in. Codex and Cursor do not need to be open. A scheduled run missed during sleep runs after waking; runs missed while powered off or logged out are not guaranteed to catch up.

The runner requests a **Mac Maintenance** notification when it removes old Cursor versions, successfully requests removal of outdated simulator builds, or encounters an error. Runs with nothing to clean remain silent. Notification visibility depends on macOS permissions and Focus settings.

Only the latest two run logs are retained:

```text
~/Library/Application Support/MacMaintenance/cleanup.log
~/Library/Application Support/MacMaintenance/cleanup.previous.log
```

Run the installed job now:

```sh
launchctl kickstart "gui/$(id -u)/com.ste.mac-maintenance"
```

Check its status and last exit code:

```sh
launchctl print "gui/$(id -u)/com.ste.mac-maintenance"
```

Read the latest log:

```sh
cat "$HOME/Library/Application Support/MacMaintenance/cleanup.log"
```

## Disable or re-enable

Disable the job without deleting its files:

```sh
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.ste.mac-maintenance.plist"
launchctl disable "gui/$(id -u)/com.ste.mac-maintenance"
```

Re-enable it:

```sh
launchctl enable "gui/$(id -u)/com.ste.mac-maintenance"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.ste.mac-maintenance.plist"
```

To uninstall, disable it first, then remove that exact plist and the `MacMaintenance` folder if you no longer want its scripts or logs.

## Update an installed job

Updating the Git checkout does not update the installed copy. Disable/unload the job using the commands above, then run:

```sh
git pull --ff-only
/usr/bin/python3 install-weekly-job.py
```

The installer refuses to replace a loaded job. It preserves existing logs when reinstalling.

## Limits and safeguards

- Apple's `--outdated` option removes superseded builds of the **same runtime identifier**. It does not enforce one major iOS version globally: installing iOS 28 will not automatically remove iOS 27. Review those separately in Xcode's Components settings.
- Active Cursor versions are checked before each deletion. Avoid running cleanup during an agent upgrade; process checks cannot eliminate every update race.
- If Xcode inspection fails, the script stops before proceeding to Cursor cleanup. Missing or unfamiliar Cursor layouts also stop the run and appear in the log.
- Reclaimed disk space may differ from summed file sizes because APFS can share storage blocks.
- The schedule and no-change path were tested on the author's Mac. Directory layouts and supported Xcode options can change between releases.

## Licence

MIT. See [LICENSE](LICENSE).
