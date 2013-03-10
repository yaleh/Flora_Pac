#!/usr/bin/env coffee

# Faked test stubs to simulate PAC running env
isInNet = (ipaddr, pattern, maskstr) ->
  host = convert_addr(ipaddr)
  pat = convert_addr(pattern)
  mask = convert_addr(maskstr)
  (host & mask) is (pat & mask)

myIpAddress = ->
  "192.168.0.2"

HASH_BASE = 3
MASK_STEP = 2

min_prefixlen = 10
max_prefixlen = 24

### LOCAL_IP_BALANCE_BEGIN ###

local_ip_balance = (proxies) ->
  myseg = parseInt(myIpAddress().split(".")[3])
  l = proxies.length
  k = myseg % l
  s = ''
  s += proxies[(k+i) % l] for i in [0...l]
  s

### LOCAL_IP_BALANCE_END ###

### TARGET_HOST_BALANCE_BEGIN ###

target_host_balance = (proxies, host) ->

  hash_string = (s) ->
    hash = 0
    for c in s
      hash = (hash << 5) - hash + c.charCodeAt(0)
      hash = hash & hash & 0xFFFF
      hash &= 0xFFFF
    hash
            
  l = proxies.length
  console.log hash_string(host)
  k = hash_string(host) % l
  s = ''
  s += proxies[(k+i) % l] for i in [0...l]
  s  

### TARGET_HOST_BALANCE_END ###

### FLORA_BEGIN ###

convert_addr = (ipchars) ->
  bytes = ipchars.split(".")
  result = ((bytes[0] & 0xff) << 24) | ((bytes[1] & 0xff) << 16) \
  | ((bytes[2] & 0xff) << 8) | (bytes[3] & 0xff)
  result

dot2num = (dot) ->
  d = dot.split(".")
#  ((((((+d[0]) << 8) | (+d[1])) << 8) | (+d[2])) << 8) | (+d[3])
  ((((((+d[0])*256)+(+d[1]))*256)+(+d[2]))*256)+(+d[3])

num2dot = (ip) ->
  [ip >>> 24, ip >>> 16 & 0xFF, ip >>> 8 & 0xFF, ip & 0xFF].join "."
  
hash_masked_ip = (ip, mask_len, mod_base) ->
  offset = 32 - mask_len
  net = ip >>> offset
  net *= 2 for i in [0...offset]
#  console.log net
#  console.log mod_base
  return net % mod_base

prefixlen2mask = (prefixlen) ->
  imask = 0xFFFFFFFF << (32 - prefixlen)
  (imask >> 24 & 0xFF) + '.' + (imask >> 16 & 0xFF) + '.' + \
  (imask >> 8 & 0xFF) + '.' + (imask & 0xFF)

rebuild_net = (pair) ->
  result = ['', '']
  result[0] = num2dot pair[0] << (32 - pair[1])
  result[1] = prefixlen2mask(pair[1])
  return result

lookup_ip = (ip) ->
  len = min_prefixlen
  n_ip = dot2num(ip)
#  console.log n_ip
  while len <= max_prefixlen
#    console.log len
    k = hash_masked_ip(n_ip, len, HASH_BASE)
#    console.log k
    for i in hashed_nets[k]
      n = rebuild_net i
      return true if isInNet ip, n[0], n[1]
#      console.log n
    len += MASK_STEP
  false

### FLORA_END ###

hashed_nets = [
        [
            [13248647, 24],
            [828605, 20],
            [13305856, 24],
        ],
        [
            [3313729, 22],
        ],
        [
            [173367, 20],
        ],
      ]

console.log dot2num("192.168.1.23")

console.log hash_masked_ip(dot2num("192.168.1.23"), 24, 1009)
console.log hash_masked_ip(dot2num("192.168.1.3"), 24, 1009)


for a in hashed_nets
  console.log a
  for i in a
    console.log i
    console.log rebuild_net(i)

console.log lookup_ip "202.65.4.0"
console.log lookup_ip "203.208.37.20"

console.log local_ip_balance ['S0', 'S1', 'S2']
console.log target_host_balance ['S0', 'S1', 'S2'], "google.com"