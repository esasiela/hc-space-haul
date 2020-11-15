from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from project2.model.ship import Ship

from project2.util.hc_observable import Observer
from project2.controller.space_haul_controller import SpaceHaulController, SpaceHaulControllerEvent

class ShipAddComm(QObject):
    signal = pyqtSignal(Ship)


class ShipChangeComm(QObject):
    signal = pyqtSignal(Ship)


class ShipSummaryWidget(QWidget, Observer):
    def __init__(self, parent=None, controller: SpaceHaulController = None, title: str = "", ship: Ship = None,
                 watch_hovered: bool = False, watch_selected: bool = False, **kwargs):
        QWidget.__init__(self, parent=parent, **kwargs)
        self.controller = controller
        self.controller.add_observer(self)

        self.ship = ship
        self.watch_hovered = watch_hovered
        self.watch_selected = watch_selected

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.slot_ship_change)

        layout = QVBoxLayout()
        self.title_label = QLabel(self)
        self.title_label.setText(title)

        layout.addWidget(self.title_label)

        self.name_label = QLabel(self)
        self.name_label.move(4, 3)

        self.location_x_label = QLabel(self)
        self.location_y_label = QLabel(self)
        self.location_z_label = QLabel(self)

        self.velocity_x_label = QLabel(self)
        self.velocity_y_label = QLabel(self)
        self.velocity_z_label = QLabel(self)

        self.destination_star_label = QLabel(self)
        self.departure_star_label = QLabel(self)
        self.docked_star_label = QLabel(self)

        layout.addWidget(self.name_label)
        layout.addWidget(self.location_x_label)
        layout.addWidget(self.location_y_label)
        layout.addWidget(self.location_z_label)

        layout.addWidget(self.velocity_x_label)
        layout.addWidget(self.velocity_y_label)
        layout.addWidget(self.velocity_z_label)

        layout.addWidget(self.departure_star_label)
        layout.addWidget(self.destination_star_label)
        layout.addWidget(self.docked_star_label)

        self.setLayout(layout)

    def observable_update(self, o, e=None):
        if isinstance(e, SpaceHaulControllerEvent):
            if e.event_type == "repaint":
                self.ship_change_comm.signal.emit(Ship())

            elif self.watch_hovered:
                if e.event_type == "ship-hover":
                    self.ship = self.controller.hovered_ship
                    # if self.ship is not None:
                    #    self.ship.add_observer(self)
                    self.ship_change_comm.signal.emit(self.ship)
                elif e.event_type == "ship-unhover":
                    # if self.ship is not None:
                    #    self.ship.remove_observer(self)
                    self.ship = None
                    self.ship_change_comm.signal.emit(Ship())

            elif self.watch_selected:
                if e.event_type == "ship-select":
                    self.ship = self.controller.selected_ship
                    # if self.ship is not None:
                    #    self.ship.add_observer(self)
                    self.ship_change_comm.signal.emit(self.ship)
                elif e.event_type == "ship-unselect":
                    #if self.ship is not None:
                    #    self.ship.remove_observer(self)
                    self.ship = None
                    self.ship_change_comm.signal.emit(Ship())

        elif isinstance(o, Ship):
            # our ship changed attributes
            self.ship_change_comm.signal.emit(o)

    def slot_ship_change(self):
        if self.ship is None:
            self.name_label.setText("")
            self.location_x_label.setText("")
            self.location_y_label.setText("")
            self.location_z_label.setText("")
            self.velocity_x_label.setText("")
            self.velocity_y_label.setText("")
            self.velocity_z_label.setText("")
            self.departure_star_label.setText("")
            self.destination_star_label.setText("")
            self.docked_star_label.setText("")
        else:
            self.name_label.setText(self.ship.name)
            self.location_x_label.setText("Loc.X={0}".format(self.ship.location.x))
            self.location_y_label.setText("Loc.Y={0}".format(self.ship.location.y))
            self.location_z_label.setText("Loc.Z={0}".format(self.ship.location.z))
            self.velocity_x_label.setText("Vel.X={0}".format(self.ship.velocity.x))
            self.velocity_y_label.setText("Vel.Y={0}".format(self.ship.velocity.y))
            self.velocity_z_label.setText("Vel.Z={0}".format(self.ship.velocity.z))

            if self.ship.departure_star is not None:
                self.departure_star_label.setText("Departing: {0}".format(self.ship.departure_star.name))
            else:
                self.departure_star_label.setText("Departing: NONE")

            if self.ship.destination_star is not None:
                self.destination_star_label.setText("Destination: {0}".format(self.ship.destination_star.name))
            else:
                self.destination_star_label.setText("Destination: NONE")

            if self.ship.docked_star is not None:
                self.docked_star_label.setText("Docked: {0}".format(self.ship.docked_star.name))
            else:
                self.docked_star_label.setText("Docked: NONE")

        self.repaint()
