"""
Module for simulating a dynamic number of different MQTT clients, i.e. sensors and actuators.
Each client is run in its own thread.
"""

# pylint: disable=too-many-arguments, unused-argument

from abc import abstractmethod
import json
import logging
import random
import threading
import time
import uuid
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import paho.mqtt.client as mqtt

logger = logging.getLogger('mqtt_simulation')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel("DEBUG")
ch.setLevel("DEBUG")


def get_next_random(lower: int, upper: int) -> float:
    """
    Function for getting a new random number with 'lower' and 'upper'
    with two-digit precision.
    """
    return round(random.uniform(lower, upper), 2)


class MQTTClient():
    """
    Abstract class for MQTT-based clients.
    Handles basic callbacks, logging, and instantiation of paho.mqtt.client
    """
    broker_url = "192.168.21.105"
    broker_port = 1883
    main_topic = "mind2"

    @abstractmethod
    def __init__(self, topic: str, enable_detailed_logger=False):
        self.name = topic
        self.client = mqtt.Client(client_id=self.name, protocol=mqtt.MQTTv5)
        self.topic = f"{self.main_topic}/{topic}"
        self.client.on_connect = self.__on_connect
        self.client.on_disconnect = self.__on_disconnect
        self.client.on_publish = self.__on_publish
        self.client.on_subscribe = self.__on_subscribe
        self.client.on_unsubscribe = self.__on_unsubscribe
        self.client.on_message = self.__on_message

        if enable_detailed_logger:
            self.client.enable_logger(logger)

    def connect(self):
        """
        Helper function to connect to the MQTT-broker using paho.mqtt.client
        """
        self.client.connect(self.broker_url, self.broker_port, keepalive=60)

    def publish(self, payload: str, correlation_data: None or str = None):
        """
        Helper function to publish a message to a topic of the MQTT-broker using paho.mqtt.client
        """
        properties = Properties(PacketTypes.PUBLISH)
        properties.CorrelationData = bytes(str(uuid.uuid1()), "utf-8") if not correlation_data else correlation_data
        self.client.publish(self.topic, qos=2, payload=payload, properties=properties, retain=False)

    def subscribe(self, topic):
        """
        Helper function to subscribe to a topic of the MQTT-broker using paho.mqtt.client
        """
        self.client.subscribe(topic, qos=2, options=None, properties=None)

    def __on_publish(self, client, userdata, mid):
        logger.info("%s published (Mid: %s)", self.name, mid)

    def __on_connect(self, client, userdata, flags, response_code, properties):
        if response_code == 0:
            logger.info("\033[0;36m %s connected to %s:%s \033[0m", self.name, self.broker_url, self.broker_port)
        else:
            logger.warning("Failed to connect, return code %d\n", response_code)

    def __on_disconnect(self, client, userdata, flags, response_code):
        logger.info("\033[0;36m %s disconnected from %s:%s \033[0m", self.name, self.broker_url, self.broker_port)

    def __on_subscribe(self, client, userdata, mid, granted_qos, properties):
        logger.info("%s subscribed '%s' with QoS %s (mid=%s)", self.name, self.topic, granted_qos[0], mid)

    def __on_unsubscribe(self, client, userdata, mid, granted_qos, properties):
        logger.info("%s unsubscribed from '%s'", self.name, self.topic)

    def __on_message(self, client, userdata, message):
        logger.info("%s received message: %s", self.name, message.payload.decode('utf-8'))


class MQTTSensor(MQTTClient):
    """
    Abstract class for a simple MQTT-based sensor based on the abstract MQTTClient class.
    The sensor publishes simulated status updates to a topic named after the sensor itself.
    """
    @abstractmethod
    def __init__(self, client_name: str, simulation):
        super().__init__(client_name)
        self.connect()
        self.client.loop_start()
        self.__tick = simulation

    def loop(self):
        """
        Function to keep the sensor alive within its independent thread.
        """
        while SIMULATION_ALIVE:
            self.__tick()
        self.client.disconnect()


class TemperatureSensor(MQTTSensor):
    """
    Object simulating an MQTT-based temperature sensor.
    """
    def __init__(self, sensor_name: str):
        super().__init__(sensor_name, self.__simulation)

    def __simulation(self):
        message = {
            "temperature": get_next_random(18, 26),
            "humidity": get_next_random(40, 90),
            "battery": get_next_random(89, 92),
            "linkquality": get_next_random(50, 255)}
        self.publish(payload=json.dumps(message))
        time.sleep(random.randint(10, 15))


