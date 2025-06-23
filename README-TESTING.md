# Flora PAC Testing Guide

This document describes the testing setup for the Flora PAC project.

## Test Structure

The test suite includes:

- **test_simple.py**: Basic import and functionality tests
- **test_basic_functionality.py**: Core algorithm tests without external dependencies
- **test_ip_data.py**: Tests for IP data fetching and parsing (requires responses mock)
- **test_network_ops.py**: Tests for network operations and hashing
- **test_pac_generation.py**: Tests for PAC file generation
- **test_integration.py**: End-to-end integration tests

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip3 install -r requirements-test.txt

# Run basic tests (fastest)
python3 -m pytest tests/test_simple.py tests/test_basic_functionality.py -v

# Run all tests
python3 -m pytest tests/ -v
```

### Using Test Runner

```bash
# Install dependencies and run tests
./test_runner.py

# Run with verbose output
./test_runner.py -v

# Run with coverage
./test_runner.py -c
```

### Using Makefile

```bash
# Install dependencies
make install-deps

# Run tests
make test

# Run with verbose output
make test-verbose

# Run with coverage
make test-coverage
```

## Test Dependencies

- `pytest`: Test framework
- `pytest-mock`: Mocking utilities
- `responses`: HTTP request mocking
- `urllib3`: HTTP library (already required by main project)

## Notes

- Some tests use mocking to avoid network calls to APNIC
- Basic functionality tests run without external dependencies
- Integration tests may take longer due to subprocess calls
- Coverage reports are generated in `htmlcov/` directory

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention (`test_*.py`)
2. Use descriptive test names that explain the functionality being tested
3. Group related tests in classes
4. Mock external dependencies when possible
5. Include both positive and negative test cases