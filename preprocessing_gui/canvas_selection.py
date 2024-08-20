from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import os
import cv2 as cv
sys.path.append("/Users/adeleyounis/Desktop/illumisonics/image-pre/")
from mask_creation import ImageProcessor
from shapely import geometry
from create_section_grid import SectionProcessor
from raw_image_processing import get_label_section, get_tissue_section, get_tissue_mask

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
        self._pixmap = pixmap  # global pixmap
        self.points = QPointList()  # call our QPointList creator class
        self.image_processor = ImageProcessor()  # call image processor class
        self.setMouseTracking(True)  # enable mouse track

        self.auto_mode_points = []
        self.dragging_point = None  # track what point we are holding
        self.drawing_polygon = True  # Flag to determine if we are drawing a polygon

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if not self._pixmap.isNull():
            painter.drawPixmap(self.rect(), self._pixmap.scaled(self.size(), Qt.KeepAspectRatio))

        # Draw manual points
        painter.setPen(QPen(Qt.red, 3))
        brush_colour = QColor(150, 0, 0, 70)
        painter.setBrush(brush_colour)
        manual_points = self.points.get_points()
        painter.drawPoints(manual_points)
        if manual_points:
            poly = QPolygon(manual_points)
            painter.drawPolygon(poly)

        # Draw auto mode points
        if len(self.auto_mode_points) > 0:
            brush_colour = QColor(150, 0, 0, 70)
            painter.setBrush(brush_colour)
            auto_mode_qpoints = [QPoint(pt[0], pt[1]) for pt in self.auto_mode_points]
            poly = QPolygon(auto_mode_qpoints)
            painter.drawPolygon(poly)
            for pt in self.auto_mode_points:
                x, y = pt
                painter.drawEllipse(QPointF(x, y), 5, 5)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            if not self.drawing_polygon:
                # print("mouse on drag mode")
                auto_mode_qpoints = [QPoint(pt[0], pt[1]) for pt in self.auto_mode_points]
                for i, point in enumerate(auto_mode_qpoints):
                    if (point - pos).manhattanLength() < 20:
                        self.dragging_point = i
                        break

            elif self.drawing_polygon:
                # print("mouse on draw mode")
                x, y = pos.x(), pos.y()
                # print(f"Adding point: ({x}, {y})")
                self.points.add_point(x, y)
                self.update()  # repaint
                self.update_area()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.dragging_point is not None:
            if 0 <= self.dragging_point < len(self.auto_mode_points):
                self.auto_mode_points[self.dragging_point] = (pos.x(), pos.y())
                self.update()
                self.update_area()

    def mouseReleaseEvent(self, event):
        if self.dragging_point is not None:
            self.dragging_point = None

    def start_drawing_polygon(self):
        """Start drawing a polygon."""

        self.drawing_polygon = True
        self.points.clear_stack()  # Clear existing points if any
        self.update()
        # print("start drawing polygon")

    def stop_drawing_polygon(self):
        """Stop drawing a polygon."""
        self.drawing_polygon = False
        self.update()
        # print("Stopped drawing polygon")

    def paint_area(self):
        """ Calculates area of painted polygon"""
        if not self.drawing_polygon:
            qpoints = [QPoint(pt[0], pt[1]) for pt in self.auto_mode_points]
        elif self.drawing_polygon:
            # print("getting area as u draw")
            qpoints = self.points.get_points()

        poly = QPolygon(qpoints)
        mm_area = 0.0
        if (poly.count()) > 2:  # start calculating area when at least 3 sides are present
            points_tuples = [(p.x(), p.y()) for p in poly]
            shapely_polygon = geometry.Polygon(points_tuples)
            pixel_area = shapely_polygon.area
            mm_per_pixel_w = 0.0146
            mm_per_pixel_h = 0.0129
            mm_area = pixel_area * (mm_per_pixel_w * mm_per_pixel_h)
        return mm_area, qpoints

    def update_area(self):
        """Update the area and notify the parent Canvas."""
        mm_area, qpoints = self.paint_area()
        if self.parent():
            self.parent().update_area_labels(mm_area)
        return mm_area, qpoints

    def undo(self):
        self.points.undo_last_point()
        self.update()
        self.update_area()

    def redo(self):
        self.points.redo_last_point()
        self.update()
        self.update_area()

    def set_auto_mode_points(self, points):
        """Set the auto mode points and trigger a redraw."""
        self.auto_mode_points = points
        self.update()

    def setPixmap(self, pixmap):
        """Set the pixmap for the image widget and update the display."""
        self._pixmap = pixmap
        self.update()

    def clear_drawing_stack(self):
        self.points.clear_stack()  # This should clear any drawn points or shapes
        self.update()

    def enable_manual_mode(self):
        """Prepare the widget for manual mode."""
        self.auto_mode_points = []  # Clear auto mode points
        self.points.clear_stack()  # Clear manual points if any
        self.drawing_polygon = False
        self.update()


