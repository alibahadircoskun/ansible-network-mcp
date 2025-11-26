# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-21

### Added
- Initial release of Ansible Network MCP Server
- 30+ tools for Ansible automation through Claude Desktop
- Directory and file management tools
- Inventory management (read, write, add/remove hosts)
- Variables management (group_vars and host_vars)
- Configuration file management (ansible.cfg)
- Playbook operations (create, read, edit, delete, validate, run, check)
- Device interaction tools (ping, facts, config, commands, push)
- Template management (Jinja2)
- Automatic file backups before modifications
- Input sanitization for security
- Password masking in output
- Support for Juniper JunOS devices
- Support for Cisco IOS devices
- Support for Arista EOS devices
- Comprehensive documentation
- Example configurations and playbooks
- Installation script
- MIT License

### Security
- Path restrictions to prevent directory traversal
- Input sanitization to prevent command injection
- Automatic backups before file modifications
- Password masking in tool outputs

## [Unreleased]

### Planned
- Role management tools
- Ansible Vault integration
- Git integration for playbook versioning
- Enhanced error reporting
- Multi-inventory support
- Playbook templates library
- Integration with network monitoring tools
- Configuration compliance checking
- Automated testing framework
