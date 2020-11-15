from typing import List

from PyQt5.QtWidgets import QWidget, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QDesktopWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal, QRect

from project.util.hc_observable import ThreadedObserver

from project.controller.space_haul_controller import SpaceHaulController, SpaceHaulControllerEvent

from project.model.location import Location
from project.model.star import Star, StarList
from project.model.ship import Ship, ShipList

from project.view.console_frames import ConsoleFrame
from project.view.ship_gui import ShipAddComm, ShipChangeComm, ShipListFrame, HoveredShipSummaryWidget,\
    SelectedShipSummaryWidget


class StarAddComm(QObject):
    signal = pyqtSignal(Star)


class StarChangeComm(QObject):
    signal = pyqtSignal(Star)


class HoveredStarSummaryWidget(QWidget, ThreadedObserver):
    def __init__(self, parent=None, controller: SpaceHaulController = None, **kwargs):
        QWidget.__init__(self, parent=parent, **kwargs)
        self.controller = controller

        self.controller.add_observer(self)

        self.star_change_comm = StarChangeComm()
        self.star_change_comm.signal.connect(self.star_change)

        layout = QVBoxLayout()

        # create a title label
        self.title_label = QLabel(self)
        self.title_label.setText("Hovered Star")

        layout.addWidget(self.title_label)

        # label with the name of the VIP star
        self.name_label = QLabel(self)
        self.name_label.move(4, 3)

        layout.addWidget(self.name_label)

        if self.controller.hovered_star() is not None:
            self._label.setText(self.controller.hovered_star().name())

        self.setLayout(layout)

    def observable_update(self, o, e=None):
        if isinstance(e, SpaceHaulControllerEvent):
            if e.event_type == "hover" and isinstance(e.o, Star):
                e.o.add_observer(self)
                self.star_change_comm.signal.emit(e.o)

            elif e.event_type == "unhover" and isinstance(e.o, Star):
                e.o.remove_observer(self)
                self.star_change_comm.signal.emit(Star(-1, "", Location(0, 0, 0)))

        elif isinstance(o, Star):
            # the hovered star changed attributes
            self.star_change_comm.signal.emit(o)

    def star_change(self, star: Star):
        if star.star_id() == -1:
            self.name_label.setText("")
        else:
            self.name_label.setText(star.name())


class StarWidget(QWidget, ThreadedObserver):
    def __init__(self, parent=None, controller: SpaceHaulController = None, star: Star = None, **kwargs):
        QWidget.__init__(self, parent, **kwargs)
        ThreadedObserver.__init__(self, **kwargs)
        self.controller = controller
        self.star = star
        self.star.add_observer(self)

        self.star_change_comm = StarChangeComm()
        self.star_change_comm.signal.connect(self.star_change)

    def star_change(self, star: Star):
        self.repaint()

    def enterEvent(self, event):
        self.controller.set_hovered_star(self.star)

    def leaveEvent(self, event):
        self.controller.set_hovered_star(None)

    def observable_update(self, o, e=None):
        self.observable_update_gui(o)
        self.star_change_comm.signal.emit(self.star)

    def observable_update_gui(self, o):
        """
        Children widgets should override this method to do any gui changes based on the observable change.
        Children should NOT call QWidget.update(), that will be called by the parent class after this
        function returns.
        :param o:
        :return:
        """
        return


class StarListStarWidget(StarWidget):
    def __init__(self, parent=None, controller: SpaceHaulController = None, star: Star = None, **kwargs):
        StarWidget.__init__(self, parent=parent, controller=controller, star=star, **kwargs)
        self._label = QLabel(self)
        self._label.setText(self.star.name())
        self._label.move(4, 3)

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.star.is_hovered():
            painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))

        painter.setBrush(QBrush(QColor.fromRgb(150, 160, 70), Qt.SolidPattern))
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
        painter.end()

    def sizeHint(self):
        return QSize(190, 20)

    def observable_update_gui(self, o):
        self._label.setText(self.star.name())


class StarListFrame(QFrame, ThreadedObserver):
    def __init__(self, parent=None, controller=None):
        QFrame.__init__(self, parent)
        self.controller = controller
        self.controller.star_list().add_observer(self)

        self.star_add_comm = StarAddComm()
        self.star_add_comm.signal.connect(self.star_add)

        self.star_change_comm = StarChangeComm()
        self.star_change_comm.signal.connect(self.star_change)

        self.setFixedWidth(200)
        self.setMaximumWidth(200)

        self.my_layout = QVBoxLayout()
        self.my_layout.addWidget(QLabel("Star List"))

        for star in self.controller.stars():
            self.my_layout.addWidget(StarListStarWidget(self, self.controller, star))

        self.setLayout(self.my_layout)

    def observable_update(self, o, e=None):

        if isinstance(o, Star):
            # an individual star was updated
            self.star_change_comm.signal.emit(o)
        elif isinstance(o, StarList):
            # the list was updated, that's an add or delete
            self.star_add_comm.signal.emit(e)
        else:
            print("StarListFrame.observable_update() unknown observation type")

    def star_add(self, star: Star):
        star.add_observer(self)
        self.my_layout.addWidget(StarListStarWidget(self, self.controller, star))

    def star_change(self, star: Star):
        self.repaint()
