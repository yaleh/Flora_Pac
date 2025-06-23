import pytest
import sys
import os

# Add parent directory to path to import flora_pac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flora_pac


def test_simple_import():
    """Test that flora_pac can be imported"""
    assert hasattr(flora_pac, 'generate_pac')
    assert hasattr(flora_pac, 'fetch_ip_data')
    assert hasattr(flora_pac, 'merge_nets')


def test_hash_address():
    """Test hash_address function with simple inputs"""
    # Create a simple IP address
    import ipaddress
    addr = ipaddress.ip_address('192.168.1.1')
    
    result = flora_pac.hash_address(addr, 100)
    
    assert isinstance(result, int)
    assert 0 <= result < 100


def test_generate_balanced_proxy_simple():
    """Test basic proxy generation"""
    result = flora_pac.generate_balanced_proxy(['SOCKS5 127.0.0.1:1984'], 'no')
    
    expected = "return 'SOCKS5 127.0.0.1:1984' ;"
    assert result == expected


def test_generate_no_proxy_simple():
    """Test basic no-proxy generation"""
    result = flora_pac.generate_no_proxy(['192.168.1.1'])
    
    expected = " ip == '192.168.1.1' ||"
    assert result == expected