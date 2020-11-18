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
    CommandErrorException,
    ConnectionClosedException,
)
import napalm.base.constants as C
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

    def get_arp_table(self, vrf=""):
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

    def get_config(self, retrieve='all', full=False, sanitized=False):
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
            startup = self._send_command('show startup-config')
            configs['startup'] = self._get_config_filter(startup)

        if retrieve in ('all', 'running'):
            # IOS supports "full" only on "show running-config"
            run_full = " detailed" if full else ""
            running = self._send_command('show running-config' + run_full)
            configs['running'] = self._get_config_filter(running)

        if sanitized:
            configs = self._get_config_sanitized(configs)

        return configs

    def _get_config_filter(self, config):
        # The output of get_config should be directly usable by load_replace_candidate()

        # remove header
        filter_strings = [
            r"(?sm)^config-file-header.*^@$",
        ]

        for ft in filter_strings:
            config = re.sub(ft, "", config)

        return config

    def _get_config_sanitized(self, configs):
        # Do not output sensitive information

        # use Cisco IOS filters
        configs = napalm.base.helpers.sanitize_configs(configs, C.CISCO_SANITIZE_FILTERS)

        # defina my own filters
        s350_filters = {
            r"^(.* password) (\S+) (\S+) (.*)$": r"\1 \2 <removed> \4",
            r"^(snmp-server location) (\S+).*$": r"\1 <removed>",
        }

        configs = napalm.base.helpers.sanitize_configs(configs, s350_filters)

        return configs

    def get_facts(self):
        """Return a set of facts from the device."""
        serial_number, fqdn, os_version, hostname, domainname = ('Unknown',) * 5

        # Submit commands to the device.
        show_ver = self._send_command('show version')
        show_sys = self._send_command('show system')
        show_inv = self._send_command('show inventory')
        show_hosts = self._send_command('show hosts')
        show_int_st = self._send_command('show interface status')

        os_version = self._get_facts_parse_os_version(show_ver)

        # hostname
        hostname = self._get_facts_hostname(show_sys)
        # special case for SG500 fw v1.4.x
        if hostname == 'Unknown':
            hostname = self._get_facts_hostname_from_config(
                                self._send_command('show running-config')
                        )

        # uptime
        uptime_str = self._get_facts_uptime(show_sys)
        uptime = self._parse_uptime(uptime_str)

        # serial_number and model
        inventory = self._get_facts_parse_inventory(show_inv)['1']
        serial_number = inventory['sn']
        model = inventory['pid']

        # fqdn
        domainname = napalm.base.helpers.textfsm_extractor(self, 'hosts',
                                                           show_hosts)[0]
        domainname = domainname['domain_name']
        if domainname == 'Domain':
            domainname = 'Unknown'
        if domainname != "Unknown" and hostname != "Unknown":
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
            'fqdn': str(fqdn),
            'hostname': str(hostname),
            'interface_list': interfaces,
            'model': str(model),
            'os_version': str(os_version),
            'serial_number': str(serial_number),
            'uptime': uptime,
            'vendor': u'Cisco',
        }

    def _get_facts_hostname_from_config(self, show_running):
        # special case for SG500 fw v1.4.x
        hostname = 'Unknown'
        for line in show_running.splitlines():
            if line.startswith('hostname '):
                _, hostname = line.split('hostname')
                hostname = hostname.strip()
                break

        return hostname

    def _get_facts_hostname(self, show_sys):
        hostname = 'Unknown'
        for line in show_sys.splitlines():
            if line.startswith('System Name:'):
                _, hostname = line.split('System Name:')
                hostname = hostname.strip()
                break

        return hostname

    def _get_facts_uptime(self, show_sys):
        i = 0
        syslines = []
        fields = []
        uptime_header_lineNo = None
        uptime_str = None
        for line in show_sys.splitlines():
            # All models except SG500 fw 1.4.x
            if line.startswith('System Up Time (days,hour:min:sec):'):
                _, uptime_str = line.split('System Up Time (days,hour:min:sec):')
                break

            line = re.sub(r'  *', ' ', line, re.M)
            line = line.strip()

            fields = line.split(' ')
            syslines.append(fields)

            if 'Unit' in syslines[i] and 'time' in syslines[i]:
                uptime_header_lineNo = i

            i += 1

        # SG500 fw 1.4.x
        if not uptime_str:
            uptime_str = syslines[uptime_header_lineNo+2][1]

        return uptime_str

    def _get_facts_parse_inventory(self, show_inventory):
        """ inventory can list more modules/devices """
        # make 1 module 1 line
        show_inventory = re.sub(r'\nPID', '  PID', show_inventory, re.M)
        # delete empty lines
        show_inventory = re.sub(r'^\n', '', show_inventory, re.M)
        show_inventory = re.sub(r'\n\n', '', show_inventory, re.M)
        show_inventory = re.sub(r'\n\s*\n', r'\n', show_inventory, re.M)
        lines = show_inventory.splitlines()

        modules = {}
        for line in lines:
            match = re.search(r"""
                ^
                NAME:\s"(?P<name>\S+)"\s*
                DESCR:\s"(?P<descr>[^"]+)"\s*
                PID:\s(?P<pid>\S+)\s*
                VID:\s(?P<vid>.+\S)\s*
                SN:\s(?P<sn>\S+)\s*
                """, line, re.X)
            module = match.groupdict()
            modules[module['name']] = module

        if modules:
            return modules

    def _get_facts_parse_os_version(self, show_ver):
        # os_version
        # detect os ver > 2
        if re.search(r"^Active-image", show_ver):
            for line in show_ver.splitlines():
                # First version line is the active version
                if re.search(r"Version:", line):
                    _, os_version = line.split('Version: ')
                    break
        elif re.search(r"^SW version", show_ver):
            for line in show_ver.splitlines():
                if re.search(r"^SW version", line):
                    _, ver = line.split('    ')
                    os_version, _ = ver.split(' (')
                    break
        else:
            # show_ver = re.sub(r'^\n', '', show_ver, re.M)
            for line in show_ver.splitlines():
                line = re.sub(r'  *', ' ', line, re.M)
                line = line.strip()
                line_comps = line.split(' ')
                if line_comps[0] == '1':
                    os_version = line_comps[1]
                    break

        return os_version

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
                if "Po" in status_line:
                    interface, _, _, speed, _, _, link_state = status_line.split()
                else:
                    interface, _, _, speed, _, _, link_state, _, _ = status_line.split()

                # Since the MAC address for all the local ports are equal, get the address
                # from the first port and use it everywhere.
                if mac == '0':
                    show_system_output = self._send_command('show lldp local ' + interface)
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
        show_ip_int = self._send_command('show ip int')

        header = True    # cycle trought header
        for line in show_ip_int.splitlines():
            if header:
                # last line of first header
                match = re.match(r'^---+ -+ .*$', line)
                if match:
                    header = False
                    fields_end = self._get_ip_int_fields_end(line)
                continue

            # next header, stop processing text
            if re.match(r'^---+ -+ .*$', line):
                break

            line_elems = self._get_ip_int_line_to_fields(line, fields_end)

            # only valid interfaces
            # in diferent firmwares there is 'Status' field allwais on last place
            if line_elems[len(line_elems) - 1] != 'Valid':
                continue

            cidr = line_elems[0]
            interface = line_elems[1]

            ip = netaddr.IPNetwork(cidr)
            family = 'ipv{0}'.format(ip.version)

            interfaces[interface] = {
                family: {
                   str(ip.ip): {
                        'prefix_length': ip.prefixlen
                    }
                }
            }

        return interfaces

    def _get_ip_int_line_to_fields(self, line, fields_end):
        """ dynamic fields lenghts """
        line_elems = {}
        index = 0
        f_start = 0
        for f_end in fields_end:
            line_elems[index] = line[f_start:f_end].strip()
            index += 1
            f_start = f_end
        return line_elems

    def _get_ip_int_fields_end(self, dashline):
        """ fields length are diferent device to device, detect them on horizontal lin """

        fields_end = [m.start() for m in re.finditer(' ', dashline.strip())]
        # fields_position.insert(0,0)
        fields_end.append(len(dashline))

        return fields_end

    def get_lldp_neighbors(self):
        """get_lldp_neighbors implementation for s350"""
        neighbors = {}
        output = self._send_command('show lldp neighbors')

        header = True    # cycle trought header
        local_port = ''  # keep previous context - multiline syname
        remote_port = ''
        remote_name = ''
        for line in output.splitlines():
            if header:
                # last line of header
                match = re.match(r'^--------- -+ .*$', line)
                if match:
                    header = False
                    fields_end = self._get_lldp_neighbors_fields_end(line)
                continue

            line_elems = self._get_lldp_neighbors_line_to_fields(line, fields_end)

            # info owerflow to the other line
            if line_elems[0] == '' or line_elems[4] == '' or line_elems[5] == '' :
                # complete owerflown fields
                local_port = local_port + line_elems[0]
                remote_port = remote_port + line_elems[2]
                remote_name = remote_name + line_elems[3]
                # then reuse old values na rewrite previous entry
            else:
                local_port = line_elems[0]
                remote_port = line_elems[2]
                remote_name = line_elems[3]

            neighbor = {
                'hostname': remote_name,
                'port': remote_port,
            }
            neighbor_list = [neighbor, ]
            neighbors[local_port] = neighbor_list

        return neighbors

    def _get_lldp_neighbors_line_to_fields(self, line, fields_end):
        """ dynamic fields lenghts """
        line_elems = {}
        index = 0
        f_start = 0
        for f_end in fields_end:
            line_elems[index] = line[f_start:f_end].strip()
            index += 1
            f_start = f_end
        return line_elems

    def _get_lldp_neighbors_fields_end(self, dashline):
        """ fields length are diferent device to device, detect them on horizontal lin """

        fields_end = [m.start() for m in re.finditer(' ', dashline)]
        fields_end.append(len(dashline))

        return fields_end

    def _get_lldp_line_value(self, line):
        """
        Safe-ish method to get the value from an 'lldp neighbors $IF' line.
        """
        try:
            value = line.split(':')[1:][0].strip()
        except KeyError:
            value = u'N/A'

        return value

    def get_lldp_neighbors_detail(self, interface=""):
        """
        get_lldp_neighbors_detail() implementation for s350
        """
        details = {}

        # First determine all interfaces with valid LLDP neighbors
        for local_port in self.get_lldp_neighbors().keys():
            if interface:
                if interface == local_port:
                    entry = self._get_lldp_neighbors_detail_parse(local_port)
                    details[local_port] = [entry, ]

            else:
                entry = self._get_lldp_neighbors_detail_parse(local_port)
                details[local_port] = [entry, ]

        return details

    def _get_lldp_neighbors_detail_parse(self, local_port):
        # Set defaults, just in case the remote fails to provide a field.
        remote_port_id, remote_port_description, remote_chassis_id, \
            remote_system_name, remote_system_description, \
            remote_system_capab, remote_system_enable_capab = (u'N/A',) * 7

        output = self._send_command('show lldp neighbors {}'.format(local_port))

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
                caps = self._get_lldp_neighbors_detail_capabilities_parse(line)

        entry = {
            'parent_interface': u'N/A',
            'remote_port': remote_port_id,
            'remote_port_description': remote_port_description,
            'remote_chassis_id': remote_chassis_id,
            'remote_system_name': remote_system_name,
            'remote_system_description': remote_system_description,
            'remote_system_capab': caps,
            'remote_system_enable_capab': caps,
        }

        return entry

    def _get_lldp_neighbors_detail_capabilities_parse(self, line):
        # Only the enabled capabilities are displayed.
        try:
            # Split a line like 'Capabilities: Bridge, Router, Wlan-Access-Point'
            capabilities = line.split(':')[1:][0].split(',')
        except KeyError:
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

        return caps

    def get_ntp_servers(self):
        """Returns NTP servers."""
        ntp_servers = {}
        output = self._send_command('show sntp status')

        servers = re.findall(r'^Server\s*:\s*(\S+)\s*.*$', output, re.M)

        for server in servers:
            ntp_servers[server] = {}

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
