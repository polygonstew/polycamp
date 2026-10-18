#!/bin/sh
# Syntax-check every browser module:  sh tools/jscheck.sh
cd "$(dirname "$0")/.." || exit 1
bad=0
for f in web/js/*.js web/js/views/*.js; do
  if ! node --input-type=module --check < "$f" 2>/tmp/jscheck.err; then
    echo "SYNTAX ERROR in $f"; cat /tmp/jscheck.err; bad=1
  fi
done
[ $bad = 0 ] && echo "all JS modules parse"
exit $bad
