from typing import List
import time
import threading
import random
import sys

from kafka import KafkaConsumer
from kafka import KafkaProducer

from project2.model.star import Star
from project2.model.ship import Ship
from project2.model.location import Location


class Coordinator:
    running: bool = True
    running_lock = threading.Condition()


class PhysicalShipThread:

    def __init__(self, ship: Ship, stars, producer: KafkaProducer, max_trips: int = 500,
                 delay_between_steps: float = 0.001, delay_between_trips: float = 1.5, **kwargs):
        super().__init__(**kwargs)

        self.ship = ship
        self.stars = stars
        self.producer = producer

        self.trip_number = 0
        self.max_trips = max_trips

        self.delay_between_steps = delay_between_steps
        self.delay_between_trips = delay_between_trips

        self.im_still_running = True

        self._thread = threading.Thread(target=self._process)
        self._thread.daemon = True

    def start_thread(self):
        self._thread.start()

    def _verify_running(self, text=None):
        if not Coordinator.running:
            Coordinator.running_lock.acquire()
            print("PhysicalShipThread.process({0}) pausing:".format(self.ship.name), text, flush=True)

            Coordinator.running_lock.wait()
            print("PhysicalShipThread.process({0}) resuming:".format(self.ship.name), text, flush=True)
            Coordinator.running_lock.release()

    def _process(self):

        while self.trip_number < self.max_trips:

            self._verify_running("between trips")

            self.trip_number += 1

            new_dest = None
            # choose a target star
            dest_is_selected = False
            while not dest_is_selected:
                new_dest = random.choice(self.stars)
                if new_dest.star_id != self.ship.docked_star.star_id:
                    print("\n{0}, dockId-{1} != newDestId-{2}, new loc ({3}, {4}, {5})".format(
                        self.ship.name, self.ship.docked_star.star_id, new_dest.star_id,
                        new_dest.location.x, new_dest.location.y, new_dest.location.z
                    ))
                    dest_is_selected = True

            print("\n{0}, selected new dest {1}, loc ({2}, {3}, {4})".format(
                self.ship.name, new_dest.name, new_dest.location.x, new_dest.location.y, new_dest.location.z
            ))

            self.ship.departure_star = self.ship.docked_star
            self.ship.destination_star = new_dest
            self.ship.docked_star = None

            #self.ship.velocity = Location(
            #    (self.ship.destination_star.location.x - self.ship.departure_star.location.x) / 400,
            #    (self.ship.destination_star.location.y - self.ship.departure_star.location.y) / 400,
            #    (self.ship.destination_star.location.z - self.ship.departure_star.location.z) / 400
            #)

            print("\n{0}, departing from {1} for {2} at location ({3}, {4}, {5}), velocity ({6}, {7}, {8})".format(
                self.ship.name, self.ship.departure_star.name, self.ship.destination_star.name,
                self.ship.destination_star.location.x, self.ship.destination_star.location.y, self.ship.destination_star.location.z,
                self.ship.velocity.x, self.ship.velocity.y, self.ship.velocity.z
            ), flush=True)

            while self.ship.docked_star is None:
                # iterate until we get there
                self._verify_running("between steps")

                # apply acceleration (flip to negative if we're past half way)


                #if self.ship.location.distance(self.ship.destination_star.location) < self.ship.location.distan


                self.ship.location = Location(
                    self.ship.location.x + self.ship.velocity.x,
                    self.ship.location.y + self.ship.velocity.y,
                    self.ship.location.z + self.ship.velocity.z
                )

                my_json = self.ship.to_json()
                # print("JSON", my_json)

                self.producer.send(topic_name, value=my_json.encode('utf-8'), headers=[("type", b'ship')])

                flush_and_repaint(self.producer)
                time.sleep(self.delay_between_steps)

            # you made it to the star, finalize the location just to make it tidy
            self.ship.docked_star = self.ship.destination_star
            self.ship.location = self.ship.docked_star.location.copy()
            self.ship.velocity = Location(0, 0, 0)

            self.ship.destination_star = None
            self.ship.departure_star = None

            my_json = self.ship.to_json()
            self.producer.send(topic_name, value=my_json.encode('utf-8'), headers=[("type", b'ship')])
            print("{0}, arrived at {1}".format(self.ship.name, self.ship.docked_star.name), flush=True)

            flush_and_repaint(producer)
            time.sleep(self.delay_between_trips)
        print("thread reached max number of trips, exiting")
        self.im_still_running = False


