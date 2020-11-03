# -*- coding: utf-8 -*-
# Copyright 2018 Jasper Lievisse Adriaanse. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Napalm driver for Cisco S350 devices.

Read https://napalm.readthedocs.io for more information.
"""

from __future__ import print_function
from __future__ import unicode_literals

import netaddr
import re
import socket

from netmiko import ConnectHandler
from napalm.base import NetworkDriver
from napalm.base.exceptions import (
    ConnectionException,
    SessionLockedException,
    MergeConfigException,
    ReplaceConfigException,
    CommandErrorException,
)

import napalm.base.helpers


class S350Driver(NetworkDriver):
    """Napalm driver for S350."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        if optional_args is None:
            optional_args = {}

        self._dest_file_system = optional_args.get('dest_file_system', None)

        # Netmiko possible arguments
        netmiko_argument_map = {
            'port': None,
            'secret': '',
            'verbose': False,
            'keepalive': 30,
            'global_delay_factor': 1,
            'use_keys': False,
            'key_file': None,
            'ssh_strict': False,
            'system_host_keys': False,
            'alt_host_keys': False,
            'alt_key_file': '',
            'ssh_config_file': None,
            'allow_agent': False,
        }

        # Allow for passing additional Netmiko arguments
        self.netmiko_optional_args = {}
        for k, v in netmiko_argument_map.items():
            try:
                self.netmiko_optional_args[k] = optional_args[k]
            except KeyError:
                pass

        self.port = optional_args.get('port', 22)
        self.device = None

    def open(self):
        """Open a connection to the device."""
        self.device = ConnectHandler(device_type='cisco_s300',
                                     host=self.hostname,
                                     username=self.username,
                                     password=self.password,
                                     **self.netmiko_optional_args)
        self.device.enable()


    def _discover_file_system(self):
        try:
            return self.device._autodetect_fs()
        except Exception:
            msg = "Netmiko _autodetect_fs failed (to work around specify " \
                  "dest_file_system in optional_args)."
            raise CommandErrorException(msg)


    def close(self):
        """Close the connection to the device."""
        self.device.disconnect()

    def _send_command(self, command):
        """Wrapper for self.device.send.command().

        If command is a list will iterate through commands until valid command.
        """
        try:
            if isinstance(command, list):
                for cmd in command:
                    output = self.device.send_command(cmd)
                    if "% Invalid" not in output:
                        break
            else:
                output = self.device.send_command(command)
            return output.strip()
        except (socket.error, EOFError) as e:
            raise ConnectionClosedException(str(e))


    def _parse_uptime(self, uptime_str):
        """Parse an uptime string into number of seconds"""
        uptime_str = uptime_str.strip()
        days, timespec = uptime_str.split(',')

        hours, minutes, seconds = timespec.split(':')

        uptime_sec = (int(days) * 86400) + (int(hours) * 3600) + (int(minutes) * 60) + int(seconds)
        return uptime_sec


    def get_arp_table(self, vrf = None):
        """
        Get the ARP table, the age isn't readily available so we leave that out for now.

        vrf is needed for test - no support on s350
        """

        arp_table = []

        output = self._send_command('show arp')

        for line in output.splitlines():
            # A VLAN may not be set for the entry
            if 'vlan' not in line:
                continue
            if len(line.split()) == 4:
                interface, ip, mac, _ = line.split()
            elif len(line.split()) == 5:
                if1, if2, ip, mac, _ = line.split()
                interface = "{} {}".format(if1, if2)
            elif len(line.split()) == 6:
                _, _, interface, ip, mac, _ = line.split()
            else:
                raise ValueError('Unexpected output: {}'.format(line.split()))

            entry = {
                'interface': interface,
                'mac': napalm.base.helpers.mac(mac),
                'ip': ip,
                'age': 0.0,
            }

            arp_table.append(entry)

        return arp_table


    def get_config(self, retrieve='all'):
        """
        get_config for S350. Since this firmware doesn't support a candidate
        configuration we leave it empty.
        """

        configs = {
            'startup': '',
            'running': '',
            'candidate': '',
        }

        if retrieve in ('all', 'startup'):
            output = self._send_command('show startup-config')
            configs['startup'] = output

        if retrieve in ('all', 'running'):
            output = self._send_command('show running-config')
            configs['running'] = output

        return configs

    def get_facts(self):
        """Return a set of facts from the device."""
        serial_number, fqdn, os_version, hostname, domain_name = ('Unknown',) * 5

        # Submit commands to the device.
        show_ver = self._send_command('show version')
        show_sys = self._send_command('show system')
        show_inv = self._send_command('show inventory')
        show_hosts = self._send_command('show hosts')
        show_int_st = self._send_command('show interface status')

        # os_version
        # detect os ver > 2
        if 'Active-image' in show_ver:
            for line in show_ver.splitlines():
                # First version line is the active version
                if 'Version' in line:
                    _, os_version = line.split('Version: ')
                    break
        else:
            for line in show_ver.splitlines():
                if 'SW version' in line:
                    _, ver = line.split('    ')
                    os_version, _ = ver.split(' (')
                    break

        # hostname, uptime
        for line in show_sys.splitlines():
            if line.startswith('System Name:'):
                _, hostname = line.split('System Name:')
                hostname = hostname.strip()
                continue
            elif line.startswith('System Description:'):
                _, model = line.split('System Description:')
                model = model.strip()
                continue
            elif line.startswith('System Up Time (days,hour:min:sec):'):
                _, uptime_str = line.split('System Up Time (days,hour:min:sec):')
                uptime = self._parse_uptime(uptime_str)

        # serial_number
        for line in show_inv.splitlines():
            if 'SN:' in line:
                serial_number = line.split('SN: ')[-1]
                break

        # fqdn
        domainname = napalm.base.helpers.textfsm_extractor(self, 'hosts',
                                                           show_hosts)[0]
        domainname = domainname['domain_name']
        if domainname == 'Domain':
            domainname = ''
        fqdn = '{0}.{1}'.format(hostname, domainname)

        # interface_list
        interfaces = []
        show_int_st = show_int_st.strip()
        # remove the header information
        show_int_st = re.sub(
            r"(^-.*$|^Port .*$|^Ch .*$)|^\s.*$|^.*Flow.*$", "", show_int_st,
            flags=re.M
        )
        for line in show_int_st.splitlines():
            if not line:
                continue
            interface = line.split()[0]
            interfaces.append(str(interface))

        return {
            'fqdn':str(fqdn),
            'hostname': str(hostname),
            'interface_list': interfaces,
            'model': str(model),
            'os_version': str(os_version),
            'serial_number': str(serial_number),
            'uptime': uptime,
            'vendor': u'Cisco',
        }


    def get_interfaces(self):
        """
        get_interfaces() implementation for S350
        """
        interfaces = {}

        show_status_output = self._send_command('show interfaces status')
        show_description_output = self._send_command('show interfaces description')

        # by documentation SG350
        show_jumbo_frame = self._send_command('show ports jumbo-frame')
        match = re.search(r'Jumbo frames are enabled', show_jumbo_frame, re.M)
        if match:
            mtu = 9000
        else:
            mtu = 1518

        mac = '0'

        for status_line in show_status_output.splitlines():
            if 'Up' in status_line or 'Down' in status_line:
                interface, _, _, speed, _, _, link_state, _, _ = status_line.split()

                # Since the MAC address for all the local ports are equal, get the address
                # from the first port and use it everywhere.
                if mac == '0':
                    show_system_output = self._send_command('show lldp local ' + interface )

                    mac = show_system_output.splitlines()[0].split(':', maxsplit=1)[1].strip()

                if speed == '--':
                    is_enabled = False
                    speed = 0
                else:
                    is_enabled = True
                    speed = int(speed)

                is_up = (link_state == 'Up')

                for descr_line in show_description_output.splitlines():
                    description = 0
                    if descr_line.startswith(interface):
                        description = ' '.join(descr_line.split()[1:])
                        break

                # last_flapped can not be get - setting to default
                entry = {
                    'is_up': is_up,
                    'is_enabled': is_enabled,
                    'speed': speed,
                    'mtu': mtu,
                    'last_flapped': -1.0,
                    'description': description,
                    'mac_address': napalm.base.helpers.mac(mac)
                }

                interfaces[interface] = entry

        return interfaces


    def get_interfaces_ip(self):
        """Returns all configured interface IP addresses."""
        interfaces = {}
        valid_interfaces = []
        show_ip_int = self._send_command('show ip int')

        # Limit to valid interfaces (i.e. ignore vlan 1)
        for line in show_ip_int.splitlines():
            if ('UP' in line or 'DOWN' in line) and line.split()[-1] == 'Valid':
                valid_interfaces.append(line)

        for interface in valid_interfaces:
            network, name = interface.split()[:2]

            ip = netaddr.IPNetwork(network)

            family = 'ipv{0}'.format(ip.version)

            interfaces[name] = {
                family: {
                    str(ip.ip): {
                        'prefix_length': ip.prefixlen
                    }
                }
            }

        return interfaces

    def get_lldp_neighbors(self):
        """get_lldp_neighbors implementation for s350"""
        neighbors = {}
        #output = self._send_command('show lldp neighbors | begin \ \ Port')
        output = self._send_command('show lldp neighbors')

        header = True # cycle trought header
        for line in output.splitlines():
            if header:
                # last line of header
                match = re.match(r'^--------- -+ .*$', line)
                if match:
                    header = False
                continue

            line_elems = line.split()
            local_port = line_elems[0]
            remote_port = line_elems[2]
            remote_name = line_elems[3]

            neighbor = {
                'hostname': remote_name,
                'port': remote_port,
            }
            neighbor_list= [ neighbor, ]
            neighbors[local_port] = neighbor_list
            
        return neighbors

    def _get_lldp_line_value(self, line):
        """
        Safe-ish method to get the value from an 'lldp neighbors $IF' line.
        """
        try:
            value = line.split(':')[1:][0].strip()
        except:
            value = u'N/A'

        return value


    def get_lldp_neighbors_detail(self):
        """
        get_lldp_neighbors_detail() implementation for s350
        """
        details = {}

        # First determine all interfaces with valid LLDP neighbors
        for local_port in self.get_lldp_neighbors().keys():
            # Set defaults, just in case the remote fails to provide a field.
            remote_port_id, remote_port_description, remote_chassis_id, \
                remote_system_name, remote_system_description, \
                remote_system_capab, remote_system_enable_capab = (u'N/A',) * 7

            output = self._send_command('show lldp neighbor {}'.format(local_port))

            for line in output.splitlines():
                if line.startswith('Port ID'):
                    remote_port_id = line.split()[-1]
                elif line.startswith('Device ID'):
                    remote_chassis_id = line.split()[-1]
                elif line.startswith('Port description'):
                    remote_port_description = self._get_lldp_line_value(line)
                elif line.startswith('System Name'):
                    remote_system_name = self._get_lldp_line_value(line)
                elif line.startswith('System description'):
                    remote_system_description = self._get_lldp_line_value(line)
                elif line.startswith('Capabilities'):
                    # Only the enabled capabilities are displayed.
                    try:
                        # Split a line like 'Capabilities: Bridge, Router, Wlan-Access-Point'
                        capabilities = line.split(':')[1:][0].split(',')
                    except:
                        capabilities = []

                    caps = []
                    # For all capabilities, except 'Repeater', the shorthand
                    # is the first character.
                    for cap in capabilities:
                        cap = cap.strip()
                        if cap == 'Repeater':
                            caps.append('r')
                        else:
                            caps.append(cap[0])

            entry = {
                'parent_interface': u'N/A',
                'remote_port': remote_port_id,
                'remote_port_description': remote_port_description,
                'remote_chassis_id': remote_chassis_id,
                'remote_system_name': remote_system_name,
                'remote_system_description': remote_system_description,
                'remote_system_capab': u', '.join(caps),
                'remote_system_enable_capab': u', '.join(caps),
            }

            details[local_port] = entry


        return details


    def get_ntp_servers(self):
        """get_ntp_servers implementation for S350"""
        ntp_servers = {}
        output = self._send_command('show sntp status')

        for line in output.splitlines():
            ntp_servers[line.split()[2]] = {}

        return ntp_servers

    def is_alive(self):
        """Returns an indication of the state of the connection."""
        null = chr(0)

        if self.device is None:
            return {'is_alive': False}

        # Send a NUL byte to keep the connection alive.
        try:
            self.device.write_channel(null)
            return {'is_alive': self.device.remote_conn.transport.is_active()}
        except (socket.error, EOFError):
            # If we couldn't send it, the connection is not available.
            return {'is_alive': False}

        # If we made it here, assume the worst.
        return {'is_alive': False}


    @property
    def dest_file_system(self):
        # First ensure we have an open connection.
        if self.device and self._dest_file_system is None:
            self._dest_file_system = self._discover_file_system()
        return self._dest_file_system
