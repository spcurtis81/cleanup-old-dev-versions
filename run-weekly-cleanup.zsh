#!/bin/zsh
set -u
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
folder="$HOME/Library/Application Support/MacMaintenance"
log="$folder/cleanup.log"
notify() {
    /usr/bin/osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "Mac Maintenance"' -e 'end run' "$1"
}
if [[ -f "$log" ]]; then
    /bin/mv -f "$log" "$folder/cleanup.previous.log" || { notify 'Weekly cleanup could not rotate its log.'; exit 1; }
fi
exec >"$log" 2>&1 || { notify 'Weekly cleanup could not open its log.'; exit 1; }
/bin/date '+Cleanup started: %Y-%m-%d %H:%M:%S %Z'
/usr/bin/python3 -u "$folder/cleanup-old-dev-versions.py" --apply
result=$?
/bin/date '+Cleanup finished: %Y-%m-%d %H:%M:%S %Z'
print "Exit status: $result"
if (( result != 0 )); then
    notify 'Weekly cleanup encountered an error. Check the Mac Maintenance cleanup log.' || print 'Notification delivery failed.'
elif /usr/bin/grep -Eq '^CLEANUP_CHANGED:|^Removed Cursor agent:' "$log"; then
    notify 'Weekly cleanup removed old developer versions. Details are in the Mac Maintenance cleanup log.' || print 'Notification delivery failed.'
fi
exit "$result"
