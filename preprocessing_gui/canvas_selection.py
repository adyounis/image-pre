from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import os
import cv2 as cv
sys.path.append("/Users/adeleyounis/Desktop/illumisonics/image-pre/")
from mask_creation import ImageProcessor
from shapely import geometry

class QPointList:
    """ Class handles all events related to creating a list of Points for the polygon tracer"""
    def __init__(self):
        self.points = []
        self.undo_stack = []

    def clear_stack(self):
        self.points.clear()
        self.undo_stack.clear()

    def add_point(self, x, y):
        self.points.append(QPoint(x, y))
        self.undo_stack.clear()

    def undo_last_point(self):
        if self.points:
            last = self.points.pop()
            self.undo_stack.append(last)

    def redo_last_point(self):
        if self.undo_stack:
            last = self.undo_stack.pop()
            self.points.append(last)

    def get_points(self):
        return self.points

class ImageWidget(QWidget):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap  # paint canvas must be QPixmap element
        self.points = QPointList()
        self.image_processor = ImageProcessor()
        self.setMouseTracking(True)
        self.manual_mode = True  # flag for whether it is using autodetection or manual detection
        self.processed_image = None
    def paintEvent(self, event):
        """ Receives points from QPointsList Class item points, and draws polygon"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if not self.pixmap.isNull():
            painter.drawPixmap(self.rect(), self.pixmap.scaled(self.size(), Qt.KeepAspectRatio))

        if self.processed_image is not None:
            painter.drawPixmap(self.rect(), self.processed_image.scaled(self.size(), Qt.KeepAspectRatio))

        painter.setPen(QPen(Qt.red, 3))
        brush_colour = QColor(150, 0, 0, 70)  # (R, G, B, Alpha)
        painter.setBrush(brush_colour)
        painter.drawPoints(self.points.get_points())
        poly = QPolygon(self.points.get_points())
        painter.drawPolygon(poly)

    def paint_area(self):
        """ Calculates area of painted polygon"""
        poly = QPolygon(self.points.get_points())
        mm_area = 0.0
        if (poly.count()) > 2:  # start calculating area when at least 3 sides are present
            points_tuples = [(p.x(), p.y()) for p in poly]
            shapely_polygon = geometry.Polygon(points_tuples)
            pixel_area = shapely_polygon.area
            mm_per_pixel = 0.015  # TODO: adjust once real values come in (currently estimated to be 15 um)
            mm_area = pixel_area * (mm_per_pixel ** 2) * 7  # TODO: fix!!!! only multiplying by 7 rn because
        return mm_area

    def update_area(self):
        """Update the area and notify the parent Canvas."""
        mm_area = self.paint_area()
        if self.parent():
            self.parent().update_area_labels(mm_area)
        return mm_area

    def mouseMoveEvent(self, event):
        pos = event.pos()
        # show cursor for mouse position within the image widget
        if self.rect().contains(pos):
            # attach (x,y) coordinates to cursor
            QToolTip.showText(event.globalPos(), f"({pos.x()}, {pos.y()})")

    def mousePressEvent(self, event):
        # links mouse click to
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if self.rect().contains(pos):
                if self.manual_mode:
                    # Add point in the image coordinate system
                    self.points.add_point(pos.x(), pos.y())
                    self.update()
                    self.update_area()

    def undo(self):
        self.points.undo_last_point()
        self.update()
        self.update_area()

    def redo(self):
        self.points.redo_last_point()
        self.update()
        self.update_area()

    def setPixmap(self, pixmap):
        """Set the pixmap for the image widget and update the display."""
        self.pixmap = pixmap
        self.update()

    def enable_manual_mode(self):
        """Enable manual mode for user annotations."""
        img_path = "/home/adele/Downloads/1.BMP"
        if self.manual_mode == False:
            self.manual_mode = True
            img = cv.imread(img_path)
            height, width, _ = img.shape
            bytes_per_line = 3 * width
            q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            self.processed_image = pixmap
            self.setPixmap(self.processed_image)
            area = 0.0
        else:
            self.manual_mode = False
            img, area = self.image_processor.edge_detection(img_path)
            height, width, _ = img.shape
            bytes_per_line = 3 * width
            q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            self.processed_image = pixmap
            self.setPixmap(self.processed_image)
            self.points.clear_stack()
        return area

class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Tissue Selector")
        self.resize(1200, 600)

        # Create main layout
        main_layout = QHBoxLayout(self)

        # Create the top layout
        left_layout = QVBoxLayout()

        # Load the background image
        self.background_pixmap = QPixmap("/home/adele/Downloads/1.BMP")
        self.image_widget = ImageWidget(self.background_pixmap, self)
        self.image_widget.setMinimumSize(900, 500)

        # Create bottom section
        bottom_section = QWidget(self)
        bottom_section.setFixedSize(1220, 100)
        bottom_section.setStyleSheet('background-color: lightgray')

        self.undo_button = QPushButton("Undo", self)
        self.redo_button = QPushButton("Redo", self)
        self.override_button = QPushButton("Automated Selection", self)

        self.undo_button.clicked.connect(self.image_widget.undo)
        self.redo_button.clicked.connect(self.image_widget.redo)
        self.override_button.clicked.connect(self.enable_manual_mode)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.undo_button)
        bottom_layout.addWidget(self.redo_button)
        bottom_layout.addWidget(self.override_button)
        bottom_section.setLayout(bottom_layout)

        side_section = QWidget(self)
        side_section.setFixedSize(300, 800)  # Use minimum size instead of fixed size
        side_section.setStyleSheet('background-color: lightgray')

        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.clicked.connect(self.confirm_edges)

        self.label_pixmap = QPixmap("/home/adele/Downloads/label.png")
        self.label_image = QLabel(self)
        self.label_image.setFixedSize(295, 200)
        self.label_image.setPixmap(self.label_pixmap)
        self.label_image.setAlignment(Qt.AlignCenter)

        self.label_name = QLineEdit("Default name", self)

        self.area_label = QLabel("Area: 0.00 mm²", self)
        self.area_label.setFixedSize(295, 50)
        self.area_label.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("~0 minutes to scan", self)
        self.time_label.setMaximumSize(295, 50)
        self.time_label.setStyleSheet("QLabel{font-size: 8pt;}")
        self.time_label.setAlignment(Qt.AlignCenter)

        side_layout = QVBoxLayout()
        side_layout.addWidget(self.label_image)
        side_layout.addWidget(self.label_name)
        side_layout.addWidget(self.area_label)
        side_layout.addWidget(self.time_label)
        side_layout.addWidget(self.confirm_button)
        side_section.setLayout(side_layout)

        left_layout.addWidget(self.image_widget)
        left_layout.addWidget(bottom_section)

        main_layout.addLayout(left_layout)
        main_layout.addWidget(side_section)

        # Set the main layout for the window
        self.setLayout(main_layout)

    def confirm_edges(self):
        input_text = self.label_name.text()
        self.stored_name = input_text
        QMessageBox.information(self, f"{self.stored_name}", "Done! Processing tissue sections...")

    def enable_manual_mode(self):
        area = self.image_widget.enable_manual_mode()
        self.update_area_labels(area)

    def update_area_labels(self, area):
        self.area_label.setText(f"Area: {area:.2f} mm²")
        self.time_label.setText(f"~ {area*0.4:.2f} minutes to scan")  # TODO: figure out the actualy multiplier - currently based of 1cm^2 in 40 mins

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Canvas()
    window.show()
    sys.exit(app.exec())
