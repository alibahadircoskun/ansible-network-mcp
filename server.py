#!/usr/bin/env python3
"""Ansible Network MCP Server - Network device configuration and troubleshooting for home lab."""

import subprocess
import sys
import os
import json
import re
import logging
import shutil
from datetime import datetime

# Configure logging to stderr (required for MCP)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("ansible-network-mcp")

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("ansible-network-mcp")

# Configuration - Uses environment variable or defaults to ~/ansible
ANSIBLE_DIR = os.environ.get("ANSIBLE_DIR", os.path.expanduser("~/ansible"))
INVENTORY_DIR = os.path.join(ANSIBLE_DIR, "inventory")
INVENTORY_PATH = os.path.join(INVENTORY_DIR, "hosts.ini")
PLAYBOOKS_DIR = os.path.join(ANSIBLE_DIR, "playbooks")
GROUP_VARS_DIR = os.path.join(ANSIBLE_DIR, "group_vars")
HOST_VARS_DIR = os.path.join(ANSIBLE_DIR, "host_vars")
ROLES_DIR = os.path.join(ANSIBLE_DIR, "roles")
TEMPLATES_DIR = os.path.join(ANSIBLE_DIR, "templates")
FILES_DIR = os.path.join(ANSIBLE_DIR, "files")

# Ensure directories exist (only if we have permission)
for d in [INVENTORY_DIR, PLAYBOOKS_DIR, GROUP_VARS_DIR, HOST_VARS_DIR, ROLES_DIR, TEMPLATES_DIR, FILES_DIR]:
    try:
        os.makedirs(d, exist_ok=True)
    except PermissionError:
        logger.warning(f"Cannot create directory {d} - will create when needed with sudo or different permissions")


def sanitize_input(value: str) -> str:
    """Sanitize input to prevent command injection."""
    if not value:
        return ""
    dangerous_chars = [";", "&", "|", "$", "`", "(", ")", "{", "}", "<", ">", "\\"]
    for char in dangerous_chars:
        value = value.replace(char, "")
    return value.strip()


def sanitize_filename(value: str) -> str:
    """Sanitize filename - allow only safe characters."""
    if not value:
        return ""
    safe = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', value)
    return safe.strip('_.')


def safe_path_join(base_dir: str, filename: str) -> str:
    """Safely join paths preventing directory traversal."""
    filename = sanitize_filename(filename)
    full_path = os.path.normpath(os.path.join(base_dir, filename))
    if not full_path.startswith(os.path.normpath(base_dir)):
        raise ValueError("Path traversal detected")
    return full_path


def run_ansible_command(cmd: list, timeout: int = 300) -> str:
    """Execute an Ansible command and return formatted output."""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=ANSIBLE_DIR,
            env={**os.environ, "ANSIBLE_HOST_KEY_CHECKING": "False", "ANSIBLE_FORCE_COLOR": "false"}
        )
        output_parts = []
        if result.stdout:
            output_parts.append("=== OUTPUT ===\n" + result.stdout)
        if result.stderr:
            output_parts.append("=== STDERR ===\n" + result.stderr)
        if result.returncode != 0:
            output_parts.append(f"\n=== RETURN CODE: {result.returncode} ===")
        return "\n".join(output_parts) if output_parts else "Command completed with no output."
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after {} seconds.".format(timeout)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return f"ERROR: {str(e)}"


def parse_ansible_output(raw_output: str) -> str:
    """Parse Ansible output and return a summary."""
    lines = raw_output.split("\n")
    summary_lines = []
    in_play_recap = False
    for line in lines:
        if "PLAY RECAP" in line:
            in_play_recap = True
        if in_play_recap:
            summary_lines.append(line)
        elif "fatal:" in line.lower() or "failed:" in line.lower():
            summary_lines.append(line)
        elif "changed:" in line.lower() and "ok=" not in line.lower():
            summary_lines.append(line)
    if summary_lines:
        return "=== SUMMARY ===\n" + "\n".join(summary_lines) + "\n\n=== FULL OUTPUT ===\n" + raw_output
    return raw_output


def get_available_playbooks() -> list:
    """Get list of available playbooks."""
    playbooks = []
    if os.path.exists(PLAYBOOKS_DIR):
        for f in os.listdir(PLAYBOOKS_DIR):
            if f.endswith((".yml", ".yaml")):
                playbooks.append(f)
    root_playbook = os.path.join(ANSIBLE_DIR, "playbook.yml")
    if os.path.exists(root_playbook):
        playbooks.append("playbook.yml (root)")
    return playbooks


