from enoslib.api import discover_networks
from enoslib.service.monitoring import Monitoring
from enoslib.infra.enos_static.provider import Static
from enoslib.infra.enos_static.configuration import Configuration

import os

# Dummy functionnal test running inside a docker container

provider_conf = {
    "resources": {
        "machines": [
            {
                "roles": ["control"],
                "address": "localhost",
                "alias": "test_machine",
                "extra": {"ansible_connection": "local"},
            }
        ],
        "networks": [
            {
                "roles": ["local"],
                "start": "172.17.0.0",
                "end": "172.17.255.255",
                "cidr": "172.17.0.0/16",
                "gateway": "172.17.0.1",
                "dns": "172.17.0.1",
            }
        ],
    }
}

inventory = os.path.join(os.getcwd(), "hosts")
conf = Configuration.from_dictionnary(provider_conf)
provider = Static(conf)

roles, networks = provider.init()
discover_networks(roles, networks)

m = Monitoring(collector=roles["control"],
               agent=roles["control"],
               ui=roles["control"])
m.deploy()
