from typing import List
import json

from project2.model.star import Star
from project2.model.star import Location
from project2.util.hc_observable import Observable


class Ship(Observable):
    """
    A Spaceship in space or docked at a star
    """
    def __init__(self, ship_id: int = 0, name: str = "", location: Location = Location(), empty_mass: float = 100000,
                 thrust: float = 100000, **kwargs):
        super().__init__(**kwargs)
        self.ship_id = ship_id
        self.name = name
        self.location = location

        self.empty_mass = empty_mass
        self.thrust = thrust

        self.docked_star: Star = None
        self.destination_star: Star = None
        self.departure_star: Star = None

        self.velocity: Location = Location()

        self.selected = False
        self.hovered = False



    @classmethod
    def from_dict(cls, d, stars: List[Star]) -> 'Ship':
        ship = Ship(d["ship_id"], d["name"], Location.from_dict(d["location"]))
        ship.velocity = Location.from_dict(d["velocity"])

        if d["docked_star"] is not None:
            for star in stars:
                if star.star_id == d["docked_star"]:
                    ship.docked_star = star
                    break

        if d["destination_star"] is not None:
            for star in stars:
                if star.star_id == d["destination_star"]:
                    ship.destination_star = star
                    break

        if d["departure_star"] is not None:
            for star in stars:
                if star.star_id == d["departure_star"]:
                    ship.departure_star = star
                    break

        return ship

    def to_json(self) -> str:
        x = self.__dict__.copy()
        x["location"] = self.location.__dict__.copy()
        x["velocity"] = self.velocity.__dict__.copy()

        if self.docked_star is not None:
            x["docked_star"] = self.docked_star.star_id

        if self.destination_star is not None:
            x["destination_star"] = self.destination_star.star_id

        if self.departure_star is not None:
            x["departure_star"] = self.departure_star.star_id

        # specifically remove the "bad" ones
        del x["_observers"]
        del x["_observable_lock"]
        del x["selected"]
        del x["hovered"]

        return json.dumps(x)

    def copy(self, ship: 'Ship'):
        self.ship_id = ship.ship_id
        self.name = ship.name
        self.location = ship.location.copy()
        self.velocity = ship.velocity.copy()

        self.docked_star = ship.docked_star
        self.destination_star = ship.destination_star
        self.departure_star = ship.departure_star