class ShipThread:

    def __init__(self, ship: Ship, stars, producer: KafkaProducer, trip_steps: int = 700, max_trips: int = 500,
                 delay_between_steps: float = 0.001, delay_between_trips: float = 1.5, **kwargs):
        super().__init__(**kwargs)

        self.ship = ship
        self.stars = stars
        self.producer = producer

        self.trip_number = 0
        self.max_trips = max_trips

        self.trip_steps = trip_steps
        self.step_delay = delay_between_steps
        self.delay_between_trips = delay_between_trips

        self.im_still_running = True

        self._thread = threading.Thread(target=self._process)
        self._thread.daemon = True

    def start_thread(self):
        self._thread.start()

    def _verify_running(self, text=None):
        if not Coordinator.running:
            Coordinator.running_lock.acquire()
            print("ShipThread.process({0}) pausing:".format(self.ship.name), text, flush=True)

            if self.ship.ship_id == 1:
                print("SHIP-1 pausing and dumping stars...")
                for star in self.stars:
                    print("\t{0} loc ({1}, {2}, {3})".format(star.star_id, star.location.x, star.location.y,
                                                             star.location.z))
                print("SHIP-1 done dumping.")

            Coordinator.running_lock.wait()
            print("ShipThread.process({0}) resuming:".format(self.ship.name), text, flush=True)
            Coordinator.running_lock.release()

    def _process(self):

        while self.trip_number < self.max_trips:

            self._verify_running("between trips")

            self.trip_number += 1

            new_dest = None
            # choose a target star
            dest_is_selected = False
            while not dest_is_selected:
                new_dest = random.choice(self.stars)
                if new_dest.star_id != self.ship.docked_star.star_id:
                    print("\n{0}, dockId-{1} != newDestId-{2}, new loc ({3}, {4}, {5})".format(
                        self.ship.name, self.ship.docked_star.star_id, new_dest.star_id,
                        new_dest.location.x, new_dest.location.y, new_dest.location.z
                    ))
                    dest_is_selected = True

            print("\n{0}, selected new dest {1}, loc ({2}, {3}, {4})".format(
                self.ship.name, new_dest.name, new_dest.location.x, new_dest.location.y, new_dest.location.z
            ))

            self.ship.departure_star = self.ship.docked_star
            self.ship.destination_star = new_dest
            self.ship.docked_star = None


            #print("Calculating velocity from {0} to {1}".format(
            #    self.ship.departure_star.name, self.ship.destination_star.name
            #    ), flush=True)
            #print("Location departure:", self.ship.departure_star.location.x, self.ship.departure_star.location.y,
            #      flush=True)
            #print("Location destinate:", self.ship.destination_star.location.x, self.ship.destination_star.location.y,
            #      flush=True)
            self.ship.velocity = Location(
                (self.ship.destination_star.location.x - self.ship.departure_star.location.x) / self.trip_steps,
                (self.ship.destination_star.location.y - self.ship.departure_star.location.y) / self.trip_steps,
                (self.ship.destination_star.location.z - self.ship.departure_star.location.z) / self.trip_steps
            )

            print("\n{0}, departing from {1} for {2} at location ({3}, {4}, {5}), velocity ({6}, {7}, {8})".format(
                self.ship.name, self.ship.departure_star.name, self.ship.destination_star.name,
                self.ship.destination_star.location.x, self.ship.destination_star.location.y, self.ship.destination_star.location.z,
                self.ship.velocity.x, self.ship.velocity.y, self.ship.velocity.z
            ), flush=True)

            for step_idx in range(self.trip_steps):
                self._verify_running("between steps")


                # self.ship.location.x = self.ship.location.x + self.ship.velocity.x
                # self.ship.location.y = self.ship.location.y + self.ship.velocity.y
                # self.ship.location.z = self.ship.location.z + self.ship.velocity.z
                self.ship.location = Location(
                    self.ship.location.x + self.ship.velocity.x,
                    self.ship.location.y + self.ship.velocity.y,
                    self.ship.location.z + self.ship.velocity.z
                )

                my_json = self.ship.to_json()
                # print("JSON", my_json)

                self.producer.send(topic_name, value=my_json.encode('utf-8'), headers=[("type", b'ship')])

                flush_and_repaint(self.producer)
                time.sleep(self.step_delay)

            # you made it to the star, finalize the location just to make it tidy
            self.ship.docked_star = self.ship.destination_star
            self.ship.location = self.ship.docked_star.location.copy()
            self.ship.velocity = Location(0, 0, 0)

            self.ship.destination_star = None
            self.ship.departure_star = None

            my_json = self.ship.to_json()
            self.producer.send(topic_name, value=my_json.encode('utf-8'), headers=[("type", b'ship')])
            print("{0}, arrived at {1}".format(self.ship.name, self.ship.docked_star.name), flush=True)

            flush_and_repaint(producer)
            time.sleep(self.delay_between_trips)
        print("thread reached max number of trips, exiting")
        self.im_still_running = False


