from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal

from project.util.hc_observable import ThreadedObserver
from project.controller.space_haul_controller import SpaceHaulController, SpaceHaulControllerEvent
from project.model.location import Location
from project.model.ship import Ship, ShipList


class ShipAddComm(QObject):
    signal = pyqtSignal(Ship)


class ShipChangeComm(QObject):
    signal = pyqtSignal(Ship)


class SelectedShipSummaryWidget(QWidget, ThreadedObserver):
    def __init__(self, parent=None, controller: SpaceHaulController = None, **kwargs):
        QWidget.__init__(self, parent=parent, **kwargs)
        self.controller = controller

        self.controller.add_observer(self)

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.ship_change)

        layout = QVBoxLayout()

        # create a title label
        self.title_label = QLabel(self)
        self.title_label.setText("Selected Ship")

        layout.addWidget(self.title_label)

        # label with the name of the VIP ship
        self.name_label = QLabel(self)
        self.name_label.move(4, 3)

        layout.addWidget(self.name_label)

        if self.controller.selected_ship() is not None:
            self._label.setText(self.controller.selected_ship().name())

        self.setLayout(layout)

    def observable_update(self, o, e=None):
        if isinstance(e, SpaceHaulControllerEvent):
            if e.event_type == "select" and isinstance(e.o, Ship):
                e.o.add_observer(self)
                self.ship_change_comm.signal.emit(e.o)

            elif e.event_type == "unselect" and isinstance(e.o, Ship):
                e.o.remove_observer(self)
                self.ship_change_comm.signal.emit(Ship(-1, "", Location(0, 0, 0)))

        elif isinstance(o, Ship):
            # the selected star changed attributes
            self.ship_change_comm.signal.emit(o)

    def ship_change(self, ship: Ship):
        if ship.ship_id() == -1:
            self.name_label.setText("")
        else:
            self.name_label.setText(ship.name())


class HoveredShipSummaryWidget(QWidget, ThreadedObserver):
    def __init__(self, parent=None, controller: SpaceHaulController = None, **kwargs):
        QWidget.__init__(self, parent=parent, **kwargs)
        self.controller = controller

        self.controller.add_observer(self)

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.ship_change)

        layout = QVBoxLayout()

        # create a title label
        self.title_label = QLabel(self)
        self.title_label.setText("Hovered Ship")

        layout.addWidget(self.title_label)

        # label with the name of the VIP ship
        self.name_label = QLabel(self)
        self.name_label.move(4, 3)

        layout.addWidget(self.name_label)

        if self.controller.hovered_ship() is not None:
            self._label.setText(self.controller.hovered_ship().name())

        self.setLayout(layout)

    def observable_update(self, o, e=None):
        if isinstance(e, SpaceHaulControllerEvent):
            if e.event_type == "hover" and isinstance(e.o, Ship):
                e.o.add_observer(self)
                self.ship_change_comm.signal.emit(e.o)

            elif e.event_type == "unhover" and isinstance(e.o, Ship):
                e.o.remove_observer(self)
                self.ship_change_comm.signal.emit(Ship(-1, "", Location(0, 0, 0)))

        elif isinstance(o, Ship):
            # the hovered star changed attributes
            self.ship_change_comm.signal.emit(o)

    def ship_change(self, ship: Ship):
        if ship.ship_id() == -1:
            self.name_label.setText("")
        else:
            self.name_label.setText(ship.name())


class ShipWidget(QWidget, ThreadedObserver):
    def __init__(self, parent=None, controller: SpaceHaulController = None, ship: Ship = None, **kwargs):
        QWidget.__init__(self, parent, **kwargs)
        ThreadedObserver.__init__(self, **kwargs)
        self.controller = controller
        self.ship = ship
        self.ship.add_observer(self)

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.ship_change)

    def enterEvent(self, event):
        self.controller.set_hovered_ship(self.ship)

    def leaveEvent(self, event):
        self.controller.set_hovered_ship(None)

    def mousePressEvent(self, event):
        if self.ship.is_selected():
            self.controller.set_selected_ship(None)
        else:
            self.controller.set_selected_ship(self.ship)

    def ship_change(self, ship: Ship):
        self.repaint()

    def observable_update(self, o, e=None):
        self.observable_update_gui(o)
        self.ship_change_comm.signal.emit(self.ship)

    def observable_update_gui(self, o):
        """
        Children widgets should override this method to do any gui changes based on the observable change.
        Children should NOT call QWidget.update(), that will be called by the parent class after this
        function returns.
        :param o:
        :return:
        """
        return


class ShipListShipWidget(ShipWidget):
    def __init__(self, parent=None, controller: SpaceHaulController = None, ship: Ship = None, **kwargs):
        ShipWidget.__init__(self, parent=parent, controller=controller, ship=ship, **kwargs)
        self._label = QLabel(self)
        self._label.setText(self.ship.name())
        self._label.move(4, 3)

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.ship.is_hovered():
            painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
        elif self.ship.is_selected():
            painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))

        painter.setBrush(QBrush(QColor.fromRgb(200, 210, 50), Qt.SolidPattern))
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

        painter.end()

    def sizeHint(self):
        return QSize(190, 20)

    def observable_update_gui(self, o):
        self._label.setText(self.ship.name())


class ShipListFrame(QFrame, ThreadedObserver):
    def __init__(self, parent=None, controller=None):
        QFrame.__init__(self, parent)
        self.controller = controller
        self.controller.ship_list().add_observer(self)

        self.ship_add_comm = ShipAddComm()
        self.ship_add_comm.signal.connect(self.ship_add)

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.ship_change)

        self.setFixedWidth(200)
        self.setMaximumWidth(200)

        self.my_layout = QVBoxLayout()
        self.my_layout.addWidget(QLabel("Ship List"))

        for ship in self.controller.ships():
            self.my_layout.addWidget(ShipListShipWidget(self, self.controller, ship))

        self.setLayout(self.my_layout)

    def observable_update(self, o, e=None):

        if isinstance(o, Ship):
            # an individual ship was updated
            self.ship_change_comm.signal.emit(o)
        elif isinstance(o, ShipList):
            # the list was updated, that's an add or delete
            self.ship_add_comm.signal.emit(e)
        else:
            print("ShipListFrame.observable_update() unknown observation type")

    def ship_add(self, ship: Ship):
        ship.add_observer(self)
        self.my_layout.addWidget(ShipListShipWidget(self, self.controller, ship))

    def ship_change(self, ship: Ship):
        self.repaint()
