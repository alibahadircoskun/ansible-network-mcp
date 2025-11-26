# Ansible Network MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop to manage Ansible environments and execute network automation tasks on network devices.

## Overview

The Ansible Network MCP Server bridges conversational AI and network infrastructure management. It allows network engineers to describe automation goals in natural language and have Claude execute them through Ansible.

## Features

**Directory and File Management**
- Browse complete Ansible directory structure
- Read and write any file in the Ansible workspace
- Automatic file backups before modifications

**Inventory Management**
- Read and update inventory files
- Add or remove hosts dynamically
- List all hosts and groups

**Variables Management**
- Manage group_vars and host_vars files
- Read and write YAML variable files
- View computed variables for any host

**Configuration Management**
- Read and update ansible.cfg
- Configure connection settings
- Set timeouts and other parameters

**Playbook Operations**
- Create new playbooks from descriptions
- Edit existing playbooks
- Validate playbook syntax
- Run playbooks with various options
- Execute dry-run checks

**Device Interaction**
- Test connectivity with ping
- Gather device facts
- Retrieve running configurations
- Execute show commands
- Push configuration changes

**Template Management**
- Create and manage Jinja2 templates
- List available templates
- Read template contents

## Prerequisites

- Linux system (Ubuntu 24.04 or similar)
- Python 3.10 or higher
- Claude Desktop application
- Network devices with NETCONF or SSH access
- Network connectivity to target devices

## Installation

### 1. Create Python Virtual Environment

```bash
cd ~
python3 -m venv ~/ansible-venv
source ~/ansible-venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install mcp fastmcp ansible-core
```

### 3. Install Ansible Collections

```bash
# For Juniper devices
ansible-galaxy collection install junipernetworks.junos

# For Cisco devices
ansible-galaxy collection install cisco.ios cisco.nxos

# For Arista devices
ansible-galaxy collection install arista.eos
```

### 4. Create Directory Structure

```bash
mkdir -p ~/ansible/{inventory,group_vars,host_vars,playbooks,roles,templates,files}
mkdir -p ~/ansible-network-mcp
```

### 5. Deploy MCP Server

Copy `server.py` to `~/ansible-network-mcp/` and make it executable:

```bash
chmod +x ~/ansible-network-mcp/server.py
```

### 6. Configure Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ansible-network-mcp": {
      "command": "/home/USERNAME/ansible-venv/bin/python",
      "args": ["/home/USERNAME/ansible-network-mcp/server.py"],
      "env": {
        "ANSIBLE_HOST_KEY_CHECKING": "False",
        "ANSIBLE_FORCE_COLOR": "false"
      }
    }
  }
}
```

Replace `USERNAME` with your actual username.

### 7. Restart Claude Desktop

Completely quit and restart Claude Desktop to load the MCP server.

## Directory Structure

After installation:

```
~/ansible/
├── ansible.cfg
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── switches.yml
├── host_vars/
├── playbooks/
├── roles/
├── templates/
└── files/
```

## Quick Start

### Initial Setup

1. Open Claude Desktop
2. Ask: "Show me my Ansible directory structure"
3. Ask: "Create an inventory file with my lab devices"
4. Ask: "Create group_vars for my device groups"

### Example Workflows

**Backup Device Configurations:**
```
You: Create a playbook that backs up all device configs
Claude: [creates backup_configs.yml playbook]
You: Run it in check mode first
Claude: [executes dry-run]
You: Looks good, run it for real
Claude: [executes playbook]
```

**Configure OSPF:**
```
You: Create a playbook to configure OSPF area 0 on all routers
Claude: [creates ospf_config.yml playbook]
You: Test it on router-01 only
Claude: [runs with --limit router-01]
```

**Troubleshoot Connectivity:**
```
You: Ping all my devices
Claude: [runs ansible ping module]
You: Why is router-02 unreachable?
Claude: [analyzes and suggests fixes]
```

## Usage Examples

### Managing Inventory

- "Show me my current inventory"
- "Add a new host called router-03 with IP 192.168.1.3 to the routers group"
- "Remove switch-old from inventory"
- "List all hosts in the core_switches group"

### Working with Variables

- "Show me the group_vars for routers"
- "Create group_vars for core_switches with NETCONF settings"
- "What are the effective variables for router-01?"
- "Update the ansible_user in group_vars/all.yml"

### Creating Playbooks

- "Create a playbook that sets the hostname on all devices"
- "Create a playbook to configure NTP servers"
- "Create a playbook that gathers interface statistics"

### Running Playbooks

- "Run the backup playbook"
- "Run ntp_config.yml on the routers group only"
- "Check what changes the ospf playbook would make"
- "Validate the syntax of my backup playbook"

### Device Operations

- "Get the running config from all switches"
- "Run 'show version' on router-01"
- "Push this config to switch-01: set system name-server 8.8.8.8"
- "Gather facts from all devices"

## Available Tools

The server provides 30+ tools organized by function:

**Structure Management**
- `ansible_show_structure` - Display directory tree
- `ansible_read_file` - Read any file
- `ansible_write_file` - Write/create files

**Inventory**
- `ansible_read_inventory` - View hosts.ini
- `ansible_write_inventory` - Update inventory
- `ansible_add_host` - Add new host
- `ansible_remove_host` - Remove host
- `ansible_list_inventory` - List hosts and groups

**Variables**
- `ansible_list_vars` - List all var files
- `ansible_read_group_vars` - Read group variables
- `ansible_write_group_vars` - Update group variables
- `ansible_read_host_vars` - Read host variables
- `ansible_write_host_vars` - Update host variables
- `ansible_show_host_vars` - Show computed variables

**Configuration**
- `ansible_read_config` - Read ansible.cfg
- `ansible_write_config` - Update ansible.cfg

**Playbooks**
- `ansible_list_playbooks` - List all playbooks
- `ansible_create_playbook` - Create new playbook
- `ansible_read_playbook` - View playbook
- `ansible_edit_playbook` - Update playbook
- `ansible_delete_playbook` - Remove playbook
- `ansible_validate_playbook` - Check syntax
- `ansible_run_playbook` - Execute playbook
- `ansible_check_playbook` - Dry-run playbook

**Device Operations**
- `ansible_ping_devices` - Test connectivity
- `ansible_get_facts` - Gather device facts
- `ansible_get_config` - Get running config
- `ansible_run_command` - Execute show commands
- `ansible_push_config` - Push configuration
- `ansible_adhoc_command` - Run any Ansible module

**Templates**
- `ansible_list_templates` - List templates
- `ansible_read_template` - View template
- `ansible_create_template` - Create template

## Configuration

### Ansible Directory Location

By default, the server uses `~/ansible`. To use a different location, set the `ANSIBLE_DIR` environment variable in the Claude Desktop configuration:

```json
{
  "mcpServers": {
    "ansible-network-mcp": {
      "command": "/home/USERNAME/ansible-venv/bin/python",
      "args": ["/home/USERNAME/ansible-network-mcp/server.py"],
      "env": {
        "ANSIBLE_DIR": "/custom/path/to/ansible",
        "ANSIBLE_HOST_KEY_CHECKING": "False"
      }
    }
  }
}
```

### Inventory Example

Sample `inventory/hosts.ini`:

```ini
[routers]
router-01 ansible_host=192.168.1.1
router-02 ansible_host=192.168.1.2

