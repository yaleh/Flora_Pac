"""
PAC File Generation Module

This module handles the generation of Proxy Auto-Config (PAC) files
with embedded JavaScript for IP lookup and proxy balancing.
"""

import ipaddress
from typing import List

from .ip_data import fetch_ip_data, merge_all
from .network_ops import fregment_nets, hash_nets, calculate_prefix_range


def generate_balanced_proxy(proxies: List[str], balance: str) -> str:
    """
    Generate JavaScript code for proxy balancing based on strategy.
    
    Args:
        proxies: List of proxy server strings
        balance: Balancing strategy ('no', 'local_ip', 'host')
        
    Returns:
        JavaScript code for proxy selection
    """
    if balance == 'no':
        return "return '%s' ;" % (';'.join(proxies))
    elif balance == 'local_ip':
        return '''
  var local_ip_balance = function(proxies) {
    var i, k, l, myseg, s, _i;
    myseg = parseInt(myIpAddress().split(".")[3]);
    l = proxies.length;
    k = myseg % l;
    s = '';
    for (i = _i = 0; 0 <= l ? _i < l : _i > l; i = 0 <= l ? ++_i : --_i) {
      s += proxies[(k + i) % l];
    }
    return s;
  };
''' + """
  return local_ip_balance([%s]);
""" % (','.join(map(lambda p: "'%s'" % p, proxies)))
    elif balance == 'host':
        return '''
  var target_host_balance = function(proxies, host) {
    var hash_string, i, k, l, s, _i;
    hash_string = function(s) {
      var c, hash, _i, _len;
      hash = 0;
      for (_i = 0, _len = s.length; _i < _len; _i++) {
        c = s[_i];
        hash = (hash << 5) - hash + c.charCodeAt(0);
        hash = hash & hash & 0xFFFF;
        hash &= 0xFFFF;
      }
      return hash;
    };
    l = proxies.length;
    k = hash_string(host) % l;
    s = '';
    for (i = _i = 0; 0 <= l ? _i < l : _i > l; i = 0 <= l ? ++_i : --_i) {
      s += proxies[(k + i) % l];
    }
    return s;
  };
''' + """
  return target_host_balance([%s], host);
""" % (','.join(map(lambda p: "'%s'" % p, proxies)))


def generate_no_proxy(no_proxy: List[str]) -> str:
    """
    Generate JavaScript code for no-proxy rules.
    
    Args:
        no_proxy: List of IPs, networks, or hostnames to bypass proxy
        
    Returns:
        JavaScript condition code for no-proxy rules
    """
    s = ''
    for n in no_proxy:
        try:
            # Single IP address
            ip = ipaddress.ip_address(u"%s" % n)
            s += " ip == '%s' ||" % n
            continue
        except ValueError:
            pass
        
        try:
            # Network with mask or mask prefix 
            net = ipaddress.ip_network(u"%s" % n)
            s += " isInNet(ip, '%s', '%s') ||" % (net.network_address, net.netmask)
            continue
        except ValueError:
            pass

        # Hostname
        s += " host == '%s' ||" % n

    return s


def generate_pac(proxies: List[str], balance: str, no_proxy: List[str], 
                hash_base: int = 3011, mask_step: int = 2, 
                output_file: str = 'flora_pac.pac') -> None:
    """
    Generate complete PAC file with embedded JavaScript and hash tables.
    
    Args:
        proxies: List of proxy server strings
        balance: Proxy balancing strategy
        no_proxy: List of networks/hosts to bypass proxy
        hash_base: Hash table size for performance tuning
        mask_step: Network fragmentation step size
        output_file: Output PAC filename
    """
    # Fetch and process IP data
    print("Processing IP data...")
    results = merge_all(fetch_ip_data())
    
    # Calculate prefix length range
    min_prefixlen, max_prefixlen = calculate_prefix_range(results)
    print("PrefixLen: [%d, %d]" % (min_prefixlen, max_prefixlen))
    
    # Fragment and hash networks
    print("Fragmenting and hashing networks...")
    hashed_results = hash_nets(fregment_nets(results, mask_step), hash_base)
    
    # Generate PAC file content
    pac_content = _generate_pac_content(
        hashed_results, proxies, balance, no_proxy,
        hash_base, mask_step, min_prefixlen, max_prefixlen, results
    )
    
    # Write PAC file
    with open(output_file, 'w') as rfile:
        rfile.write(pac_content)
    
    # Print statistics
    _print_generation_stats(hashed_results, results, min_prefixlen, max_prefixlen, mask_step, output_file)


