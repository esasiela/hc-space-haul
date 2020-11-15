import configparser
from PyQt5.QtGui import QColor


class SpaceHaulConfig(configparser.SectionProxy):
    def __init__(self, parser, name):
        configparser.SectionProxy.__init__(self, parser, name)

    def getcolor(self, option):
        rgb = [int(c) for c in self.get(option).split(',')]
        return QColor(rgb[0], rgb[1], rgb[2])
