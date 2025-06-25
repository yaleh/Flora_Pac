"""
Flora PAC - Proxy Auto-Config generator for China IP ranges

This package provides modular components for generating PAC files that
automatically route Chinese IPs direct while proxying other traffic.
"""

from .ip_data import fetch_ip_data, merge_nets, merge_all
from .network_ops import fregment_net, fregment_nets, hash_address, hash_nets
from .pac_generator import generate_balanced_proxy, generate_no_proxy, generate_pac
from .web_ui import create_web_ui, launch_web_ui

__version__ = "1.0.0"
__author__ = "Yale Huang (optimized fork of @leaskh original)"

__all__ = [
    'fetch_ip_data',
    'merge_nets', 
    'merge_all',
    'fregment_net',
    'fregment_nets',
    'hash_address',
    'hash_nets',
    'generate_balanced_proxy',
    'generate_no_proxy',
    'generate_pac',
    'create_web_ui',
    'launch_web_ui',
]