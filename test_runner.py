#!/usr/bin/env python3
"""
Test runner script for Flora PAC
Provides a simple way to run tests without requiring make
"""

import sys
import subprocess
import os

def run_tests(verbose=False, coverage=False):
    """Run the test suite"""
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("pytest is not installed. Installing test dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-test.txt'])
        import pytest
    
    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
    
    # Run tests
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Flora PAC tests')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Run tests with verbose output')
    parser.add_argument('-c', '--coverage', action='store_true',
                       help='Run tests with coverage report')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install test dependencies only')
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("Installing test dependencies...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-test.txt'])
        return result.returncode
    
    return run_tests(verbose=args.verbose, coverage=args.coverage)

if __name__ == '__main__':
    sys.exit(main())