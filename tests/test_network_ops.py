import pytest
import ipaddress
import sys
import os

# Add parent directory to path to import flora_pac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flora_pac
fregment_net = flora_pac.fregment_net
fregment_nets = flora_pac.fregment_nets
hash_address = flora_pac.hash_address
hash_nets = flora_pac.hash_nets


class TestNetworkFragmentation:
    """Test network fragmentation functionality"""
    
    def test_fregment_net_basic(self):
        """Test basic network fragmentation"""
        # Test with /20 network, should fragment to /22 (MASK_STEP=2)
        net = ipaddress.ip_network('192.168.0.0/20')
        
        result = fregment_net(net)
        
        # /20 -> /22 creates 4 subnets
        assert len(result) == 4
        
        expected_networks = [
            '192.168.0.0/22',
            '192.168.4.0/22', 
            '192.168.8.0/22',
            '192.168.12.0/22'
        ]
        
        result_strs = [str(subnet) for subnet in result]
        for expected in expected_networks:
            assert expected in result_strs
    
    def test_fregment_net_already_aligned(self):
        """Test fragmentation of network already aligned to MASK_STEP"""
        # Test with /22 network (already aligned to MASK_STEP=2)
        net = ipaddress.ip_network('192.168.0.0/22')
        
        result = fregment_net(net)
        
        # Should return the same network
        assert len(result) == 1
        assert str(result[0]) == '192.168.0.0/22'
    
    def test_fregment_net_small_network(self):
        """Test fragmentation of small network"""
        # Test with /30 network
        net = ipaddress.ip_network('192.168.1.0/30')
        
        result = fregment_net(net)
        
        # /30 -> /32 creates 4 subnets
        assert len(result) == 4
        
        expected_networks = [
            '192.168.1.0/32',
            '192.168.1.1/32',
            '192.168.1.2/32', 
            '192.168.1.3/32'
        ]
        
        result_strs = [str(subnet) for subnet in result]
        for expected in expected_networks:
            assert expected in result_strs
    
    def test_fregment_nets_multiple(self):
        """Test fragmentation of multiple networks"""
        networks = [
            ipaddress.ip_network('192.168.0.0/20'),
            ipaddress.ip_network('10.0.0.0/21')
        ]
        
        result = fregment_nets(networks)
        
        # /20 -> 4 subnets, /21 -> 2 subnets (/21 -> /22)
        assert len(result) == 6
        
        # Check some expected subnets
        result_strs = [str(subnet) for subnet in result]
        assert '192.168.0.0/22' in result_strs
        assert '10.0.0.0/22' in result_strs
        assert '10.0.4.0/22' in result_strs
    
    def test_fregment_nets_empty(self):
        """Test fragmentation of empty network list"""
        result = fregment_nets([])
        assert result == []


class TestHashingAlgorithms:
    """Test hashing algorithms for IP addresses and networks"""
    
    def test_hash_address_basic(self):
        """Test basic address hashing"""
        # Test with IPv4 address as integer
        address = ipaddress.ip_address('192.168.1.1')
        
        result = hash_address(address, 1000)
        
        # Should return hash within modulo range
        assert 0 <= result < 1000
        assert isinstance(result, int)
    
    def test_hash_address_consistency(self):
        """Test that same address always produces same hash"""
        address = ipaddress.ip_address('192.168.1.1')
        
        result1 = hash_address(address, 1000)
        result2 = hash_address(address, 1000)
        
        assert result1 == result2
    
    def test_hash_address_different_addresses(self):
        """Test that different addresses produce potentially different hashes"""
        addr1 = ipaddress.ip_address('192.168.1.1')
        addr2 = ipaddress.ip_address('192.168.1.2')
        
        hash1 = hash_address(addr1, 1000)
        hash2 = hash_address(addr2, 1000)
        
        # While not guaranteed, they're likely to be different
        # At minimum, they should be valid hash values
        assert 0 <= hash1 < 1000
        assert 0 <= hash2 < 1000
    
    def test_hash_address_different_mod_base(self):
        """Test hashing with different modulo bases"""
        address = ipaddress.ip_address('192.168.1.1')
        
        hash_100 = hash_address(address, 100)
        hash_1000 = hash_address(address, 1000)
        
        assert 0 <= hash_100 < 100
        assert 0 <= hash_1000 < 1000
    
    def test_hash_nets_basic(self):
        """Test hashing of network list"""
        networks = [
            ipaddress.ip_network('192.168.0.0/24'),
            ipaddress.ip_network('192.168.1.0/24'),
            ipaddress.ip_network('10.0.0.0/24')
        ]
        
        result = hash_nets(networks, 100)
        
        # Should return list of 100 buckets
        assert len(result) == 100
        
        # Each bucket should be a list
        for bucket in result:
            assert isinstance(bucket, list)
        
        # All networks should be distributed among buckets
        total_networks = sum(len(bucket) for bucket in result)
        assert total_networks == 3
    
    def test_hash_nets_empty(self):
        """Test hashing of empty network list"""
        result = hash_nets([], 100)
        
        # Should return 100 empty buckets
        assert len(result) == 100
        for bucket in result:
            assert bucket == []
    
    def test_hash_nets_distribution(self):
        """Test that networks are properly distributed in hash buckets"""
        # Create many networks to test distribution
        networks = []
        for i in range(0, 100):
            networks.append(ipaddress.ip_network(f'192.168.{i}.0/24'))
        
        result = hash_nets(networks, 50)
        
        # Should have 50 buckets
        assert len(result) == 50
        
        # Total networks should be preserved
        total_networks = sum(len(bucket) for bucket in result)
        assert total_networks == 100
        
        # At least some buckets should have networks
        non_empty_buckets = sum(1 for bucket in result if len(bucket) > 0)
        assert non_empty_buckets > 0
    
    def test_hash_nets_consistency(self):
        """Test that hashing is consistent across calls"""
        networks = [
            ipaddress.ip_network('192.168.0.0/24'),
            ipaddress.ip_network('10.0.0.0/24')
        ]
        
        result1 = hash_nets(networks, 100)
        result2 = hash_nets(networks, 100)
        
        # Results should be identical
        assert len(result1) == len(result2)
        for i in range(len(result1)):
            assert len(result1[i]) == len(result2[i])
            for j in range(len(result1[i])):
                assert result1[i][j] == result2[i][j]