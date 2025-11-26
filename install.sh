#!/bin/bash
# Ansible Network MCP Server - Installation Script
# Run this script from the ansible-network-mcp directory

set -e

echo "=========================================="
echo "Ansible Network MCP Server - Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root (required for /root/ansible)
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo ./install.sh)${NC}"
    exit 1
fi

# Step 1: Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo "$PYTHON_VERSION >= 3.10" | bc)" -eq 1 ]; then
    echo -e "${GREEN}Python $PYTHON_VERSION found - OK${NC}"
else
    echo -e "${RED}Python 3.10+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi

# Step 2: Create/activate virtual environment
echo ""
echo -e "${YELLOW}[2/7] Setting up Python virtual environment...${NC}"
if [ ! -d "/root/ansible-venv" ]; then
    python3 -m venv /root/ansible-venv
    echo -e "${GREEN}Created new virtual environment at /root/ansible-venv${NC}"
else
    echo -e "${GREEN}Using existing virtual environment at /root/ansible-venv${NC}"
fi
source /root/ansible-venv/bin/activate

# Step 3: Install Python dependencies
echo ""
echo -e "${YELLOW}[3/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install mcp fastmcp ansible-core

# Step 4: Install Juniper Ansible Collection
echo ""
echo -e "${YELLOW}[4/7] Installing Juniper Networks Ansible collection...${NC}"
ansible-galaxy collection install junipernetworks.junos --force

# Step 5: Create improved directory structure
echo ""
echo -e "${YELLOW}[5/7] Setting up improved Ansible directory structure...${NC}"
ANSIBLE_DIR="/root/ansible"

# Create directories
mkdir -p "$ANSIBLE_DIR/inventory"
mkdir -p "$ANSIBLE_DIR/group_vars"
mkdir -p "$ANSIBLE_DIR/host_vars"
mkdir -p "$ANSIBLE_DIR/playbooks"
mkdir -p "$ANSIBLE_DIR/roles"

# Move existing files if they exist in root
if [ -f "$ANSIBLE_DIR/hosts.ini" ] && [ ! -f "$ANSIBLE_DIR/inventory/hosts.ini" ]; then
    cp "$ANSIBLE_DIR/hosts.ini" "$ANSIBLE_DIR/inventory/hosts.ini"
    echo -e "${GREEN}Copied hosts.ini to inventory/hosts.ini${NC}"
fi

if [ -f "$ANSIBLE_DIR/playbook.yml" ] && [ ! -f "$ANSIBLE_DIR/playbooks/playbook.yml" ]; then
    cp "$ANSIBLE_DIR/playbook.yml" "$ANSIBLE_DIR/playbooks/playbook.yml"
    echo -e "${GREEN}Copied playbook.yml to playbooks/playbook.yml${NC}"
fi

# Create group_vars file for qfx_switches if it doesn't exist
if [ ! -f "$ANSIBLE_DIR/group_vars/qfx_switches.yml" ]; then
    cat > "$ANSIBLE_DIR/group_vars/qfx_switches.yml" << 'EOF'
---
# Group variables for qfx_switches
# Connection settings
ansible_network_os: junipernetworks.junos.junos
ansible_connection: netconf
ansible_port: 830

# SSH settings
ansible_ssh_common_args: '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

# Credentials (consider using Ansible Vault for production)
ansible_user: root
ansible_password: Admin123_
EOF
    echo -e "${GREEN}Created group_vars/qfx_switches.yml${NC}"
fi

# Create simplified inventory file
if [ ! -f "$ANSIBLE_DIR/inventory/hosts.ini" ]; then
    cat > "$ANSIBLE_DIR/inventory/hosts.ini" << 'EOF'
[qfx_switches]
VMX33-PE ansible_host=192.168.100.33
VMX34-P ansible_host=192.168.100.34
VMX35-PE ansible_host=192.168.100.35
EOF
    echo -e "${GREEN}Created simplified inventory/hosts.ini (credentials now in group_vars)${NC}"
fi

# Step 6: Update ansible.cfg
echo ""
echo -e "${YELLOW}[6/7] Updating ansible.cfg...${NC}"
cat > "$ANSIBLE_DIR/ansible.cfg" << 'EOF'
[defaults]
inventory = /root/ansible/inventory/hosts.ini
host_key_checking = False
timeout = 30
deprecation_warnings = False
interpreter_python = auto_silent

[persistent_connection]
connect_timeout = 30
command_timeout = 30
EOF
echo -e "${GREEN}Updated ansible.cfg${NC}"

# Step 7: Copy server files
echo ""
echo -e "${YELLOW}[7/7] Installing MCP server...${NC}"
MCP_DIR="/root/ansible-network-mcp"
mkdir -p "$MCP_DIR"

# Copy server.py if running from the distribution directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/server.py" ]; then
    cp "$SCRIPT_DIR/server.py" "$MCP_DIR/server.py"
    echo -e "${GREEN}Installed server.py to $MCP_DIR${NC}"
fi

# Make server executable
chmod +x "$MCP_DIR/server.py"

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Directory structure created:"
echo "  /root/ansible/"
echo "  ├── ansible.cfg"
echo "  ├── inventory/"
echo "  │   └── hosts.ini"
echo "  ├── group_vars/"
echo "  │   └── qfx_switches.yml"
echo "  ├── host_vars/"
echo "  ├── playbooks/"
echo "  └── roles/"
echo ""
echo "MCP Server installed at: $MCP_DIR/server.py"
echo ""
echo "Next steps:"
echo "1. Review and update credentials in /root/ansible/group_vars/qfx_switches.yml"
echo "2. Update your Claude Desktop configuration (see README.md)"
echo "3. Restart Claude Desktop"
echo ""
echo "To test the server manually:"
echo "  source /root/ansible-venv/bin/activate"
echo "  python $MCP_DIR/server.py"
echo ""
