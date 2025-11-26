# Troubleshooting Guide

This guide covers common issues and their solutions when using the Ansible Network MCP Server.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Connection Problems](#connection-problems)
3. [Authentication Errors](#authentication-errors)
4. [Playbook Execution Issues](#playbook-execution-issues)
5. [Claude Desktop Integration](#claude-desktop-integration)

## Installation Issues

### Python Virtual Environment Not Found

**Symptom:** `bash: venv/bin/activate: No such file or directory`

**Solution:**
```bash
cd ~
python3 -m venv ~/ansible-venv
source ~/ansible-venv/bin/activate
```

### Module Installation Fails

**Symptom:** `pip install` commands fail

**Solution:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Then install packages
pip install mcp fastmcp ansible-core
```

### Ansible Collection Installation Fails

**Symptom:** `ansible-galaxy` cannot install collections

**Solution:**
```bash
# Ensure Ansible is installed
pip install ansible-core

# Install with verbose output
ansible-galaxy collection install junipernetworks.junos -vvv
```

## Connection Problems

### Cannot Connect to Devices

**Symptom:** `UNREACHABLE` or connection timeout errors

**Check List:**
1. Verify network connectivity: `ping 192.168.1.1`
2. Check SSH/NETCONF is enabled on devices
3. Verify firewall rules allow connections
4. Confirm correct port (22 for SSH, 830 for NETCONF)

**Test NETCONF Connection:**
```bash
ssh -p 830 admin@192.168.1.1 -s netconf
```

**Test SSH Connection:**
```bash
ssh admin@192.168.1.1
```

### NETCONF Not Working

**Symptom:** Connection to port 830 fails

**Solution for Juniper:**
```
set system services netconf ssh
commit
```

**Solution for Cisco:**
```
netconf-yang
netconf-yang ssh
```

### Host Key Verification Failed

**Symptom:** `Host key verification failed`

**Solution:**
Add to your ansible.cfg:
```ini
[defaults]
host_key_checking = False
```

Or in group_vars:
```yaml
ansible_ssh_common_args: '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
```

## Authentication Errors

### Authentication Failed

**Symptom:** `Authentication or permission failure`

**Check List:**
1. Verify credentials in group_vars or host_vars
2. Confirm user has correct permissions
3. Check privilege escalation settings

**View Computed Variables:**
Ask Claude: "Show me the effective variables for router-01"

Or run manually:
```bash
ansible-inventory -i ~/ansible/inventory/hosts.ini --host router-01
```

### Permission Denied for Privilege Escalation

**Symptom:** Commands fail that require elevated privileges

**Solution:**
For Cisco devices, add to group_vars:
```yaml
ansible_become: yes
ansible_become_method: enable
ansible_become_password: your_enable_password
```

### Credentials Not Being Used

**Symptom:** Wrong credentials being applied

**Solution:**
Check variable precedence:
1. host_vars (highest priority)
2. group_vars
3. inventory file (lowest priority)

Ensure credentials are in the right location.

## Playbook Execution Issues

### Playbook Syntax Errors

**Symptom:** YAML parsing errors

**Solution:**
Validate syntax:
```bash
ansible-playbook playbook.yml --syntax-check
```

Or ask Claude: "Validate the syntax of my playbook"

### Module Not Found

**Symptom:** `ERROR! couldn't resolve module/action`

**Solution:**
```bash
# List installed collections
ansible-galaxy collection list

# Install missing collection
ansible-galaxy collection install vendor.collection_name
```

### Tasks Timeout

**Symptom:** Tasks take too long and timeout

**Solution:**
Increase timeouts in ansible.cfg:
```ini
[defaults]
timeout = 60

[persistent_connection]
command_timeout = 60
```

Or in group_vars:
```yaml
ansible_command_timeout: 60
ansible_connect_timeout: 60
```

### Playbook Hangs

**Symptom:** Playbook stops responding

**Solution:**
1. Check if prompts are expected (use `-vvv` for verbose)
2. Ensure `gather_facts: no` for network devices
3. Verify device is responding
4. Check for configuration prompts that need answers

## Claude Desktop Integration

### Server Not Starting

**Symptom:** Claude Desktop shows server disconnected

**Test Server Manually:**
```bash
source ~/ansible-venv/bin/activate
python ~/ansible-network-mcp/server.py
```

**Check for Errors:**
Look for Python tracebacks or error messages.

### Permission Denied (EACCES)

**Symptom:** `spawn /path/to/python EACCES`

**Solution:**
```bash
chmod +x ~/ansible-network-mcp/server.py
chown -R $USER:$USER ~/ansible ~/ansible-venv
```

### Tools Not Appearing

**Symptom:** Claude does not see any tools

**Solution:**
1. Restart Claude Desktop completely
2. Check configuration file syntax
3. Verify paths in config are correct
4. Check Claude Desktop logs

**View Logs:**
```bash
# Linux
tail -f ~/.config/Claude/logs/mcp*.log

# macOS
tail -f ~/Library/Logs/Claude/mcp*.log
```

### Wrong Python Interpreter

**Symptom:** Import errors or module not found

**Solution:**
Verify the correct Python is being used:
```bash
which python
# Should show: /home/USERNAME/ansible-venv/bin/python
```

Update Claude Desktop config with full path:
```json
{
  "mcpServers": {
    "ansible-network-mcp": {
      "command": "/home/USERNAME/ansible-venv/bin/python",
      "args": ["/home/USERNAME/ansible-network-mcp/server.py"]
    }
  }
}
```

### Environment Variables Not Set

**Symptom:** Server cannot find Ansible directory

**Solution:**
Add environment variables to config:
```json
{
  "mcpServers": {
    "ansible-network-mcp": {
      "command": "/home/USERNAME/ansible-venv/bin/python",
      "args": ["/home/USERNAME/ansible-network-mcp/server.py"],
      "env": {
        "ANSIBLE_DIR": "/home/USERNAME/ansible",
        "ANSIBLE_HOST_KEY_CHECKING": "False"
      }
    }
  }
}
```

## Getting More Help

### Enable Verbose Logging

Run Ansible commands with verbose flags:
```bash
ansible-playbook playbook.yml -vvv
```

### Check Ansible Facts

Gather facts manually:
```bash
ansible -i inventory/hosts.ini router-01 -m junipernetworks.junos.junos_facts
```

### Test Individual Tools

Test specific MCP tools by asking Claude to use them with verbose output.

### Report Issues

If you encounter issues not covered here:
1. Check existing GitHub issues
2. Gather diagnostic information:
   - OS and Python version
   - Ansible version
   - Device vendor and OS version
   - Error messages and logs
3. Create a new issue with details

## Quick Diagnostics Checklist

Run these commands to gather diagnostic information:

```bash
# Python version
python3 --version

# Ansible version
ansible --version

# Installed collections
ansible-galaxy collection list

# Test connectivity
ansible -i inventory/hosts.ini all -m ping

# Check inventory
ansible-inventory -i inventory/hosts.ini --list

# Verify server runs
source ~/ansible-venv/bin/activate
python ~/ansible-network-mcp/server.py
```

Include this information when reporting issues.
