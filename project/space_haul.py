import sys
from PyQt5.QtWidgets import QApplication

from project.controller.space_haul_controller import SpaceHaulController
from project.view.space_haul_gui import SpaceHaulGui


# Backup the reference to the exception hook
sys._excepthook = sys.excepthook


def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


sys.excepthook = my_exception_hook


if __name__ == "__main__":
    print("Hello, World!")

    app = QApplication(sys.argv)

    controller = SpaceHaulController()
    gui = SpaceHaulGui(controller)

    gui.create_gui()

    try:
        ret = app.exec_()
        app.exit(ret)
    except:
        print("exiting")

    print("Good bye, World!")
