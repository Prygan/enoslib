from enoslib.errors import *
from enoslib.host import Host
from enoslib.ansible_utils import _generate_inventory_string, update_hosts, map_device_on_host_networks
from enoslib.utils import gen_rsc
import mock
import unittest


class TestGenerateInventoryString(unittest.TestCase):
    def test_address(self):
        h = Host("1.2.3.4")
        self.assertEqual("1.2.3.4 ansible_host=1.2.3.4 ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'", _generate_inventory_string(h))

    def test_address_alias(self):
        h = Host("1.2.3.4", alias="alias")
        role = "test"
        self.assertEqual("alias ansible_host=1.2.3.4 ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'", _generate_inventory_string(h))


    def test_address_user(self):
        h = Host("1.2.3.4", user="foo")
        self.assertEqual("1.2.3.4 ansible_host=1.2.3.4 ansible_ssh_user=foo ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'", _generate_inventory_string(h))

    def test_address_gateway(self):
        h = Host("1.2.3.4", extra={'gateway': '4.3.2.1'})
        self.assertEqual("1.2.3.4 ansible_host=1.2.3.4 ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ProxyCommand=\"ssh -W %h:%p -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null 4.3.2.1\"'", _generate_inventory_string(h))

    def test_address_gateway_same_user(self):
        h = Host("1.2.3.4", user="foo", extra={'gateway': '4.3.2.1'})
        self.assertEqual("1.2.3.4 ansible_host=1.2.3.4 ansible_ssh_user=foo ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ProxyCommand=\"ssh -W %h:%p -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -l foo 4.3.2.1\"'", _generate_inventory_string(h))



class TestGetHostNet(unittest.TestCase):
    def test_map_devices_all_match_single(self):
        networks = [{
            "cidr": "1.2.3.4/24"
            }, {
            "cidr": "4.5.6.7/24"
            }]
        devices = [{
            "device": "eth0",
            "ipv4": [{"address": "1.2.3.5"}]
        }, {
            "device": "eth1",
            "ipv4": [{"address": "4.5.6.7"}]
        }]
        expected = [{
            "cidr": "4.5.6.7/24",
            "device": "eth1"
            }, {
            "cidr": "1.2.3.4/24",
            "device": "eth0"
            }]
        self.assertItemsEqual(expected, map_device_on_host_networks(networks, devices))

    def test_map_devices_all_match_multiple(self):
        networks = [{
            "cidr": "1.2.3.4/24"
            }, {
            "cidr": "4.5.6.7/24"
            }]
        devices = [{
            "device": "eth0",
            "ipv4": [{"address": "1.2.3.5"}]
        }, {
            "device": "eth1",
            "ipv4": [{"address": "1.2.3.254"}]
        }]
        # only the last match is taken into account
        expected = [{
            "cidr": "1.2.3.4/24",
            "device": "eth1"
            }, {
            "cidr": "4.5.6.7/24",
            "device": None
            }]
        self.assertItemsEqual(expected, map_device_on_host_networks(networks, devices))

    def test_map_devices_net_veth(self):
        networks = [{
            "cidr": "1.2.3.4/24"
            }, {
            "cidr": "4.5.6.7/24"
            }]
        devices = [{
            "device": "eth0",
            "ipv4": [{"address": "1.2.3.5"}]
        }, {
            "device": "veth0",
            "ipv4": []
        }]
        expected = [{
            "cidr": "4.5.6.7/24",
            "device": None
            }, {
            "cidr": "1.2.3.4/24",
            "device": "eth0"
            }]
        self.assertItemsEqual(expected, map_device_on_host_networks(networks, devices))


class TestUpdateHosts(unittest.TestCase):

    def test_update_hosts(self):
        rsc = {"control": [Host("1.2.3.4", alias="foo"), Host("1.2.3.5", alias="bar")]}
        facts = {
                "foo": {
                    "networks": [{
                        "cidr": "1.2.3.0/24",
                        "device": "eth0",
                        "roles": ["network1"]

                    }, {
                        "cidr": "2.2.3.0/24",
                        "device": "eth1",
                        "roles": ["network2"]
                    }]},
                "bar": {
                    "networks": [{
                        "cidr": "1.2.3.0/24",
                        "device": "eth0",
                        "roles": ["network1"]
                    }, {
                        "cidr": "2.2.3.0/24",
                        "device": "eth1",
                        "roles": ["network2"]
                    }]},
                }

        update_hosts(rsc, facts)
        for host in gen_rsc(rsc):
            self.assertEqual("eth0", host.extra["network1"])
            self.assertEqual("eth1", host.extra["network2"])

    def test_update_hosts_inverted(self):
        rsc = {"control": [Host("1.2.3.4", alias="foo"), Host("1.2.3.5", alias="bar")]}
        facts = {
            "foo": {
                "networks": [{
                    "cidr": "1.2.3.0/24",
                    "device": "eth0",
                    "roles": ["network1"]
                }, {
                    "cidr": "2.2.3.0/24",
                    "device": "eth1",
                    "roles": ["network2"]
                }]},
            "bar": {
                "networks": [{
                    "cidr": "1.2.3.0/24",
                    "device": "eth1",
                    "roles": ["network1"]
                }, {
                    "cidr": "2.2.3.0/24",
                    "device": "eth0",
                    "roles": ["network2"]
                }]},
            }

        update_hosts(rsc, facts)
        for host in gen_rsc(rsc):
            if host.alias == "foo":
                self.assertEqual("eth0", host.extra["network1"])
                self.assertEqual("eth1", host.extra["network2"])
            elif host.alias == "bar":
                self.assertEqual("eth1", host.extra["network1"])
                self.assertEqual("eth0", host.extra["network2"])

    def test_update_hosts_unmatch(self):
        rsc = {"control": [Host("1.2.3.4", alias="foo")]}
        facts = {
                "foo": {
                    "networks": [{
                        "cidr": "1.2.3.0/24",
                        "device": "eth0",
                        "roles": ["network1"]
                    }, {
                        "cidr": "2.2.3.0/24",
                        "device": None
                    }]},
                }

        update_hosts(rsc, facts)
        for host in gen_rsc(rsc):
            self.assertEqual("eth0", host.extra["network1"])
            self.assertTrue("network2" not in host.extra)