def read_stdin_and_pause_threads():
    for line in sys.stdin:
        print("have stdin data, toggling state from current value =", Coordinator.running)
        Coordinator.running_lock.acquire()
        if Coordinator.running:
            print("stdin thread, setting running to false")
            Coordinator.running = False

        else:
            print("stdin thread, setting running to true and waking everybody up")
            Coordinator.running = True
            Coordinator.running_lock.notifyAll()
        Coordinator.running_lock.release()


def create_random_stars(num_stars, universe_size, minimum_distance) -> List[Star]:
    stars = []
    # print("starting create_random_stars")
    while len(stars) < num_stars:
        star_id = len(stars) + 1
        name = "Star-{0}".format(star_id)
        location = None

        attempt_count = 0
        max_attempts = 10000

        crowded = False
        found_safe_spot = False
        while attempt_count < max_attempts and not found_safe_spot:
            attempt_count += 1

            # print("iterating an attempt")
            location = Location(
                random.randint(-1 * universe_size[0], universe_size[0]),
                random.randint(-1 * universe_size[1], universe_size[1]),
                0
            )

            for star in stars:
                if star.location.distance(location) <= minimum_distance:
                    crowded = True
                    break

            if not crowded:
                print("found a safe spot, adding star {0} attempts={1}".format(name, attempt_count))
                found_safe_spot = True
                stars.append(Star(star_id, name, location))

        if not found_safe_spot:
            # we iterated until max_attempts and STILL didnt find a nice location
            print("Did NOT find a nice location after {1} attempts, returning the {0} stars I have".format(
                len(stars), attempt_count)
            )
            break

    return stars


def flush_and_repaint(producer):
    # j = '{"repaint": "true"}'
    # print("Producer sending JSON [{0}]".format(j))
    # producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'repaint')])
    #print("About to flush kafka producer", flush=True)
    producer.flush()
    #print("Done flushing kafka producer", flush=True)


if __name__ == "__main__":
    topic_name = "quickstart-events"
    # kafka_host = "172.18.110.6"
    kafka_host = "localhost"
    # kafka_host = "127.0.1.1"
    kafka_port = 9092
    producer = KafkaProducer(bootstrap_servers="{0}:{1}".format(kafka_host, kafka_port))

    star_count = 50
    ship_count = 100

    stdin_thread = threading.Thread(target=read_stdin_and_pause_threads)
    stdin_thread.daemon = True
    stdin_thread.start()

    my_stars = create_random_stars(star_count, (800000, 800000, 0), 40000)

    my_ships = []
    my_ship_threads = []

    for ship_idx in range(ship_count):
        my_ship = Ship(ship_idx + 1, "ShipThread-{0}".format(ship_idx+1), my_stars[ship_idx % len(my_stars)].location)
        my_ship.docked_star = my_stars[ship_idx % len(my_stars)]

        my_ships.append(my_ship)
        my_ship_threads.append(ShipThread(my_ship, my_stars, producer, trip_steps=200+50*ship_idx, max_trips=10000))
        # my_ship_threads.append(ShipThread(my_ship, my_stars, producer, max_trips=10000))

    for s in my_stars:
        j = s.to_json()
        print("Producer sending JSON [{0}]".format(j))
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'star')])

    for s in my_ships:
        j = s.to_json()
        print("Producer sending JSON [{0}]".format(j))
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])

    flush_and_repaint(producer)
    time.sleep(1)

    for st in my_ship_threads:
        st.start_thread()

    time_to_quit = False
    while not time_to_quit:
        time.sleep(0.1)

        time_to_quit = True
        for t in my_ship_threads:
            if t.im_still_running:
                time_to_quit = False
                break

    print("thread is done, i'm out")


if __name__ == "__main__3":

