# 🤝 Contributing to ServMC

Thank you for your interest in contributing to ServMC! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [🌟 Ways to Contribute](#ways-to-contribute)
- [🚀 Getting Started](#getting-started)
- [💻 Development Setup](#development-setup)
- [📝 Coding Standards](#coding-standards)
- [🧪 Testing](#testing)
- [📚 Documentation](#documentation)
- [🐛 Bug Reports](#bug-reports)
- [💡 Feature Requests](#feature-requests)
- [🔄 Pull Request Process](#pull-request-process)
- [👥 Community](#community)

## 🌟 Ways to Contribute

There are many ways you can contribute to ServMC:

### 🔧 Code Contributions
- **Bug fixes**: Help resolve issues and improve stability
- **New features**: Add functionality that benefits the community
- **Performance improvements**: Optimize existing code
- **Platform support**: Improve Linux/macOS compatibility

### 📚 Documentation
- **User guides**: Write tutorials and how-to guides
- **Code documentation**: Improve inline documentation
- **API documentation**: Document API endpoints and usage
- **Translations**: Help translate the interface

### 🎨 Design & UX
- **UI improvements**: Enhance the user interface
- **UX research**: Conduct usability studies
- **Icon design**: Create icons and graphics
- **Accessibility**: Improve accessibility features

### 🧪 Testing & Quality Assurance
- **Manual testing**: Test new features and report bugs
- **Automated testing**: Write unit and integration tests
- **Performance testing**: Test resource usage and optimization
- **Cross-platform testing**: Test on different operating systems

### 💬 Community Support
- **Answer questions**: Help users in discussions and issues
- **Moderate discussions**: Help maintain a positive community
- **Create tutorials**: Share knowledge through blog posts or videos

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **Git** for version control
- **Java 8+** for testing Minecraft servers
- **Code editor** (VS Code, PyCharm, etc.)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ServMC.git
   cd ServMC
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-owner/ServMC.git
   ```

## 💻 Development Setup

### Environment Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Project Structure

```
ServMC/
├── servmc/              # Main application code
│   ├── gui/            # GUI components
│   ├── server.py       # Server management
│   ├── mod_manager.py  # Mod and modpack handling
│   ├── config.py       # Configuration management
│   └── web_interface.py # Web interface
├── tests/              # Test files
├── docs/               # Documentation
├── assets/             # Images, icons, etc.
├── requirements.txt    # Production dependencies
├── requirements-dev.txt # Development dependencies
└── launch.py           # Application entry point
```

### Running the Application

```bash
# Run the desktop application
python launch.py

# Run with development settings
python launch.py --debug

# Run web interface only
python -m servmc.web_interface --debug
```

## 📝 Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces
- **String quotes**: Use double quotes `"` for strings
- **Imports**: Group imports (standard library, third-party, local)

### Code Formatting

We use automated code formatting tools:

```bash
# Format code with black
black servmc/ tests/

# Sort imports with isort
isort servmc/ tests/

# Check code style with flake8
flake8 servmc/ tests/
```

### Type Hints

Use type hints for function parameters and return values:

```python
from typing import Dict, List, Optional

def create_server(name: str, server_type: str, version: str) -> bool:
    """Create a new Minecraft server."""
    pass

def get_servers() -> List[Dict[str, str]]:
    """Get list of all servers."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def install_modpack(modpack_id: str, server_name: str) -> bool:
    """Install a modpack to a server.
    
    Args:
        modpack_id: The Modrinth modpack ID
        server_name: Name of the target server
        
    Returns:
        True if installation was successful, False otherwise
        
    Raises:
        ValueError: If modpack_id is invalid
        FileNotFoundError: If server doesn't exist
    """
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=servmc

# Run specific test file
python -m pytest tests/test_server_creation.py

# Run tests with verbose output
python -m pytest -v
```

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Follow the AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

Example test:

```python
import pytest
from unittest.mock import Mock, patch
from servmc.mod_manager import ModManager

def test_install_modpack_success():
    # Arrange
    config = Mock()
    mod_manager = ModManager(config)
    
    # Act
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"files": []}
        
        result = mod_manager.install_modpack("test-pack", "test-server")
    
    # Assert
    assert result is True
    mock_get.assert_called()
```

### Test Categories

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete user workflows
- **Performance tests**: Test resource usage and speed

## 📚 Documentation

### Code Documentation

- **Document all public APIs**: Functions, classes, and methods
- **Use clear examples**: Show how to use the code
- **Keep it updated**: Update docs when code changes
- **Include type information**: Document parameter and return types

### User Documentation

- **Tutorial style**: Step-by-step guides for common tasks
- **Reference material**: Complete API documentation
- **Troubleshooting**: Common problems and solutions
- **Screenshots**: Visual guides where helpful

### Documentation Tools

- **Docstrings**: For code documentation
- **Markdown**: For user guides and README files
- **Sphinx**: For API documentation generation
- **MkDocs**: For comprehensive documentation sites

## 🐛 Bug Reports

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to ensure it's not already fixed
3. **Gather information** about your environment
4. **Create minimal reproduction** if possible

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Windows 10, Ubuntu 20.04]
- Python version: [e.g. 3.9.7]
- ServMC version: [e.g. 3.0.0]
- Java version: [e.g. OpenJDK 17]

**Additional Context**
Any other context about the problem.
```

## 💡 Feature Requests

### Before Requesting

1. **Check existing discussions** for similar requests
2. **Consider the scope** and impact of the feature
3. **Think about implementation** challenges
4. **Provide use cases** and examples

### Feature Request Template

```markdown
**Feature Description**
A clear description of what you want to happen.

**Problem/Use Case**
What problem does this solve? What's the use case?

**Proposed Solution**
How would you like this feature to work?

**Alternatives Considered**
Alternative solutions you've considered.

**Additional Context**
Screenshots, mockups, or examples.
```

## 🔄 Pull Request Process

### Before Creating a PR

1. **Create an issue** to discuss the change
2. **Fork and create branch** from `main`
3. **Follow coding standards** and write tests
4. **Update documentation** as needed
5. **Test your changes** thoroughly

### PR Guidelines

1. **Clear title**: Summarize the change in the title
2. **Detailed description**: Explain what and why
3. **Link issues**: Reference related issues
4. **Small changes**: Keep PRs focused and manageable
5. **Clean history**: Use meaningful commit messages

### PR Template

```markdown
**Description**
Brief description of changes.

**Related Issue**
Fixes #123

**Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

**Testing**
- [ ] Tests pass
- [ ] New tests added
- [ ] Manual testing completed

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated checks** must pass (tests, linting)
2. **Code review** by maintainers
3. **Discussion and feedback** incorporated
4. **Final approval** and merge

## 👥 Community

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time community chat
- **Email**: For sensitive matters

### Getting Help

- **Documentation**: Check the wiki and README first
- **Search issues**: Look for existing solutions
- **Ask questions**: Use discussions for help
- **Be patient**: Maintainers are volunteers

### Recognition

Contributors are recognized in:
- **README.md**: Featured contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributors graph
- **Discord**: Special contributor roles

## 🎯 Priority Areas

We especially need help with:

1. **🌐 Internationalization**: Translating the interface
2. **🧪 Testing**: Writing tests and manual testing
3. **📱 Mobile Support**: Improving the web interface
4. **🔧 Platform Support**: Linux and macOS improvements
5. **📚 Documentation**: User guides and tutorials
6. **🎨 UI/UX**: Design improvements and accessibility

## 📞 Contact

- **Project Lead**: [@maintainer](https://github.com/maintainer)
- **Discord**: [ServMC Community](https://discord.gg/servmc)
- **Email**: contribute@servmc.org

---

**Thank you for contributing to ServMC! 🎉**

Your contributions help make Minecraft server management better for everyone. 