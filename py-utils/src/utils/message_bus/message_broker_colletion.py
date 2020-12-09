#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import errno
from collections import namedtuple
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.message_broker import MessageBroker

ConsumerRecord = namedtuple("ConsumerRecord", \
    ["message_type", "message", "partition", "offset", "key"])

class KafkaMessageBroker(MessageBroker):
    """ Kafka Server based message broker implementation """

    name = 'kafka'

    def __init__(self, broker_conf):
        """ Initialize Kafka based Configurations """
        super().__init__(broker_conf)

        kafka_conf = {'bootstrap.servers': self._servers}
        self._admin = AdminClient(kafka_conf)

        self._clients = {'producer': None, 'consumer': None}

    def init_client(self, **client_conf):
        """ Obtain Kafka based Producer/Consumer """

        """ Validate and return if client already exists """
        if client_type not in self._clients.keys():
            raise MessageBusError(errno.EINVAL, "Invalid client type %s",
                client_type)

        if self._clients[client_type] != None: return
    
        """ validate input config """
        for entry in ['client_id', 'method']:
            if entry not in client_conf.keys():
                raise MessageBusError(errno.EINVAL, "No entry for %s in conf", \
                    entry)

        kafka_conf = {}
        kafka_conf['bootstrap.servers'] = self.servers
        kafka_conf['client.id'] = client_conf['client_id']

        if client_type == 'producer':
            producer = Producer(**kafka_conf)
            self._clients[client_type] = producer

        else:
            for entry in ['offset', 'consumer_group', 'message_type']:
                if entry not in client_conf.keys():
                    raise MessageBusError(errno.EINVAL, "Missing conf entry %s", \
                        entry)
                         
            kafka_conf['auto.offset.reset'] = client_conf['offset']
            kafka_conf['group.id'] = client_conf['consumer_group']

            consumer = Consumer(**kafka_conf)
            consumer.subscribe(client_conf['message_type'])
            self._clients[client_type] = consumer

    def send(self, message_type: str, method: str, messages: list):
        """ Sends list of messages to Kafka cluster(s) """
        producer = self._clients['producer']
        if producer == None:
            raise MessageBusError(errno.EINVAL, "init_client is not called")

        for message in messages:
            producer.produce(message_type, bytes(message, 'utf-8'))
        if method == 'sync': producer.flush()

    def receive(self, timeout=0.5) -> list:
        """ Receives list of messages to Kafka cluster(s) """
        consumer = self._clients['consumer']
        if consumer == None:
            raise MessageBusError(errno.EINVAL, "init_client is not called")
        try:
            while True:
                msg = consumer.poll(timeout=timeout)
                if msg is None: continue
                if msg.error():
                    raise MessageBusError(errno.ECONN, "Cant receive. %s", \
                        msg.error())
                yield ConsumerRecord(msg.topic(), msg.value(), msg.partition(), msg.offset(), str(msg.key()))

        except KeyboardInterrupt:
            raise MessageBusError(errno.EINTR, "Aborted by user")

    def ack(self):
        """ To manually commit offset """
        consumer = self._clients['consumer']
        if consumer == None:
            raise MessageBusError(errno.EINVAL, "init_client is not called")
        consumer.commit()
        consumer.close()
