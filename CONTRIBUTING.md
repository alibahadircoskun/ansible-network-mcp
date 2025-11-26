# Contributing to Ansible Network MCP Server

Thank you for your interest in contributing to the Ansible Network MCP Server project.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check existing issues to avoid duplicates
2. Create a new issue with a clear title and description
3. Include steps to reproduce for bugs
4. Provide your environment details (OS, Python version, Ansible version)

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages (`git commit -m 'Add feature: description'`)
6. Push to your fork (`git push origin feature/your-feature-name`)
7. Open a Pull Request

### Code Guidelines

**Python Code Style**
- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

**Security**
- Never commit credentials or sensitive data
- Sanitize all user inputs
- Validate file paths to prevent traversal
- Use subprocess safely with proper escaping

**Testing**
- Test with real network devices in a lab environment
- Verify all tools work correctly
- Test error handling and edge cases
- Ensure backward compatibility

### Development Setup

1. Clone your fork:
```bash
git clone https://github.com/YOUR-USERNAME/ansible-network-mcp.git
cd ansible-network-mcp
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install mcp fastmcp ansible-core
ansible-galaxy collection install junipernetworks.junos
```

4. Set up test environment:
```bash
mkdir -p ~/ansible-test/{inventory,group_vars,host_vars,playbooks}
```

5. Test your changes:
```bash
ANSIBLE_DIR=~/ansible-test python server.py
```

### Adding New Tools

When adding new MCP tools:

1. Add the `@mcp.tool()` decorator
2. Use only simple string parameters (no typing imports)
3. Return strings only
4. Add clear docstrings
5. Sanitize all inputs
6. Update the README with the new tool

Example:
```python
@mcp.tool()
def ansible_new_feature(param1: str = "", param2: str = "") -> str:
    """Brief description of what this tool does."""
    if not param1:
        return "ERROR: param1 is required"
    
    # Sanitize inputs
    param1 = sanitize_input(param1)
    
    # Implementation
    try:
        result = perform_operation(param1)
        return f"SUCCESS: {result}"
    except Exception as e:
        return f"ERROR: {str(e)}"
```

### Adding Device Support

To add support for new network device types:

1. Install the Ansible collection
2. Add example group_vars configuration
3. Update README with device-specific instructions
4. Test with actual devices

### Documentation

When updating documentation:

- Keep language clear and concise
- Include code examples
- Update both README and inline comments
- Add troubleshooting tips for common issues

### Commit Messages

Write clear commit messages:

```
Add feature: brief description

Longer explanation of what changed and why.
Include any breaking changes or migration notes.
```

Examples:
- `Add support for Arista EOS devices`
- `Fix permission handling in ansible_write_file`
- `Update README with new installation steps`
- `Refactor inventory management tools`

### Review Process

1. All PRs require review before merging
2. Address review comments promptly
3. Keep PRs focused on a single feature or fix
4. Ensure CI checks pass (when implemented)

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a welcoming environment

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Ask in pull request comments
- Reach out to maintainers

Thank you for contributing to make network automation more accessible!
