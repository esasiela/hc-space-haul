import json

from project2.model.location import Location
from project.util.hc_observable import Observable


class Star(Observable):
    """
    A Star in space
    """
    def __init__(self, star_id: int = 0, name: str = "", location: Location = Location(), **kwargs):
        super().__init__(**kwargs)
        self.star_id = star_id
        self.name = name
        self.location = location

        self.selected = False
        self.hovered = False

    @classmethod
    def from_dict(cls, d) -> 'Star':
        return Star(d["star_id"], d["name"], Location.from_dict(d["location"]))

    def to_json(self) -> str:
        x = self.__dict__.copy()
        x["location"] = self.location.__dict__.copy()

        # specifically remove the "bad" ones
        del x["_observers"]
        del x["_observable_lock"]
        del x["selected"]
        del x["hovered"]

        return json.dumps(x)

    def copy(self, star: 'Star'):
        self.star_id = star.star_id
        self.name = star.name
        self.location = star.location.copy()

    def change(self, star_id: int = None, name: str = None, location: Location = None, hovered: bool = None,
               selected: bool = None):

        if star_id is not None:
            self.star_id = star_id

        if name is not None:
            self.name = name

        if location is not None:
            self.location = location

        if hovered is not None:
            self.hovered = hovered

        if selected is not None:
            self.selected = selected

        self.notify_observers()
