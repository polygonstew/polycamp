#!/bin/sh
# Start Polycamp on the LAN (default port 8570). Needs only Python 3.8+.  Data lives in ./data (or $POLYCAMP_DATA).
cd "$(dirname "$0")" || exit 1
exec python3 server/polycamp.py "$@"
