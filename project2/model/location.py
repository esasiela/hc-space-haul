import math


class Location(object):
    """
    A location in space
    """
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x: float = x
        self.y: float = y
        self.z: float = z

    @classmethod
    def from_dict(cls, d):
        return Location(d["x"], d["y"], d["z"])

    def copy(self) -> 'Location':
        return Location(self.x, self.y, self.z)

    def distance(self, loc: 'Location'):
        return math.sqrt(
            math.pow(loc.x - self.x, 2) +
            math.pow(loc.y - self.y, 2) +
            math.pow(loc.z - self.z, 2)
        )

    def to_tuple(self) -> (float, float, float):
        return self.x, self.y, self.z
