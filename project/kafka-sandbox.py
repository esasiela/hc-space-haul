from typing import List
import time
import random

from kafka import KafkaConsumer
from kafka import KafkaProducer

from project.model.star import Star
from project.model.ship import Ship
from project.model.location import Location


def create_random_stars(num_stars, universe_size, minimum_distance) -> List[Star]:
    stars = []
    print("starting create_random_stars")
    while len(stars) < num_stars:
        star_id = len(stars) + 1
        name = "Star-{0}".format(star_id)
        location = None

        attempt_count = 0
        max_attempts = 1000

        found_safe_spot = False
        while attempt_count < max_attempts and not found_safe_spot:
            print("iterating an attempt")
            location = Location(
                random.randint(-1 * universe_size[0], universe_size[0]),
                random.randint(-1 * universe_size[1], universe_size[1]),
                0
            )

            for star in stars:
                if Location.distance(location, star.location()) <= minimum_distance:
                    break

            # if we made it here, we found a safe spot
            print("setting found_safe_spot to True")
            found_safe_spot = True

        if found_safe_spot:
            print("found safe spot, adding star to list")
            stars.append(Star(star_id, name, location))
        else:
            # we iterated until max_attempts and STILL didnt find a nice location
            print("Iterated {0} times and did NOT find a nice location, returning the stars I have".format(len(stars)))
            break


    print("ending create_random_stars {0}".format(len(stars)))
    return stars


if __name__ == "__main__":
    print("Publishing a star to kafka...")

    gummerton = Star(1, "Gummerton", Location(-600000, 100, 0))
    new_gumbria = Star(2, "New Gumbria", Location(500000, -600000, 0))
    gummi_glen = Star(3, "Gummi Glen", Location(300000, 300000, 0))
    stars = [
        gummerton,
        new_gumbria,
        gummi_glen
    ]

    gss_toadie = Ship(1, "GSS Toadie", Location(gummerton.location().x, gummerton.location().y, gummerton.location().z))
    print("first gss_toadie.location()", gss_toadie.location())
    ships = [
        gss_toadie
    ]

    stars = create_random_stars(2, (700000, 700000, 0), 100000)
    gss_toadie.set_location(stars[0].location())

    topic_name = "quickstart-events"
    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    for s in stars:
        j = s.to_json()
        print("Producer sending JSON [{0}]".format(j))
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'star')])

    star_src = stars[0]
    gss_toadie.set_docked_star(star_src)

    for s in ships:
        j = s.to_json()
        print("Producer sending JSON [{0}]".format(j))
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])

    producer.flush()

    time.sleep(1)

    # toadie starts in gummerton, and is destined for new_gumbria
    steps = 1000
    delay = 0.01

    star_src = stars[0]

    gss_toadie.set_docked_star(star_src)

    trip_count = 0
    while trip_count < 1000:
        trip_count += 1

        # choose a target star
        star_is_selected = False
        while not star_is_selected:
            star_trg = random.choice(stars)
            if star_trg.star_id() != star_src.star_id():
                star_is_selected = True

        print("Departing for:", star_trg.name())

        gss_toadie.set_departure_star(gss_toadie.docked_star())
        gss_toadie.set_destination_star(star_trg)
        gss_toadie.set_docked_star(None)

        velocity = (
            (star_trg.location().x - star_src.location().x) / steps,
            (star_trg.location().y - star_src.location().y) / steps,
            (star_trg.location().z - star_src.location().z) / steps
        )

        for i in range(steps):
            # print("gss_toadie.location()", gss_toadie.location())
            gss_toadie.location().x = gss_toadie.location().x + velocity[0]
            gss_toadie.location().y = gss_toadie.location().y + velocity[1]
            j = gss_toadie.to_json()
            producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])
            producer.flush()
            time.sleep(delay)

        # you made it to the star, finalize the location just to make it tidy
        gss_toadie.location().x = star_trg.location().x
        gss_toadie.location().y = star_trg.location().y
        gss_toadie.location().z = star_trg.location().z

        gss_toadie.set_docked_star(star_trg)
        gss_toadie.set_destination_star(None)
        gss_toadie.set_departure_star(None)

        j = gss_toadie.to_json()
        producer.send(topic_name, value=j.encode('utf-8'), headers=[("type", b'ship')])
        producer.flush()

        print("Arrived at destination:", star_trg.name())
        star_src = star_trg

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
