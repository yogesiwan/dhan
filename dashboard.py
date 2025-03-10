from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                            QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, 
                            QFrame, QStackedWidget, QSizePolicy, QWIDGETSIZE_MAX)
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap, QPen, QTransform, QKeyEvent, QPainterPath
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QRectF, pyqtProperty
import os
import sys
import math

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class GlassmorphicCard(QFrame):
    def __init__(self, title, value, change, parent=None):
        super().__init__(parent)
        self.setObjectName("glassmorphicCard")
        
        self.setStyleSheet("""
            QFrame#glassmorphicCard {
                background-color: rgba(40, 50, 80, 0.5);
                border-radius: 10px;
                padding: 40px;
            }
        """)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        self.title = title
        self.value = value
        self.change = change
        
        try:
            self.change_value = float(change.strip('%').replace(',', '.'))
        except ValueError:
            self.change_value = 0
            
        self.change_color = "green" if self.change_value >= 0 else "red"
        
        self.front_widget = QWidget()
        self.back_widget = QWidget()
        
        self.setup_front_side()
        self.setup_back_side()
        
        self.stacked_layout = QStackedWidget(self)
        self.stacked_layout.addWidget(self.front_widget)
        self.stacked_layout.addWidget(self.back_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_layout)
        
        self._rotation = 0
        self.is_flipped = False
        
        self.setMouseTracking(True)
    
    def setup_front_side(self):
        layout = QVBoxLayout(self.front_widget)
        layout.setContentsMargins(0, 10, 10, 10)
        layout.setSpacing(10)
        
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        logo_label = QLabel()
        logo_path = f"logos/unique_{hash(self.title) % 83 + 1}.png"
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(40,40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_layout.addWidget(logo_label)
        
        title_layout.addSpacing(8)
        
        title_font_size = 25
        if any(stock in self.title for stock in ["Reliance", "TCS", "HDFC Bank", "Infosys", "Bharti Airtel", "ITC"]):
            title_font_size = int(title_font_size * 1.2)
            
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", title_font_size, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        layout.addSpacing(50)
        
        value_label = QLabel(self.value)
        value_label.setFont(QFont("Segoe UI", 25, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        change_layout = QHBoxLayout()
        change_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        change_label = QLabel(f"{self.change}")
        change_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        change_label.setStyleSheet(f"color: {self.change_color}; font-weight: bold;")
        
        arrow_label = QLabel()
        arrow_pixmap = QPixmap(resource_path("up_arrow.png" if self.change_value >= 0 else "down_arrow.png"))
        arrow_label.setPixmap(arrow_pixmap.scaled(35,35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        change_layout.addWidget(change_label)
        change_layout.addWidget(arrow_label)
        change_layout.addStretch()
        
        layout.addLayout(change_layout)
    
    def setup_back_side(self):
        layout = QVBoxLayout(self.back_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(f"{self.title} - Performance Graph")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        self.graph_widget = QFrame()
        self.graph_widget.setStyleSheet("background-color: transparent;")
        
        def paintEvent(event):
            painter = QPainter(self.graph_widget)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            width = self.graph_widget.width()
            height = self.graph_widget.height()
            
            painter.fillRect(0, 0, width, height, QColor(30, 40, 60, 200))
            
            painter.setPen(QPen(QColor("white"), 1))
            
            x_axis_y = int(height * 0.8)
            painter.drawLine(40, x_axis_y, width - 10, x_axis_y)
            painter.drawLine(40, 20, 40, x_axis_y)
            
            painter.setFont(QFont("Segoe UI", 8))
            
            time_periods = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
            x_step = (width - 50) / (len(time_periods) - 1)
            
            for i, period in enumerate(time_periods):
                x = 40 + i * x_step
                painter.drawText(QRectF(x - 15, x_axis_y + 5, 30, 20), Qt.AlignmentFlag.AlignCenter, period)
                painter.drawLine(int(x), x_axis_y, int(x), x_axis_y + 5)
            
            max_value = 10
            y_step = (x_axis_y - 20) / 4
            
            for i in range(5):
                y = x_axis_y - i * y_step
                value = i * max_value / 4
                painter.drawText(QRectF(0, y - 10, 35, 20), Qt.AlignmentFlag.AlignRight, f"{value:.1f}%")
                painter.drawLine(35, int(y), 40, int(y))
            
            painter.setPen(QPen(QColor(self.change_color), 2))
            
            import random
            random.seed(abs(hash(self.title)))
            
            points = []
            num_points = len(time_periods)
            
            trend_factor = self.change_value / 2
            
            for i in range(num_points):
                x = 40 + i * x_step
                base_value = random.uniform(2, 5)
                trend = trend_factor * (i / (num_points - 1))
                variation = random.uniform(-0.5, 0.5)
                value = base_value + trend + variation
                y = x_axis_y - (value / max_value) * (x_axis_y - 20)
                points.append(QPoint(int(x), int(y)))
            
            for i in range(1, len(points)):
                painter.drawLine(points[i-1], points[i])
            
            for point in points:
                painter.setBrush(QColor(self.change_color))
                painter.drawEllipse(point, 3, 3)
            
            last_point = points[-1]
            value_text = f"{self.change} ({self.value})"
            
            text_rect = QRectF(last_point.x() + 5, last_point.y() - 15, 100, 30)
            painter.fillRect(text_rect, QColor(30, 40, 60, 200))
            
            painter.setPen(QColor(self.change_color))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, value_text)
        
        self.graph_widget.paintEvent = paintEvent
        layout.addWidget(self.graph_widget)
    
    def _get_rotation(self):
        return self._rotation
    
    def _set_rotation(self, value):
        self._rotation = value
        
        if value >= 90 and not self.is_flipped:
            self.stacked_layout.setCurrentIndex(1)
            self.is_flipped = True
        elif value < 90 and self.is_flipped:
            self.stacked_layout.setCurrentIndex(0)
            self.is_flipped = False
        
        self.update()
    
    rotation = pyqtProperty(float, _get_rotation, _set_rotation)
    
    def mouseDoubleClickEvent(self, event):
        self.anim = QPropertyAnimation(self, b"rotation")
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if not self.is_flipped:
            self.anim.setStartValue(0)
            self.anim.setEndValue(180)
        else:
            self.anim.setStartValue(180)
            self.anim.setEndValue(0)
        
        self.anim.start()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._rotation != 0:
            painter.save()
            
            center_x = self.width() / 2
            center_y = self.height() / 2
            
            painter.translate(center_x, center_y)
            
            scale_factor = abs(math.cos(math.radians(self._rotation)))
            painter.scale(scale_factor, 1.0)
            
            transform = QTransform()
            transform.rotate(self._rotation, Qt.Axis.YAxis)
            painter.setTransform(transform, True)
            
            painter.translate(-center_x, -center_y)
            
            painter.restore()
        
        super().paintEvent(event)

    def resizeEvent(self, event):
        width = event.size().width()
        self.setFixedHeight(int(width * 3/4))
        super().resizeEvent(event)

class ContentWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.layout = QGridLayout(container)
        self.layout.setSpacing(20)
        
        container.setMaximumWidth(int(QApplication.primaryScreen().size().width() * 0.90))
        
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.layout.setColumnMinimumWidth(0, 0)
        self.layout.setColumnMinimumWidth(1, 0)
        self.layout.setColumnMinimumWidth(2, 0)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)

class IndicesContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("NSE Indic", parent)
        
        self.screens_stack = QStackedWidget()
        self.layout.addWidget(self.screens_stack, 0, 0, 1, 3)
        
        # NSE Indices data - 54 indices (9 screens × 6 cards)
        indices_data = [
            # Screen 1
            [
                {"title": "Nifty 50", "value": "₹ 22,419.95", "change": "0.79%"},
                {"title": "Nifty Bank", "value": "₹ 47,580.30", "change": "0.82%"},
                {"title": "Nifty IT", "value": "₹ 37,890.15", "change": "1.12%"},
                {"title": "Nifty Auto", "value": "₹ 19,875.40", "change": "0.45%"},
                {"title": "Nifty FMCG", "value": "₹ 52,640.75", "change": "0.28%"},
                {"title": "Nifty Pharma", "value": "₹ 15,980.60", "change": "-0.32%"}
            ],
            # Screen 2
            [
                {"title": "Nifty Metal", "value": "₹ 7,890.25", "change": "1.45%"},
                {"title": "Nifty Media", "value": "₹ 2,340.85", "change": "-0.78%"},
                {"title": "Nifty Realty", "value": "₹ 890.45", "change": "0.92%"},
                {"title": "Nifty PSU Bank", "value": "₹ 4,570.30", "change": "1.23%"},
                {"title": "Nifty Private Bank", "value": "₹ 23,780.55", "change": "0.67%"},
                {"title": "Nifty Energy", "value": "₹ 34,560.90", "change": "-0.45%"}
            ],
            # Screen 3
            [
                {"title": "Nifty Financial Services", "value": "₹ 19,870.35", "change": "0.56%"},
                {"title": "Nifty Consumer Durables", "value": "₹ 31,240.80", "change": "-0.23%"},
                {"title": "Nifty Oil & Gas", "value": "₹ 12,450.65", "change": "0.89%"},
                {"title": "Nifty Healthcare", "value": "₹ 9,780.40", "change": "0.34%"},
                {"title": "Nifty PSE", "value": "₹ 5,670.25", "change": "-0.67%"},
                {"title": "Nifty Infrastructure", "value": "₹ 6,890.15", "change": "0.78%"}
            ],
            # Screen 4
            [
                {"title": "Nifty MNC", "value": "₹ 21,340.75", "change": "0.45%"},
                {"title": "Nifty Services Sector", "value": "₹ 27,890.60", "change": "-0.34%"},
                {"title": "Nifty India Digital", "value": "₹ 8,970.30", "change": "1.56%"},
                {"title": "Nifty India Consumption", "value": "₹ 11,230.85", "change": "0.23%"},
                {"title": "Nifty CPSE", "value": "₹ 3,450.40", "change": "-0.89%"},
                {"title": "Nifty India Manufacturing", "value": "₹ 4,560.95", "change": "0.67%"}
            ],
            # Screen 5
            [
                {"title": "Nifty Midcap 50", "value": "₹ 12,780.45", "change": "0.91%"},
                {"title": "Nifty Midcap 100", "value": "₹ 15,670.30", "change": "-0.45%"},
                {"title": "Nifty Smallcap 50", "value": "₹ 5,890.65", "change": "1.23%"},
                {"title": "Nifty Smallcap 100", "value": "₹ 7,450.20", "change": "0.78%"},
                {"title": "Nifty Midcap Liquid 15", "value": "₹ 9,230.75", "change": "-0.56%"},
                {"title": "Nifty India Defence", "value": "₹ 6,780.90", "change": "1.12%"}
            ],
            # Screen 6
            [
                {"title": "Nifty Alpha 50", "value": "₹ 18,920.35", "change": "0.34%"},
                {"title": "Nifty50 Value 20", "value": "₹ 13,450.80", "change": "-0.67%"},
                {"title": "Nifty50 Equal Weight", "value": "₹ 16,780.65", "change": "0.89%"},
                {"title": "Nifty100 Equal Weight", "value": "₹ 14,560.40", "change": "0.45%"},
                {"title": "Nifty100 Low Volatility 30", "value": "₹ 11,890.25", "change": "-0.23%"},
                {"title": "Nifty Alpha Low-Volatility 30", "value": "₹ 8,670.60", "change": "1.34%"}
            ],
            # Screen 7
            [
                {"title": "Nifty200 Quality 30", "value": "₹ 17,890.30", "change": "0.67%"},
                {"title": "Nifty100 Quality 30", "value": "₹ 15,450.85", "change": "-0.45%"},
                {"title": "Nifty50 Dividend Points", "value": "₹ 12,670.40", "change": "0.91%"},
                {"title": "Nifty Dividend Opportunities 50", "value": "₹ 9,890.95", "change": "0.23%"},
                {"title": "Nifty Growth Sectors 15", "value": "₹ 7,450.20", "change": "-0.78%"},
                {"title": "Nifty100 ESG", "value": "₹ 5,670.75", "change": "1.12%"}
            ],
            # Screen 8
            [
                {"title": "Nifty100 Enhanced ESG", "value": "₹ 14,560.30", "change": "0.45%"},
                {"title": "Nifty200 Momentum 30", "value": "₹ 11,890.85", "change": "-0.34%"},
                {"title": "Nifty Commodities", "value": "₹ 8,970.40", "change": "1.23%"},
                {"title": "Nifty India Manufacturing", "value": "₹ 6,780.95", "change": "0.56%"},
                {"title": "Nifty Microcap 250", "value": "₹ 4,560.20", "change": "-0.89%"},
                {"title": "Nifty Total Market", "value": "₹ 3,450.75", "change": "0.67%"}
            ],
            # Screen 9
            [
                {"title": "Nifty500 Value 50", "value": "₹ 13,670.30", "change": "0.91%"},
                {"title": "Nifty Next 50", "value": "₹ 10,890.85", "change": "-0.45%"},
                {"title": "Nifty100 Liquid 15", "value": "₹ 8,450.40", "change": "1.23%"},
                {"title": "Nifty MidSmallcap 400", "value": "₹ 6,780.95", "change": "0.34%"},
                {"title": "Nifty200 Alpha 30", "value": "₹ 4,560.20", "change": "-0.67%"},
                {"title": "India VIX", "value": "₹ 786.0", "change": "-0.79%"}
            ]
        ]
        
        # Create all screens first
        self.screens = []
        for screen_data in indices_data:
            screen = QWidget()
            screen_layout = QGridLayout(screen)
            screen_layout.setSpacing(20)
            
            # Create and add all cards for this screen
            for card_index, card_data in enumerate(screen_data):
                card = GlassmorphicCard(
                    card_data["title"],
                    card_data["value"],
                    card_data["change"]
                )
                row = card_index // 3
                col = card_index % 3
                screen_layout.addWidget(card, row, col)
            
            for i in range(3):
                screen_layout.setColumnStretch(i, 1)
            for i in range(2):
                screen_layout.setRowStretch(i, 1)
            
            self.screens.append(screen)
            self.screens_stack.addWidget(screen)
        
        # Initialize all screens
        for screen in self.screens:
            screen.show()
            screen.hide()
        
        self.current_screen = 0
        self.screens_stack.setCurrentIndex(0)
        self.screens[0].show()
        
        self.old_pos = None
        self.animation_in_progress = False
        self.screens_stack.installEventFilter(self)
        
        def eventFilter(self, obj, event):
            if obj == self.screens_stack:
                if event.type() == event.Type.MouseButtonPress:
                    if not self.animation_in_progress:
                        self.old_pos = event.pos()
                    return True
                
                elif event.type() == event.Type.MouseButtonRelease:
                    if self.old_pos is not None and not self.animation_in_progress:
                        delta = event.pos().x() - self.old_pos.x()
                        if abs(delta) > 50:
                            if delta > 0 and self.current_screen > 0:
                                self.change_screen(self.current_screen - 1)
                            elif delta < 0 and self.current_screen < self.screens_stack.count() - 1:
                                self.change_screen(self.current_screen + 1)
                        self.old_pos = None
                    return True
            
            return super().eventFilter(obj, event)
        
        # Replace the eventFilter method
        self.eventFilter = eventFilter.__get__(self)
    
    def change_screen(self, index):
        if index != self.current_screen and not self.animation_in_progress:
            self.animation_in_progress = True
            
            direction = 1 if index > self.current_screen else -1
            current_widget = self.screens_stack.currentWidget()
            new_widget = self.screens_stack.widget(index)
            
            if current_widget and new_widget:
                # Pre-calculate positions to reduce computation during animation
                screen_width = self.screens_stack.width()
                start_pos = QPoint(direction * screen_width, 0)
                end_pos = QPoint(-direction * screen_width, 0)
                zero_pos = QPoint(0, 0)
                
                # Set fixed size once before animation
                widget_size = self.screens_stack.size()
                current_widget.setFixedSize(widget_size)
                new_widget.setFixedSize(widget_size)
                
                current_widget.show()
                new_widget.show()
                new_widget.raise_()
                
                current_widget.move(zero_pos)
                new_widget.move(start_pos)
                
                anim_group = QParallelAnimationGroup(self)
                
                # Optimize animation settings for smoother performance
                current_anim = QPropertyAnimation(current_widget, b"pos")
                current_anim.setDuration(150)  # Reduced duration
                current_anim.setStartValue(zero_pos)
                current_anim.setEndValue(end_pos)
                current_anim.setEasingCurve(QEasingCurve.Type.Linear)  # Linear for smoother motion
                
                new_anim = QPropertyAnimation(new_widget, b"pos")
                new_anim.setDuration(150)  # Reduced duration
                new_anim.setStartValue(start_pos)
                new_anim.setEndValue(zero_pos)
                new_anim.setEasingCurve(QEasingCurve.Type.Linear)  # Linear for smoother motion
                
                anim_group.addAnimation(current_anim)
                anim_group.addAnimation(new_anim)
                
                self.current_screen = index
                
                def on_animation_finished():
                    self.animation_in_progress = False
                    self.screens_stack.setCurrentIndex(index)
                    # Reset widget sizes after animation
                    current_widget.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
                    new_widget.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
                
                anim_group.finished.connect(on_animation_finished)
                anim_group.start()

class GlassmorphicUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial Dashboard")
        
        # Hide cursor for the entire application
        self.setCursor(Qt.CursorShape.BlankCursor)
        
        self.showFullScreen()
        
        self.background = None
        
        try:
            bg_path = resource_path("bg_blurlow.png")
            self.background = QPixmap(bg_path)
            if self.background.isNull():
                print(f"Failed to load background image from: {bg_path}")
                self.background = QPixmap(self.size())
                self.background.fill(QColor(20, 30, 50))
        except Exception as e:
            print(f"Error loading background: {e}")
            self.background = QPixmap(self.size())
            self.background.fill(QColor(20, 30, 50))
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 20)
        
        self.main_layout.addStretch(7)
        
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(15)
        
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel("NSE Indices")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label)
        
        center_layout.addLayout(title_layout)
        
        self.indices_content = IndicesContent()
        center_layout.addWidget(self.indices_content)
        
        self.main_layout.addWidget(center_container)
        
        self.main_layout.addStretch(13)
        
        self.key_sequence = ""
        self.exit_sequence = "yogi"
    
    def paintEvent(self, event):
        painter = QPainter(self)
        if hasattr(self, 'background') and self.background and not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        else:
            painter.fillRect(self.rect(), QColor(20, 30, 50))
    
    def keyPressEvent(self, event):
        if event.key() >= Qt.Key.Key_A and event.key() <= Qt.Key.Key_Z:
            self.key_sequence += chr(event.key()).lower()
            
            if self.key_sequence.endswith(self.exit_sequence):
                self.close()
            
            if len(self.key_sequence) > 10:
                self.key_sequence = self.key_sequence[-10:]
        
        if event.key() == Qt.Key.Key_Escape:
            self.showNormal()
        
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = GlassmorphicUI()
    window.show()
    app.exec()