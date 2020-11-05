# Napalm-s350

NAPALM driver for Cisco SMB switches (SF3xx, SF5xx, SG3xx, SG5xx).

## Status
Master: ![Build](https://github.com/napalm-automation-community/napalm-s350/workflows/Test%20before%20push/badge.svg?branch=master&event=push)

Develop: ![Build](https://github.com/napalm-automation-community/napalm-s350/workflows/Test%20before%20push/badge.svg?branch=develop&event=push)

PyPi: [![Upload](https://github.com/napalm-automation-community/napalm-s350/workflows/Upload%20Python%20Package%20to%20PyPi.org/badge.svg)](https://github.com/napalm-automation-community/napalm-s350/actions?query=workflow%3A%22Upload+Python+Package+to+PyPi.org%22)

## Requirements

Python 3.6+, napalm 3+

## Installation 

```bash
pip3 install napalm_s350
```
## CLI test

Default information (the same as `call get_facts`
```bash
napalm --user USER --password PASSWORD --vendor s350 HOSTNAME
```

Get interfaces
```bash
napalm --user USER --password PASSWORD --vendor s350 HOSTNAME call get_interfaces
```

Get configuration file
```bash
napalm --user USER --password PASSWORD --vendor s350 HOSTNAME call get_config
```

Debug
```bash
napalm --user USER --password PASSWORD --vendor s350 --debug HOSTNAME
```

## Supported devices

This driver initially targets the Cisco SG350 device though other, similar, devices may
be supported.

| function                  | SG300 | SG500 | SG350 | SG550 | stack SG500 | stack SG550 |
| :---                      | :---: | :---: | :---: | :---: | :---:       | :---:       |
|get_arp_table              |       |       | x     |       |             |             |
|get_arp_table (with vrf)   |       |       | NI    |       |             |             |
|get_bgp_config             |       |       |       |       |             |             |
|get_bgp_neighbors          |       |       |       |       |             |             |
|get_bgp_neighbors_detail   |       |       |       |       |             |             |
|get_config                 |       |       | x     |       |             |             |
|get_config (filtered)      |       |       | x     |       |             |             |
|get_config (sanitized)     |       |       | x     |       |             |             |
|get_environment            |       |       |       |       |             |             |
|get_facts                  |       |       | x     |       |             |             |
|get_firewall_policies      |       |       |       |       |             |             |
|get_interfaces             |       |       | x     |       |             |             |
|get_interfaces_counters    |       |       |       |       |             |             |
|get_interfaces_ip          |       |       | x     |       |             |             |
|get_ipv6_neighbors_table   |       |       |       |       |             |             |
|get_lldp_neighbors         |       |       | x     |       |             |             |
|get_lldp_neighbors_detail  |       |       | x     |       |             |             |
|get_mac_address_table      |       |       |       |       |             |             |
|get_network_instances      |       |       |       |       |             |             |
|get_ntp_peers              |       |       |       |       |             |             |
|get_ntp_servers            |       |       | x     |       |             |             |
|get_ntp_stats              |       |       |       |       |             |             |
|get_optics                 |       |       |       |       |             |             |
|get_probes_config          |       |       |       |       |             |             |
|get_probes_results         |       |       |       |       |             |             |
|get_route_to               |       |       |       |       |             |             |
|get_snmp_information       |       |       |       |       |             |             |
|get_users                  |       |       |       |       |             |             |
|get_vlans                  |       |       | x     |       |             |             |
|is_alive                   |       |       |       |       |             |             |
|ping                       |       |       |       |       |             |             |
|traceroute                 |       |       |       |       |             |             |
