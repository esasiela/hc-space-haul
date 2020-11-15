import sys
import configparser
from PyQt5.QtWidgets import QApplication

from project2.util.space_haul_config import SpaceHaulConfig
from project2.controller.space_haul_controller import SpaceHaulController
from project2.view.space_haul_gui import SpaceHaulGui


# Backup the reference to the exception hook
sys._excepthook = sys.excepthook


def my_exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


sys.excepthook = my_exception_hook


if __name__ == "__main__":
    print("Space Haul 2")

    config_file = "space-haul.ini"

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)
    sh_config = SpaceHaulConfig(config, "DEFAULT")
    config = config["DEFAULT"]

    print("Config:", type(config), config)
    for item in config.items():
        print("\t", item)
    print("end config")

    print("SH Config:", type(sh_config), sh_config)
    for item in sh_config.items():
        print("\t", item)
    print("end config")

    app = QApplication(sys.argv)

    controller = SpaceHaulController(config=sh_config)
    gui = SpaceHaulGui(controller)

    gui.create_gui()

    try:
        ret = app.exec_()
        app.exit(ret)
    except Exception as inst:
        print("Exception thrown from app.exec_():", inst)

    print("Good bye, World!")
