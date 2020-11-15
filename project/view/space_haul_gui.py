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
from project.view.star_gui import StarAddComm, StarChangeComm, StarListFrame, HoveredStarSummaryWidget
from project.view.ship_gui import ShipAddComm, ShipChangeComm, ShipListFrame, HoveredShipSummaryWidget,\
    SelectedShipSummaryWidget


class SpaceHaulGui:
    def __init__(self, controller: SpaceHaulController):
        self.controller = controller

        self.kafka_log = ConsoleFrame(title="KAFKA LOG")
        self.controller._kafka_log = self.kafka_log

        self.txt_top = "TOP"
        self.txt_left = "LEFT"

        self.main_window = SpaceHaulMainWindow()

    def create_gui(self):

        outer_frame = QWidget()
        outer_layout = QVBoxLayout()

        outer_layout.addWidget(self.create_frame_top())

        middle_frame = QWidget()
        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)

        middle_layout.addWidget(self.create_frame_left())
        middle_layout.addWidget(self.create_frame_central())
        # middle_layout.addWidget(self.create_frame_right())

        middle_frame.setLayout(middle_layout)
        outer_layout.addWidget(middle_frame)
        outer_layout.addWidget(self.create_frame_bottom())

        outer_frame.setLayout(outer_layout)
        self.main_window.setCentralWidget(outer_frame)
        self.main_window.setWindowTitle("Space Haul!")

        # in development, 1=left monitor
        monitor = QDesktopWidget().screenGeometry(1)
        self.main_window.move(monitor.left() + 1300, monitor.top() + 0)

        self.main_window.show()

    def create_frame_right(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(StarListFrame(self.main_window, self.controller))
        layout.addWidget(ShipListFrame(self.main_window, self.controller))
        layout.addStretch(1)

        frame.setLayout(layout)
        return frame

    def create_frame_left(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setFixedWidth(200)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(HoveredStarSummaryWidget(controller=self.controller))
        layout.addWidget(StarListFrame(self.main_window, self.controller))

        layout.addWidget(HoveredShipSummaryWidget(controller=self.controller))
        layout.addWidget(SelectedShipSummaryWidget(controller=self.controller))
        layout.addWidget(ShipListFrame(self.main_window, self.controller))

        layout.addStretch(1)

        frame.setLayout(layout)
        return frame

    def create_frame_top(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(self.txt_top))

        frame.setLayout(layout)
        return frame

    def create_frame_bottom(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setFixedHeight(200)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.addTab(self.kafka_log, "Kafka")
        layout.addWidget(tabs)

        frame.setLayout(layout)
        return frame

    def create_frame_central(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.addStretch(1)
        layout.addWidget(SpaceFrame(self.main_window, self.controller))
        # layout.addStretch(1)

        frame.setLayout(layout)
        return frame


class SpaceFrame(QFrame, ThreadedObserver):
    def __init__(self, parent=None, controller: SpaceHaulController = None, **kwargs):
        QFrame.__init__(self, parent, **kwargs)
        ThreadedObserver.__init__(self, **kwargs)
        self.controller = controller
        self.controller.star_list().add_observer(self)
        self.controller.ship_list().add_observer(self)

        self.star_add_comm = StarAddComm()
        self.star_add_comm.signal.connect(self.add_star)

        self.star_change_comm = StarChangeComm()
        self.star_change_comm.signal.connect(self.change_star)

        self.ship_add_comm = ShipAddComm()
        self.ship_add_comm.signal.connect(self.add_ship)

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.change_ship)

        # pixel sizes to force the gui to give us some space
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)

        # center is the space coords (not gui) that the center of this gui centers on
        self.space_center_x = 0
        self.space_center_y = 0

        # width_ratio is the ratio of gui width to space width
        self.space_width_ratio = 1000

        # save the rectangles that represent widgets
        self.star_rectangles: List[(Star, QRect)] = []
        self.ship_rectangles: List[(Ship, QRect)] = []

        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        # need to detect if we are on top of a star
        for star, rect in self.star_rectangles:
            if rect.x() <= event.pos().x() <= (rect.x() + rect.width()) and rect.y() <= event.pos().y() <= (rect.y() + rect.height()):
                if not star.is_hovered():
                    # we are over the star and it is NOT hovered, set hovered flag
                    self.controller.set_hovered_star(star)
                    # star.set_hovered(True)
            elif star.is_hovered():
                # the star is hovered but our mouse is outside of it, clear hovered flag
                # star.set_hovered(False)
                self.controller.set_hovered_star(None)

        # need to detect if we are on top of a ship
        for ship, rect in self.ship_rectangles:
            if rect.x() <= event.pos().x() <= (rect.x() + rect.width()) and rect.y() <= event.pos().y() <= (rect.y() + rect.height()):
                if not ship.is_hovered():
                    # we are over the ship and it is NOT hovered, set hovered flag
                    self.controller.set_hovered_ship(ship)
            elif ship.is_hovered():
                # the ship is hovered but our mouse is outside of it, clear hovered flag
                self.controller.set_hovered_ship(None)

    def observable_update(self, o, e=None):
        # emit a signal that will get picked up by the gui thread
        if isinstance(o, Star):
            # an individual star was updated
            self.star_change_comm.signal.emit(o)
        elif isinstance(o, StarList):
            # the list was updated, that's an add or delete
            self.star_add_comm.signal.emit(e)
        elif isinstance(o, Ship):
            # an individual ship was updated
            self.ship_change_comm.signal.emit(o)
        elif isinstance(o, ShipList):
            # the list was updated, that's an add or delete
            self.ship_add_comm.signal.emit(e)
        else:
            print("SpaceFrame.observable_update() unknown observation type")

    def change_star(self, star: Star):
        self.repaint()

    def add_star(self, star: Star):
        # watch the star for updates
        star.add_observer(self)
        self.repaint()

    def change_ship(self, ship: Ship):
        self.repaint()

    def add_ship(self, ship: Ship):
        # watch the ship for updates
        ship.add_observer(self)
        self.repaint()

    def paintEvent(self, event):
        star_width = 20
        star_height = 20

        ship_width = 12
        ship_height = 12

        # print("paint, star count {0}".format(len(self.controller.stars())))
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))

        gui_center_x = self.width()/2
        gui_center_y = self.height()/2

        # we know our space_width_ratio, that's essentially the zoom level, need to map that to a height ratio given
        # our gui width/height ratio
        space_height_ratio = self.space_width_ratio * self.width() / self.height()

        # draw a point at the center
        painter.drawRect(self.width()/2-2, self.height()/2-2, 4, 4)

        painter.end()

        # we need to re-compute the rectangles every paint event
        self.star_rectangles = []
        self.ship_rectangles = []

        for star in self.controller.stars():
            star_painter = QPainter(self)

            # change in location is due to (A) center POV changing, or (B) zoom changing, or (C) star moved
            x = gui_center_x + ((star.location().x - self.space_center_x) / self.space_width_ratio) - (star_width / 2)
            y = gui_center_y + ((star.location().y - self.space_center_y) / space_height_ratio) - (star_height / 2)

            if star.is_hovered():
                star_painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))

            star_painter.setBrush(QBrush(QColor.fromRgb(150, 160, 70), Qt.SolidPattern))
            star_painter.drawEllipse(x, y, star_width - 2, star_height - 2)

            star_painter.end()

            self.star_rectangles.append((star, QRect(x, y, star_width, star_height)))

        for ship in self.controller.ships():
            ship_painter = QPainter(self)

            ship_x = gui_center_x + ((ship.location().x - self.space_center_x) / self.space_width_ratio) - (ship_width / 2)
            ship_y = gui_center_y + ((ship.location().y - self.space_center_y) / space_height_ratio) - (ship_height / 2)

