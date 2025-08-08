import sys

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QVBoxLayout, QPushButton, QLabel, QLineEdit, QWidget, \
    QFormLayout, QComboBox
import lmfit

import MoreModels


class PeakSelector(QDialog):
    # Define a signal to send data back to the main window
    data_signal = pyqtSignal(object)

    def __init__(self, existing_names):
        super().__init__()
        self.setWindowTitle("PeakSelector")
        self.existing_names = existing_names

        # Set up the layout and widgets for the popup
        self.layout = QFormLayout()

        self.curr_name = "Name must be unique and without spaces"
        self.name_field = QLineEdit(self)
        self.name_field.textEdited.connect(self.check_name)
        self.name_label = QLabel(text="Choose a unique name")
        self.layout.addRow(self.name_label, self.name_field)

        self.implemented_models = {"Shirley background": lambda pref: lmfit.Model(MoreModels.calculate_shirley,prefix=pref, independent_vars=['x','y']),
                                    "Voigt": lambda pref: lmfit.models.VoigtModel(prefix=pref),
                                   "CasaLA": lambda pref: MoreModels.ConvGaussianSplitLorentz(prefix=pref)
                                   }
        self.combobox = QComboBox()
        self.combobox.addItems(self.implemented_models.keys())
        self.combobox_label = QLabel(text="Peak type")
        self.layout.addRow(self.combobox_label, self.combobox)

        self.ok_button = QPushButton("Add Peak", self)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        self.ok_button.setEnabled(False)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def check_name(self):
        error_style = """
            QLineEdit {
                background-color: #f8d7da; /* Pale red background */
                color: #721c24; /* Dark red text color */
                border: 1px solid #f5c6cb; /* Soft border color */
                padding: 5px;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #f1a7b3; /* Border changes when focused */
            }
        """
        default_style = """
            QLineEdit {
                background-color: transparent;
                color: black;
                border: 1px solid lightgray;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid blue; /* Blue border on focus */
            }
        """

        new_name = self.name_field.text()
        if (new_name in self.existing_names) or (new_name == "") or (new_name is None):
            self.ok_button.setEnabled(False)
            self.name_field.setStyleSheet(error_style)
        else:
            self.ok_button.setEnabled(True)
            self.curr_name = new_name
            self.name_field.setStyleSheet(default_style)

    def on_ok_clicked(self):
        peak_type = self.combobox.currentText()
        model = self.implemented_models[peak_type]
        self.data_signal.emit(model(self.curr_name))  # Emit the signal with the data
        self.accept()  # Close the popup


# 2. Define the Main Window (QMainWindow)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")

        # Set up the layout and widgets for the main window
        self.layout = QVBoxLayout()

        self.label = QLabel("Enter something in the popup", self)
        self.layout.addWidget(self.label)

        self.open_button = QPushButton("Open Popup", self)
        self.open_button.clicked.connect(self.open_popup)
        self.layout.addWidget(self.open_button)

        # Set the central widget
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def open_popup(self):
        # Create the popup window
        popup = PeakSelector(["Not allowed", "Also not allowed"])

        # Connect the signal from the popup to a method in the main window
        popup.data_signal.connect(self.on_data_received)

        # Show the popup
        popup.exec()

    def on_data_received(self, data):
        # This method is called when data is received from the popup
        self.label.setText(f"Received data: {data}")


# 3. Create the main application and window
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
