import pytest
import responses
import ipaddress
from unittest.mock import patch, mock_open
import sys
import os

# Add parent directory to path to import flora_pac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from flora_pac script
import flora_pac
fetch_ip_data = flora_pac.fetch_ip_data
merge_nets = flora_pac.merge_nets
merge_all = flora_pac.merge_all


class TestFetchIPData:
    """Test IP data fetching and parsing from APNIC"""
    
    @responses.activate
    def test_fetch_ip_data_success(self):
        """Test successful fetching and parsing of APNIC data"""
        mock_data = """2|apnic|20230101|46214|19830101|20230101|+1000
apnic|CN|ipv4|1.0.1.0|256|20110414|allocated
apnic|CN|ipv4|1.0.2.0|512|20110414|allocated
apnic|CN|ipv4|27.8.0.0|1024|20110414|allocated
apnic|JP|ipv4|1.0.16.0|4096|20110414|allocated
apnic|CN|ipv4|203.208.32.0|512|20110414|allocated"""
        
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body=mock_data,
            status=200
        )
        
        result = fetch_ip_data()
        
        # Should return only CN entries
        assert len(result) == 4
        
        # Check specific networks
        networks = [str(net) for net in result]
        assert '1.0.1.0/24' in networks  # 256 IPs = /24
        assert '1.0.2.0/23' in networks  # 512 IPs = /23
        assert '27.8.0.0/22' in networks  # 1024 IPs = /22
        assert '203.208.32.0/23' in networks  # 512 IPs = /23
        
        # Should not include JP entries
        jp_networks = [net for net in result if str(net).startswith('1.0.16')]
        assert len(jp_networks) == 0
    
    @responses.activate
    def test_fetch_ip_data_network_error(self):
        """Test handling of network errors"""
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body="Connection error",
            status=500
        )
        
        with pytest.raises(Exception):
            fetch_ip_data()
    
    @responses.activate
    def test_fetch_ip_data_empty_response(self):
        """Test handling of empty or invalid data"""
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body="",
            status=200
        )
        
        result = fetch_ip_data()
        assert result == []
    
    @responses.activate
    def test_fetch_ip_data_malformed_entries(self):
        """Test handling of malformed APNIC entries"""
        mock_data = """apnic|CN|ipv4|1.0.1.0|256|20110414|allocated
apnic|CN|ipv4|invalid_ip|512|20110414|allocated
apnic|CN|ipv4|1.0.2.0|invalid_count|20110414|allocated
apnic|CN|ipv4|1.0.3.0|1024|20110414|allocated"""
        
        responses.add(
            responses.GET,
            'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest',
            body=mock_data,
            status=200
        )
        
        # Should skip malformed entries and process valid ones
        result = fetch_ip_data()
        assert len(result) == 2  # Only valid entries
        networks = [str(net) for net in result]
        assert '1.0.1.0/24' in networks
        assert '1.0.3.0/22' in networks


class TestNetworkMerging:
    """Test network merging functionality"""
    
    def test_merge_nets_adjacent_networks(self):
        """Test merging of adjacent networks"""
        net1 = ipaddress.ip_network('192.168.0.0/25')
        net2 = ipaddress.ip_network('192.168.0.128/25')
        
        result = merge_nets(net1, net2)
        assert result == ipaddress.ip_network('192.168.0.0/24')
    
    def test_merge_nets_non_adjacent_networks(self):
        """Test that non-adjacent networks don't merge"""
        net1 = ipaddress.ip_network('192.168.0.0/24')
        net2 = ipaddress.ip_network('192.168.2.0/24')
        
        result = merge_nets(net1, net2)
        assert result is None
    
    def test_merge_nets_overlapping_networks(self):
        """Test that overlapping networks don't merge incorrectly"""
        net1 = ipaddress.ip_network('192.168.0.0/23')
        net2 = ipaddress.ip_network('192.168.0.0/24')
        
        result = merge_nets(net1, net2)
        assert result is None
    
    def test_merge_all_multiple_networks(self):
        """Test merging multiple networks"""
        networks = [
            ipaddress.ip_network('192.168.0.0/25'),
            ipaddress.ip_network('192.168.0.128/25'),
            ipaddress.ip_network('192.168.1.0/25'),
            ipaddress.ip_network('192.168.1.128/25'),
            ipaddress.ip_network('10.0.0.0/24')
        ]
        
        result = merge_all(networks)
        
        # Should merge adjacent /25 networks into /24
        result_strs = [str(net) for net in result]
        assert '192.168.0.0/24' in result_strs
        assert '192.168.1.0/24' in result_strs
        assert '10.0.0.0/24' in result_strs
        assert len(result) == 3
    
    def test_merge_all_no_mergeable_networks(self):
        """Test with networks that cannot be merged"""
        networks = [
            ipaddress.ip_network('192.168.0.0/24'),
            ipaddress.ip_network('192.168.2.0/24'),
            ipaddress.ip_network('10.0.0.0/24')
        ]
        
        result = merge_all(networks)
        
        # Should return same networks
        assert len(result) == 3
        result_strs = [str(net) for net in result]
        assert '192.168.0.0/24' in result_strs
        assert '192.168.2.0/24' in result_strs
        assert '10.0.0.0/24' in result_strs
    
    def test_merge_all_empty_list(self):
        """Test with empty network list"""
        result = merge_all([])
        assert result == []