# Contributing to Orthodoxy

Thank you for your interest in contributing to Orthodoxy! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Development Process

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature-name
   ```

2. Make your changes, following these guidelines:
   - Follow PEP 8 style guidelines
   - Add tests for new functionality
   - Update documentation as needed
   - Keep commits focused and write clear commit messages

3. Run tests to ensure everything works:
   ```bash
   pytest
   ```

4. Push your changes and create a pull request

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation in the `docs/` directory if needed
3. Ensure all tests pass and the code follows the project's style guidelines
4. The PR will be reviewed by maintainers who may request changes
5. Once approved, your PR will be merged

## Testing

- Write tests for all new functionality
- Place tests in the `tests/` directory
- Ensure tests are descriptive and cover edge cases
- Run the full test suite before submitting changes

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Comment complex logic when necessary

## Documentation

- Update documentation for any changed functionality
- Include docstrings for new functions and classes
- Update schema files in `docs/schemas/` if making changes to data structures
- Keep documentation clear and concise

## Questions or Problems?

- Check existing issues before creating a new one
- Provide clear descriptions when creating issues
- Include steps to reproduce for bug reports
- Tag issues appropriately

## License

By contributing to Orthodoxy, you agree that your contributions will be licensed under the project's license.