#    gummerton = Star(1, "Gummerton", Location(-600000, 100, 0))
#    new_gumbria = Star(2, "New Gumbria", Location(500000, -600000, 0))
#    gummi_glen = Star(3, "Gummi Glen", Location(300000, 300000, 0))
#    stars = [
#        gummerton,
#        new_gumbria,
#        gummi_glen
#    ]

    stars = create_random_stars(30, (700000, 700000, 0), 5000)
    num_ships = 3

    #gss_toadie = Ship(1, "GSS Toadie", Location(gummerton.location().x, gummerton.location().y, gummerton.location().z))
    gss_toadie = Ship(ship_id=1, name="GSS Toadie", location=stars[0].location.copy())
    gss_toadie.docked_star = stars[0]

    ships = [
        gss_toadie
    ]

    if len(stars) > 1:
        gss_dookie = Ship(ship_id=2, name="GSS Dookie", location=stars[1].location.copy())
        gss_dookie.docked_star = stars[1]
        ships.append(gss_dookie)

    if num_ships > 0:
        ships = []

        for i in range(num_ships):
            if i < len(stars):
                ship = Ship(i+1, "Ship-{0}".format(i+1), location=stars[i].location.copy())
                ship.docked_star = stars[i]
                ships.append(ship)

    topic_name = "quickstart-events"
    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    for s in stars:
        j = s.to_json()
        print("Producer sending JSON [{0}]".format(j))
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'star')])

    for s in ships:
        j = s.to_json()
        print("Producer sending JSON [{0}]".format(j))
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])

    #producer.flush()
    flush_and_repaint(producer)
    time.sleep(1)

    # toadie starts in gummerton, and is destined for new_gumbria
    steps = 1000
    delay = 0.0005

    trip_count = 0
    while trip_count < 1000:
        trip_count += 1

        for ship in ships:
            star_trg = None
            # choose a target star
            star_is_selected = False
            while not star_is_selected:
                star_trg = random.choice(stars)
                if star_trg.star_id != ship.docked_star.star_id:
                    star_is_selected = True

            ship.departure_star = ship.docked_star
            ship.destination_star = star_trg
            ship.docked_star = None

            print("\n{0}, departing for {1}".format(ship.name, ship.destination_star.name), flush=True)

            print("Calculating velocity from {0} to {1}".format(
                ship.departure_star.name, ship.destination_star.name
            ), flush=True)
            print("Location departure:", ship.departure_star.location.x, ship.departure_star.location.y, flush=True)
            print("Location destinate:", ship.destination_star.location.x, ship.destination_star.location.y, flush=True)

            ship.velocity.x = (ship.destination_star.location.x - ship.departure_star.location.x) / steps
            ship.velocity.y = (ship.destination_star.location.y - ship.departure_star.location.y) / steps
            ship.velocity.z = (ship.destination_star.location.z - ship.departure_star.location.z) / steps

            print("velocity = ({0}, {1}, {2})".format(ship.velocity.x, ship.velocity.y, ship.velocity.z), flush=True)

        print("\nAll ships have a destination, now we travel...", flush=True)

        for i in range(steps):
            for ship in ships:
                ship.location.x = ship.location.x + ship.velocity.x
                ship.location.y = ship.location.y + ship.velocity.y
                ship.location.z = ship.location.z + ship.velocity.z

                j = ship.to_json()

                print("JSON", j)

                producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])

            #print("All ships have new location and we flush...", flush=True)
            #producer.flush()
            flush_and_repaint(producer)
            #print("Done flushing.", flush=True)
            time.sleep(delay)
            #exit(1)

        # you made it to the star, finalize the location just to make it tidy
        for ship in ships:
            ship.docked_star = ship.destination_star
            ship.location = ship.docked_star.location.copy()

            ship.destination_star = None
            ship.departure_star = None

            j = ship.to_json()
            producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])
            print("{0}, arrived at {1}".format(ship.name, ship.docked_star.name), flush=True)

        print("all ships have arrived at their locations and we flush...", flush=True)
        #producer.flush()
        flush_and_repaint(producer)
        print("done flushing.", flush=True)
        time.sleep(2)

    print("exiting.")


if __name__ == "__main__2":
    print("Hello, World!")

    topic_name = "quickstart-events"
    consumer = KafkaConsumer(topic_name, bootstrap_servers="localhost:9092")
    for msg in consumer:
        print("Consumed Event [{0}]".format(msg))

        print("\tvalue [{0}]".format(msg.value))

        if msg.value.decode() == "exit":
            break

    print("Good bye, World!")
