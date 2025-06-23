"""
Tests for the modular network_ops module
"""
import pytest
import ipaddress
import sys
import os

# Add parent directory to path to import flora_pac_lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flora_pac_lib.network_ops import (
    fregment_net, fregment_nets, hash_address, hash_nets, calculate_prefix_range
)


class TestModularNetworkOps:
    """Test modular network operations functionality"""
    
    def test_fregment_net_modular_custom_mask_step(self):
        """Test fragmentation with custom mask step"""
        net = ipaddress.ip_network('192.168.0.0/20')
        
        # Test with mask_step=3
        result = fregment_net(net, mask_step=3)
        
        # /20 -> /21 (next multiple of 3 from 20 is 21)
        assert len(result) == 2
        expected_networks = ['192.168.0.0/21', '192.168.8.0/21']
        result_strs = [str(subnet) for subnet in result]
        for expected in expected_networks:
            assert expected in result_strs
    
    def test_fregment_net_modular_already_aligned(self):
        """Test that already aligned networks are returned as-is"""
        net = ipaddress.ip_network('192.168.0.0/20')  # Already aligned to step 2
        
        result = fregment_net(net, mask_step=2)
        
        assert len(result) == 1
        assert result[0] == net
    
    def test_fregment_nets_modular_mixed_networks(self):
        """Test fragmentation of mixed network sizes"""
        networks = [
            ipaddress.ip_network('10.0.0.0/19'),   # /19 -> /20 (2 subnets)
            ipaddress.ip_network('192.168.0.0/20'), # Already aligned (1 subnet)
            ipaddress.ip_network('172.16.0.0/21')   # /21 -> /22 (2 subnets)
        ]
        
        result = fregment_nets(networks, mask_step=2)
        
        # Should have 1*2 + 1*1 + 1*2 = 5 networks
        assert len(result) == 5
        
        # Check some expected results
        result_strs = [str(net) for net in result]
        assert '10.0.0.0/20' in result_strs
        assert '192.168.0.0/20' in result_strs
        assert '172.16.0.0/22' in result_strs
    
    def test_hash_address_modular_consistency(self):
        """Test that hash_address is consistent and deterministic"""
        address = ipaddress.ip_address('192.168.1.100')
        
        # Multiple calls should return same result
        hash1 = hash_address(address, 1000)
        hash2 = hash_address(address, 1000)
        hash3 = hash_address(address, 1000)
        
        assert hash1 == hash2 == hash3
        assert 0 <= hash1 < 1000
    
    def test_hash_address_modular_distribution(self):
        """Test that different addresses produce different hashes"""
        addresses = [
            ipaddress.ip_address(f'192.168.1.{i}') for i in range(1, 11)
        ]
        
        hashes = [hash_address(addr, 100) for addr in addresses]
        
        # All hashes should be in valid range
        for h in hashes:
            assert 0 <= h < 100
        
        # Most should be different (allowing for some collisions)
        unique_hashes = set(hashes)
        assert len(unique_hashes) >= 7  # At least 70% unique
    
    def test_hash_nets_modular_bucket_distribution(self):
        """Test that hash_nets distributes networks properly"""
        networks = [
            ipaddress.ip_network(f'192.168.{i}.0/24') for i in range(20)
        ]
        
        result = hash_nets(networks, 10)
        
        # Should have 10 buckets
        assert len(result) == 10
        
        # All networks should be distributed
        total_networks = sum(len(bucket) for bucket in result)
        assert total_networks == 20
        
        # Each bucket should be a list
        for bucket in result:
            assert isinstance(bucket, list)
    
    def test_hash_nets_modular_empty_input(self):
        """Test hash_nets with empty network list"""
        result = hash_nets([], 50)
        
        assert len(result) == 50
        for bucket in result:
            assert bucket == []
    
    def test_calculate_prefix_range_modular(self):
        """Test calculate_prefix_range function"""
        networks = [
            ipaddress.ip_network('192.168.0.0/16'),  # min
            ipaddress.ip_network('10.0.0.0/20'),
            ipaddress.ip_network('172.16.1.0/28'),   # max
            ipaddress.ip_network('203.0.113.0/24')
        ]
        
        min_prefix, max_prefix = calculate_prefix_range(networks)
        
        assert min_prefix == 16
        assert max_prefix == 28
    
    def test_calculate_prefix_range_modular_empty(self):
        """Test calculate_prefix_range with empty list"""
        min_prefix, max_prefix = calculate_prefix_range([])
        
        assert min_prefix == 32
        assert max_prefix == 0
    
    def test_calculate_prefix_range_modular_single_network(self):
        """Test calculate_prefix_range with single network"""
        networks = [ipaddress.ip_network('192.168.0.0/24')]
        
        min_prefix, max_prefix = calculate_prefix_range(networks)
        
        assert min_prefix == 24
        assert max_prefix == 24