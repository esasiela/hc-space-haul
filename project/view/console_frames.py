from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFrame, QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QLabel


class ConsoleComm(QObject):
    """
    ConsoleComm is used to send Qt signal to ConsoleFrame for text edit updates in the GUI thread
    """
    text_signal = pyqtSignal(str)
    msg_signal = pyqtSignal(str, int)


class ConsoleFrame(QFrame):
    """
    Console Frame provides a text edit that you append messages to for display in GUI rather
    than stdout console.
    """
    def __init__(self, parent=None, title=None, show_border=True):
        QFrame.__init__(self, parent)

        self.title = title

        self.console_comm = ConsoleComm()
        self.console_comm.text_signal.connect(self.process_text_signal)
        self.console_comm.msg_signal.connect(self.process_msg_signal)

        if show_border:
            self.setFrameStyle(QFrame.StyledPanel)

        self.text_area = QTextEdit(parent)
        self.text_area.setReadOnly(True)
        self.text_area.setLineWrapMode(QTextEdit.NoWrap)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.click_clear)

        top_frame = QFrame()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(QLabel(title))
        top_layout.addWidget(self.clear_button)
        top_frame.setLayout(top_layout)

        layout = QVBoxLayout()
        if not show_border:
            layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(top_frame)
        layout.addWidget(self.text_area)
        self.setLayout(layout)

    def click_clear(self):
        self.text_area.clear()

    def log_text(self, text):
        """
        Invoke this guy from any thread and he'll emit the signal that makes the GUI thread handle the update
        :param text:
        :return:
        """
        self.console_comm.text_signal.emit(text)

    def log(self, text, msg_type=0):
        """
        Invoke this guy from any thread and he'll emit the signal that makes the GUI thread handle the update
        :param text:
        :param msg_type:
        :return:
        """
        self.console_comm.msg_signal.emit(text, msg_type)

    def process_text_signal(self, text):
        """
        This guy runs in the Qt GUI thread when we emit the signal
        :param text: string to log
        :return: nothing
        """
        self.text_area.append(text)

    def process_msg_signal(self, text, msg_type):
        """
        This guy runs in the Qt GUI thread when we emit the signal
        :param text: string to log
        :param msg_type: the type of message, used for coloration and filtering
        :return: nothing
        """
        # TODO implement coloration and filtering by msg_type
        self.text_area.append(text)