class MotionSensor(MQTTSensor):
    """
    Object simulating an MQTT-based motion sensor.
    """
    def __init__(self, sensor_name: str):
        super().__init__(sensor_name, self.__simulation)

    def __simulation(self):
        decision = [True, False, False, False, False, False, False, False]
        message = {
            "on": True,
            "alert": decision[random.randint(0, len(decision)-1)],
            "battery": get_next_random(89, 92),
            "linkquality": get_next_random(50, 255)}
        self.publish(payload=json.dumps(message))
        time.sleep(random.randint(30, 60))


class WindowSensor(MQTTSensor):
    """
    Object simulating an MQTT-based window sensor.
    """
    def __init__(self, sensor_name: str):
        super().__init__(sensor_name, self.__simulation)

    def __simulation(self):
        decision = [True, False, False, False, False, False, False, False]
        message = {
            "open": decision[random.randint(0, len(decision)-1)],
            "battery": get_next_random(89, 92),
            "linkquality": get_next_random(50, 255)}
        self.publish(payload=json.dumps(message))
        time.sleep(random.randint(100, 200))


class DoorSensor(MQTTSensor):
    """
    Object simulating an MQTT-based door-opening sensor.
    """
    def __init__(self, sensor_name: str):
        super().__init__(sensor_name, self.__simulation)

    def __simulation(self):
        decision = [True, False, False, False, False, False, False, False]
        message = {
            "open": decision[random.randint(0, len(decision)-1)],
            "battery": get_next_random(89, 92),
            "linkquality": get_next_random(50, 255)}
        self.publish(payload=json.dumps(message))
        time.sleep(random.randint(100, 200))


class SmokeDetector(MQTTSensor):
    """
    Object simulating an MQTT-based smoke detector.
    """
    def __init__(self, sensor_name: str):
        super().__init__(sensor_name, self.__simulation)

    def __simulation(self):
        decision = [True, False, False, False, False, False, False, False, False, False, False]
        message = {
            "on": True,
            "alert": decision[random.randint(0, len(decision)-1)],
            "battery": get_next_random(89, 92),
            "linkquality": get_next_random(50, 255)}
        self.publish(payload=json.dumps(message))
        time.sleep(random.randint(100, 200))


class MQTTActuator(MQTTClient):
    """
    Abstract class for a simple MQTT-based actuator based on the abstract MQTTClient class.
    The actuator subscribes to a topic in the format 'actuator_name/toggleState' and
    simulate a reaction based on the messages posted in this topic. The reactions are published
    in the topic named after the actuator itself.
    """

    @abstractmethod
    def __init__(self, client_name: str, simulation):
        super().__init__(client_name)
        self.client.on_connect = self.__on_connect
        self.simulation = simulation
        self.client.on_message = self.__on_message
        self.connect()
        self.client.loop_start()

    def __on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info("\033[0;36m %s connected to %s:%s \033[0m", self.name, self.broker_url, self.broker_port)
            self.subscribe(f"{self.topic}/toggleState")
        else:
            logger.warning("Failed to connect, return code %d\n", rc)

    def __on_message(self, client, userdata, message):
        time.sleep(random.randint(1, 10)/1000)
        in_message = json.loads(message.payload.decode("utf-8"))
        logger.info("%s received message %s", self.name, in_message)
        out_message = self.simulation(in_message)
        out_message["battery"] = get_next_random(89, 92)
        out_message["linkquality"] = get_next_random(50, 255)
        self.publish(json.dumps(out_message), message.properties.CorrelationData)

    def loop(self):
        """
        Function for keeping the actuator alive within independent thread.
        """
        while SIMULATION_ALIVE:
            time.sleep(0.1)
        self.client.unsubscribe(self.topic)
        self.client.disconnect()


class DoorActuator(MQTTActuator):
    """
    Object simulating an MQTT-based door.
    """
    def __init__(self, actuator_name: str):
        super().__init__(actuator_name, self.__simulation)

    def __simulation(self, message):
        out_message = {"open": True}
        out_message["open"] = message["open"]
        return out_message


class Thermostat(MQTTActuator):
    """
    Object simulating an MQTT-based thermostat.
    """
    def __init__(self, actuator_name: str):
        super().__init__(actuator_name, self.__simulation)

    def __simulation(self, message):
        out_message = {"active": True, "state": 0}
        out_message["active"] = message["active"]
        if out_message["active"]:
            out_message["state"] = message["state"]
        return out_message


