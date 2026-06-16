#!/bin/bash
##############################################################################
# VS Code Remote SSH Setup — JustDo Raspberry Pi
#
# Run this on your engineering PC (Git Bash on Windows, or Terminal on Mac/Linux)
# It sets up passwordless SSH to the Pi and validates the VS Code connection.
#
# Usage:  bash vscode_pi_ssh_setup.sh
##############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PI_IP="192.168.2.11"
PI_USER="pi"
PI_HOST="justdo-pi"
PI_JUSTDO_PATH="/home/pi/JustDo"

# On Windows (Git Bash), HOME maps to the Windows user profile
SSH_DIR="$HOME/.ssh"
SSH_KEY="$SSH_DIR/id_rsa"
SSH_CONFIG="$SSH_DIR/config"

PASS=0
FAIL=0

ok()   { echo -e "${GREEN}  ✓ $1${NC}"; PASS=$((PASS+1)); }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
fail() { echo -e "${RED}  ✗ $1${NC}"; FAIL=$((FAIL+1)); }
step() { echo -e "\n${BLUE}[$1]${NC} $2"; }

echo -e "${BLUE}"
echo "==========================================================="
echo " VS Code Remote SSH Setup — JustDo / Raspberry Pi"
echo "==========================================================="
echo -e "${NC}"

# ─── STEP 1: SSH directory ───────────────────────────────────────────────────
step 1 "Checking SSH directory..."

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
ok "SSH directory ready: $SSH_DIR"

# ─── STEP 2: SSH key generation ──────────────────────────────────────────────
step 2 "Checking SSH key..."

if [ -f "$SSH_KEY" ]; then
    ok "SSH private key exists: $SSH_KEY"
else
    warn "No SSH key found. Generating 4096-bit RSA key pair..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY" -N "" -C "justdo-pi@$(hostname)"
    chmod 600 "$SSH_KEY"
    chmod 644 "$SSH_KEY.pub"
    ok "SSH key pair generated"
fi

echo "    Public key:"
echo "    $(cat "$SSH_KEY.pub")"

# ─── STEP 3: SSH config ───────────────────────────────────────────────────────
step 3 "Configuring SSH config file..."

if [ -f "$SSH_CONFIG" ]; then
    cp "$SSH_CONFIG" "$SSH_CONFIG.backup.$(date +%s)"
    ok "Backed up existing SSH config"
fi

if grep -q "^Host $PI_HOST" "$SSH_CONFIG" 2>/dev/null; then
    warn "Host entry '$PI_HOST' already exists in SSH config — skipping"
else
    cat >> "$SSH_CONFIG" << EOF

# ── JustDo Raspberry Pi ──────────────────────────────────────────────────────
Host $PI_HOST
    HostName $PI_IP
    User $PI_USER
    IdentityFile $SSH_KEY
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts
EOF
    chmod 600 "$SSH_CONFIG"
    ok "Added host '$PI_HOST' to SSH config"
fi

# ─── STEP 4: Ping check ───────────────────────────────────────────────────────
step 4 "Checking network — can we reach the Pi?"

if ping -c 1 -W 2 "$PI_IP" &>/dev/null 2>&1 || ping -n 1 "$PI_IP" &>/dev/null 2>&1; then
    ok "Pi is reachable at $PI_IP"
else
    fail "Cannot ping $PI_IP"
    warn "Check that the Pi is powered on and on the same network (192.168.2.x)"
fi

# ─── STEP 5: Copy public key to Pi ───────────────────────────────────────────
step 5 "Copying public key to Raspberry Pi (you may be prompted for Pi password)..."

KEY_ALREADY_COPIED=false

# Test if key auth already works (no password needed)
if timeout 8 ssh -o ConnectTimeout=5 -o BatchMode=yes \
       -o StrictHostKeyChecking=accept-new \
       "$PI_USER@$PI_IP" "echo ok" &>/dev/null; then
    ok "Key already accepted by Pi — no copy needed"
    KEY_ALREADY_COPIED=true
fi

