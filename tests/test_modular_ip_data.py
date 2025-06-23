"""
Tests for the modular ip_data module
"""
import pytest
import responses
import ipaddress
import sys
import os

# Add parent directory to path to import flora_pac_lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flora_pac_lib.ip_data import fetch_ip_data, merge_nets, merge_all


class TestModularIPData:
    """Test modular IP data functionality"""
    
    @responses.activate
    def test_fetch_ip_data_modular(self):
        """Test the modular fetch_ip_data function"""
        mock_data = """2|apnic|20230101|46214|19830101|20230101|+1000
apnic|CN|ipv4|1.0.1.0|256|20110414|allocated
apnic|CN|ipv4|1.0.2.0|512|20110414|allocated
apnic|JP|ipv4|1.0.16.0|4096|20110414|allocated"""
        
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body=mock_data,
            status=200
        )
        
        result = fetch_ip_data()
        
        # Should return only CN entries
        assert len(result) == 2
        
        # Verify network objects are correctly created
        networks = [str(net) for net in result]
        assert '1.0.1.0/24' in networks
        assert '1.0.2.0/23' in networks
        
        # Should not include JP entries
        jp_networks = [net for net in result if '1.0.16' in str(net)]
        assert len(jp_networks) == 0
    
    def test_merge_nets_modular(self):
        """Test modular merge_nets function with type hints"""
        net1 = ipaddress.ip_network('192.168.0.0/25')
        net2 = ipaddress.ip_network('192.168.0.128/25')
        
        result = merge_nets(net1, net2)
        
        assert result is not None
        assert result == ipaddress.ip_network('192.168.0.0/24')
    
    def test_merge_nets_modular_non_adjacent(self):
        """Test that non-adjacent networks return None"""
        net1 = ipaddress.ip_network('192.168.0.0/24')
        net2 = ipaddress.ip_network('192.168.2.0/24')
        
        result = merge_nets(net1, net2)
        
        assert result is None
    
    def test_merge_all_modular_empty_list(self):
        """Test merge_all with empty list"""
        result = merge_all([])
        assert result == []
    
    def test_merge_all_modular_sorted_input(self):
        """Test that merge_all handles unsorted input correctly"""
        networks = [
            ipaddress.ip_network('192.168.1.128/25'),
            ipaddress.ip_network('192.168.0.0/25'),
            ipaddress.ip_network('192.168.0.128/25'),
            ipaddress.ip_network('192.168.1.0/25'),
        ]
        
        result = merge_all(networks)
        
        # Should merge into two /24 networks
        result_strs = sorted([str(net) for net in result])
        expected = ['192.168.0.0/24', '192.168.1.0/24']
        assert result_strs == expected