from typing import List
import math

from PyQt5.QtWidgets import QWidget, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QDesktopWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QSize, QObject, pyqtSignal, QRect

from project2.util.space_haul_config import SpaceHaulConfig
from project2.util.hc_observable import Observer

from project2.controller.space_haul_controller import SpaceHaulController, SpaceHaulControllerEvent

from project2.model.location import Location
from project2.model.star import Star
from project2.model.ship import Ship
from project2.model.ship import Ship

from project2.view.star_gui import StarAddComm, StarChangeComm, StarSummaryWidget
from project2.view.ship_gui import ShipChangeComm, ShipSummaryWidget


class SpaceHaulGui:
    def __init__(self, controller: SpaceHaulController):
        self.controller = controller
        self.config: SpaceHaulConfig = self.controller.config
        # self.kafka_log = ConsoleFrame(title="KAFKA LOG")
        # self.controller._kafka_log = self.kafka_log

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

        # middle_layout.addWidget(self.create_frame_left())
        middle_layout.addWidget(self.create_frame_central())
        middle_layout.addWidget(self.create_frame_right())

        middle_frame.setLayout(middle_layout)
        outer_layout.addWidget(middle_frame)
        outer_layout.addWidget(self.create_frame_bottom())

        outer_frame.setLayout(outer_layout)
        self.main_window.setCentralWidget(outer_frame)
        self.main_window.setWindowTitle(self.config["window.title"])

        # in development, 1=left monitor
        monitor = QDesktopWidget().screenGeometry(1)
        self.main_window.move(monitor.left() + 1300, monitor.top() + 0)

        self.main_window.showMaximized()

    def create_frame_left(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("LEFTY"))
        #layout.addWidget(StarListFrame(self.main_window, self.controller))
        #layout.addWidget(ShipListFrame(self.main_window, self.controller))
        layout.addStretch(1)

        frame.setLayout(layout)
        return frame

    def create_frame_right(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setFixedWidth(200)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(StarSummaryWidget(controller=self.controller, title="Hovered Star", watch_hovered=True))
        layout.addWidget(StarSummaryWidget(controller=self.controller, title="Selected Star", watch_selected=True))

        layout.addWidget(ShipSummaryWidget(controller=self.controller, title="Hovered Ship", watch_hovered=True))
        layout.addWidget(ShipSummaryWidget(controller=self.controller, title="Selected Ship", watch_selected=True))

        # layout.addWidget(StarListFrame(self.main_window, self.controller))

        # layout.addWidget(HoveredShipSummaryWidget(controller=self.controller))
        # layout.addWidget(SelectedShipSummaryWidget(controller=self.controller))
        # layout.addWidget(ShipListFrame(self.main_window, self.controller))

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

        #tabs = QTabWidget()
        #tabs.addTab(self.kafka_log, "Kafka")
        #layout.addWidget(tabs)

        layout.addWidget(QLabel("BOTTOMY"))

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


class SpaceFrame(QFrame, Observer):
    def __init__(self, parent=None, controller: SpaceHaulController = None, **kwargs):
        QFrame.__init__(self, parent, **kwargs)
        Observer.__init__(self, **kwargs)
        self.controller = controller
        self.controller.add_observer(self)
        self.config: SpaceHaulConfig = self.controller.config

        self.star_add_comm = StarAddComm()
        self.star_add_comm.signal.connect(self.slot_star_add)

        self.star_change_comm = StarChangeComm()
        self.star_change_comm.signal.connect(self.slot_star_change)

#        self.ship_add_comm = ShipAddComm()
#        self.ship_add_comm.signal.connect(self.add_ship)

        self.ship_change_comm = ShipChangeComm()
        self.ship_change_comm.signal.connect(self.slot_ship_change)

        # self.setStyleSheet("background-color: yellow")
        self.setStyleSheet(self.config.get("spaceframe.stylesheet"))

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
            if rect.x() <= event.pos().x() <= (rect.x() + rect.width()) and\
                    rect.y() <= event.pos().y() <= (rect.y() + rect.height()):
                if not star.hovered:
                    # we are over the star and it is NOT hovered, set hovered flag
                    self.controller.set_hovered_star(star)
                    # star.set_hovered(True)
            elif star.hovered:
                # the star is hovered but our mouse is outside of it, clear hovered flag
                # star.set_hovered(False)
                self.controller.set_hovered_star(None)

        # need to detect if we are on top of a ship
        for ship, rect in self.ship_rectangles:
            if rect.x() <= event.pos().x() <= (rect.x() + rect.width()) and\
                    rect.y() <= event.pos().y() <= (rect.y() + rect.height()):
                if not ship.hovered:
                    # we are over the ship and it is NOT hovered, set hovered flag
                    self.controller.set_hovered_ship(ship)
            elif ship.hovered:
                # the ship is hovered but our mouse is outside of it, clear hovered flag
                self.controller.set_hovered_ship(None)

    def mousePressEvent(self, event):
        for star, rect in self.star_rectangles:
            if rect.x() <= event.pos().x() <= (rect.x() + rect.width()) and\
                    rect.y() <= event.pos().y() <= (rect.y() + rect.height()):
                if not star.selected:
                    # we clicked the star and he is NOT selected, set selected flag
                    self.controller.set_selected_star(star)
                else:
                    # we clicked the star and he IS selected, clear the selected flag
                    self.controller.set_selected_star(None)

        for ship, rect in self.ship_rectangles:
            if rect.x() <= event.pos().x() <= (rect.x() + rect.width()) and\
                    rect.y() <= event.pos().y() <= (rect.y() + rect.height()):
                if not ship.selected:
                    self.controller.set_selected_ship(ship)
                else:
                    self.controller.set_selected_ship(None)

    def observable_update(self, o, e=None):
        if isinstance(e, SpaceHaulControllerEvent):

            if e.event_type == "repaint":
                self.star_change_comm.signal.emit(Star())

        else:
            print("SpaceFrame.observable_update() unimplemented event:", e)

    def slot_star_change(self, star: Star):
        self.repaint()

    def slot_star_add(self, star: Star):
        # watch the star for updates
        # star.add_observer(self)
        self.repaint()

    def slot_ship_change(self, ship: Ship):
        self.repaint()

    def brush_and_pen(self, painter, prefix):
        painter.setBrush(QBrush(
            self.config.getcolor("{0}.brush.color".format(prefix)),
            Qt.SolidPattern
        ))
        painter.setPen(QPen(
            self.config.getcolor("{0}.pen.color".format(prefix)),
            self.config.getint("{0}.pen.width".format(prefix)),
            Qt.SolidLine
        ))

    def paintEvent(self, event):
        self.controller.lock.acquire()

        velocity_scale_factor = self.config.getfloat("spaceframe.ship.velocity.scale")

        star_width = self.config.getint("spaceframe.star.width")
        star_height = self.config.getint("spaceframe.star.height")

        ship_width = self.config.getint("spaceframe.ship.width")
        ship_height = self.config.getint("spaceframe.ship.height")

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

        # we need to re-compute the rectangles every paint event
        self.star_rectangles = []
        self.ship_rectangles = []

        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))

        # first draw lines to/from moving ships and their stars
        for ship in self.controller.ships:
            if (ship.selected or ship.hovered) and ship.destination_star is not None:
                self.brush_and_pen(painter, "spaceframe.ship.destination")
                painter.drawLine(
                    gui_center_x + ((ship.destination_star.location.x - self.space_center_x) / self.space_width_ratio),
                    gui_center_y + ((ship.destination_star.location.y - self.space_center_y) / space_height_ratio),
                    gui_center_x + ((ship.location.x - self.space_center_x) / self.space_width_ratio),
                    gui_center_y + ((ship.location.y - self.space_center_y) / space_height_ratio)
                )

        # next draw line between selected star and hovered star
        for star in self.controller.stars:
            if star.hovered and self.controller.selected_star is not None and self.controller.selected_star.star_id != star.star_id:
                self.brush_and_pen(painter, "spaceframe.star.selected_hovered")
                s = self.controller.selected_star
                painter.drawLine(
                    gui_center_x + ((star.location.x - self.space_center_x) / self.space_width_ratio),
                    gui_center_y + ((star.location.y - self.space_center_y) / space_height_ratio),
                    gui_center_x + ((s.location.x - self.space_center_x) / self.space_width_ratio),
                    gui_center_y + ((s.location.y - self.space_center_y) / space_height_ratio)
                )

        for star in self.controller.stars:
            x = gui_center_x + ((star.location.x - self.space_center_x) / self.space_width_ratio) - (star_width / 2)
            y = gui_center_y + ((star.location.y - self.space_center_y) / space_height_ratio) - (star_height / 2)

            if star.hovered:
                self.brush_and_pen(painter, "spaceframe.star.hovered")
            elif star.selected:
                self.brush_and_pen(painter, "spaceframe.star.selected")
            else:
                self.brush_and_pen(painter, "spaceframe.star.default")

            painter.drawEllipse(x, y, star_width, star_height)

            painter.setFont(QFont('Decorative', 10))
            painter.drawText(x + 2, y + star_height/2 + 4, "{0}".format(star.star_id))

            self.star_rectangles.append((star, QRect(x, y, star_width, star_height)))

        for ship in self.controller.ships:
            x = gui_center_x + ((ship.location.x - self.space_center_x) / self.space_width_ratio) - (ship_width / 2)
            y = gui_center_y + ((ship.location.y - self.space_center_y) / space_height_ratio) - (ship_height / 2)

            if ship.hovered:
                self.brush_and_pen(painter, "spaceframe.ship.hovered")
            elif ship.selected:
                self.brush_and_pen(painter, "spaceframe.ship.selected")
            else:
                self.brush_and_pen(painter, "spaceframe.ship.default")

            painter.drawEllipse(x, y, ship_width - 2, ship_height - 2)

            # if travelling (not docked) draw a visual indicator of the velocity
            if ship.docked_star is None:
                self.brush_and_pen(painter, "spaceframe.ship.velocity")

                # center of ship (gui coords)
                ship_x = x + ship_width / 2
                ship_y = y + ship_height / 2

                # center of destination star (gui coords)
                star_x = gui_center_x + (
                        (ship.destination_star.location.x - self.space_center_x) / self.space_width_ratio)
                star_y = gui_center_y + (
                        (ship.destination_star.location.y - self.space_center_y) / space_height_ratio)

                big_h = math.sqrt(math.pow(star_x - ship_x, 2) + math.pow(star_y - ship_y, 2))
                h = 10
                x_prime = ((star_x - ship_x) * h) / big_h if big_h != 0 else ship_x
                y_prime = ((star_y - ship_y) * h) / big_h if big_h != 0 else ship_y

                vel_x = x + (ship_width / 2) + x_prime
                vel_y = y + (ship_height / 2) + y_prime

                painter.drawLine(
                    vel_x,
                    vel_y,
                    vel_x + velocity_scale_factor * (ship.velocity.x / self.space_width_ratio),
                    vel_y + velocity_scale_factor * (ship.velocity.y / space_height_ratio)
                )

            self.ship_rectangles.append((ship, QRect(x, y, ship_width, ship_height)))

        painter.end()

        self.controller.lock.release()


class SpaceHaulMainWindow(QMainWindow):
    def __init__(self, parent=None, controller=None):
        QWidget.__init__(self, parent)
        self.controller = controller

    def closeEvent(self, event):
        print("Closing Main Window")
