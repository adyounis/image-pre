from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import os
import cv2 as cv
sys.path.append("/Users/adeleyounis/Desktop/illumisonics/image-pre/")
from border_detection import BorderDetector
from skimage.exposure import is_low_contrast

class QPointList:
    def __init__(self):
        self.points = []  # Initialize an empty list to hold QPoint objects

    def add_point(self, x, y):
        """Add a new QPoint to the list."""
        self.points.append(QPoint(x, y))

    def remove_last_point(self):
        """Remove the last QPoint from the list."""
        if self.points:
            self.points.pop()

    def get_points(self):
        """Return the list of QPoint objects."""
        return self.points

class ImageWidget(QWidget):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.points = QPointList()
        self.setMouseTracking(True)
        self.manual_mode = False  # Flag to toggle between manual and automatic modes
        self.processed_image = None
        self.original_pixmap = pixmap
        self.set_initial_pixmap()

    def set_initial_pixmap(self):
        """Set the initial pixmap to the result of automatic edge detection."""
        if not self.processed_image:
            self.automatic_edge_detection()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if not self.pixmap.isNull():
            painter.drawPixmap(self.rect(), self.pixmap.scaled(self.size(), Qt.KeepAspectRatio))

        if self.processed_image is not None:
            painter.drawPixmap(self.rect(), self.processed_image.scaled(self.size(), Qt.KeepAspectRatio))

        # Draw the points on top of the image
        painter.setPen(QPen(Qt.red, 5))
        brush_colour = QColor(150, 0, 0, 70)  # (R, G, B, Alpha)
        painter.setBrush(brush_colour)
        painter.drawPoints(self.points.get_points())
        poly = QPolygon(self.points.get_points())
        painter.drawPolygon(poly)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        # Show tooltip for mouse position within the image widget
        if self.rect().contains(pos):
            QToolTip.showText(event.globalPos(), f"({pos.x()}, {pos.y()})")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if self.rect().contains(pos):
                if self.manual_mode:
                    # Add point in the image coordinate system
                    self.points.add_point(pos.x(), pos.y())
                    self.update()

    def undo(self):
        """Remove the last point and update the widget."""
        self.points.remove_last_point()
        self.update()
    
    def automatic_edge_detection(self):
        detector = BorderDetector()

        img_path = "/Users/adeleyounis/Desktop/illumisonics/lighting_exp/full/1_mask.BMP"
        img = cv.imread(img_path)
  
        # Convert the result to a QPixmap and update the widget
        height, width, _ = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.processed_image = pixmap
        self.setPixmap(self.processed_image)  # Initially set the processed image

    def setPixmap(self, pixmap):
        """Set the pixmap for the image widget and update the display."""
        self.pixmap = pixmap
        self.update()

    def enable_manual_mode(self):
        """Enable manual mode for user annotations."""
        self.manual_mode = True
        img_path = "/Users/adeleyounis/Desktop/illumisonics/lighting_exp/full/1.BMP"
        img = cv.imread(img_path)
        height, width, _ = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.processed_image = pixmap
        self.setPixmap(self.processed_image)  # Initially set the processed image


class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tissue Selector")
        self.resize(1200, 600)

        # Create main layout
        main_layout = QHBoxLayout(self)

        # Load the background image
        self.background_pixmap = QPixmap("/Users/adeleyounis/Desktop/illumisonics/lighting_exp/full/1.BMP")
        if self.background_pixmap.isNull():
            print("Error: Background pixmap is null. Check the image path.")

        # Create the image widget
        self.image_widget = ImageWidget(self.background_pixmap, self)
        self.image_widget.setFixedSize(900, 500)  # Set size for image area

        # Create the side section widget 
        side_section = QWidget(self)
        side_section.setFixedSize(300, 500)  # Set size for side section

        # create button layout
        button_layout = QVBoxLayout()
        self.undo_button = QPushButton("Undo", self)
        self.confirm_button = QPushButton("Confirm", self)
        self.override_button = QPushButton("Override automated edge detection", self)
        
        self.undo_button.clicked.connect(self.image_widget.undo)
        self.confirm_button.clicked.connect(self.confirm_edges)
        self.override_button.clicked.connect(self.enable_manual_mode)
        
        # add buttons to layout
        button_layout.addWidget(self.override_button)
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.confirm_button)
        side_section.setLayout(button_layout)

        # Add widgets to the main layout
        main_layout.addWidget(self.image_widget)
        main_layout.addWidget(side_section)

        self.setLayout(main_layout)
    
    def confirm_edges(self):
        QMessageBox.information(self, "Done outlining tissues", "Done! Processing tissue sections...")

    def enable_manual_mode(self):
        self.image_widget.enable_manual_mode()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Canvas()
    window.show()
    sys.exit(app.exec())
