import pytest
import ipaddress
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import flora_pac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flora_pac


class TestBasicFunctionality:
    """Test basic functionality without complex mocking"""
    
    def test_merge_nets_basic(self):
        """Test basic network merging"""
        net1 = ipaddress.ip_network('192.168.0.0/25')
        net2 = ipaddress.ip_network('192.168.0.128/25')
        
        result = flora_pac.merge_nets(net1, net2)
        assert result == ipaddress.ip_network('192.168.0.0/24')
    
    def test_merge_nets_non_adjacent(self):
        """Test that non-adjacent networks don't merge"""
        net1 = ipaddress.ip_network('192.168.0.0/24')
        net2 = ipaddress.ip_network('192.168.2.0/24')
        
        result = flora_pac.merge_nets(net1, net2)
        assert result is None
    
    def test_merge_all_basic(self):
        """Test merging multiple networks"""
        networks = [
            ipaddress.ip_network('192.168.0.0/25'),
            ipaddress.ip_network('192.168.0.128/25'),
            ipaddress.ip_network('10.0.0.0/24')
        ]
        
        result = flora_pac.merge_all(networks)
        
        # Should merge adjacent /25 networks into /24
        result_strs = [str(net) for net in result]
        assert '192.168.0.0/24' in result_strs
        assert '10.0.0.0/24' in result_strs
        assert len(result) == 2
    
    def test_fregment_net_basic(self):
        """Test basic network fragmentation"""
        net = ipaddress.ip_network('192.168.0.0/22')
        
        result = flora_pac.fregment_net(net)
        
        # /22 should stay as /22 (aligned to MASK_STEP=2)
        assert len(result) == 1
        assert str(result[0]) == '192.168.0.0/22'
    
    def test_hash_nets_basic(self):
        """Test basic network hashing"""
        networks = [
            ipaddress.ip_network('192.168.0.0/24'),
            ipaddress.ip_network('10.0.0.0/24')
        ]
        
        result = flora_pac.hash_nets(networks, 10)
        
        # Should return list of 10 buckets
        assert len(result) == 10
        
        # Each bucket should be a list
        for bucket in result:
            assert isinstance(bucket, list)
        
        # All networks should be distributed
        total_networks = sum(len(bucket) for bucket in result)
        assert total_networks == 2
    
    def test_generate_balanced_proxy_variations(self):
        """Test different proxy balancing strategies"""
        proxies = ['SOCKS5 127.0.0.1:1984', 'SOCKS5 127.0.0.1:1989']
        
        # Test no balancing
        result_no = flora_pac.generate_balanced_proxy(proxies, 'no')
        assert 'SOCKS5 127.0.0.1:1984;SOCKS5 127.0.0.1:1989' in result_no
        
        # Test local IP balancing
        result_local = flora_pac.generate_balanced_proxy(proxies, 'local_ip')
        assert 'local_ip_balance' in result_local
        assert 'myIpAddress()' in result_local
        
        # Test host balancing
        result_host = flora_pac.generate_balanced_proxy(proxies, 'host')
        assert 'target_host_balance' in result_host
        assert 'hash_string' in result_host
    
    def test_generate_no_proxy_variations(self):
        """Test different no-proxy configurations"""
        # Test single IP
        result_ip = flora_pac.generate_no_proxy(['192.168.1.1'])
        assert "ip == '192.168.1.1'" in result_ip
        
        # Test network
        result_net = flora_pac.generate_no_proxy(['192.168.0.0/24'])
        assert "isInNet(ip, '192.168.0.0', '255.255.255.0')" in result_net
        
        # Test hostname
        result_host = flora_pac.generate_no_proxy(['example.com'])
        assert "host == 'example.com'" in result_host
        
        # Test mixed
        result_mixed = flora_pac.generate_no_proxy(['192.168.1.1', '10.0.0.0/8', 'localhost'])
        assert "ip == '192.168.1.1'" in result_mixed
        assert "isInNet(ip, '10.0.0.0', '255.0.0.0')" in result_mixed
        assert "host == 'localhost'" in result_mixed