if [ "$KEY_ALREADY_COPIED" = false ]; then
    # Try ssh-copy-id (available on Linux/Mac; NOT on native Windows)
    if command -v ssh-copy-id &>/dev/null; then
        if ssh-copy-id -i "$SSH_KEY.pub" "$PI_USER@$PI_IP"; then
            ok "Public key copied via ssh-copy-id"
            KEY_ALREADY_COPIED=true
        fi
    fi

    # Fallback: pipe key over plain SSH (works on Windows Git Bash too)
    if [ "$KEY_ALREADY_COPIED" = false ]; then
        warn "ssh-copy-id not available — trying manual key copy..."
        if cat "$SSH_KEY.pub" | ssh \
               -o StrictHostKeyChecking=accept-new \
               "$PI_USER@$PI_IP" \
               "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"; then
            ok "Public key installed via manual method"
            KEY_ALREADY_COPIED=true
        else
            fail "Could not copy key automatically"
            echo ""
            warn "Do this manually on the Pi:"
            echo "    mkdir -p ~/.ssh && chmod 700 ~/.ssh"
            echo "    echo '$(cat "$SSH_KEY.pub")' >> ~/.ssh/authorized_keys"
            echo "    chmod 600 ~/.ssh/authorized_keys"
        fi
    fi
fi

# ─── STEP 6: Test passwordless SSH ───────────────────────────────────────────
step 6 "Testing SSH connection..."

if timeout 10 ssh -o ConnectTimeout=5 "$PI_HOST" "echo 'SSH Connection Successful!'" 2>/dev/null; then
    ok "Passwordless SSH to '$PI_HOST' works"

    PI_INFO=$(ssh "$PI_HOST" "uname -a" 2>/dev/null)
    echo "    Pi: $PI_INFO"

    if ssh "$PI_HOST" "[ -d $PI_JUSTDO_PATH ]" 2>/dev/null; then
        ok "JustDo directory found at $PI_JUSTDO_PATH"
    else
        warn "JustDo not found at $PI_JUSTDO_PATH"
        ACTUAL=$(ssh "$PI_HOST" "ls /home/pi/" 2>/dev/null)
        echo "    Contents of /home/pi/: $ACTUAL"
    fi
else
    fail "SSH connection failed — check Pi is on and SSH is enabled"
fi

# ─── STEP 7: Check VS Code Remote SSH extension ───────────────────────────────
step 7 "Checking VS Code Remote - SSH extension..."

if command -v code &>/dev/null; then
    if code --list-extensions 2>/dev/null | grep -q "ms-vscode-remote.remote-ssh"; then
        ok "Remote - SSH extension is installed"
    else
        warn "Remote - SSH extension not found"
        echo "    Install it:"
        echo "    code --install-extension ms-vscode-remote.remote-ssh"
        echo "    Or: VS Code → Extensions → search 'Remote - SSH' → Install"
    fi
else
    warn "VS Code 'code' CLI not found in PATH (this is OK — just install the extension manually)"
fi

# ─── STEP 8: Check Flask on Pi ───────────────────────────────────────────────
step 8 "Checking Flask status on Pi..."

if timeout 5 ssh "$PI_HOST" "pgrep -f 'python.*app.py\|flask' > /dev/null 2>&1" 2>/dev/null; then
    ok "Flask/app.py process detected on Pi"
    echo "    Port forward command: ssh -L 5000:localhost:5000 $PI_HOST"
else
    warn "Flask not currently running on the Pi"
    echo "    Start it on the Pi with:  python3 app.py"
fi

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
echo -e "\n${BLUE}==========================================================="
echo " Setup Complete — Summary"
echo -e "===========================================================${NC}\n"

echo -e "  Passed: ${GREEN}$PASS${NC}  Failed: ${RED}$FAIL${NC}"
echo ""
echo -e "${YELLOW}  Next steps:${NC}"
echo ""
echo "  1. Open VS Code"
echo "  2. Click Remote Explorer (left sidebar)"
echo "  3. You should see '$PI_HOST' listed"
echo "  4. Click Connect → Open Folder → $PI_JUSTDO_PATH"
echo ""
echo "  OR open directly from the command line:"
echo "    code --remote ssh-remote+$PI_HOST $PI_JUSTDO_PATH"
echo ""
echo "  Tunnel Flask locally (open browser at http://localhost:5000):"
echo "    ssh -L 5000:localhost:5000 $PI_HOST"
echo ""
