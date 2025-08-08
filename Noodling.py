import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Matplotlib in PyQt6")
        self.setGeometry(100, 100, 800, 600)

        # Create the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Create the layout
        layout = QVBoxLayout(self.main_widget)

        # Create a matplotlib figure
        self.figure = plt.figure()

        # Use GridSpec to create subplots
        grid = self.figure.add_gridspec(2, 1, height_ratios=[1, 5])

        # Main axes (full width)
        ax1 = self.figure.add_subplot(grid[1])
        ax1.plot([0, 1, 2, 3], [0, 1, 4, 9])  # Example plot

        # Smaller axes (on top)
        ax2 = self.figure.add_subplot(grid[0], sharex=ax1)
        ax2.plot([0, 1, 2, 3], [0, -1, -2, -3])  # Example small plot

        # Hide x-axis for the smaller plot
        ax2.xaxis.set_visible(False)
        ax2.axhline(y=0, color='r', linestyle='--', linewidth=1)

        # Adjust the spacing between the plots using subplots_adjust()
        plt.subplots_adjust(hspace=0.0)  # Reduce vertical gap between subplots

        # Create a canvas and add it to the layout
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Show the window
        self.show()


# Application setup
app = QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec())
