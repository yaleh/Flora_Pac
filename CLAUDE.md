# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flora PAC is a Python-based PAC (Proxy Auto-Config) file generator that fetches China IP ranges and creates optimized proxy configuration files. The project helps users bypass GFW by automatically routing Chinese IPs direct while sending other traffic through proxies.

**Key optimization**: Yale Huang's fork is performance-optimized, matching ~100x faster than original with files compressed to <50KB using UglifyJS.

## Architecture

### Modular Structure (Refactored)
- **flora_pac**: Main executable script (single entry point)
- **flora_pac_lib/**: Core package containing modular components
  - **ip_data.py**: IP data fetching and network merging logic
  - **network_ops.py**: Network fragmentation and hashing operations
  - **pac_generator.py**: PAC file generation and JavaScript templating
- **tests/**: Comprehensive test suite for all components
- **flora_pac_legacy.py**: Original monolithic implementation (archived)

### Generated Files
- **flora_pac.pac**: Generated JavaScript PAC file for browsers
- **flora_pac.min.pac**: Minified version of the PAC file
- **hash_ip.coffee**: CoffeeScript test/development file with PAC logic prototypes

### Core Algorithm
1. Fetches IP ranges from APNIC for Chinese networks
2. Fragments networks into consistent mask steps (configurable via MASK_STEP)
3. Uses hash table approach for fast IP lookups (HASH_BASE = 3011)
4. Generates JavaScript PAC file with embedded hash tables and lookup functions

## Common Commands

### Generate PAC file

```bash
# Basic usage with single proxy
./flora_pac -x "SOCKS5 127.0.0.1:1984"

# Multiple proxies with load balancing
./flora_pac -b local_ip -x "SOCKS5 127.0.0.1:1984" "SOCKS5 127.0.0.1:1989"

# With no-proxy networks and custom output
./flora_pac -x "SOCKS5 127.0.0.1:1984" -n "192.168.0.0/24" "10.0.0.0/8" -o custom.pac

# Advanced configuration with performance tuning
./flora_pac -x "SOCKS5 127.0.0.1:1984" -s 5003 -m 1 -o optimized.pac

# Host-based proxy balancing
./flora_pac -b host -x "SOCKS5 127.0.0.1:1984" "SOCKS5 127.0.0.1:1989"

# Display help and examples
./flora_pac --help
```

### Performance tuning
```bash
# Adjust hash table size (larger = faster matching, bigger file)
./flora_pac -s 5003 -x "SOCKS5 127.0.0.1:1984"

# Adjust mask step (smaller = more precise, slower)
./flora_pac -m 1 -x "SOCKS5 127.0.0.1:1984"

# Combined optimization
./flora_pac -s 7001 -m 1 -x "SOCKS5 127.0.0.1:1984" -o optimized.pac
```

### Minify generated PAC
```bash
uglifyjs -m --lint -c -o flora_pac.min.pac flora_pac.pac
```

### Test CoffeeScript prototype
```bash
coffee hash_ip.coffee
```

## Key Parameters

- **HASH_BASE**: Hash table size (default 3011) - tune for performance vs size
- **MASK_STEP**: Network mask fragmentation step (default 2) - affects precision/speed
- **Balance modes**: 'no', 'local_ip', 'host' for proxy load balancing
- **No-proxy**: Networks/IPs to bypass proxy (supports CIDR notation)

## Browser Compatibility

For maximum compatibility across browsers and OSes, use combined SOCKS format:
```bash
./flora_pac -x "SOCKS5 127.0.0.1:1984; SOCKS 127.0.0.1:1984"
```

## Testing

### Run tests
```bash
# Using pytest directly
python3 -m pytest

# Using test runner script
./test_runner.py

# Using Makefile
make test
make test-verbose
make test-coverage

# Install test dependencies
make install-deps
# or
./test_runner.py --install-deps
```

### Test structure
#### Legacy Tests (Updated for Modular Components)
- `tests/test_ip_data.py`: Tests for IP data fetching and network merging
- `tests/test_network_ops.py`: Tests for network fragmentation and hashing algorithms  
- `tests/test_pac_generation.py`: Tests for PAC file generation and proxy balancing
- `tests/test_integration.py`: End-to-end integration tests

#### Modular Component Tests
- `tests/test_modular_ip_data.py`: Enhanced tests for ip_data module
- `tests/test_modular_network_ops.py`: Enhanced tests for network_ops module
- `tests/test_modular_pac_generator.py`: Enhanced tests for pac_generator module
- `tests/test_integration_modular.py`: Integration tests for modular architecture

## Development Notes

### Modular Architecture Benefits
- **Single Entry Point**: One unified `flora_pac` script with all features
- **Separation of Concerns**: Each module handles a specific aspect (IP data, network ops, PAC generation)
- **Testability**: Individual components can be tested in isolation with comprehensive test coverage
- **Maintainability**: Code is easier to understand, modify, and extend
- **Reusability**: Modules can be imported and used independently in other projects
- **Enhanced CLI**: Improved help, examples, version info, and error handling

### Implementation Details
- The hash_ip.coffee file contains test stubs and can be run standalone for development
- PAC file generation involves network merging optimization to reduce file size
- IP lookup uses multi-step hashing for O(1) average case performance
- Generated PAC files include embedded JavaScript for IP range matching
- Modular components use type hints and comprehensive documentation