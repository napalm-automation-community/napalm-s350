# Napalm-s350

NAPALM driver for Cisco SMB switches (SF3xx, SF5xx, SG3xx, SG5xx, CBS35x).

## Status
Master: ![Build](https://github.com/napalm-automation-community/napalm-s350/workflows/Test%20before%20push/badge.svg?branch=master&event=push)

Develop: ![Build](https://github.com/napalm-automation-community/napalm-s350/workflows/Test%20before%20push/badge.svg?branch=develop&event=push)

PyPi: [![Upload](https://github.com/napalm-automation-community/napalm-s350/workflows/Upload%20Python%20Package%20to%20PyPi.org/badge.svg)](https://github.com/napalm-automation-community/napalm-s350/actions?query=workflow%3A%22Upload+Python+Package+to+PyPi.org%22)

## Requirements

Python 3.8+, napalm 4

## Installation 

```bash
pip3 install napalm_s350
```
## CLI test

Default information (the same as `call get_facts`)
```bash
napalm --user USER --password PASSWORD --vendor s350 HOSTNAME

napalm --user USER --password PASSWORD --vendor s350 HOSTNAME --optional_args "force_no_enable=True"
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

| function                  | SG300 | SG500 | SG350 | SG550 | stack SG500 | stack SG550 | CBS350 |
| :---                      | :---: | :---: | :---: | :---: | :---:       | :---:       | :---:  |
| **Send commands**                                                                              |
| cli                       | x     | x     | x     | x     | x           | x           | x      |
| **Config manipulation**                                                                        |
|get_config                 | x     | x     | x     | x     |             |             | x      |
|get_config (filtered)      | x     | x     | x     | x     |             |             | x      |
|get_config (sanitized)     | x     | x     | x     | x     |             |             | x      |
|load_merge_candidate       |       |       |       |       |             |             |        |
|load_replace_candidate     |       |       |       |       |             |             |        |
|compare_config             |       |       |       |       |             |             |        |
|commit_config              |       |       |       |       |             |             |        |
|confirm_commit             |       |       |       |       |             |             |        |
|has_pending_commit         |       |       |       |       |             |             |        |
|rollback                   |       |       |       |       |             |             |        |
|discard_config             |       |       |       |       |             |             |        |
|compliance_report          |       |       |       |       |             |             |        |
|load_template              |       |       |       |       |             |             |        |
| **Get information**                                                                            |
|get_arp_table              | x     | x     | x     | x     |             |             | x      |
|get_arp_table (with vrf)   | NS    | NS    | NS    | NS    |             |             | NS     |
|get_bgp_config             |       |       |       |       |             |             |        |
|get_bgp_neighbors          |       |       |       |       |             |             |        |
|get_bgp_neighbors_detail   |       |       |       |       |             |             |        |
|get_environment            |       |       |       |       |             |             |        |
|get_facts                  | x     | x     | x     | x     |             |             | x      |
|get_firewall_policies      |       |       |       |       |             |             |        |
|get_interfaces             | x     | x     | x     | x     |             |             | x      |
|get_interfaces_counters    |       |       |       |       |             |             |        |
|get_interfaces_ip          | x 4   | x 4   | x 4   | x 4   |             |             | x 4    |
|get_ipv6_neighbors_table   |       |       |       |       |             |             |        |
|get_lldp_neighbors         | x     | x     | x     | x     |             |             | x      |
|get_lldp_neighbors_detail  | x     | x     | x     | x     |             |             | x      |
|get_mac_address_table      |       |       |       |       |             |             |        |
|get_network_instances      |       |       |       |       |             |             |        |
|get_ntp_peers              |       |       |       |       |             |             |        |
|get_ntp_servers            | x     | x     | x     | x     |             |             | x      |
|get_ntp_stats              |       |       |       |       |             |             |        |
|get_optics                 |       |       |       |       |             |             |        |
|get_probes_config          |       |       |       |       |             |             |        |
|get_probes_results         |       |       |       |       |             |             |        |
|get_route_to               |       |       |       |       |             |             |        |
|get_snmp_information       |       |       |       |       |             |             |        |
|get_users                  |       |       |       |       |             |             |        |
|get_vlans                  | x     | x     | x     | x     |             |             | x      |
| **Other actions**                                                                              |
|is_alive                   |       |       |       |       |             |             |        |
|ping                       |       |       |       |       |             |             |        |
|traceroute                 |       |       |       |       |             |             |        |


NS - not supported - devices do not have support for that feature
4  - IPv4 only ...

## Want to add new device support?

To be sure we can support new device we use test files.

We need text output of those commands, to add new device:
```
show arp
show startup-config
show version
show system
show inventory
show hosts
show interface status
show running-config
show interfaces status
show interfaces description
show ports jumbo-frame
show ip int
show lldp neighbors
show sntp status
```

Those commands may need parameter change to suit your configuration:
```
show running-config full
show lldp local FastEthernet1
show lldp neighbors FastEthernet0/1
```

Please add each command to separate file - command `show arp` to file named `show_arp.txt`

Make pull request to /napalm-s350/tree/develop/test/unit/mocked_data/`your device type`/
or if you prefer make a Issue and add files as an atachement.
