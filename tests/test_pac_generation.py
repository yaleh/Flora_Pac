import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
import ipaddress
import sys

# Add parent directory to path to import flora_pac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flora_pac
generate_balanced_proxy = flora_pac.generate_balanced_proxy
generate_no_proxy = flora_pac.generate_no_proxy
generate_pac = flora_pac.generate_pac


class TestProxyBalancing:
    """Test proxy balancing strategy generation"""
    
    def test_generate_balanced_proxy_no_balancing(self):
        """Test proxy generation with no balancing"""
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
        
        result = generate_balanced_proxy(proxies, 'no')
        
        expected = "return 'SOCKS5 127.0.0.1:1984;SOCKS5 127.0.0.1:1989' ;"
        assert result == expected
    
    def test_generate_balanced_proxy_single_proxy(self):
        """Test proxy generation with single proxy"""
        proxies = ['SOCKS5 127.0.0.1:1984']
        
        result = generate_balanced_proxy(proxies, 'no')
        
        expected = "return 'SOCKS5 127.0.0.1:1984' ;"
        assert result == expected
    
    def test_generate_balanced_proxy_local_ip(self):
        """Test proxy generation with local IP balancing"""
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
        
        result = generate_balanced_proxy(proxies, 'local_ip')
        
        # Should contain local IP balancing function
        assert 'local_ip_balance' in result
        assert 'myIpAddress()' in result
        assert 'myseg = parseInt' in result
        assert "'SOCKS5 127.0.0.1:1984'" in result
        assert "'SOCKS5 127.0.0.1:1989'" in result
    
    def test_generate_balanced_proxy_host_balancing(self):
        """Test proxy generation with host-based balancing"""
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
        
        result = generate_balanced_proxy(proxies, 'host')
        
        # Should contain host balancing function
        assert 'target_host_balance' in result
        assert 'hash_string' in result
        assert 'charCodeAt' in result
        assert "'SOCKS5 127.0.0.1:1984'" in result
        assert "'SOCKS5 127.0.0.1:1989'" in result
    
    def test_generate_balanced_proxy_empty_proxies(self):
        """Test proxy generation with empty proxy list"""
        result = generate_balanced_proxy([], 'no')
        
        expected = "return '' ;"
        assert result == expected


class TestNoProxyGeneration:
    """Test no-proxy configuration generation"""
    
    def test_generate_no_proxy_single_ip(self):
        """Test no-proxy generation with single IP"""
        no_proxy = ['192.168.1.1']
        
        result = generate_no_proxy(no_proxy)
        
        expected = " ip == '192.168.1.1' ||"
        assert result == expected
    
    def test_generate_no_proxy_network_cidr(self):
        """Test no-proxy generation with CIDR network"""
        no_proxy = ['192.168.0.0/24']
        
        result = generate_no_proxy(no_proxy)
        
        # Should generate isInNet call
        assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in result
        assert result.endswith(" ||")
    
    def test_generate_no_proxy_network_with_mask(self):
        """Test no-proxy generation with network and mask"""
        no_proxy = ['10.0.0.0/8']
        
        result = generate_no_proxy(no_proxy)
        
        # Should generate isInNet call for /8 network
        assert "isInNet(ip, '10.0.0.0', '255.0.0.0')" in result
        assert result.endswith(" ||")
    
    def test_generate_no_proxy_hostname(self):
        """Test no-proxy generation with hostname"""
        no_proxy = ['example.com']
        
        result = generate_no_proxy(no_proxy)
        
        expected = " host == 'example.com' ||"
        assert result == expected
    
    def test_generate_no_proxy_mixed(self):
        """Test no-proxy generation with mixed types"""
        no_proxy = ['192.168.1.1', '10.0.0.0/8', 'localhost']
        
        result = generate_no_proxy(no_proxy)
        
        # Should contain all three types
        assert "ip == '192.168.1.1'" in result
        assert "isInNet(ip, '10.0.0.0', '255.0.0.0')" in result
        assert "host == 'localhost'" in result
        assert result.count(" ||") == 3
    
    def test_generate_no_proxy_empty(self):
        """Test no-proxy generation with empty list"""
        result = generate_no_proxy([])
        
        assert result == ""
    
    def test_generate_no_proxy_invalid_network(self):
        """Test no-proxy generation with invalid network (treated as hostname)"""
        no_proxy = ['invalid.network/99']
        
        result = generate_no_proxy(no_proxy)
        
        # Should treat as hostname since it's not valid IP/network
        expected = " host == 'invalid.network/99' ||"
        assert result == expected


