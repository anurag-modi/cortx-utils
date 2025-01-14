#!/bin/env python3

# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import traceback

from cortx.utils.conf_store import Conf

from . import kafka_states


class KafkaSetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" %(self._rc, self._desc,
            traceback.format_exc())

    @property
    def rc(self):
        return self._rc


class Kafka:
    """ Represents Kafka and Performs setup related actions """
    index = "kafka"

    def __init__(self, conf_url, index=None):
        self.conf_url = conf_url
        if index:
            self.index = index
        Conf.load(self.index, conf_url)

    def _conf_get(self, key):
        return Conf.get(self.index, key)

    def validate(self, phase: str):
        """ Perform validtions. Raises exceptions if validation fails """

        # Perform RPM validations
        return

    def post_install(self):
        """ Performs post install operations. Raises exception on error """

        # TODO check either arbitrary JSON can be expected here
        #      or we need to use some already defined keys in ConfStore
        nodes = self._conf_get('nodes')
        kafka_params = self._conf_get('kafka')

        kafka_servers = [
            sparams['hostname'] for server, sparams in nodes.items()
            if server in kafka_params['servers']
        ]
        kafka_version = kafka_params['version']

        curr_node_hostname = nodes[self._conf_get('machine_id')]['hostname']

        # TODO is it expected case for clients ???
        try:
            kafka_broker_id = str(kafka_servers.index(curr_node_hostname))
        except ValueError:
            # current node is not in kafka servers list
            kafka_broker_id = None

        kafka_states.set_zookeeper_properties(
            kafka_version, kafka_servers
        )

        if kafka_broker_id:
            kafka_states.set_zookeeper_myid(kafka_broker_id)

            kafka_states.set_server_properties(
                kafka_version, kafka_servers, kafka_broker_id
            )

        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def test(self, plan):
        """ Perform configuration testing. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def reset(self):
        """ Performs Configuraiton reset. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0
