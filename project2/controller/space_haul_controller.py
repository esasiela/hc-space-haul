from typing import List
import time
import threading
import json
from kafka import KafkaConsumer

from project2.model.star import Star
from project2.model.ship import Ship
from project2.model.location import Location

from project2.util.space_haul_config import SpaceHaulConfig
from project2.util.hc_observable import Observable


class SpaceHaulControllerEvent(object):
    def __init__(self, event_type: str = "", event_object: object = None):
        super().__init__()
        self.event_type = event_type
        self.event_object = event_object


class SpaceHaulController(Observable):
    """
    Main controller class for Space Haul
    """
    def __init__(self, config: SpaceHaulConfig = None, **kwargs):
        super().__init__(**kwargs)

        self.config = config

        self.lock = threading.Condition()

        self.stars: List[Star] = []
        self.ships: List[Ship] = []

        self._kafka_consumer = KafkaConsumer(
            self.config["kafka.topic"],
            bootstrap_servers=self.config["kafka.server"],
            value_deserializer=self._kafka_consumer_decoder
        )

        self._repaint_timing_thread = threading.Thread(target=self._repaint_timing_process)
        self._repaint_timing_thread.daemon = True
        self._repaint_timing_thread.start()

        self._kafka_consumer_thread = threading.Thread(target=self._kafka_consumer_process)
        self._kafka_consumer_thread.daemon = True
        self._kafka_consumer_thread.start()

        self.hovered_star: Star = None
        self.selected_star: Star = None

        self.hovered_ship: Ship = None
        self.selected_ship: Ship = None

    def set_hovered_ship(self, ship: Ship):
        # if currently hovering, make an unhover event
        if self.hovered_ship is not None:
            old_ship = self.hovered_ship
            old_ship.hovered = False

            self.hovered_ship = None
            self.notify_observers(SpaceHaulControllerEvent("ship-unhover", old_ship))

        # if incoming ship is not None, make a hover event
        if ship is not None:
            # we are hovering a ship now
            self.hovered_ship = ship
            self.hovered_ship.hovered = True
            self.notify_observers(SpaceHaulControllerEvent("ship-hover", self.hovered_ship))

    def set_hovered_star(self, star: Star):
        # if currently hovering, make an unhover event
        if self.hovered_star is not None:
            old_star = self.hovered_star
            old_star.hovered = False

            self.hovered_star = None
            self.notify_observers(SpaceHaulControllerEvent("star-unhover", old_star))

        # if incoming star is not None, make a hover event
        if star is not None:
            # we are hovering a star now
            self.hovered_star = star
            self.hovered_star.hovered = True
            self.notify_observers(SpaceHaulControllerEvent("star-hover", self.hovered_star))

    def set_selected_star(self, star: Star):
        # if we currently have a selected star, unselect him
        if self.selected_star is not None:
            old_star = self.selected_star
            old_star.selected = False

            self.selected_star = None
            self.notify_observers(SpaceHaulControllerEvent("star-unselect", old_star))

        # if incoming star is not None, make a select event
        if star is not None:
            # we have a selection now
            self.selected_star = star
            self.selected_star.selected = True
            self.notify_observers(SpaceHaulControllerEvent("star-select", self.selected_star))

    def set_selected_ship(self, ship: Ship):
        if self.selected_ship is not None:
            old_ship = self.selected_ship
            old_ship.selected = False
            self.selected_ship = None
            self.notify_observers(SpaceHaulControllerEvent("ship-unselect", old_ship))

        if ship is not None:
            self.selected_ship = ship
            self.selected_ship.selected = True
            self.notify_observers(SpaceHaulControllerEvent("ship-select", self.selected_ship))

    def universe_max_location(self) -> Location:
        """
        Returns the location of a point that creates a box with the origin and contains all objects
        :return:
        """
        max_loc = Location(0, 0, 0)
        for star in self.stars:
            if star.location.x > max_loc.x:
                max_loc.x = star.location.x

            if star.location.y > max_loc.y:
                max_loc.y = star.location.y

            if star.location.z > max_loc.z:
                max_loc.z = star.location.z

        # TODO iterate on ships for max location too (although I don't want to make ships go away from furthest star)

        return max_loc

    def log_kafka(self, text):
        #self._kafka_log.log(text)
        return

    def _repaint_timing_process(self):
        while True:
            self.notify_observers(SpaceHaulControllerEvent("repaint", Ship()))
            time.sleep(1/60)

    def _kafka_consumer_decoder(self, msg):
        try:
            value = json.loads(msg.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            print("CONSUMED EVENT: invalid json {0}".format(msg))
            value = None

        return value

    def _kafka_consumer_process(self):
        for msg in self._kafka_consumer:
            if msg.value is not None:
                self.lock.acquire()

                #print("CONSUMED EVENT: {0}".format(msg))
                #self.log_kafka("CONSUMED EVENT: {0}".format(msg))

                found_type_header = False
                for key, value in msg.headers:
                    if key == "type":
                        found_type_header = True

                        # delegate processing to the kafka event handler function
                        event_handler_name = "_kafka_event_{0}".format(value.decode('utf-8'))
                        if hasattr(self, event_handler_name) and callable(
                                event_handler_func := getattr(self, event_handler_name)
                        ):
                            event_handler_func(msg)
                        else:
                            self.log_kafka("No handler for kafka event [{0}]".format(event_handler_name))

                if not found_type_header:
                    self.log_kafka("Kafka event has no 'type' header, ignoring.")

                self.lock.release()
            else:
                self.log_kafka("Kafka event has no 'value', ignoring.")

    def _kafka_event_star(self, msg):
        self.log_kafka("KAFKA EVENT [STAR]")

        incoming_star = Star.from_dict(msg.value)

        # if we have the star, update it, else create it
        found_star = False

        for star in self.stars:
            self.log_kafka("have a star")
            if star.star_id == incoming_star.star_id:
                found_star = True
                self.log_kafka("we already have this star, do update")
                star.copy(incoming_star)
                self.notify_observers(SpaceHaulControllerEvent("star-change", star))

        if not found_star:
            # add it
            self.log_kafka("did not find star, add it")
            self.stars.append(incoming_star)
            self.notify_observers(SpaceHaulControllerEvent("star-add", incoming_star))

    def _kafka_event_ship(self, msg):
        self.log_kafka("KAFKA EVENT [SHIP]")

        incoming_ship = Ship.from_dict(msg.value, self.stars)

        # if we have the ship, update it, else create it
        found_ship = False

        for ship in self.ships:
            if ship.ship_id == incoming_ship.ship_id:
                found_ship = True
                self.log_kafka("we already have this ship, do update")
                ship.copy(incoming_ship)
                self.notify_observers(SpaceHaulControllerEvent("ship-change", ship))

        if not found_ship:
            # add it
            self.log_kafka("did not find ship, add it")
            self.ships.append(incoming_ship)
            self.notify_observers(SpaceHaulControllerEvent("ship-add", incoming_ship))

    def _kafka_event_repaint(self, msg):
        self.log_kafka("KAFKA EVENT [REPAINT]")
        self.notify_observers(SpaceHaulControllerEvent("repaint", Ship()))