class TestPACGeneration:
    """Test complete PAC file generation"""
    
    @patch('flora_pac.fetch_ip_data')
    @patch('flora_pac.merge_all')
    @patch('flora_pac.fregment_nets')
    @patch('flora_pac.hash_nets')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_pac_basic(self, mock_file, mock_hash_nets, mock_fregment, 
                               mock_merge, mock_fetch):
        """Test basic PAC file generation"""
        # Mock the data pipeline
        mock_networks = [
            ipaddress.ip_network('192.168.0.0/24'),
            ipaddress.ip_network('10.0.0.0/22')
        ]
        mock_fetch.return_value = mock_networks
        mock_merge.return_value = mock_networks
        mock_fregment.return_value = mock_networks
        
        # Mock hash result
        mock_hash_result = [[] for _ in range(3011)]  # HASH_BASE = 3011
        mock_hash_result[0] = mock_networks[:1]
        mock_hash_result[1] = mock_networks[1:]
        mock_hash_nets.return_value = mock_hash_result
        
        proxies = ['SOCKS5 127.0.0.1:1984']
        balance = 'no'
        no_proxy = ['192.168.0.0/24']
        
        generate_pac(proxies, balance, no_proxy)
        
        # Verify file operations
        mock_file.assert_called_once_with('flora_pac.pac', 'w')
        handle = mock_file()
        handle.write.assert_called_once()
        
        # Get the written content
        written_content = handle.write.call_args[0][0]
        
        # Verify PAC file structure
        assert 'function FindProxyForURL(url, host)' in written_content
        assert 'dot2num' in written_content
        assert 'lookup_ip' in written_content
        assert 'HASH_BASE = 3011' in written_content
        assert 'MASK_STEP = 2' in written_content
        assert "return 'SOCKS5 127.0.0.1:1984'" in written_content
        assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in written_content
    
    @patch('flora_pac.fetch_ip_data')
    @patch('flora_pac.merge_all')
    @patch('flora_pac.fregment_nets')
    @patch('flora_pac.hash_nets')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_pac_with_balancing(self, mock_file, mock_hash_nets, 
                                        mock_fregment, mock_merge, mock_fetch):
        """Test PAC generation with proxy balancing"""
        # Mock the data pipeline
        mock_networks = [ipaddress.ip_network('192.168.0.0/24')]
        mock_fetch.return_value = mock_networks
        mock_merge.return_value = mock_networks
        mock_fregment.return_value = mock_networks
        
        mock_hash_result = [[] for _ in range(3011)]
        mock_hash_result[0] = mock_networks
        mock_hash_nets.return_value = mock_hash_result
        
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
        balance = 'local_ip'
        no_proxy = []
        
        generate_pac(proxies, balance, no_proxy)
        
        # Get the written content
        handle = mock_file()
        written_content = handle.write.call_args[0][0]
        
        # Verify local IP balancing is included
        assert 'local_ip_balance' in written_content
        assert 'myIpAddress()' in written_content
    
    @patch('flora_pac.fetch_ip_data')
    @patch('flora_pac.merge_all') 
    @patch('flora_pac.fregment_nets')
    @patch('flora_pac.hash_nets')
    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')  # Mock print to avoid output during tests
    def test_generate_pac_empty_networks(self, mock_print, mock_file, mock_hash_nets,
                                        mock_fregment, mock_merge, mock_fetch):
        """Test PAC generation with empty network list"""
        # Mock empty data pipeline
        mock_fetch.return_value = []
        mock_merge.return_value = []
        mock_fregment.return_value = []
        
        mock_hash_result = [[] for _ in range(3011)]
        mock_hash_nets.return_value = mock_hash_result
        
        proxies = ['SOCKS5 127.0.0.1:1984']
        balance = 'no'
        no_proxy = []
        
        generate_pac(proxies, balance, no_proxy)
        
        # Should still generate valid PAC file
        mock_file.assert_called_once()
        handle = mock_file()
        written_content = handle.write.call_args[0][0]
        
        assert 'function FindProxyForURL(url, host)' in written_content
        assert 'empty_array' in written_content