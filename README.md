# Napalm-s350

NAPALM driver for Cisco SMB switches (SF3xx, SF5xx, SG250, SG3xx, SG5xx, CBS35x).

## Status

Master: [![Thorough Test](https://github.com/napalm-automation-community/napalm-s350/actions/workflows/ThoroughTest.yml/badge.svg?branch=master)](https://github.com/napalm-automation-community/napalm-s350/actions/workflows/ThoroughTest.yml)

Develop: [![Thorough Test](https://github.com/napalm-automation-community/napalm-s350/actions/workflows/ThoroughTest.yml/badge.svg?branch=develop)](https://github.com/napalm-automation-community/napalm-s350/actions/workflows/ThoroughTest.yml)

PyPi.org: [![Publish To PyPi.org](https://github.com/napalm-automation-community/napalm-s350/actions/workflows/PublishToPIP.yml/badge.svg?branch=master)](https://github.com/napalm-automation-community/napalm-s350/actions/workflows/PublishToPIP.yml)

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

This driver initially targets the Cisco SG350 device though other, similar, devices are
be supported.

| function                  | SG250 | SG300 | SG500 | SG350 | SG550 | stack SG500 | stack SG550 | CBS350 |
| :---                      | :---: | :---: | :---: | :---: | :---: | :---:       | :---:       | :---:  |
| **Send commands**                                                                                      |
| cli                       | x     | x     | x     | x     | x     | x           | x           | x      |
| **Config manipulation**                                                                                |
|get_config                 | x     | x     | x     | x     | x     |             |             | x      |
|get_config (filtered)      | x     | x     | x     | x     | x     |             |             | x      |
|get_config (sanitized)     | x     | x     | x     | x     | x     |             |             | x      |
|load_merge_candidate       |       |       |       |       |       |             |             |        |
|load_replace_candidate     |       |       |       |       |       |             |             |        |
|compare_config             |       |       |       |       |       |             |             |        |
|commit_config              |       |       |       |       |       |             |             |        |
|confirm_commit             |       |       |       |       |       |             |             |        |
|has_pending_commit         |       |       |       |       |       |             |             |        |
|rollback                   |       |       |       |       |       |             |             |        |
|discard_config             |       |       |       |       |       |             |             |        |
|compliance_report          |       |       |       |       |       |             |             |        |
|load_template              |       |       |       |       |       |             |             |        |
| **Get information**                                                                                    |
|get_arp_table              | x     | x     | x     | x     | x     |             |             | x      |
|get_arp_table (with vrf)   | NS    | NS    | NS    | NS    | NS    |             |             | NS     |
|get_bgp_config             |       |       |       |       |       |             |             |        |
|get_bgp_neighbors          |       |       |       |       |       |             |             |        |
|get_bgp_neighbors_detail   |       |       |       |       |       |             |             |        |
|get_environment            |       |       |       |       |       |             |             |        |
|get_facts                  | x     | x     | x     | x     | x     |             |             | x      |
|get_firewall_policies      |       |       |       |       |       |             |             |        |
|get_interfaces             | x     | x     | x     | x     | x     |             |             | x      |
|get_interfaces_counters    |       |       |       |       |       |             |             |        |
|get_interfaces_ip          | x 4   | x 4   | x 4   | x 4   | x 4   |             |             | x 4    |
|get_ipv6_neighbors_table   |       |       |       |       |       |             |             |        |
|get_lldp_neighbors         | x     | x     | x     | x     | x     |             |             | x      |
|get_lldp_neighbors_detail  | x     | x     | x     | x     | x     |             |             | x      |
|get_mac_address_table      |       |       |       |       |       |             |             |        |
|get_network_instances      |       |       |       |       |       |             |             |        |
|get_ntp_peers              |       |       |       |       |       |             |             |        |
|get_ntp_servers            | x     | x     | x     | x     | x     |             |             | x      |
|get_ntp_stats              |       |       |       |       |       |             |             |        |
|get_optics                 |       |       |       |       |       |             |             |        |
|get_probes_config          |       |       |       |       |       |             |             |        |
|get_probes_results         |       |       |       |       |       |             |             |        |
|get_route_to               |       |       |       |       |       |             |             |        |
|get_snmp_information       |       |       |       |       |       |             |             |        |
|get_users                  |       |       |       |       |       |             |             |        |
|get_vlans                  | x     | x     | x     | x     | x     |             |             | x      |
| **Other actions**                                                                                      |
|is_alive                   | x     | x     | x     | x     | x     | x           | x           | x      |
|ping                       |       |       |       |       |       |             |             |        |
|traceroute                 |       |       |       |       |       |             |             |        |


NS - not supported - devices do not have support for that feature
4  - IPv4 only ...

## Want to add new device support?

To be sure we can support new device we use test files.

### Fetch command output tool
There is tool for getting necessary infromatin form running switch
```
cd test/unit

# DEVICE_TYPE as PID: in "show inventory" output
# INTERFACE an inteface
# LLDP_INTERFACE inteface for getting LLDP inforation
./fetch_command_output.sh -u USER -p PASSWORD -t DEVICE_TYPE -v s350 \
    -d SWITCH_IP_or_FQDN -i INTERFACE -l LLDP_INTERFACE 
```

Output files from that tool are in "test/unit/command_output/$DEVICE_TYPE"

### By hand

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