[switches]
switch-01 ansible_host=192.168.1.10
switch-02 ansible_host=192.168.1.11
```

### Group Variables Example

Sample `group_vars/routers.yml`:

```yaml
---
# Connection settings
ansible_network_os: cisco.ios.ios
ansible_connection: network_cli
ansible_user: admin
ansible_password: secret123
ansible_become: yes
ansible_become_method: enable

# Common settings
ntp_servers:
  - 10.0.0.1
  - 10.0.0.2
```

## Security

The MCP server implements several security measures:

- **Path Restrictions:** All file operations are restricted to the Ansible directory
- **Input Sanitization:** User inputs are sanitized to prevent command injection
- **Automatic Backups:** Files are backed up before modifications
- **Password Masking:** Credentials are masked in output
- **No SSH Key Access:** Server does not access SSH keys directly

**Best Practices:**
- Use Ansible Vault for sensitive credentials
- Restrict file permissions on the Ansible directory
- Run the server under a dedicated user account
- Review playbooks before execution
- Use check mode for validation

## Troubleshooting

### Permission Denied (EACCES)

If Claude Desktop cannot execute the Python binary:

```bash
chmod +x ~/ansible-network-mcp/server.py
chown -R $USER:$USER ~/ansible ~/ansible-venv
```

### Module Not Found

Ensure you are using the correct Python from the virtual environment:

```bash
which python
# Should show: /home/USERNAME/ansible-venv/bin/python
```

### Connection Refused

Verify NETCONF or SSH is enabled on your devices:

```bash
# Test NETCONF
ssh -p 830 admin@192.168.1.1 -s netconf

# Test SSH
ssh admin@192.168.1.1
```

### Authentication Failures

Check credentials in `group_vars/` or `host_vars/`:

```bash
ansible-inventory -i ~/ansible/inventory/hosts.ini --host router-01
```

### Testing the Server

Run the server manually to check for errors:

```bash
source ~/ansible-venv/bin/activate
python ~/ansible-network-mcp/server.py
```

Expected output:
```
Starting Ansible Network MCP Server...
Ansible directory: /home/username/ansible
Inventory: /home/username/ansible/inventory/hosts.ini
Playbooks: /home/username/ansible/playbooks
```

### Claude Desktop Logs

Check Claude Desktop logs for connection issues:

```bash
# Linux
tail -f ~/.config/Claude/logs/mcp*.log

# macOS
tail -f ~/Library/Logs/Claude/mcp*.log
```

## Adding Device Types

### Cisco IOS

```bash
ansible-galaxy collection install cisco.ios
```

Create `group_vars/cisco_routers.yml`:

```yaml
---
ansible_network_os: cisco.ios.ios
ansible_connection: network_cli
ansible_user: admin
ansible_password: cisco123
ansible_become: yes
ansible_become_method: enable
```

### Arista EOS

```bash
ansible-galaxy collection install arista.eos
```

Create `group_vars/arista_switches.yml`:

```yaml
---
ansible_network_os: arista.eos.eos
ansible_connection: network_cli
ansible_user: admin
ansible_password: arista123
ansible_become: yes
ansible_become_method: enable
```

### Juniper JunOS

```bash
ansible-galaxy collection install junipernetworks.junos
```

Create `group_vars/juniper_devices.yml`:

```yaml
---
ansible_network_os: junipernetworks.junos.junos
ansible_connection: netconf
ansible_port: 830
ansible_user: root
ansible_password: juniper123
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies
4. Make your changes
5. Test with Claude Desktop

### Testing

Test the server manually:

```bash
source ~/ansible-venv/bin/activate
python server.py
```

Test with real devices in a lab environment before deploying to production.

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgments

- Anthropic for the Model Context Protocol specification
- Ansible community for network automation modules
- Network device vendors for API and NETCONF support

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.