def _generate_pac_content(hashed_results: List[List[ipaddress.IPv4Network]], 
                         proxies: List[str], balance: str, no_proxy: List[str],
                         hash_base: int, mask_step: int, 
                         min_prefixlen: int, max_prefixlen: int,
                         results: List[ipaddress.IPv4Network]) -> str:
    """
    Generate the complete PAC file content as a string.
    
    Returns:
        Complete PAC file content
    """
    # PAC file header and JavaScript functions
    pac_content = '''
// Flora_Pac by @leaskh
// www.leaskh.com, i@leaskh.com
// Optimized by @yaleh
   
function FindProxyForURL(url, host) {
  var HASH_BASE, MASK_STEP, a, dot2num, hash_masked_ip, hashed_nets, i, lookup_ip, max_prefixlen, min_prefixlen, num2dot, prefixlen2mask, rebuild_net, _i, _j, _len, _len1;

  dot2num = function(dot) {
    var d;
    d = dot.split(".");
    return ((((((+d[0]) * 256) + (+d[1])) * 256) + (+d[2])) * 256) + (+d[3]);
  };

  num2dot = function(ip) {
    return [ip >>> 24, ip >>> 16 & 0xFF, ip >>> 8 & 0xFF, ip & 0xFF].join(".");
  };

  hash_masked_ip = function(ip, mask_len, mod_base) {
    var i, net, offset, _i;
    offset = 32 - mask_len;
    net = ip >>> offset;
    for (i = _i = 0; 0 <= offset ? _i < offset : _i > offset; i = 0 <= offset ? ++_i : --_i) {
      net *= 2;
    }
    return net % mod_base;
  };

  prefixlen2mask = function(prefixlen) {
    var imask;
    imask = 0xFFFFFFFF << (32 - prefixlen);
    return (imask >> 24 & 0xFF) + '.' + (imask >> 16 & 0xFF) + '.' + (imask >> 8 & 0xFF) + '.' + (imask & 0xFF);
  };

  rebuild_net = function(pair) {
    var masks, result;
    result = ['', ''];
    result[0] = num2dot(pair[0] << (32 - pair[1]));
    result[1] = prefixlen2mask(pair[1]);
    return result;
  };

  lookup_ip = function(ip) {
    var i, k, len, n, n_ip, _i, _len, _ref;
    len = min_prefixlen;
    n_ip = dot2num(ip);
    while (len <= max_prefixlen) {
      k = hash_masked_ip(n_ip, len, HASH_BASE);
      _ref = hashed_nets[k];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        i = _ref[_i];
        n = rebuild_net(i);
        if (isInNet(ip,n[0],n[1])) {
          return true;
        }
      }
      len += MASK_STEP;
    }
    return false;
  };
'''
    
    # Add configuration constants
    pac_content += f"""

  HASH_BASE = {hash_base};
  MASK_STEP = {mask_step};
  min_prefixlen = {min_prefixlen};
  max_prefixlen = {max_prefixlen};

"""
    
    # Add mask step variables
    for i in range(min_prefixlen, max_prefixlen + 1, mask_step):
        pac_content += f"""    var m{i} = {i};
"""
    
    # Add hashed networks data
    pac_content += """    var empty_array = [];
    var hashed_nets = [
"""
    
    for i in range(len(hashed_results)):
        if len(hashed_results[i]) > 0:
            pac_content += "\n        ["
            for net in hashed_results[i]:
                pac_content += f"\n            [{int(net.network_address) >> (32 - net.prefixlen)}, m{net.prefixlen}],"
            pac_content += "\n        ],"
        else:
            pac_content += "\n        empty_array,"
    
    # Add main PAC logic
    pac_content += f"""
    ];

    if (isPlainHostName(host)
     || (host == '127.0.0.1')
     || (host == 'localhost')
     ) {{
        return 'DIRECT';
    }}

    var ip = dnsResolve(host);

    if (ip == null || ip == '' || {generate_no_proxy(no_proxy)} lookup_ip(ip)) {{
        return 'DIRECT';
    }}

    {generate_balanced_proxy(proxies, balance)}

}}
"""
    
    return pac_content


def _print_generation_stats(hashed_results: List[List[ipaddress.IPv4Network]], 
                           results: List[ipaddress.IPv4Network],
                           min_prefixlen: int, max_prefixlen: int, 
                           mask_step: int, output_file: str) -> None:
    """Print generation statistics."""
    none_empty_count = sum(1 for bucket in hashed_results if len(bucket) > 0)
    avg_len = float(len(results)) / none_empty_count if none_empty_count > 0 else 0
    steps = (max_prefixlen - min_prefixlen) / mask_step + 1
    
    print("Average matching length: %f" % avg_len)
    print("Steps to match: %d" % steps)
    print("Matching cost est.: %f" % (avg_len * steps))
    print("Rules: %d items." % len(results))
    print(f"Usage: Use the newly created {output_file} as your web browser's "
          "automatic proxy configuration (.pac) file.")