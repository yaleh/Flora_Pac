"""
Network Operations Module

This module handles network fragmentation and hashing operations
for optimizing IP lookup performance in PAC files.
"""

import ipaddress
from typing import List


def fregment_net(net: ipaddress.IPv4Network, mask_step: int = 2) -> List[ipaddress.IPv4Network]:
    """
    Fragment a network into subnets aligned to mask_step boundaries.
    
    Args:
        net: Network to fragment
        mask_step: Step size for mask alignment (default: 2)
        
    Returns:
        List of fragmented networks
    """
    # Calculate the target prefix length using integer division
    # This finds the smallest multiple of MASK_STEP that is >= net.prefixlen
    target_prefixlen = (net.prefixlen - 1) // mask_step * mask_step + mask_step
    
    try:
        # Fragment the network into subnets with target prefix length
        subnets = list(net.subnets(new_prefix=target_prefixlen))
        return subnets
    except ValueError as e:
        # If fragmentation fails, return original network
        print(f"Warning: Could not fragment network {net}: {e}")
        return [net]


def fregment_nets(nets: List[ipaddress.IPv4Network], mask_step: int = 2) -> List[ipaddress.IPv4Network]:
    """
    Fragment multiple networks into subnets aligned to mask_step boundaries.
    
    Args:
        nets: List of networks to fragment
        mask_step: Step size for mask alignment (default: 2)
        
    Returns:
        List of all fragmented networks
    """
    results = []
    for net in nets:
        results.extend(fregment_net(net, mask_step))
    return results


def hash_address(address: ipaddress.IPv4Address, mod_base: int) -> int:
    """
    Hash an IP address using modulo operation.
    
    Args:
        address: IPv4 address to hash
        mod_base: Modulo base for hashing
        
    Returns:
        Hash value (0 <= result < mod_base)
    """
    return int(address) % mod_base


def hash_nets(nets: List[ipaddress.IPv4Network], mod_base: int) -> List[List[ipaddress.IPv4Network]]:
    """
    Distribute networks into hash buckets based on their network address.
    
    Args:
        nets: List of networks to hash
        mod_base: Number of hash buckets
        
    Returns:
        List of buckets, each containing networks that hash to that bucket
    """
    hashed = [[] for _ in range(mod_base)]
    
    for net in nets:
        bucket_index = hash_address(net.network_address, mod_base)
        hashed[bucket_index].append(net)
    
    return hashed


def calculate_prefix_range(networks: List[ipaddress.IPv4Network]) -> tuple:
    """
    Calculate the minimum and maximum prefix lengths in a network list.
    
    Args:
        networks: List of networks
        
    Returns:
        Tuple of (min_prefixlen, max_prefixlen)
    """
    if not networks:
        return (32, 0)
    
    min_prefixlen = min(net.prefixlen for net in networks)
    max_prefixlen = max(net.prefixlen for net in networks)
    
    return (min_prefixlen, max_prefixlen)