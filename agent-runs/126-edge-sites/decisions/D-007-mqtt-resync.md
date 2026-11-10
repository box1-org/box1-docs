# D-007 MQTT session resync after the first connect

Camel's Paho consumers (`paho` and `paho-mqtt5`, Camel 4.22.1) connect before registering the message callback.
With a durable session the broker may push the backlog in that gap, and Paho leaves those messages unacknowledged
(manual acks) until the next reconnect. The gateway reconnects once per client after the route starts, with the
callback in place. A containers test (broker backlog after a reconnect) passes with and without the resync: the gap
did not occur against Artemis 2.42 in that run; the resync is kept as a safeguard. Review finding RF-3.