class FireAlarm(MQTTActuator):
    """
    Object simulating an MQTT-based fire alarm.
    """
    def __init__(self, actuator_name: str):
        super().__init__(actuator_name, self.__simulation)

    def __simulation(self, message):
        out_message = {"alert": True}
        out_message["alert"] = message["alert"]
        return out_message


class Shutter(MQTTActuator):
    """
    Object simulating an MQTT-based shutter.
    """
    def __init__(self, actuator_name: str):
        super().__init__(actuator_name, self.__simulation)

    def __simulation(self, message):
        out_message = {"active": True, "percentage": 0}
        out_message["active"] = message["active"]
        if out_message["active"]:
            out_message["percentage"] = message["percentage"]
        return out_message


class LedBulb(MQTTActuator):
    """
    Object simulating an MQTT-based led lightbulb.
    """
    def __init__(self, actuator_name: str):
        super().__init__(actuator_name, self.__simulation)

    def __simulation(self, message):
        out_message = {"on": True}
        out_message["on"] = message["on"]
        return out_message


if __name__ == "__main__":
    SIMULATION_ALIVE = True

    temperature_sensors = ["livingroom", "kitchen", "bathroom", "garage", "garden1", "garden2", "garden3"]
    motion_sensors = ["livingroom", "kitchen", "bathroom", "garage", "garden1", "garden2", "garden3"]
    window_sensors = ["livingroom1", "livingroom2", "livingroom3", "bathroom1", "kitchen1", "kitchen2", "garage"]
    door_sensors = ["main", "garage"]
    smoke_detectors = ["livingroom", "kitchen", "bathroom", "garage"]
    SENSORS_COUNT = len(temperature_sensors) + len(motion_sensors) + len(window_sensors) + len(door_sensors) + len(smoke_detectors)

    led_actuators = ["livingroom1", "livingroom2", "kitchen1", "kitchen2", "bathroom", "garden1", "garden2", "garage"]
    firealarm_actuators = ["livingroom", "kitchen", "bathroom", "garage"]
    shutter_actuators = ["livingroom1", "livingroom2", "livingroom3", "bathroom1", "kitchen1", "kitchen2", "garage"]
    door_actuators = ["livingroom", "kitchen", "bathroom", "garage"]
    thermostat_actuators = ["livingroom1", "livingroom2", "livingroom3", "bathroom", "kitchen1", "kitchen2", "garage"]
    ACTUATORS_COUNT = len(led_actuators) + len(firealarm_actuators) + len(shutter_actuators) + len(door_actuators) + len(thermostat_actuators)

    logger.info("Starting simulation with %d sensors and %d actuators...", SENSORS_COUNT, ACTUATORS_COUNT)

    for sensor in temperature_sensors:
        name = f"{sensor}-sensor-temperature"
        threading.Thread(name=name, target=TemperatureSensor(name).loop).start()

    for sensor in motion_sensors:
        name = f"{sensor}-sensor-motion"
        threading.Thread(name=name, target=MotionSensor(name).loop).start()

    for sensor in window_sensors:
        name = f"{sensor}-sensor-window"
        threading.Thread(name=name, target=WindowSensor(name).loop).start()

    for sensor in door_sensors:
        name = f"{sensor}-sensor-door"
        threading.Thread(name=name, target=DoorSensor(name).loop).start()

    for sensor in smoke_detectors:
        name = f"{sensor}-sensor-smokedetector"
        threading.Thread(name=name, target=SmokeDetector(name).loop).start()

    for actuator in led_actuators:
        name = f"{actuator}-actuator-led"
        threading.Thread(name=name, target=LedBulb(name).loop).start()

    for actuator in firealarm_actuators:
        name = f"{actuator}-actuator-firealarm"
        threading.Thread(name=name, target=FireAlarm(name).loop).start()

    for actuator in shutter_actuators:
        name = f"{actuator}-actuator-shutter"
        threading.Thread(name=name, target=Shutter(name).loop).start()

    for actuator in door_actuators:
        name = f"{actuator}-actuator-door"
        threading.Thread(name=name, target=DoorActuator(name).loop).start()

    for actuator in thermostat_actuators:
        name = f"{actuator}-actuator-thermostat"
        threading.Thread(name=name, target=Thermostat(name).loop).start()

    while SIMULATION_ALIVE:
        try:
            time.sleep(.1)
        except KeyboardInterrupt:
            SIMULATION_ALIVE = False

    logger.info("Unsubscribing and disconnecting clients. This may take a while...")
