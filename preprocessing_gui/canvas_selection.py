from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyautogui

class QPointList:
    def __init__(self):
        self.points = []  # Initialize an empty list to hold QPoint objects

    def add_point(self, x, y):
        """Add a new QPoint to the list."""
        self.points.append(QPoint(x, y))

    def get_points(self):
        """Return the list of QPoint objects."""
        return self.points

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setMouseTracking(True)

        self.points = QPointList()
        self.background_pixmap = QPixmap("/home/adele/Downloads/test_canvas.png")  # Load your image here

    def initUI(self):
        self.setWindowTitle("Tissue Selector")
        self.resize(1000, 500)

        # self.central_widget = QWidget(self)
        # self.setCentralWidget(self.central_widget)
        # self.horizontal_layout = QHBoxLayout(self.central_widget)

        self.slide_section = QLabel(self)
        self.slide_section.setGeometry(30, 100, 700, 300)
        self.slide_section.setAlignment(Qt.AlignLeft)
        self.slide_section.setStyleSheet("background-image : url(/home/adele/Downloads/test_canvas.png)")
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawPixmap(self.rect(), self.slide_section)

        painter.setPen(QPen(Qt.red, 5))
        brush_colour = QColor(150, 0, 0, 70)  #(R, G, B, Alpha)
        painter.setBrush(brush_colour)
        painter.drawPoints(self.points.get_points())
        poly = QPolygon(self.points.get_points())
        painter.drawPolygon(poly)
    def mouseMoveEvent(self, event):
        pos = pyautogui.position()
        # pos = self.mapToGlobal(pos)
        point = QPoint(pos[0], pos[1])
        # print(f"Mouse Position: ({point})")  # Print mouse position
        QToolTip.showText(point, f"({pos[0]}, {pos[1]})")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.points.add_point(event.x(), event.y())  # Add point relative to widget
            self.update()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = Canvas()
    window.show()
    sys.exit(app.exec())
