import json
import paho.mqtt.client as mqtt

from paho.mqtt.client import MQTTMessage
from typing import Callable

__all__ = [
    "MqttTopic"
]

class MqttTopic:
    def __init__(self, client:mqtt.Client, topicName:str, *args: str):
        self._name = topicName.replace('+', '%s') % (args)
        self._client = client

        # print("create topic %s" % (self._name))

    def subscribe(self, *on_payload_funcs: Callable[[object], None]):
        def on_message(client, userdata, message: MQTTMessage):
            payload:object = json.loads(str(message.payload, 'utf-8'))
            for on_payload in on_payload_funcs:
                if on_payload:
                    # print("  call %s at %s" % (on_payload, self._name))
                    on_payload(payload)

        self._client.subscribe(self._name)
        if on_payload_funcs:
            self._client.message_callback_add(self._name, on_message)
        return self

    def publish(self, obj:object=None):
        # print("# publish ", self._name, 'at', obj)
        self._client.publish(self._name, json.dumps(obj))
