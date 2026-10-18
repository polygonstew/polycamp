#!/bin/sh
# Install Polycamp as a systemd USER service (Linux): starts on login, restarts if it dies.
set -e
DIR="$HOME/.jcodes/polycamp"
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
cp "$DIR/tools/polycamp.service" "$UNIT_DIR/polycamp.service"
systemctl --user daemon-reload
systemctl --user enable --now polycamp.service
sleep 1
systemctl --user --no-pager status polycamp.service | head -5 || true
IP=$(ip -4 route get 1.1.1.1 2>/dev/null | grep -oP 'src \K[\d.]+' | head -1)
echo "Polycamp: http://${IP:-127.0.0.1}:8570"
echo "Logs:     journalctl --user -u polycamp -f"
echo "Firewall: if another PC cannot connect, allow TCP 8570 (for ufw: sudo ufw allow 8570/tcp)"
