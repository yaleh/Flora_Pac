"""
IP Data Fetching and Network Merging Module

This module handles fetching IP range data from APNIC and merging
adjacent networks for optimization.
"""

import re
import math
import urllib3
import ipaddress
from typing import List


def fetch_ip_data() -> List[ipaddress.IPv4Network]:
    """
    Fetch China IP ranges from APNIC and return as IPv4Network objects.
    
    Returns:
        List of IPv4Network objects representing China IP ranges
        
    Raises:
        Exception: If network request fails or data parsing fails
    """
    print("Fetching data from apnic.net, it might take a few minutes, please wait...")
    url = r'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest'
    
    # Use PoolManager to make the request
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    
    if response.status != 200:
        raise Exception(f"Failed to fetch APNIC data: HTTP {response.status}")
    
    data = response.data.decode('utf-8')
    
    # Regex to match China IPv4 entries
    cnregex = re.compile(r'apnic\|cn\|ipv4\|[0-9\.]+\|[0-9]+\|[0-9]+\|a.*', re.IGNORECASE)
    cndata = cnregex.findall(data)
    
    results = []
    
    for item in cndata:
        try:
            unit_items = item.split('|')
            starting_ip = unit_items[3]
            num_ip = int(unit_items[4])
            
            # Calculate network mask from IP count
            imask = 0xffffffff ^ (num_ip - 1)
            # Convert to string
            imask = hex(imask)[2:]
            mask = [0] * 4
            mask[0] = imask[0:2]
            mask[1] = imask[2:4]
            mask[2] = imask[4:6]
            mask[3] = imask[6:8]
            
            # Convert str to int
            mask = [int(i, 16) for i in mask]
            mask = "%d.%d.%d.%d" % tuple(mask)
            
            # Create network object
            net = ipaddress.ip_network(u"%s/%s" % (starting_ip, mask))
            results.append(net)
            
        except (ValueError, IndexError, TypeError) as e:
            # Skip malformed entries
            print(f"Warning: Skipping malformed entry: {item} - {e}")
            continue
    
    return results


def merge_nets(net1: ipaddress.IPv4Network, net2: ipaddress.IPv4Network) -> ipaddress.IPv4Network:
    """
    Merge two adjacent networks if possible.
    
    Args:
        net1: First network
        net2: Second network
        
    Returns:
        Merged network if networks are adjacent, None otherwise
    """
    try:
        super_net1 = net1.supernet()
        super_net2 = net2.supernet()
        
        if (super_net1 == super_net2 and 
            super_net1.network_address == net1.network_address and
            super_net1.broadcast_address == net2.broadcast_address):
            return super_net1
            
    except ValueError:
        # Networks cannot be merged
        pass
        
    return None


def merge_all(networks: List[ipaddress.IPv4Network]) -> List[ipaddress.IPv4Network]:
    """
    Merge all adjacent networks in a list to optimize the network list.
    
    Args:
        networks: List of IPv4Network objects
        
    Returns:
        Optimized list with adjacent networks merged
    """
    if not networks:
        return []
        
    # Sort networks for consistent merging
    networks = sorted(networks)
    
    i = 1
    while i < len(networks):
        if i == 0:
            i += 1
            continue
            
        merged_net = merge_nets(networks[i-1], networks[i])
        if merged_net is None:
            i += 1
            continue
            
        networks[i-1] = merged_net
        networks.pop(i)
        if i > 1:
            i -= 1
    
    return networks