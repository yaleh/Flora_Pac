Flora PAC
---------

by @leaskh and @yaleh (no, we are not cousins)

A PAC(Proxy auto-config) file generator with fetched China IP range, which helps walk around
GFW.

Yale Huang's fork was optimized for both performance and size: it matches about 100 times faster than the original version, and the size can be shrinked to less than 50KB with uglifyjs, which can be deployed at lowend gateways (i.e. my OpenWRT router of about 8 years history with only 2MB storage) easier. 

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

### Avoid proxy for a subnet

    ./flora_pac -x "PROXY_PROTOCOL PROXY_IP:PROXY_PORT" -n "NETWORK_ADDRESS/NETMASK"
	
### Avoid proxy for multiple subnets and specific hosts (no wildcard support for hosts yet)

    ./flora_pac -x "PROXY_PROTOCOL PROXY_IP:PROXY_PORT" -n "NETWORK_ADDRESS1/NETMASK1" "NETWORK_ADDRESS2/NETMASK2" "HOST1" "HOST2"

## Tips

### How to make SOCKS proxy setting compatible with most OSs and browsers

It's found that Chrome accepts only proxy string of "SOCKS5", iOS Safari accepts only "SOCKS", Mozilla accepts both. To make them work together, the proxy argument should look like this:

    "SOCKS5 PROXY_IP:PROXY_PORT; SOCKS PROXY_IP:PROXY_PORT"


Notice: don't mass the order.
  
So, a real case of balancing with two SOCKS proxies looks like this
  
    ./flora_pac -b local_ip -x "SOCKS5 127.0.0.1:1984; SOCKS 127.0.0.1:1984" "SOCKS5 127.0.0.1:1989; SOCKS 127.0.0.1:1989"

### Minify/uglify generated PAC file

To make the generate PAC file smaller, it can be minified/uglified like this:

    uglifyjs -m --lint -c -o flora_pac.min.pac flora_pac.pac

### A total solution with OpenWRT

1. AuthSSH for SOCKS proxy

2. Copy the geneated PAC file to /www/wpad.dat (yes, filename wpad.dat is MUST for compatibility)

3. Add following DHCP options (if you want to get the proxy configuration from DHCP automatically)

        option local-pac-server code 252 = text; 
        option local-pac-server "http://YOUR_GAETWAY/wpad.dat"; 

## For Developers

### Debugging generated PAC file

pacparser(https://code.google.com/p/pacparser/) works.


### Generate JS code with CoffeeScript

Most JS code of the PAC file are generate with the CoffeeScript file hash_ip.coffee. Actually, I even implemented a test stub of isInNet, so the code can be test from command line like this:

    coffee hash_ip

BTW: JS shift ops really suck.
