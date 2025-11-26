# Security Policy

## Supported Versions

Currently supported versions of the Ansible Network MCP Server:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Measures

The Ansible Network MCP Server implements several security measures:

### Path Restrictions
- All file operations are restricted to the Ansible directory
- Path traversal attacks are prevented through normalization checks
- Users cannot access files outside the designated workspace

### Input Sanitization
- All user inputs are sanitized before execution
- Command injection attempts are blocked
- Dangerous characters are filtered from inputs

### Credential Protection
- Passwords and secrets are masked in output
- Credentials should be stored in Ansible Vault (recommended)
- No credentials are logged or displayed in clear text

### File Operations
- Automatic backups are created before modifications
- Timestamped backups allow rollback if needed
- File permissions are preserved during operations

### Process Execution
- Commands are executed with limited privileges
- Subprocess calls use safe parameter passing
- No shell interpretation of user inputs

## Best Practices

When using the Ansible Network MCP Server:

1. **Use Ansible Vault** for storing credentials
2. **Restrict file permissions** on the Ansible directory
3. **Run under a dedicated user account** with limited privileges
4. **Review playbooks** before execution in production
5. **Use check mode** to validate changes before applying
6. **Keep backups** of critical configurations
7. **Monitor logs** for suspicious activity
8. **Update regularly** to get security fixes

## Reporting a Vulnerability

If you discover a security vulnerability in the Ansible Network MCP Server:

1. **Do not** open a public GitHub issue
2. Email the maintainers directly with details
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to:
- Verify the vulnerability
- Develop a fix
- Release a security update
- Credit you (if desired) in the advisory

## Security Updates

Security updates will be released as soon as possible after verification. Users will be notified through:
- GitHub Security Advisories
- Release notes
- CHANGELOG.md updates

## Responsible Disclosure

We follow responsible disclosure practices:
- Vulnerabilities are fixed before public disclosure
- Security advisories are published with fixes
- Contributors are credited (unless they prefer anonymity)

## Third-Party Dependencies

The server relies on:
- **Python standard library** - security updates via system packages
- **mcp and fastmcp** - maintained by Anthropic
- **ansible-core** - maintained by Ansible community

Keep these dependencies updated to receive security fixes.

## Audit Log

No security vulnerabilities have been reported to date.

## Questions?

For security questions or concerns that are not vulnerabilities, please open a GitHub issue or discussion.

Thank you for helping keep the Ansible Network MCP Server secure.
