from enoslib.service import Netem
from enoslib.api import discover_networks
from enoslib.infra.enos_vagrant.provider import Enos_vagrant
from enoslib.infra.enos_vagrant.configuration import Configuration

import logging
import os

logging.basicConfig(level=logging.INFO)

conf = Configuration()\
       .add_machine(roles=["control"],
                    flavour="tiny",
                    number=1)\
       .add_machine(roles=["compute"],
                    flavour="tiny",
                    number=1)\
        .add_network(roles=["mynetwork"],
                      cidr="192.168.42.0/24")\
       .finalize()

# claim the resources
provider = Enos_vagrant(conf)
roles, networks = provider.init()

# generate an inventory compatible with ansible
discover_networks(roles, networks)

tc = {
    "enable": True,
    "default_delay": "20ms",
    "default_rate": "1gbit",
}

netem = Netem(tc, roles=roles)
netem.deploy()
netem.validate()
netem.backup()
netem.destroy()

# destroy the boxes
provider.destroy()
