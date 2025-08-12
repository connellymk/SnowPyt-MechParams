# Contributing to SnowPyt-MechParams

Thank you for your interest in contributing to SnowPyt-MechParams! This collaborative project brings together academic researchers from multiple institutions to advance snow science through open source software development. This document provides guidelines and information for all contributors, with special emphasis on academic collaboration.

## Ways to Contribute

### Academic Contributions
- **Empirical Methods**: Contribute new scientifically-validated estimation methods
- **Research Data**: Provide validation datasets from field studies
- **Scientific Review**: Peer review of new methods and implementations
- **Publications**: Collaborate on academic papers featuring the library

### Technical Contributions  
- **Bug Reports**: Report issues or unexpected behavior
- **Feature Requests**: Suggest new functionality or improvements
- **Documentation**: Improve or add to documentation
- **Code**: Fix bugs, add features, or improve performance
- **Testing**: Add test cases or improve test coverage
- **Examples**: Contribute usage examples or tutorials

## Getting Started

### For Academic Collaborators

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

1. **Documentation**: Include full citation and brief description
2. **Testing**: Add tests with known values from literature
3. **Validation**: Compare against existing methods when possible

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
3. **Scientific Review**: For new methods, peer review by domain experts
4. **Academic Validation**: External validation by collaborating researchers when appropriate
5. **Testing**: Reviewer may test functionality
6. **Documentation**: Check clarity and completeness

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


### Academic Attribution
- Properly cite all source publications
- Acknowledge data contributors and method developers
- Consider co-authorship opportunities for significant contributions
- Maintain transparent attribution in code comments and documentation

### Units and Conventions
- Use SI units internally
- Provide unit conversion utilities
- Follow snow science naming conventions
- Use physically meaningful variable names

### Validation and Quality Assurance
- Compare new methods against established ones
- Use field data for validation when possible
- Document method limitations and uncertainty
- Provide guidance on method selection
- Encourage multi-institutional validation studies

## Recognition and Academic Credit

### Contributor Recognition
Contributors will be recognized in:
- CHANGELOG.md for each release
- README.md contributors section
- Method documentation with proper attribution
- Citation information for significant contributions

## Questions?

- **GitHub Discussions**: General questions about contributing and academic collaboration
- **Issues**: Specific bugs or feature requests
- **Email**: connellymarykate@gmail.com for direct contact

## Academic Collaboration Framework

### Institutional Partnerships
We welcome formal partnerships with academic institutions. These may include:
- Shared research objectives and funding opportunities
- Student researcher participation and mentorship
- Access to specialized datasets and field sites
- Joint publication and presentation opportunities

### Research Integration
Contributors can integrate their research with the library through:
- Implementation of novel empirical relationships from their work
- Validation studies using institutional datasets
- Case studies demonstrating library applications
- Collaborative development of new features addressing research needs

Thank you for contributing to advancing snow science through collaborative open source software development!
