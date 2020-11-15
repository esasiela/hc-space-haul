import json

from project.model.location import Location
from project.util.hc_observable import Observable


class Star(Observable):
    """
    A Star in space
    """
    def __init__(self, star_id: int, name: str, location: Location, **kwargs):
        super().__init__(**kwargs)
        self._star_id = star_id
        self._name = name
        self._location = location

        self._selected = False
        self._hovered = False

    @classmethod
    def from_dict(cls, d):
        return Star(d["_star_id"], d["_name"], Location.from_dict(d["_location"]))

    def to_json(self) -> str:
        x = self.__dict__.copy()
        x["_location"] = self.location().__dict__.copy()

        # specifically remove the "bad" ones
        del x["_observers"]
        del x["_observable_lock"]
        del x["_selected"]
        del x["_hovered"]

        return json.dumps(x)

    def update_from_star(self, s: 'Star'):
        # YES, update the ID.  If its a kafka update, it'll stay the same, but if its hovered/selected it'll update
        if s is None:
            self._star_id = -1
            self._name = ""
            self._location = Location(0, 0, 0)
        else:
            self._star_id = s.star_id()
            self._name = s.name()
            self._location = s.location()

        self.notify_observers()

    def star_id(self) -> int:
        return self._star_id

    def set_star_id(self, star_id: int):
        self._star_id = star_id
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


class StarList(Observable):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self._stars = [Star(0, "New Gumbria", Location(0, 0, 0)), Star(1, "Gummerton", Location(100, 100, 0))]
        self._stars = []

    def add_star(self, star: Star):
        self._stars.append(star)
        self.notify_observers(star)

    def stars(self):
        return self._stars
