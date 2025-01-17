from enoslib.api import discover_networks, play_on
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.infra.enos_vagrant.configuration import Configuration

import logging


logging.basicConfig(level=logging.DEBUG)

# The conf let us define the resources wanted.
# This is provider specific
conf = Configuration.from_settings(backend="libvirt",
                                   box="generic/debian9")\
                    .add_machine(roles=["server"],
                                 flavour="tiny",
                                 number=1)\
                    .add_machine(roles=["client"],
                                 flavour="tiny",
                                 number=1)\
                    .add_network(roles=["mynetwork"],
                                 cidr="192.168.42.0/24")\
                    .finalize()

provider = Enos_vagrant(conf)

# The code below is intended to be provider agnostic

# Start the resources
roles, networks = provider.init()

# Add some specific knowledge to the returned roles (e.g on the server the ip
# for mynetwork is 192.168.42.254)
discover_networks(roles, networks)

# Experimentation logic starts here
with play_on(roles=roles) as p:
    # flent requires python3, so we default python to python3
    p.shell("update-alternatives --install /usr/bin/python python /usr/bin/python3 1")
    p.apt_repository(repo="deb http://deb.debian.org/debian stretch main contrib non-free",
                     state="present")
    p.apt(name=["flent", "netperf", "python3-setuptools"],
          state="present")

with play_on(pattern_hosts="server", roles=roles) as p:
    p.shell("nohup netperf &")

with play_on(pattern_hosts="client", roles=roles) as p:
    p.shell("flent rrul -p all_scaled "
            + "-l 60 "
            + "-H {{ hostvars[groups['server'][0]].inventory_hostname }} "
            + "-t 'bufferbloat test' "
            + "-o result.png")
    p.fetch(src="result.png",
            dest="result")