#            if ship.destination_star() is not None:
#
#                # DON'T subtract star size, we want the center
#                dest_x = gui_center_x + ((ship.destination_star().location().x - self.space_center_x) / self.space_width_ratio)
#                dest_y = gui_center_y + ((ship.destination_star().location().y - self.space_center_y) / space_height_ratio)
#
#               ship_painter.setBrush(QBrush(QColor.fromRgb(200, 10, 150), Qt.SolidPattern))
#                ship_painter.drawLine(ship_x + (ship_width / 2), ship_y + (ship_height / 2), dest_x, dest_y)

            if ship.is_hovered():
                ship_painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
            elif ship.is_selected():
                ship_painter.setPen(QPen(Qt.green, 1, Qt.SolidLine))

            ship_painter.setBrush(QBrush(QColor.fromRgb(200, 210, 50), Qt.SolidPattern))
            ship_painter.drawEllipse(ship_x, ship_y, ship_width - 2, ship_height - 2)

            ship_painter.end()

            self.ship_rectangles.append((ship, QRect(ship_x, ship_y, ship_width, ship_height)))

    def convert_item_location_to_gui(
            self,
            gui_center: (float, float),
            location: Location,
            px_dim: (int, int),
            space_ratio: (float, float)
    ) -> (float, float):
        # x = gui_center_x + ((ship.location().x - self.space_center_x) / self.space_width_ratio) - (ship_width / 2)
        # y = gui_center_y + ((ship.location().y - self.space_center_y) / space_height_ratio) - (ship_height / 2)

        return (
            gui_center[0] + ((location.x - self.space_center_x) / space_ratio[0]) - (px_dim[0] / 2),
            gui_center[1] + ((location.y - self.space_center_y) / space_ratio[1]) - (px_dim[1] / 2)
        )


class SpaceHaulMainWindow(QMainWindow):
    def __init__(self, parent=None, controller=None):
        QWidget.__init__(self, parent)
        self.controller = controller

    def closeEvent(self, event):
        print("Closing Main Window")