class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_coords = []
        self.manual_mode = True  # Initialize in manual mode
        self.auto_mode = False  # Initialize auto mode as False

    def initUI(self):
        self.raw_img_path = "/home/adele/Downloads/pretty_pics/L.BMP"
        self.img_path = get_tissue_section(self.raw_img_path)
        self.label_path = get_label_section(self.raw_img_path)

        self.setWindowTitle("Tissue Selector")

        # main layout
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        self.background_pixmap = QPixmap(self.img_path)
        self.image_widget = ImageWidget(self.background_pixmap, self)
        self.image_widget.setMinimumSize(3746, 1601)

        bottom_section = QWidget(self)
        bottom_section.setFixedSize(3000, 100)
        bottom_section.setStyleSheet('background-color: lightgray')

        self.undo_button = QPushButton("Undo", self)
        self.redo_button = QPushButton("Redo", self)
        self.override_button = QPushButton("Automated Selection", self)
        self.manual_button = QPushButton("Manual Selection", self)

        self.undo_button.clicked.connect(self.image_widget.undo)
        self.redo_button.clicked.connect(self.image_widget.redo)
        self.override_button.clicked.connect(self.switch_to_auto_mode)
        self.manual_button.clicked.connect(self.switch_to_manual_mode)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.undo_button)
        bottom_layout.addWidget(self.redo_button)
        bottom_layout.addWidget(self.override_button)
        bottom_layout.addWidget(self.manual_button)
        bottom_section.setLayout(bottom_layout)

        side_section = QWidget(self)
        side_section.setFixedSize(350, 800)
        side_section.setStyleSheet('background-color: lightgray')

        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.clicked.connect(self.confirm_edges)
        self.confirm_button.clicked.connect(self.save_selection)

        self.label_pixmap = QPixmap(self.label_path)
        self.label_image = QLabel(self)
        self.label_image.setFixedSize(323, 230)
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

    def switch_to_auto_mode(self):
        # print("switching to auto")
        self.auto_mode = True
        self.manual_mode = False
        self.image_widget.clear_drawing_stack()
        self.image_widget.setMouseTracking(True)
        self.image_widget.stop_drawing_polygon()  # Ensure no polygon drawing

        img_path = self.img_path
        img, area, pts = get_tissue_mask(img_path)

        self.image_widget.processed_image = QPixmap()
        self.image_widget.setPixmap(self.background_pixmap)

        self.image_widget.clear_drawing_stack()
        self.auto_mode_pts = pts.reshape(-1, 2)
        self.image_widget.set_auto_mode_points(self.auto_mode_pts)

        self.update_area_labels(area)
        return self.auto_mode_pts

    def switch_to_manual_mode(self):
        # print("switching to manual, draw your shape")
        self.update_area_labels(0.0)  # reset area text
        self.image_widget.clear_drawing_stack()  # get rid of any points

        self.image_widget.setMouseTracking(True)  # enable drawing :)
        self.image_widget.enable_manual_mode()
        self.image_widget.start_drawing_polygon()

        self.image_widget.processed_image = QPixmap()
        self.image_widget.setPixmap(self.background_pixmap)


    def draw_points_on_image_widget(self, points):
        points = points.reshape(-1, 2)  # initially a weird format
        self.image_widget.set_auto_mode_points(points)

    def confirm_edges(self):
        input_text = self.label_name.text()
        self.stored_name = input_text
        QMessageBox.information(self, f"{self.stored_name}", "Done! Processing tissue sections...")


    def update_area_labels(self, area):
        self.area_label.setText(f"Area: {area:.2f} mm²")
        self.time_label.setText(
            f"~ {area * 0.4:.2f} minutes to scan")  # TODO: figure out the actual multiplier - currently based on 1cm² in 40 mins

    def save_selection(self):
        if self.manual_mode:
            print("got some manual coords")

            points = self.image_widget.points.get_points()
            perimeter_points = []

            if len(points) < 3:
                return

            for i in range(len(points)):
                # get pts along the line of
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]

                line = QLineF(p1, p2)
                length = line.length()

                num_points = int(length / 10)
                for j in range(num_points + 1):
                    t = j / num_points
                    x = p1.x() + t * (p2.x() - p1.x())
                    y = p1.y() + t * (p2.y() - p1.y())
                    perimeter_points.append(QPointF(x, y))

            with open("/home/adele/Development/illumiSonics/image-pre/selection_coords.txt", 'w') as file:
                for pt in perimeter_points:
                    x = pt.x() * 58.20
                    y = pt.y() * 51.64
                    scaled_pt = f"{x:0.2f} {y:0.2f}"
                    file.write(scaled_pt + '\n')

        if self.auto_mode:
            _, pts = self.image_widget.update_area()
            print(pts)
            perimeter_points = []

            if len(pts) < 3:
                return

            for i in range(len(pts)):
                # get pts along the line of
                p1 = pts[i]
                p2 = pts[(i + 1) % len(pts)]

                line = QLineF(p1, p2)
                length = line.length()

                num_points = int(length / 10)
                for j in range(num_points + 1):
                    t = j / num_points
                    x = p1.x() + t * (p2.x() - p1.x())
                    y = p1.y() + t * (p2.y() - p1.y())
                    perimeter_points.append(QPointF(x, y))

            with open("/home/adele/Development/illumiSonics/image-pre/selection_coords.txt", 'w') as file:
                for pt in perimeter_points:
                    x = pt.x() * 58.20
                    y = pt.y() * 51.64
                    scaled_pt = f"{x:0.2f} {y:0.2f}"
                    file.write(scaled_pt + '\n')

        ex = SectionProcessor()
        sections = ex.get_tissue_sections()
        sorted_sections = ex.sort_with_direction_flip(sections)
        sorted_sections = ex.determine_section_focus(sorted_sections)
        ex.export_sections(sorted_sections)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Canvas()
    window.show()
    sys.exit(app.exec())
