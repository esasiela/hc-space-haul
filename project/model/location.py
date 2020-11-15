import math


class Location(object):
    """
    A location in space
    """
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    def from_dict(cls, d):
        return Location(d["x"], d["y"], d["z"])

    @classmethod
    def distance(cls, a: 'Location', b: 'Location'):
        return math.sqrt(
            math.pow(b.x - a.x, 2) +
            math.pow(b.y - a.y, 2) +
            math.pow(b.z - a.z, 2)
        )
