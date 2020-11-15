import threading
import json
from kafka import KafkaConsumer

from project.model.star import Star, StarList
from project.model.ship import Ship, ShipList
from project.model.location import Location
from project.util.hc_observable import Observable


class SpaceHaulControllerEvent(object):
    def __init__(self, event_type: str = "", o: object = None):
        super().__init__()
        self.event_type = event_type
        self.o = o


class SpaceHaulController(Observable):
    """
    Main controller class for Space Haul
    """
    def __init__(self, kafka_log=None, **kwargs):
        super().__init__(**kwargs)

        self._star_list = StarList()
        self._ship_list = ShipList()

        self._kafka_log = kafka_log

        self._kafka_consumer = KafkaConsumer(
            "quickstart-events",
            bootstrap_servers="localhost:9092",
            value_deserializer=self._kafka_consumer_decoder
        )

        self._kafka_consumer_thread = threading.Thread(target=self._kafka_consumer_process)
        self._kafka_consumer_thread.daemon = True
        self._kafka_consumer_thread.start()

        self._hovered_star = None
        self._selected_star = None

        self._hovered_ship = None
        self._selected_ship = None

    def hovered_ship(self):
        return self._hovered_ship

    def set_hovered_ship(self, ship: Ship):
        # if currently hovering, make an unhover event
        if self._hovered_ship is not None:
            self._hovered_ship.set_hovered(False)
            old_ship = self._hovered_ship
            self._hovered_ship = None
            self.notify_observers(SpaceHaulControllerEvent("unhover", old_ship))

        # if incoming ship is not None, make a hover event
        if ship is not None:
            # we are hovering a ship now
            self._hovered_ship = ship
            self._hovered_ship.set_hovered(True)
            self.notify_observers(SpaceHaulControllerEvent("hover", self._hovered_ship))

    def selected_ship(self):
        return self._selected_ship

    def set_selected_ship(self, ship: Ship):
        # if currently selected, make an unselect event
        if self._selected_ship is not None:
            self._selected_ship.set_selected(False)
            old_ship = self._selected_ship
            self._selected_ship = None
            self.notify_observers(SpaceHaulControllerEvent("unselect", old_ship))

        # if incoming ship is not None, make a select event
        if ship is not None:
            # we are selecting a ship now
            self._selected_ship = ship
            self._selected_ship.set_selected(True)
            self.notify_observers(SpaceHaulControllerEvent("select", self._selected_ship))

    def hovered_star(self):
        return self._hovered_star

    def set_hovered_star(self, star: Star):
        # if currently hovering, make an unhover event
        if self._hovered_star is not None:
            self._hovered_star.set_hovered(False)
            old_star = self._hovered_star
            self._hovered_star = None
            self.notify_observers(SpaceHaulControllerEvent("unhover", old_star))

        # if incoming star is not None, make a hover event
        if star is not None:
            # we are hovering a star now
            self._hovered_star = star
            self._hovered_star.set_hovered(True)
            self.notify_observers(SpaceHaulControllerEvent("hover", self._hovered_star))

    def selected_star(self):
        return self._selected_star

    def set_selected_star(self, star: Star):
        # copy the data, dont's just overlay the whole object, so ppl watching will get notice
        self._selected_star.update_from_star(star)

    def star_list(self) -> StarList:
        return self._star_list

    def stars(self) -> [Star]:
        return self._star_list.stars()

    def ship_list(self) -> ShipList:
        return self._ship_list

    def ships(self) -> [Ship]:
        return self._ship_list.ships()

    def universe_max_locationZZZ(self):
        """
        Returns the location of a point that creates a box with the origin and contains all objects
        :return:
        """
        max_loc = Location(0, 0, 0)
        for star in self.star_list():
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
                self.log_kafka("CONSUMED EVENT: {0}".format(msg))

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
            else:
                self.log_kafka("Kafka event has no 'value', ignoring.")

    def _kafka_event_star(self, msg):
        self.log_kafka("KAFKA EVENT [STAR]")

        incoming_star = Star.from_dict(msg.value)

        # if we have the star, update it, else create it
        found_star = False

        for star in self.stars():
            self.log_kafka("have a star")
            if star.star_id() == incoming_star.star_id():
                found_star = True
                self.log_kafka("we already have this star, do update")
                star.update_from_star(incoming_star)

        if not found_star:
            # add it
            self.log_kafka("did not find star, add it")
            self.star_list().add_star(incoming_star)

    def _kafka_event_ship(self, msg):
        self.log_kafka("KAFKA EVENT [SHIP]")

        incoming_ship = Ship.from_dict(msg.value, self.star_list())

        # if we have the ship, update it, else create it
        found_ship = False

        for ship in self.ships():
            if ship.ship_id() == incoming_ship.ship_id():
                found_ship = True
                self.log_kafka("we already have this ship, do update")
                ship.update_from_ship(incoming_ship)

        if not found_ship:
            # add it
            self.log_kafka("did not find ship, add it")
            self.ship_list().add_ship(incoming_ship)
