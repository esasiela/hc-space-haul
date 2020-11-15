from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from project2.model.star import Star

from project2.util.hc_observable import Observer
from project2.controller.space_haul_controller import SpaceHaulController, SpaceHaulControllerEvent

class StarAddComm(QObject):
    signal = pyqtSignal(Star)


class StarChangeComm(QObject):
    signal = pyqtSignal(Star)


class StarSummaryWidget(QWidget, Observer):
    def __init__(self, parent=None, controller: SpaceHaulController = None, title: str = "", star: Star = None,
                 watch_hovered: bool = False, watch_selected: bool = False, **kwargs):
        QWidget.__init__(self, parent=parent, **kwargs)
        self.controller = controller
        self.controller.add_observer(self)

        self.star = star
        self.watch_hovered = watch_hovered
        self.watch_selected = watch_selected

        self.star_change_comm = StarChangeComm()
        self.star_change_comm.signal.connect(self.slot_star_change)

        layout = QVBoxLayout()
        self.title_label = QLabel(self)
        self.title_label.setText(title)

        layout.addWidget(self.title_label)

        self.name_label = QLabel(self)
        self.name_label.move(4, 3)

        self.location_x_label = QLabel(self)
        self.location_y_label = QLabel(self)
        self.location_z_label = QLabel(self)

        layout.addWidget(self.name_label)
        layout.addWidget(self.location_x_label)
        layout.addWidget(self.location_y_label)
        layout.addWidget(self.location_z_label)

        self.distance_to_selected_label = None
        if self.watch_hovered:
            self.distance_to_selected_label = QLabel(self)
            layout.addWidget(self.distance_to_selected_label)

        self.setLayout(layout)

    def observable_update(self, o, e=None):
        if isinstance(e, SpaceHaulControllerEvent):
            if e.event_type == "repaint":
                self.star_change_comm.signal.emit(Star())

            elif self.watch_hovered:
                if e.event_type == "star-hover":
                    self.star = self.controller.hovered_star
                    # self.star.add_observer(self)
                    self.star_change_comm.signal.emit(self.star)
                elif e.event_type == "star-unhover":
                    # self.star.remove_observer(self)
                    self.star = None
                    self.star_change_comm.signal.emit(Star())
                elif e.event_type == "star-select" or e.event_type == "star-unselect":
                    self.star_change_comm.signal.emit(Star())

            elif self.watch_selected:
                if e.event_type == "star-select":
                    self.star = self.controller.selected_star
                    # self.star.add_observer(self)
                    self.star_change_comm.signal.emit(self.star)
                elif e.event_type == "star-unselect":
                    # self.star.remove_observer(self)
                    self.star = None
                    self.star_change_comm.signal.emit(Star())

        elif isinstance(o, Star):
            # our star changed attributes
            self.star_change_comm.signal.emit(o)

    def slot_star_change(self):
        if self.star is None:
            self.name_label.setText("")
            self.location_x_label.setText("")
            self.location_y_label.setText("")
            self.location_z_label.setText("")
            if self.distance_to_selected_label is not None:
                self.distance_to_selected_label.setText("")
        else:
            self.name_label.setText(self.star.name)
            self.location_x_label.setText("X={0:,.0f}".format(self.star.location.x))
            self.location_y_label.setText("Y={0:,.0f}".format(self.star.location.y))
            self.location_z_label.setText("Z={0:,.0f}".format(self.star.location.z))

            if self.distance_to_selected_label is not None:
                if self.controller.selected_star is not None:
                    self.distance_to_selected_label.setText("Dist to Selected={0:,.0f}".format(
                        self.star.location.distance(self.controller.selected_star.location)
                    ))
                else:
                    self.distance_to_selected_label.setText("")

        self.repaint()
