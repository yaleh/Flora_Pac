Flora PAC
---------

by @leaskh and @yaleh (no, we are not cousins)

A PAC(Proxy auto-config) file generator with fetched China IP range, which helps walk around
GFW.

## New Features

* March 2013
  * Optimized matching alrightm, which is much faster at iOS devices
  * Load balancing strategies (see Usage)

## Installation

    git clone https://github.com/Trantect/Flora_Pac.git
	
## Uasge

### Simplest way

    ./flora_pac -x "PROXY_PROTOCOL PROXY_IP:PROXY_PORT"

### With multiple proxies but no balancing (failover only)

    ./flora_pac -x "PROXY1_PROTOCOL PROXY1_IP:PROXY1_PORT" "PROXY2_PROTOCOL PROXY2_IP:PROXY2_PORT"

### With multiple proxy and balanced by local IP (and failover)

    ./flora_pac -b local_ip -x "PROXY1_PROTOCOL PROXY1_IP:PROXY1_PORT" "PROXY2_PROTOCOL PROXY2_IP:PROXY2_PORT"

### With multiple proxy and balanced by target host name (and failover)

    ./flora_pac -b host -x "PROXY1_PROTOCOL PROXY1_IP:PROXY1_PORT" "PROXY2_PROTOCOL PROXY2_IP:PROXY2_PORT"

## Tips

### How to make SOCKS proxy setting compatible with most OSs and browsers?

It's found that Chrome accepts only proxy string of "SOCKS5", iOS Safari accepts only "SOCKS", Mozilla accepts both. To make them work together, the proxy argument should look like this:

    "SOCKS5 PROXY_IP:PROXY_PORT; SOCKS PROXY_IP:PROXY_PORT"


Notice: don't mass the order.
  
So, a real case of balancing with multiple SOCKS proxy looks like this
  
    ./flora_pac -b local_ip -x "SOCKS5 127.0.0.1:1984; SOCKS 127.0.0.1:1984" "SOCKS5 127.0.0.1:1989; SOCKS 127.0.0.1:1989"

### Minify/uglify generated PAC file

To make the generate PAC file smaller, it can be minified/uglified like this:

    uglifyjs -m --lint -c -o flora_pac.min.pac flora_pac.pac
