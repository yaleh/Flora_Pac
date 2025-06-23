# Flora PAC Makefile

.PHONY: test test-verbose test-coverage install-deps clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  install-deps   - Install test dependencies"
	@echo "  clean          - Clean up test artifacts"
	@echo "  help           - Show this help message"

# Install test dependencies
install-deps:
	pip3 install -r requirements-test.txt

# Run tests
test:
	python3 -m pytest

# Run tests with verbose output
test-verbose:
	python3 -m pytest -v

# Run tests with coverage
test-coverage:
	python3 -m pytest --cov=. --cov-report=html --cov-report=term

# Clean up test artifacts
clean:
	rm -rf __pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f flora_pac.pac
	rm -f flora_pac.min.pac