def backup_file(filepath: str) -> str:
    """Create a timestamped backup of a file."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.{timestamp}.bak"
        shutil.copy2(filepath, backup_path)
        return backup_path
    return ""


# =============================================================================
# ANSIBLE DIRECTORY STRUCTURE TOOLS
# =============================================================================

@mcp.tool()
def ansible_show_structure() -> str:
    """Show the current Ansible directory structure and all files."""
    output = ["=== ANSIBLE DIRECTORY STRUCTURE ===", f"Base: {ANSIBLE_DIR}\n"]
    
    def list_dir(path: str, indent: int = 0) -> list:
        lines = []
        prefix = "  " * indent
        try:
            items = sorted(os.listdir(path))
            for item in items:
                full_path = os.path.join(path, item)
                if item.startswith('.') or item.endswith('.bak'):
                    continue
                if os.path.isdir(full_path):
                    lines.append(f"{prefix}📁 {item}/")
                    lines.extend(list_dir(full_path, indent + 1))
                else:
                    size = os.path.getsize(full_path)
                    lines.append(f"{prefix}📄 {item} ({size} bytes)")
        except PermissionError:
            lines.append(f"{prefix}⛔ Permission denied")
        return lines
    
    output.extend(list_dir(ANSIBLE_DIR))
    return "\n".join(output)


@mcp.tool()
def ansible_read_file(file_path: str = "") -> str:
    """Read any file in the Ansible directory. Use relative path from /root/ansible/ like inventory/hosts.ini or group_vars/all.yml"""
    if not file_path:
        return "ERROR: No file path specified. Examples: inventory/hosts.ini, group_vars/qfx_switches.yml, ansible.cfg"
    
    file_path = file_path.lstrip('/')
    full_path = os.path.normpath(os.path.join(ANSIBLE_DIR, file_path))
    
    if not full_path.startswith(ANSIBLE_DIR):
        return "ERROR: Access denied - path must be within Ansible directory."
    
    if not os.path.exists(full_path):
        return f"ERROR: File not found: {file_path}"
    
    if os.path.isdir(full_path):
        files = os.listdir(full_path)
        return f"'{file_path}' is a directory containing:\n" + "\n".join(f"  - {f}" for f in sorted(files))
    
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return f"=== FILE: {file_path} ===\n\n{content}"
    except Exception as e:
        return f"ERROR: Failed to read file: {str(e)}"


@mcp.tool()
def ansible_write_file(file_path: str = "", content: str = "", create_backup: str = "yes") -> str:
    """Write content to any file in the Ansible directory. Creates parent directories if needed. Use relative path from /root/ansible/"""
    if not file_path:
        return "ERROR: No file path specified."
    if not content:
        return "ERROR: No content provided."
    
    file_path = file_path.lstrip('/')
    full_path = os.path.normpath(os.path.join(ANSIBLE_DIR, file_path))
    
    if not full_path.startswith(ANSIBLE_DIR):
        return "ERROR: Access denied - path must be within Ansible directory."
    
    # Create parent directories
    parent_dir = os.path.dirname(full_path)
    os.makedirs(parent_dir, exist_ok=True)
    
    # Backup existing file
    backup_path = ""
    if create_backup.lower() in ["yes", "true", "1"] and os.path.exists(full_path):
        backup_path = backup_file(full_path)
    
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        
        msg = f"SUCCESS: File written to {file_path}"
        if backup_path:
            msg += f"\nBackup saved to: {os.path.basename(backup_path)}"
        return msg
    except Exception as e:
        return f"ERROR: Failed to write file: {str(e)}"


# =============================================================================
# INVENTORY MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def ansible_read_inventory() -> str:
    """Read and display the current inventory file (hosts.ini)."""
    if not os.path.exists(INVENTORY_PATH):
        return f"ERROR: Inventory file not found at {INVENTORY_PATH}\n\nUse ansible_write_inventory to create one."
    
    try:
        with open(INVENTORY_PATH, 'r') as f:
            content = f.read()
        return f"=== INVENTORY: {INVENTORY_PATH} ===\n\n{content}"
    except Exception as e:
        return f"ERROR: Failed to read inventory: {str(e)}"


@mcp.tool()
def ansible_write_inventory(content: str = "") -> str:
    """Write/update the inventory file (hosts.ini). Provide the complete INI-format inventory content."""
    if not content:
        return "ERROR: No inventory content provided. Example format:\n\n[group_name]\nhost1 ansible_host=192.168.1.1\nhost2 ansible_host=192.168.1.2"
    
    backup_path = backup_file(INVENTORY_PATH)
    
    try:
        os.makedirs(INVENTORY_DIR, exist_ok=True)
        with open(INVENTORY_PATH, 'w') as f:
            f.write(content)
        
        # Validate with ansible-inventory
        cmd = ["ansible-inventory", "-i", INVENTORY_PATH, "--list"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ANSIBLE_DIR)
        
        if result.returncode == 0:
            msg = f"SUCCESS: Inventory updated at {INVENTORY_PATH}"
            if backup_path:
                msg += f"\nBackup: {os.path.basename(backup_path)}"
            return msg
        else:
            return f"WARNING: Inventory written but validation failed:\n{result.stderr}\n\nBackup: {os.path.basename(backup_path)}"
    except Exception as e:
        return f"ERROR: Failed to write inventory: {str(e)}"


@mcp.tool()
def ansible_add_host(hostname: str = "", ansible_host: str = "", group: str = "all", extra_vars: str = "") -> str:
    """Add a new host to the inventory. extra_vars format: var1=value1 var2=value2"""
    if not hostname:
        return "ERROR: No hostname specified."
    if not ansible_host:
        return "ERROR: No ansible_host (IP address) specified."
    
    hostname = sanitize_input(hostname)
    ansible_host = sanitize_input(ansible_host)
    group = sanitize_input(group) or "all"
    
    # Read current inventory
    current_content = ""
    if os.path.exists(INVENTORY_PATH):
        with open(INVENTORY_PATH, 'r') as f:
            current_content = f.read()
    
    # Check if host already exists
    if hostname in current_content:
        return f"ERROR: Host '{hostname}' already exists in inventory."
    
    # Build host line
    host_line = f"{hostname} ansible_host={ansible_host}"
    if extra_vars:
        host_line += f" {sanitize_input(extra_vars)}"
    
    # Find or create group
    lines = current_content.split('\n')
    group_header = f"[{group}]"
    group_found = False
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip() == group_header:
            group_found = True
            # Insert host after group header
            new_lines.append(host_line)
    
    if not group_found:
        # Add new group at end
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(group_header)
        new_lines.append(host_line)
    
    backup_file(INVENTORY_PATH)
    with open(INVENTORY_PATH, 'w') as f:
        f.write('\n'.join(new_lines))
    
    return f"SUCCESS: Added host '{hostname}' ({ansible_host}) to group '{group}'"


@mcp.tool()
def ansible_remove_host(hostname: str = "", confirm: str = "no") -> str:
    """Remove a host from the inventory. Set confirm=yes to actually remove."""
    if not hostname:
        return "ERROR: No hostname specified."
    
    if confirm.lower() not in ["yes", "true", "1"]:
        return f"WARNING: This will remove '{hostname}' from inventory. Set confirm=yes to proceed."
    
    hostname = sanitize_input(hostname)
    
    if not os.path.exists(INVENTORY_PATH):
        return "ERROR: Inventory file not found."
    
    with open(INVENTORY_PATH, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    removed = False
    for line in lines:
        if line.strip().startswith(hostname + " ") or line.strip() == hostname:
            removed = True
            continue
        new_lines.append(line)
    
    if not removed:
        return f"ERROR: Host '{hostname}' not found in inventory."
    
    backup_file(INVENTORY_PATH)
    with open(INVENTORY_PATH, 'w') as f:
        f.writelines(new_lines)
    
    return f"SUCCESS: Removed host '{hostname}' from inventory."


# =============================================================================
# GROUP_VARS / HOST_VARS MANAGEMENT
# =============================================================================

@mcp.tool()
def ansible_list_vars() -> str:
    """List all group_vars and host_vars files."""
    output = ["=== ANSIBLE VARIABLES ===\n"]
    
    # Group vars
    output.append("GROUP VARS (group_vars/):")
    if os.path.exists(GROUP_VARS_DIR):
        files = [f for f in os.listdir(GROUP_VARS_DIR) if f.endswith(('.yml', '.yaml'))]
        if files:
            for f in sorted(files):
                group_name = f.rsplit('.', 1)[0]
                output.append(f"  📁 {group_name} -> {f}")
        else:
            output.append("  (no files)")
    else:
        output.append("  (directory not found)")
    
    output.append("\nHOST VARS (host_vars/):")
    if os.path.exists(HOST_VARS_DIR):
        files = [f for f in os.listdir(HOST_VARS_DIR) if f.endswith(('.yml', '.yaml'))]
        if files:
            for f in sorted(files):
                host_name = f.rsplit('.', 1)[0]
                output.append(f"  📁 {host_name} -> {f}")
        else:
            output.append("  (no files)")
    else:
        output.append("  (directory not found)")
    
    return "\n".join(output)


@mcp.tool()
def ansible_read_group_vars(group_name: str = "") -> str:
    """Read variables for a group from group_vars/."""
    if not group_name:
        # List available groups
        if os.path.exists(GROUP_VARS_DIR):
            files = [f.rsplit('.', 1)[0] for f in os.listdir(GROUP_VARS_DIR) if f.endswith(('.yml', '.yaml'))]
            if files:
                return "Available group_vars:\n- " + "\n- ".join(sorted(files))
        return "ERROR: No group name specified and no group_vars found."
    
    group_name = sanitize_filename(group_name)
    
    # Try both .yml and .yaml
    for ext in ['.yml', '.yaml']:
        filepath = os.path.join(GROUP_VARS_DIR, group_name + ext)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            return f"=== GROUP VARS: {group_name} ===\n\n{content}"
    
    return f"ERROR: group_vars file not found for group '{group_name}'"


@mcp.tool()
def ansible_write_group_vars(group_name: str = "", content: str = "") -> str:
    """Write/update variables for a group in group_vars/. Provide YAML content."""
    if not group_name:
        return "ERROR: No group name specified."
    if not content:
        return "ERROR: No content provided. Provide YAML-formatted variables."
    
    group_name = sanitize_filename(group_name)
    filepath = os.path.join(GROUP_VARS_DIR, group_name + '.yml')
    
    os.makedirs(GROUP_VARS_DIR, exist_ok=True)
    
    if os.path.exists(filepath):
        backup_file(filepath)
    
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        return f"SUCCESS: group_vars/{group_name}.yml updated."
    except Exception as e:
        return f"ERROR: Failed to write group_vars: {str(e)}"


@mcp.tool()
def ansible_read_host_vars(hostname: str = "") -> str:
    """Read variables for a specific host from host_vars/."""
    if not hostname:
        if os.path.exists(HOST_VARS_DIR):
            files = [f.rsplit('.', 1)[0] for f in os.listdir(HOST_VARS_DIR) if f.endswith(('.yml', '.yaml'))]
            if files:
                return "Available host_vars:\n- " + "\n- ".join(sorted(files))
        return "ERROR: No hostname specified and no host_vars found."
    
    hostname = sanitize_filename(hostname)
    
    for ext in ['.yml', '.yaml']:
        filepath = os.path.join(HOST_VARS_DIR, hostname + ext)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            return f"=== HOST VARS: {hostname} ===\n\n{content}"
    
    return f"ERROR: host_vars file not found for host '{hostname}'"


@mcp.tool()
def ansible_write_host_vars(hostname: str = "", content: str = "") -> str:
    """Write/update variables for a specific host in host_vars/. Provide YAML content."""
    if not hostname:
        return "ERROR: No hostname specified."
    if not content:
        return "ERROR: No content provided. Provide YAML-formatted variables."
    
    hostname = sanitize_filename(hostname)
    filepath = os.path.join(HOST_VARS_DIR, hostname + '.yml')
    
    os.makedirs(HOST_VARS_DIR, exist_ok=True)
    
    if os.path.exists(filepath):
        backup_file(filepath)
    
    try:
        with open(filepath, 'w') as f:
            f.write(content)
        return f"SUCCESS: host_vars/{hostname}.yml updated."
    except Exception as e:
        return f"ERROR: Failed to write host_vars: {str(e)}"


# =============================================================================
# ANSIBLE.CFG MANAGEMENT
# =============================================================================

@mcp.tool()
def ansible_read_config() -> str:
    """Read the ansible.cfg configuration file."""
    cfg_path = os.path.join(ANSIBLE_DIR, "ansible.cfg")
    
    if not os.path.exists(cfg_path):
        return "ERROR: ansible.cfg not found. Use ansible_write_config to create one."
    
    with open(cfg_path, 'r') as f:
        content = f.read()
    return f"=== ANSIBLE.CFG ===\n\n{content}"


@mcp.tool()
def ansible_write_config(content: str = "") -> str:
    """Write/update the ansible.cfg configuration file."""
    if not content:
        return "ERROR: No content provided. Provide INI-formatted ansible.cfg content."
    
    cfg_path = os.path.join(ANSIBLE_DIR, "ansible.cfg")
    
    if os.path.exists(cfg_path):
        backup_file(cfg_path)
    
    try:
        with open(cfg_path, 'w') as f:
            f.write(content)
        return "SUCCESS: ansible.cfg updated."
    except Exception as e:
        return f"ERROR: Failed to write ansible.cfg: {str(e)}"


# =============================================================================
# PLAYBOOK MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
def ansible_run_playbook(playbook_name: str = "", limit_hosts: str = "", extra_vars: str = "", tags: str = "", verbose: str = "no") -> str:
    """Run an Ansible playbook. Use limit_hosts to target specific hosts/groups. Use extra_vars for variables. Use tags to run specific tasks."""
    if not playbook_name:
        available = get_available_playbooks()
        if available:
            return "ERROR: No playbook specified. Available:\n- " + "\n- ".join(available)
        return "ERROR: No playbook specified."
    
    playbook_name = sanitize_input(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    if not os.path.exists(playbook_path):
        alt_path = os.path.join(ANSIBLE_DIR, playbook_name)
        if os.path.exists(alt_path):
            playbook_path = alt_path
        else:
            return f"ERROR: Playbook not found: {playbook_name}"
    
    cmd = ["ansible-playbook", "-i", INVENTORY_PATH, playbook_path]
    
    if limit_hosts:
        cmd.extend(["--limit", sanitize_input(limit_hosts)])
    if extra_vars:
        cmd.extend(["--extra-vars", sanitize_input(extra_vars)])
    if tags:
        cmd.extend(["--tags", sanitize_input(tags)])
    if verbose.lower() in ["yes", "true", "1"]:
        cmd.append("-vvv")
    
    raw_output = run_ansible_command(cmd)
    return parse_ansible_output(raw_output)


@mcp.tool()
def ansible_check_playbook(playbook_name: str = "", limit_hosts: str = "") -> str:
    """Preview a playbook in check mode (dry-run). Shows what would change without making changes."""
    if not playbook_name:
        available = get_available_playbooks()
        if available:
            return "ERROR: No playbook specified. Available:\n- " + "\n- ".join(available)
        return "ERROR: No playbook specified."
    
    playbook_name = sanitize_input(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    if not os.path.exists(playbook_path):
        alt_path = os.path.join(ANSIBLE_DIR, playbook_name)
        if os.path.exists(alt_path):
            playbook_path = alt_path
        else:
            return f"ERROR: Playbook not found: {playbook_name}"
    
    cmd = ["ansible-playbook", "-i", INVENTORY_PATH, playbook_path, "--check", "--diff"]
    
    if limit_hosts:
        cmd.extend(["--limit", sanitize_input(limit_hosts)])
    
    raw_output = run_ansible_command(cmd)
    return "=== DRY RUN (CHECK MODE) ===\n" + parse_ansible_output(raw_output)


@mcp.tool()
def ansible_create_playbook(playbook_name: str = "", content: str = "", description: str = "") -> str:
    """Create a new Ansible playbook. Provide the name and full YAML content."""
    if not playbook_name:
        return "ERROR: No playbook name specified."
    if not content:
        return "ERROR: No playbook content provided."
    
    playbook_name = sanitize_filename(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    
    if os.path.exists(playbook_path):
        return f"ERROR: Playbook '{playbook_name}' already exists. Use ansible_edit_playbook to modify."
    
    os.makedirs(PLAYBOOKS_DIR, exist_ok=True)
    
    try:
        with open(playbook_path, "w") as f:
            if description:
                f.write(f"# {description}\n")
            f.write(content)
        
        # Validate syntax
        cmd = ["ansible-playbook", "-i", INVENTORY_PATH, playbook_path, "--syntax-check"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=ANSIBLE_DIR)
        
        if result.returncode == 0:
            return f"SUCCESS: Playbook '{playbook_name}' created and validated.\nPath: {playbook_path}"
        else:
            return f"WARNING: Playbook created but has syntax errors:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"ERROR: Failed to create playbook: {str(e)}"


@mcp.tool()
def ansible_read_playbook(playbook_name: str = "") -> str:
    """Read and display the contents of a playbook."""
    if not playbook_name:
        available = get_available_playbooks()
        if available:
            return "Available playbooks:\n- " + "\n- ".join(available)
        return "ERROR: No playbooks found."
    
    playbook_name = sanitize_input(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    if not os.path.exists(playbook_path):
        alt_path = os.path.join(ANSIBLE_DIR, playbook_name)
        if os.path.exists(alt_path):
            playbook_path = alt_path
        else:
            return f"ERROR: Playbook not found: {playbook_name}"
    
    try:
        with open(playbook_path, "r") as f:
            content = f.read()
        return f"=== PLAYBOOK: {playbook_name} ===\n\n{content}"
    except Exception as e:
        return f"ERROR: Failed to read playbook: {str(e)}"


@mcp.tool()
def ansible_edit_playbook(playbook_name: str = "", content: str = "") -> str:
    """Update an existing playbook with new content. Creates a backup first."""
    if not playbook_name:
        available = get_available_playbooks()
        if available:
            return "ERROR: No playbook specified. Available:\n- " + "\n- ".join(available)
        return "ERROR: No playbook specified."
    if not content:
        return "ERROR: No new content provided."
    
    playbook_name = sanitize_input(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    if not os.path.exists(playbook_path):
        alt_path = os.path.join(ANSIBLE_DIR, playbook_name)
        if os.path.exists(alt_path):
            playbook_path = alt_path
        else:
            return f"ERROR: Playbook not found: {playbook_name}"
    
    backup_path = backup_file(playbook_path)
    
    try:
        with open(playbook_path, "w") as f:
            f.write(content)
        
        # Validate syntax
        cmd = ["ansible-playbook", "-i", INVENTORY_PATH, playbook_path, "--syntax-check"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=ANSIBLE_DIR)
        
        if result.returncode == 0:
            return f"SUCCESS: Playbook updated.\nBackup: {os.path.basename(backup_path)}"
        else:
            return f"WARNING: Playbook updated but has syntax errors:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"ERROR: Failed to update playbook: {str(e)}"


@mcp.tool()
def ansible_delete_playbook(playbook_name: str = "", confirm: str = "no") -> str:
    """Delete a playbook. Set confirm=yes to actually delete."""
    if not playbook_name:
        available = get_available_playbooks()
        if available:
            return "ERROR: No playbook specified. Available:\n- " + "\n- ".join(available)
        return "ERROR: No playbook specified."
    
    if confirm.lower() not in ["yes", "true", "1"]:
        return f"WARNING: This will delete '{playbook_name}'. Set confirm=yes to proceed."
    
    playbook_name = sanitize_input(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    if not os.path.exists(playbook_path):
        return f"ERROR: Playbook not found: {playbook_name}"
    
    try:
        backup_file(playbook_path)  # Backup before delete
        os.remove(playbook_path)
        return f"SUCCESS: Playbook '{playbook_name}' deleted (backup created)."
    except Exception as e:
        return f"ERROR: Failed to delete playbook: {str(e)}"


@mcp.tool()
def ansible_list_playbooks() -> str:
    """List all available playbooks with descriptions."""
    playbooks = []
    
    if os.path.exists(PLAYBOOKS_DIR):
        for f in sorted(os.listdir(PLAYBOOKS_DIR)):
            if f.endswith((".yml", ".yaml")) and not f.endswith('.bak'):
                playbook_path = os.path.join(PLAYBOOKS_DIR, f)
                desc = ""
                try:
                    with open(playbook_path, "r") as pf:
                        first_line = pf.readline().strip()
                        if first_line.startswith("#"):
                            desc = first_line[1:].strip()
                except:
                    pass
                playbooks.append({"name": f, "description": desc})
    
    # Check root directory
    root_pb = os.path.join(ANSIBLE_DIR, "playbook.yml")
    if os.path.exists(root_pb):
        playbooks.append({"name": "playbook.yml (root)", "description": "Legacy root playbook"})
    
    if not playbooks:
        return f"No playbooks found in {PLAYBOOKS_DIR}\n\nUse ansible_create_playbook to create one."
    
    output = ["=== PLAYBOOKS ===\n"]
    for pb in playbooks:
        if pb["description"]:
            output.append(f"• {pb['name']}: {pb['description']}")
        else:
            output.append(f"• {pb['name']}")
    
    output.append(f"\nTotal: {len(playbooks)} playbook(s)")
    return "\n".join(output)


@mcp.tool()
def ansible_validate_playbook(playbook_name: str = "") -> str:
    """Validate playbook syntax without running it."""
    if not playbook_name:
        available = get_available_playbooks()
        if available:
            return "ERROR: No playbook specified. Available:\n- " + "\n- ".join(available)
        return "ERROR: No playbook specified."
    
    playbook_name = sanitize_input(playbook_name)
    if not playbook_name.endswith((".yml", ".yaml")):
        playbook_name += ".yml"
    
    playbook_path = os.path.join(PLAYBOOKS_DIR, playbook_name)
    if not os.path.exists(playbook_path):
        alt_path = os.path.join(ANSIBLE_DIR, playbook_name)
        if os.path.exists(alt_path):
            playbook_path = alt_path
        else:
            return f"ERROR: Playbook not found: {playbook_name}"
    
    cmd = ["ansible-playbook", "-i", INVENTORY_PATH, playbook_path, "--syntax-check"]
    raw_output = run_ansible_command(cmd, timeout=60)
    
    if "ERROR" not in raw_output.upper() or "playbook:" in raw_output.lower():
        return f"✓ Playbook '{playbook_name}' syntax is valid."
    
    return f"✗ Syntax errors in '{playbook_name}':\n{raw_output}"


# =============================================================================
# DEVICE INTERACTION TOOLS
# =============================================================================

@mcp.tool()
def ansible_adhoc_command(module_name: str = "", module_args: str = "", target_hosts: str = "all") -> str:
    """Run an ad-hoc Ansible command. Common modules: junos_command, junos_config, ping, raw."""
    if not module_name:
        return "ERROR: No module specified. Common modules: junipernetworks.junos.junos_command, junipernetworks.junos.junos_config, ping, raw"
    
    module_name = sanitize_input(module_name)
    target_hosts = sanitize_input(target_hosts) or "all"
    
    cmd = ["ansible", "-i", INVENTORY_PATH, target_hosts, "-m", module_name]
    
    if module_args:
        cmd.extend(["-a", module_args])
    
    return run_ansible_command(cmd)


@mcp.tool()
def ansible_ping_devices(target_hosts: str = "all") -> str:
    """Test connectivity to network devices using Ansible ping."""
    target_hosts = sanitize_input(target_hosts) or "all"
    cmd = ["ansible", "-i", INVENTORY_PATH, target_hosts, "-m", "ping"]
    raw_output = run_ansible_command(cmd, timeout=120)
    
    success_count = raw_output.count("SUCCESS")
    failed_count = raw_output.count("UNREACHABLE") + raw_output.count("FAILED")
    
    summary = f"=== CONNECTIVITY ===\n✓ Reachable: {success_count}\n✗ Failed: {failed_count}\n\n"
    return summary + raw_output


@mcp.tool()
def ansible_get_facts(target_hosts: str = "all", gather_subset: str = "") -> str:
    """Gather device facts. Use gather_subset to limit (e.g., hardware, config, interfaces)."""
    target_hosts = sanitize_input(target_hosts) or "all"
    
    module_args = ""
    if gather_subset:
        module_args = f"gather_subset={sanitize_input(gather_subset)}"
    
    cmd = ["ansible", "-i", INVENTORY_PATH, target_hosts, "-m", "junipernetworks.junos.junos_facts"]
    if module_args:
        cmd.extend(["-a", module_args])
    
    return run_ansible_command(cmd, timeout=180)


@mcp.tool()
def ansible_get_config(target_hosts: str = "all", config_format: str = "text") -> str:
    """Retrieve running configuration. Formats: text, set, json, xml."""
    target_hosts = sanitize_input(target_hosts) or "all"
    config_format = sanitize_input(config_format) or "text"
    
    if config_format not in ["text", "set", "json", "xml"]:
        return "ERROR: Invalid format. Use: text, set, json, xml"
    
    module_args = f"display={config_format}"
    cmd = ["ansible", "-i", INVENTORY_PATH, target_hosts, "-m", "junipernetworks.junos.junos_config", "-a", module_args]
    
    return run_ansible_command(cmd, timeout=180)


@mcp.tool()
def ansible_run_command(target_hosts: str = "all", commands: str = "") -> str:
    """Run operational commands on devices (e.g., show version). Separate multiple with comma."""
    if not commands:
        return "ERROR: No commands specified. Example: commands='show version' or 'show version,show interfaces'"
    
    target_hosts = sanitize_input(target_hosts) or "all"
    
    cmd_list = [c.strip() for c in commands.split(",")]
    cmd_json = json.dumps(cmd_list)
    
    module_args = f"commands={cmd_json}"
    cmd = ["ansible", "-i", INVENTORY_PATH, target_hosts, "-m", "junipernetworks.junos.junos_command", "-a", module_args]
    
    return run_ansible_command(cmd, timeout=180)


@mcp.tool()
def ansible_push_config(target_hosts: str = "", config_lines: str = "", config_format: str = "set", commit: str = "yes", check_mode: str = "no") -> str:
    """Push configuration to devices. config_format: set, text, json. Set commit=no for candidate only."""
    if not target_hosts:
        return "ERROR: No target hosts specified."
    if not config_lines:
        return "ERROR: No configuration provided."
    
    target_hosts = sanitize_input(target_hosts)
    config_format = sanitize_input(config_format) or "set"
    
    if config_format not in ["set", "text", "json"]:
        return "ERROR: Invalid format. Use: set, text, json"
    
    lines_list = [line.strip() for line in config_lines.split("\n") if line.strip()]
    lines_json = json.dumps(lines_list)
    
    commit_flag = "yes" if commit.lower() in ["yes", "true", "1"] else "no"
    module_args = f"lines={lines_json} update=merge commit={commit_flag}"
    
    cmd = ["ansible", "-i", INVENTORY_PATH, target_hosts, "-m", "junipernetworks.junos.junos_config", "-a", module_args]
    
    if check_mode.lower() in ["yes", "true", "1"]:
        cmd.append("--check")
        return "=== DRY RUN ===\n" + run_ansible_command(cmd, timeout=180)
    
    return run_ansible_command(cmd, timeout=180)


@mcp.tool()
def ansible_list_inventory(show_vars: str = "no") -> str:
    """List all hosts and groups in the inventory."""
    cmd = ["ansible-inventory", "-i", INVENTORY_PATH, "--list"]
    raw_output = run_ansible_command(cmd, timeout=60)
    
    if show_vars.lower() not in ["yes", "true", "1"]:
        try:
            if "=== OUTPUT ===" in raw_output:
                json_str = raw_output.split("=== OUTPUT ===")[1].split("=== STDERR ===")[0].strip()
            else:
                json_str = raw_output
            
            inv_data = json.loads(json_str)
            summary = ["=== INVENTORY ===\n"]
            
            if "_meta" in inv_data and "hostvars" in inv_data["_meta"]:
                hosts = list(inv_data["_meta"]["hostvars"].keys())
                summary.append(f"Total Hosts: {len(hosts)}")
                summary.append("Hosts: " + ", ".join(hosts))
            
            groups = [k for k in inv_data.keys() if k not in ["_meta", "all"]]
            if groups:
                summary.append(f"\nGroups ({len(groups)}):")
                for group in groups:
                    if "hosts" in inv_data.get(group, {}):
                        summary.append(f"  [{group}]: {', '.join(inv_data[group]['hosts'])}")
            
            return "\n".join(summary)
        except:
            pass
    
    return raw_output


@mcp.tool()
def ansible_show_host_vars(hostname: str = "") -> str:
    """Show all effective variables for a host (combines inventory, group_vars, host_vars)."""
    if not hostname:
        return "ERROR: No hostname specified."
    
    hostname = sanitize_input(hostname)
    cmd = ["ansible-inventory", "-i", INVENTORY_PATH, "--host", hostname]
    raw_output = run_ansible_command(cmd, timeout=60)
    
    try:
        if "=== OUTPUT ===" in raw_output:
            json_str = raw_output.split("=== OUTPUT ===")[1].split("=== STDERR ===")[0].strip()
        else:
            json_str = raw_output
        
        vars_data = json.loads(json_str)
        output = [f"=== EFFECTIVE VARIABLES: {hostname} ===\n"]
        
        # Mask passwords
        safe_vars = {}
        for key, value in vars_data.items():
            if "password" in key.lower() or "secret" in key.lower():
                safe_vars[key] = "********"
            else:
                safe_vars[key] = value
        
        output.append(json.dumps(safe_vars, indent=2))
        return "\n".join(output)
    except:
        return raw_output


# =============================================================================
# TEMPLATE MANAGEMENT
# =============================================================================

@mcp.tool()
def ansible_list_templates() -> str:
    """List all Jinja2 templates in the templates directory."""
    if not os.path.exists(TEMPLATES_DIR):
        return f"No templates directory found at {TEMPLATES_DIR}"
    
    templates = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(('.j2', '.jinja2'))]
    
    if not templates:
        return "No templates found.\n\nUse ansible_create_template to create one."
    
    output = ["=== TEMPLATES ===\n"]
    for t in sorted(templates):
        output.append(f"• {t}")
    
    return "\n".join(output)


@mcp.tool()
def ansible_read_template(template_name: str = "") -> str:
    """Read a Jinja2 template file."""
    if not template_name:
        return ansible_list_templates()
    
    template_name = sanitize_filename(template_name)
    if not template_name.endswith(('.j2', '.jinja2')):
        template_name += '.j2'
    
    filepath = os.path.join(TEMPLATES_DIR, template_name)
    
    if not os.path.exists(filepath):
        return f"ERROR: Template not found: {template_name}"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    return f"=== TEMPLATE: {template_name} ===\n\n{content}"


@mcp.tool()
def ansible_create_template(template_name: str = "", content: str = "") -> str:
    """Create a new Jinja2 template file."""
    if not template_name:
        return "ERROR: No template name specified."
    if not content:
        return "ERROR: No template content provided."
    
    template_name = sanitize_filename(template_name)
    if not template_name.endswith(('.j2', '.jinja2')):
        template_name += '.j2'
    
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    filepath = os.path.join(TEMPLATES_DIR, template_name)
    
    if os.path.exists(filepath):
        return f"ERROR: Template '{template_name}' already exists."
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return f"SUCCESS: Template '{template_name}' created."


if __name__ == "__main__":
    logger.info("Starting Ansible Network MCP Server...")
    logger.info(f"Ansible directory: {ANSIBLE_DIR}")
    logger.info(f"Inventory: {INVENTORY_PATH}")
    logger.info(f"Playbooks: {PLAYBOOKS_DIR}")
    mcp.run()
