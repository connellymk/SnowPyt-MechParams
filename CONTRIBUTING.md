# Contributing to SnowPyt-MechParams

Thank you for your interest in contributing to SnowPyt-MechParams! This document provides guidelines and information for contributors.

## Ways to Contribute

- **Bug Reports**: Report issues or unexpected behavior
- **Feature Requests**: Suggest new functionality or improvements
- **Documentation**: Improve or add to documentation
- **Code**: Fix bugs, add features, or improve performance
- **Testing**: Add test cases or improve test coverage
- **Examples**: Contribute usage examples or tutorials

## Getting Started

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/snowpyt-mechparams.git
   cd snowpyt-mechparams
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests**
   ```bash
   pytest                    # Run all tests
   pytest --cov             # Run with coverage
   black src/ tests/        # Format code
   flake8 src/ tests/       # Lint code
   mypy src/               # Type checking
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python Style
- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 88)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for function signatures

### Docstring Style
- Use [NumPy docstring format](https://numpydoc.readthedocs.io/en/latest/format.html)
- Include all parameters, returns, and examples
- Add scientific references where applicable

### Testing Guidelines

1. **Test Coverage**: Aim for >90% test coverage
2. **Test Types**:
   - Unit tests for individual functions
   - Integration tests for workflows
   - Property-based tests for edge cases
3. **Test Structure**:
   ```python
   def test_function_name():
       # Arrange
       input_data = create_test_data()
       
       # Act
       result = function_under_test(input_data)
       
       # Assert
       assert result == expected_value
   ```

4. **Fixtures**: Use pytest fixtures for reusable test data
5. **Parametrize**: Use `@pytest.mark.parametrize` for multiple test cases

## Scientific Contributions

### Adding New Empirical Relationships

When adding new scientific methods:

1. **Literature Review**: Ensure the method is peer-reviewed and validated
2. **Documentation**: Include full citation and brief description
3. **Testing**: Add tests with known values from literature
4. **Validation**: Compare against existing methods when possible

**Example Implementation:**
```python
def new_estimation_method(
    input_param: float,
    method: str = "author2024"
) -> float:
    """
    New estimation method description.
    
    References
    ----------
    Author, A., et al. (2024), Title of paper, Journal, vol(issue), pages.
    """
    if method == "author2024":
        # Implementation based on Author et al. (2024)
        result = empirical_formula(input_param)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return result
```

### Data Validation Standards

- Always validate input parameters
- Use physically reasonable bounds
- Provide clear error messages
- Handle edge cases gracefully

## Documentation

### API Documentation
- All public functions must have complete docstrings
- Include usage examples in docstrings
- Use proper cross-references

### Examples
- Create complete, runnable examples
- Include comments explaining key concepts
- Show typical workflows and use cases
- Generate meaningful plots when appropriate

## Pull Request Process

### Before Submitting
1. **Ensure tests pass**: All CI checks must pass
2. **Update documentation**: Add/update relevant docs
3. **Add changelog entry**: Describe your changes
4. **Check dependencies**: Minimize new dependencies

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Added new tests
- [ ] All tests pass
- [ ] Updated existing tests

## Documentation
- [ ] Updated docstrings
- [ ] Updated README
- [ ] Added examples

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No unnecessary dependencies added
```

### Review Process
1. **Automated Checks**: CI must pass
2. **Code Review**: At least one maintainer review
3. **Scientific Review**: For new methods, scientific validation
4. **Testing**: Reviewer may test functionality
5. **Documentation**: Check clarity and completeness

## Issue Guidelines

### Bug Reports
Include:
- Python version and operating system
- SnowPyt-MechParams version
- Minimal reproducible example
- Expected vs actual behavior
- Full error traceback

### Feature Requests
Include:
- Clear description of desired functionality
- Use case and motivation
- Proposed API design (if applicable)
- Scientific background/references

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Credit others' contributions

### Communication
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Requests**: Code contributions
- **Email**: Sensitive issues or direct contact

## Scientific Standards

### Peer Review
- All new empirical methods should be from peer-reviewed sources
- Prefer recent publications with validation data
- Include uncertainty estimates when available

### Units and Conventions
- Use SI units internally
- Provide unit conversion utilities
- Follow snow science naming conventions
- Use physically meaningful variable names

### Validation
- Compare new methods against established ones
- Use field data for validation when possible
- Document method limitations and uncertainty
- Provide guidance on method selection

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for each release
- README.md acknowledgments section
- Citation information for significant contributions
- Potential co-authorship on publications

## Questions?

- **GitHub Discussions**: General questions about contributing
- **Issues**: Specific bugs or feature requests
- **Email**: mary.connelly@example.com for direct contact

Thank you for contributing to advancing snow science through open source software!
