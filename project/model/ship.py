import json

from project.model.star import Star, StarList
from project.model.location import Location
from project.util.hc_observable import Observable


class Ship(Observable):
    """
    A Spaceship in space or at a star
    """
    def __init__(self, ship_id: int, name: str, location: Location, **kwargs):
        super().__init__(**kwargs)
        self._ship_id = ship_id
        self._name = name
        self._location = location

        self._destination_star = None
        self._departure_star = None
        self._docked_star = None

        self._selected = False
        self._hovered = False

    @classmethod
    def from_dict(cls, d, star_list: StarList):
        s = Ship(d["_ship_id"], d["_name"], Location.from_dict(d["_location"]))

        if d["_docked_star"] is not None:
            # find the star in the StarList by ID
            for star in star_list.stars():
                if star.star_id() == d["_docked_star"]:
                    s.set_docked_star(star)

        if d["_destination_star"] is not None:
            # find the star in the StarList by ID
            for star in star_list.stars():
                if star.star_id() == d["_destination_star"]:
                    s.set_destination_star(star)

        if d["_departure_star"] is not None:
            # find the star in the StarList by ID
            for star in star_list.stars():
                if star.star_id() == d["_departure_star"]:
                    s.set_departure_star(star)

        return s

    def to_json(self) -> str:
        x = self.__dict__.copy()
        x["_location"] = self.location().__dict__.copy()

        if self.docked_star() is not None:
            x["_docked_star"] = self.docked_star().star_id()

        if self.destination_star() is not None:
            x["_destination_star"] = self.destination_star().star_id()

        if self.departure_star() is not None:
            x["_departure_star"] = self.departure_star().star_id()

        # specifically remove the "bad" ones
        del x["_observers"]
        del x["_observable_lock"]
        del x["_selected"]
        del x["_hovered"]

        return json.dumps(x)

    def update_from_ship(self, s: 'Ship'):
        # YES, update the ID.  If its a kafka update, it'll stay the same, but if its hovered/selected it'll update
        if s is None:
            self._ship_id = -1
            self._name = ""
            self._location = Location(0, 0, 0)
            self._docked_star = None
            self._departure_star = None
            self._destination_star = None
        else:
            self._ship_id = s.ship_id()
            self._name = s.name()
            self._location = s.location()

            if s.docked_star() is not None and (
                self.docked_star() is None or
                s.docked_star().star_id() != self.docked_star().star_id()
            ):
                self.set_docked_star(s.docked_star())
            else:
                self.set_docked_star(None)

            if s.destination_star() is not None and (
                self.destination_star() is None or
                s.destination_star().star_id() != self.destination_star().star_id()
            ):
                self.set_destination_star(s.destination_star())
            else:
                self.set_destination_star(None)

            if s.departure_star() is not None and (
                self.departure_star() is None or
                s.departure_star().star_id() != self.departure_star().star_id()
            ):
                self.set_departure_star(s.departure_star())
            else:
                self.set_departure_star(None)

        self.notify_observers()

    def ship_id(self) -> int:
        return self._ship_id

    def set_ship_id(self, ship_id: int):
        self._ship_id = ship_id
        self.notify_observers()

    def name(self) -> str:
        return self._name

    def set_name(self, name: str):
        self._name = name
        self.notify_observers()

    def location(self) -> Location:
        return self._location

    def set_location(self, location: Location):
        self._location = location
        self.notify_observers()

    def set_selected(self, selected: bool):
        self._selected = selected
        self.notify_observers()

    def is_selected(self) -> bool:
        return self._selected

    def set_hovered(self, hovered: bool):
        self._hovered = hovered
        self.notify_observers()

    def is_hovered(self) -> bool:
        return self._hovered

    def destination_star(self) -> Star:
        return self._destination_star

    def set_destination_star(self, star: Star):
        self._destination_star = star
        self.notify_observers()

    def departure_star(self) -> Star:
        return self._departure_star

    def set_departure_star(self, star: Star):
        self._departure_star = star
        self.notify_observers()

    def docked_star(self) -> Star:
        return self._docked_star

    def set_docked_star(self, star: Star):
        self._docked_star = star
        self.notify_observers()


class ShipList(Observable):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self._stars = [Star(0, "New Gumbria", Location(0, 0, 0)), Star(1, "Gummerton", Location(100, 100, 0))]
        self._ships = []

    def add_ship(self, ship: Ship):
        self._ships.append(ship)
        self.notify_observers(ship)

    def ships(self):
        return self._ships
