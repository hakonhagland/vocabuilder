import logging
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QWidget,
)
from vocabuilder.commandline import CommandLineOptions
from vocabuilder.config import Config
from vocabuilder.local_database import LocalDatabase
from vocabuilder.mixins import StringMixin, WarningsMixin


class SelectVocabulary:
    def __init__(
        self, opts: CommandLineOptions, cfg: Config, app: QApplication
    ) -> None:
        self.opts = opts
        self.cfg = cfg
        self.app = app
        self.selected_name = None
        self.find_existing_vocabularies()
        database_name = opts.get_database_name()
        if database_name is not None:
            self.selected_name = database_name
        else:
            if not self.read_active_name():
                if not self.choose_most_recent():
                    # app.setQuitOnLastWindowClosed(False)
                    name = self.open_select_voca_window(app)
                    logging.info(f"select voca returned: {name}")
                    # app.setQuitOnLastWindowClosed(True)
                    if name is not None:
                        self.selected_name = name
                    else:
                        logging.info("No vocabulary name found. Exiting..")
                        print("Aborted by user.")
                        quit()

    def choose_most_recent(self) -> bool:
        db_dir = self.cfg.get_data_dir() / LocalDatabase.database_dir
        current_mtime = 0
        candidate = None
        for name in self.existing_vocabularies:
            dbfile = db_dir / name / LocalDatabase.database_fn
            mtime = dbfile.stat().st_mtime
            if mtime > current_mtime:
                candidate = name
        if candidate is not None:
            self.selected_name = name
            return True
        return False

    def find_existing_vocabularies(self) -> None:
        db_dir = self.cfg.get_data_dir() / LocalDatabase.database_dir
        self.existing_vocabularies = []
        if db_dir.exists():
            for file in db_dir.iterdir():
                if file.is_dir():
                    dbfile = file / LocalDatabase.database_fn
                    if dbfile.is_file():
                        self.existing_vocabularies.append(file.name)

    def get_name(self) -> str | None:
        return self.selected_name

    def open_select_voca_window(self, app: QApplication) -> str | None:
        win = SelectNewVocabularyName(self.cfg, self.app)
        win.show()
        self.app.exec()
        return win.name

    def read_active_name(self) -> bool:
        cfg_dir = self.cfg.get_config_dir()
        self.active_voca_info_fn_path = cfg_dir / LocalDatabase.active_voca_info_fn
        if self.active_voca_info_fn_path.is_file():
            txt = self.active_voca_info_fn_path.read_text(encoding="utf-8")
            txt = txt.strip()
            if txt in self.existing_vocabularies:
                self.selected_name = txt
                return True
        return False


class SelectNewVocabularyName(QMainWindow, StringMixin, WarningsMixin):
    def __init__(self, cfg: Config, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.cfg = cfg
        self.name: str | None = (
            None  # Return value to parent: The name the user selected
        )
        # Prevent self to be destroyed when the close button is clicked
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.button_config = self.cfg.config["Buttons"]
        self.resize(330, 200)
        self.setWindowTitle("Select a vocabulary name")
        layout = QGridLayout()
        vpos = 0
        vpos = self.add_info_label(layout, vpos)
        vpos = self.add_line_edit(layout, vpos)
        vpos = self.add_buttons(layout, vpos)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def add_info_label(self, layout: QGridLayout, vpos: int) -> int:
        label1 = QLabel("No vocabularies found.")
        layout.addWidget(label1, vpos, 0, 1, 2)
        vpos += 1
        label2 = QLabel('Please select a name for a new, e.g. "english-korean"')
        layout.addWidget(label2, vpos, 0, 1, 2)
        vpos += 1
        return vpos

    def add_line_edit(self, layout: QGridLayout, vpos: int) -> int:
        label = QLabel("Vocabulary name: ")
        layout.addWidget(label, vpos, 0)
        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit, vpos, 1)
        self.line_edit.returnPressed.connect(self.ok_button)
        vpos += 1
        return vpos

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        self.button_names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 1)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(self.button_names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i])
        return vpos + 1

    #    def closeEvent(self, event: QCloseEvent):
    #        # do stuff
    #        event.accept()

    def ok_button(self) -> None:
        name = self.line_edit.text()
        if self.check_space_or_empty_str(name):
            self.display_warning(
                self, "Vocabulary name is empty! Please select a valid name"
            )
            return
        elif not self.validate_name(name):
            self.display_warning(
                self,
                "The vocabulary name cannot contain slashes, quotes or spaces. "
                "Please select a valid name",
            )
            return
        else:
            self.name = name
            self.close()
            self.app.exit()

    def cancel_button(self) -> None:
        self.name = None
        self.close()
        self.app.exit()

    def validate_name(self, name: str) -> bool:
        if re.search(r"[\\/\"\']|\s", name):
            return False
        return True
