import json
import functools


__all__ = [
    "MqttTopic"
]


class MqttTopic:
    @classmethod
    @functools.lru_cache()
    def name(clazz, topicName, *args):
        if not args:
            return topicName
        return topicName.replace('+', '%s') % (args)

    def __init__(self, client, name, *args):
        self._client = client
        self._name = MqttTopic.name(name, *args)
        self.functions = set()

    def subscribe(self, on_payload_func):
        def on_message(client, userdata, message):
            payload = json.loads(str(message.payload, 'utf-8'))
            for on_payload in self.functions:
                # print("  call %s at %s" % (on_payload, self._name))
                on_payload(payload)

        if not self.functions:
            self._client.subscribe(self._name)
            self._client.message_callback_add(self._name, on_message)

        if on_payload_func not in self.functions:
            self.functions.add(on_payload_func)

    def publish(self, obj=None):
        # print("# publish ", self._name, 'at', obj)
        self._client.publish(self._name, json.dumps(obj))
