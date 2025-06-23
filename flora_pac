#!/usr/bin/env python3
"""
Flora_Pac - PAC (Proxy Auto-Config) file generator for China IP ranges

Original by @leaskh (www.leaskh.com, i@leaskh.com)
Optimized by @yaleh
Refactored for modularity and better maintainability

Based on chnroutes project (by Numb.Majority@gmail.com)
"""

import argparse
import sys
import os

# Add the flora_pac_lib package to the path for modular imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flora_pac_lib import generate_pac


def main():
    """Main entry point for Flora PAC generator."""
    parser = argparse.ArgumentParser(
        description="Generate proxy auto-config rules for China IP ranges.",
        epilog="Examples:\n"
               "  ./flora_pac -x 'SOCKS5 127.0.0.1:1984'\n"
               "  ./flora_pac -b local_ip -x 'SOCKS5 127.0.0.1:1984' 'SOCKS5 127.0.0.1:1989'\n"
               "  ./flora_pac -x 'SOCKS5 127.0.0.1:1984' -o custom.pac -s 5003",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-x', '--proxy',
                        dest='proxy',
                        default=['SOCKS 127.0.0.1:8964'],
                        nargs='*',
                        help="Proxy Server, accepts multiple values for balancing, e.g.: "
                             "-x 'SOCKS 127.0.0.1:8964' 'SOCKS5 127.0.0.1:1984' 'PROXY 127.0.0.1:1989'")
    
    parser.add_argument('-m', '--mask-step',
                        type=int,
                        dest='mask_step',
                        default=2,
                        help="Step size of mask fragment for network alignment (default: %(default)s)")
    
    parser.add_argument('-s', '--hash-base',
                        type=int,
                        dest='hash_base',
                        default=3011,
                        help='Size of the address hash table - larger values improve performance but increase file size (default: %(default)s)')
    
    parser.add_argument("-b", '--balance',
                        choices=["no", "local_ip", "host"],
                        dest='balance',
                        default="no",
                        help="Proxy balancing policy: "
                             "'no' for no balancing, "
                             "'local_ip' for balancing by local IP, "
                             "'host' for balancing by target hostname "
                             "(default: %(default)s)")
    
    parser.add_argument('-n', '--no-proxy',
                        dest='no_proxy',
                        nargs='*',
                        default=['192.168.0.0/24'],
                        help="Networks/hosts to bypass proxy, supports CIDR notation, e.g.: "
                             "'192.168.0.0/24' '10.0.0.0/8' 'localhost' "
                             "(default: %(default)s)")
    
    parser.add_argument('-o', '--output',
                        dest='output',
                        default='flora_pac.pac',
                        help="Output PAC filename (default: %(default)s)")
    
    parser.add_argument('--version',
                        action='version',
                        version='Flora PAC 1.0.0 (Modular)')

    args = parser.parse_args()
    
    try:
        # Generate PAC file using the modular library
        generate_pac(
            proxies=args.proxy,
            balance=args.balance,
            no_proxy=args.no_proxy,
            hash_base=args.hash_base,
            mask_step=args.mask_step,
            output_file=args.output
        )
        
        print(f"\nPAC file generation completed successfully!")
        print(f"Output file: {args.output}")
        print(f"Usage: Configure your browser to use {args.output} as the automatic proxy configuration file.")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating PAC file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()