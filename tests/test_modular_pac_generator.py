"""
Tests for the modular pac_generator module
"""
import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
import ipaddress
import sys

# Add parent directory to path to import flora_pac_lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flora_pac_lib.pac_generator import (
    generate_balanced_proxy, generate_no_proxy, generate_pac,
    _generate_pac_content, _print_generation_stats
)


class TestModularPACGenerator:
    """Test modular PAC generator functionality"""
    
    def test_generate_balanced_proxy_modular_empty_proxies(self):
        """Test proxy generation with empty proxy list"""
        result = generate_balanced_proxy([], 'no')
        assert result == "return '' ;"
    
    def test_generate_balanced_proxy_modular_single_proxy(self):
        """Test proxy generation with single proxy"""
        proxies = ['SOCKS5 127.0.0.1:1984']
        result = generate_balanced_proxy(proxies, 'no')
        assert result == "return 'SOCKS5 127.0.0.1:1984' ;"
    
    def test_generate_balanced_proxy_modular_multiple_proxies(self):
        """Test proxy generation with multiple proxies"""
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989', 'PROXY 127.0.0.1:8080']
        result = generate_balanced_proxy(proxies, 'no')
        expected = "return 'SOCKS5 127.0.0.1:1984;SOCKS5 127.0.0.1:1989;PROXY 127.0.0.1:8080' ;"
        assert result == expected
    
    def test_generate_balanced_proxy_modular_local_ip_detailed(self):
        """Test local IP balancing with detailed checks"""
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
        result = generate_balanced_proxy(proxies, 'local_ip')
        
        # Check for specific JavaScript patterns
        assert 'local_ip_balance = function(proxies)' in result
        assert 'myseg = parseInt(myIpAddress().split(".")[3])' in result
        assert 'k = myseg % l' in result
        assert "'SOCKS5 127.0.0.1:1984'" in result
        assert "'SOCKS5 127.0.0.1:1989'" in result
        assert 'return local_ip_balance([' in result
    
    def test_generate_balanced_proxy_modular_host_detailed(self):
        """Test host balancing with detailed checks"""
        proxies = ['SOCKS5 127.0.0.1:1984']
        result = generate_balanced_proxy(proxies, 'host')
        
        # Check for specific JavaScript patterns
        assert 'target_host_balance = function(proxies, host)' in result
        assert 'hash_string = function(s)' in result
        assert 'c.charCodeAt(0)' in result
        assert 'hash_string(host) % l' in result
        assert 'return target_host_balance([' in result
    
    def test_generate_no_proxy_modular_mixed_detailed(self):
        """Test no-proxy generation with mixed types and edge cases"""
        no_proxy = [
            '127.0.0.1',           # Single IP
            '192.168.0.0/16',      # Large network
            '10.0.0.0/8',          # Very large network
            'localhost',           # Hostname
            'example.com',         # Domain
            '*.google.com'         # Wildcard (treated as hostname)
        ]
        
        result = generate_no_proxy(no_proxy)
        
        # Check IP addresses
        assert "ip == '127.0.0.1'" in result
        
        # Check networks with proper subnet masks
        assert "isInNet(ip, '192.168.0.0', '255.255.0.0')" in result
        assert "isInNet(ip, '10.0.0.0', '255.0.0.0')" in result
        
        # Check hostnames
        assert "host == 'localhost'" in result
        assert "host == 'example.com'" in result
        assert "host == '*.google.com'" in result
        
        # Should have 6 OR conditions
        assert result.count(" ||") == 6
    
    def test_generate_no_proxy_modular_invalid_entries(self):
        """Test no-proxy generation with invalid IP/network entries"""
        no_proxy = [
            '999.999.999.999',     # Invalid IP (treated as hostname)
            '192.168.0.0/99',      # Invalid CIDR (treated as hostname)
            'not-an-ip',           # Obviously not an IP
        ]
        
        result = generate_no_proxy(no_proxy)
        
        # All should be treated as hostnames
        assert "host == '999.999.999.999'" in result
        assert "host == '192.168.0.0/99'" in result
        assert "host == 'not-an-ip'" in result
        assert result.count(" ||") == 3
    
    @patch('flora_pac_lib.pac_generator.fetch_ip_data')
    @patch('flora_pac_lib.pac_generator.merge_all')
    @patch('flora_pac_lib.pac_generator.fregment_nets')
    @patch('flora_pac_lib.pac_generator.hash_nets')
    def test_generate_pac_modular_custom_parameters(self, mock_hash_nets, mock_fregment, 
                                                   mock_merge, mock_fetch):
        """Test PAC generation with custom parameters"""
        # Mock the data pipeline
        mock_networks = [
            ipaddress.ip_network('192.168.0.0/24'),
            ipaddress.ip_network('10.0.0.0/22')
        ]
        mock_fetch.return_value = mock_networks
        mock_merge.return_value = mock_networks
        mock_fregment.return_value = mock_networks
        
        # Mock hash result with custom size
        custom_hash_base = 5003
        mock_hash_result = [[] for _ in range(custom_hash_base)]
        mock_hash_result[0] = mock_networks[:1]
        mock_hash_result[1] = mock_networks[1:]
        mock_hash_nets.return_value = mock_hash_result
        
        # Use temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pac', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
            balance = 'host'
            no_proxy = ['10.0.0.0/8', 'localhost']
            
            generate_pac(proxies, balance, no_proxy, 
                        hash_base=custom_hash_base, mask_step=3, 
                        output_file=tmp_path)
            
            # Verify file was created and contains expected content
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
            
            # Check custom parameters
            assert f'HASH_BASE = {custom_hash_base}' in content
            assert 'MASK_STEP = 3' in content
            
            # Check host balancing
            assert 'target_host_balance' in content
            
            # Check no-proxy rules
            assert "isInNet(ip, '10.0.0.0', '255.0.0.0')" in content
            assert "host == 'localhost'" in content
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_generate_pac_content_modular_structure(self):
        """Test the internal _generate_pac_content function"""
        # Create test data
        networks = [ipaddress.ip_network('192.168.0.0/24')]
        hashed_results = [[] for _ in range(100)]
        hashed_results[0] = networks
        
        proxies = ['SOCKS5 127.0.0.1:1984']
        balance = 'no'
        no_proxy = ['192.168.0.0/24']
        
        content = _generate_pac_content(
            hashed_results, proxies, balance, no_proxy,
            hash_base=100, mask_step=2, 
            min_prefixlen=24, max_prefixlen=24, results=networks
        )
        
        # Check PAC structure
        assert 'function FindProxyForURL(url, host)' in content
        assert 'dot2num = function(dot)' in content
        assert 'lookup_ip = function(ip)' in content
        assert 'HASH_BASE = 100' in content
        assert 'MASK_STEP = 2' in content
        assert 'min_prefixlen = 24' in content
        assert 'max_prefixlen = 24' in content
        
        # Check network data
        assert 'var m24 = 24' in content
        assert 'hashed_nets = [' in content
        
        # Check proxy and no-proxy logic
        assert "return 'SOCKS5 127.0.0.1:1984'" in content
        assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in content
    
    @patch('builtins.print')
    def test_print_generation_stats_modular(self, mock_print):
        """Test the statistics printing function"""
        # Create test data
        networks = [ipaddress.ip_network('192.168.0.0/24')]
        hashed_results = [[] for _ in range(100)]
        hashed_results[0] = networks
        hashed_results[1] = networks
        
        _print_generation_stats(hashed_results, networks, 24, 24, 2, 'test.pac')
        
        # Verify print was called with expected statistics
        assert mock_print.call_count >= 5
        
        # Check some of the printed content
        printed_content = [str(call) for call in mock_print.call_args_list]
        assert any('Average matching length' in content for content in printed_content)
        assert any('Steps to match' in content for content in printed_content)
        assert any('Rules: 1 items' in content for content in printed_content)
        assert any('test.pac' in content for content in printed_content)