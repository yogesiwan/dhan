from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                            QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, 
                            QFrame, QStackedWidget, QPushButton, QScrollArea, QSizePolicy)
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap, QIcon, QPen, QTransform, QKeyEvent, QLinearGradient, QPainterPath
from PyQt5.QtCore import Qt, QTime, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint, QParallelAnimationGroup, QRectF, pyqtProperty
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
        
        # Reduce transparency by 20% (increase opacity from 0.7 to 0.9)
        self.setStyleSheet("""
            QFrame#glassmorphicCard {
                background-color: rgba(40, 50, 80, 0.5);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Set size policy to expand while maintaining 2:1 ratio
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        # Store card data for graph
        self.title = title
        self.value = value
        self.change = change
        
        # Parse change percentage
        try:
            self.change_value = float(change.strip('%').replace(',', '.'))
        except ValueError:
            self.change_value = 0
            
        self.change_color = "green" if self.change_value >= 0 else "red"
        
        # Create front and back widgets
        self.front_widget = QWidget()
        self.back_widget = QWidget()
        
        # Setup front side (original card content)
        self.setup_front_side()
        
        # Setup back side (graph with axes)
        self.setup_back_side()
        
        # Setup stacked layout for front and back of card
        self.stacked_layout = QStackedWidget(self)
        self.stacked_layout.addWidget(self.front_widget)
        self.stacked_layout.addWidget(self.back_widget)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_layout)
        
        # Set up rotation property and animation
        self._rotation = 0
        self.is_flipped = False
        
        # Enable mouse tracking for double click
        self.setMouseTracking(True)
    
    def setup_front_side(self):
        # Setup layout for front side
        layout = QVBoxLayout(self.front_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title with logo - left aligned
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Add company logo next to title
        logo_label = QLabel()
        logo_path = f"logos/unique_{hash(self.title) % 83 + 1}.png"  # Map title to a logo file
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_layout.addWidget(logo_label)
        
        # Add spacing between logo and title
        title_layout.addSpacing(8)
        
        # Title - make stock names 20% larger but with larger base size
        title_font_size = 17  # Increased from 14 to make it 20% larger
        if any(stock in self.title for stock in ["Reliance", "TCS", "HDFC Bank", "Infosys", "Bharti Airtel", "ITC"]):
            title_font_size = int(title_font_size * 1.2)
            
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", title_font_size, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Add spacing to push price down by 30%
        layout.addSpacing(30)
        
        # Value - left aligned and larger
        value_label = QLabel(self.value)
        value_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(value_label)
        
        # Add stretch to push change info to bottom
        layout.addStretch()
        
        # Change with icon at the bottom
        change_layout = QHBoxLayout()
        change_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Change label with bolder font but smaller size
        change_label = QLabel(f"{self.change}")
        change_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        change_label.setStyleSheet(f"color: {self.change_color}; font-weight: bold;")
        
        # Use PNG images for arrows with smaller size
        arrow_label = QLabel()
        arrow_pixmap = QPixmap(resource_path("up_arrow.png" if self.change_value >= 0 else "down_arrow.png"))
        arrow_label.setPixmap(arrow_pixmap.scaled(12, 12, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        change_layout.addWidget(change_label)
        change_layout.addWidget(arrow_label)
        change_layout.addStretch()
        
        layout.addLayout(change_layout)
    
    def setup_back_side(self):
        # Setup layout for back side
        layout = QVBoxLayout(self.back_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title for back side
        title_label = QLabel(f"{self.title} - Performance Graph")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Graph widget that takes full card size
        self.graph_widget = QFrame()
        self.graph_widget.setStyleSheet("background-color: transparent;")
        
        # Custom paint method for detailed graph
        def paintEvent(event):
            painter = QPainter(self.graph_widget)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            width = self.graph_widget.width()
            height = self.graph_widget.height()
            
            # Draw background with reduced transparency (increased opacity)
            painter.fillRect(0, 0, width, height, QColor(30, 40, 60, 200))  # Increased from 150 to 200
            
            # Draw axes
            painter.setPen(QPen(QColor("white"), 1))
            
            # X-axis
            x_axis_y = int(height * 0.8)
            painter.drawLine(40, x_axis_y, width - 10, x_axis_y)
            
            # Y-axis
            painter.drawLine(40, 20, 40, x_axis_y)
            
            # Draw axis labels
            painter.setFont(QFont("Segoe UI", 8))
            
            # X-axis labels (time periods)
            time_periods = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
            x_step = (width - 50) / (len(time_periods) - 1)
            
            for i, period in enumerate(time_periods):
                x = 40 + i * x_step
                painter.drawText(QRectF(x - 15, x_axis_y + 5, 30, 20), Qt.AlignmentFlag.AlignCenter, period)
                # Tick mark
                painter.drawLine(int(x), x_axis_y, int(x), x_axis_y + 5)
            
            # Y-axis labels (values) - increased space for labels
            max_value = 10  # Percentage range
            y_step = (x_axis_y - 20) / 4
            
            for i in range(5):
                y = x_axis_y - i * y_step
                value = i * max_value / 4
                # Increased width for percentage labels
                painter.drawText(QRectF(0, y - 10, 35, 20), Qt.AlignmentFlag.AlignRight, f"{value:.1f}%")
                # Tick mark
                painter.drawLine(35, int(y), 40, int(y))
            
            # Draw graph line
            painter.setPen(QPen(QColor(self.change_color), 2))
            
            # Generate data points for the graph
            import random
            random.seed(abs(hash(self.title)))  # Use title as seed for consistent randomness
            
            points = []
            num_points = len(time_periods)
            
            # Generate points with a trend based on change value
            trend_factor = self.change_value / 2  # Scale down for smoother graph
            
            for i in range(num_points):
                x = 40 + i * x_step  # Adjusted x position
                
                # Base value with some randomness
                base_value = random.uniform(2, 5)
                
                # Add trend component that increases over time
                trend = trend_factor * (i / (num_points - 1))
                
                # Add some random variation
                variation = random.uniform(-0.5, 0.5)
                
                # Calculate final value
                value = base_value + trend + variation
                
                # Map to y coordinate (invert because y-axis goes down)
                y = x_axis_y - (value / max_value) * (x_axis_y - 20)
                
                points.append(QPoint(int(x), int(y)))
            
            # Draw the line connecting points
            for i in range(1, len(points)):
                painter.drawLine(points[i-1], points[i])
            
            # Draw points
            for point in points:
                painter.setBrush(QColor(self.change_color))
                painter.drawEllipse(point, 3, 3)
            
            # Draw current value
            last_point = points[-1]
            value_text = f"{self.change} ({self.value})"
            
            # Draw text background
            text_rect = QRectF(last_point.x() + 5, last_point.y() - 15, 100, 30)
            painter.fillRect(text_rect, QColor(30, 40, 60, 200))
            
            # Draw text
            painter.setPen(QColor(self.change_color))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, value_text)
        
        # Assign custom paint event
        self.graph_widget.paintEvent = paintEvent
        
        layout.addWidget(self.graph_widget)
    
    # Define rotation property
    def _get_rotation(self):
        return self._rotation
    
    def _set_rotation(self, value):
        self._rotation = value
        
        # Flip the card at 90 degrees
        if value >= 90 and not self.is_flipped:
            self.stacked_layout.setCurrentIndex(1)
            self.is_flipped = True
        elif value < 90 and self.is_flipped:
            self.stacked_layout.setCurrentIndex(0)
            self.is_flipped = False
        
        # Update the rotation effect
        self.update()
    
    rotation = pyqtProperty(float, _get_rotation, _set_rotation)
    
    def mouseDoubleClickEvent(self, event):
        # Create rotation animation
        self.anim = QPropertyAnimation(self, b"rotation")
        self.anim.setDuration(500)  # 500ms for smooth animation
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set start and end values based on current state
        if not self.is_flipped:
            self.anim.setStartValue(0)
            self.anim.setEndValue(180)
        else:
            self.anim.setStartValue(180)
            self.anim.setEndValue(0)  # Rotate back to 0 degrees
        
        # Start animation
        self.anim.start()
    
    def paintEvent(self, event):
        # Create a painter for the entire card
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Don't draw the background here - let the stacked widget handle it
        
        # Apply 3D rotation to the entire card
        if self._rotation != 0:
            # Save the current state
            painter.save()
            
            # Calculate center point
            center_x = self.width() / 2
            center_y = self.height() / 2
            
            # Translate to center
            painter.translate(center_x, center_y)
            
            # Apply perspective effect (scale based on rotation)
            scale_factor = abs(math.cos(math.radians(self._rotation)))
            painter.scale(scale_factor, 1.0)
            
            # Rotate around Y axis (vertical axis)
            # We need to use a QTransform for 3D-like rotation
            transform = QTransform()
            transform.rotate(self._rotation, Qt.Axis.YAxis)
            painter.setTransform(transform, True)
            
            # Translate back
            painter.translate(-center_x, -center_y)
            
            # Restore the painter state after applying transformations
            painter.restore()
        
        # Let the normal painting happen
        super().paintEvent(event)

    def resizeEvent(self, event):
        # Maintain 2:1 ratio during resize
        width = event.size().width()
        self.setFixedHeight(width // 2)
        super().resizeEvent(event)

class NewsCard(QFrame):
    def __init__(self, title, description, time, parent=None):
        super().__init__(parent)
        self.setObjectName("newsCard")
        self.setStyleSheet("""
            QFrame#newsCard {
                background-color: rgba(40, 50, 80, 0.7);
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title with icon
        title_layout = QHBoxLayout()
        
        # Add news icon
        icon_label = QLabel("📰")
        icon_label.setFont(QFont("Segoe UI", 17))
        title_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))  # Increased from 14
        title_label.setStyleSheet("color: white;")
        title_label.setWordWrap(True)
        title_layout.addWidget(title_label, 1)
        
        layout.addLayout(title_layout)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 14))  # Increased from 12
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Time with icon
        time_layout = QHBoxLayout()
        
        time_icon = QLabel("🕒")
        time_icon.setFont(QFont("Segoe UI", 12))
        time_icon.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        time_layout.addWidget(time_icon)
        
        time_label = QLabel(time)
        time_label.setFont(QFont("Segoe UI", 12))  # Increased from 10
        time_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        time_layout.addWidget(time_label)
        time_layout.addStretch()
        
        layout.addLayout(time_layout)

class ContentWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        
        # Create a container widget to center the grid and control its size
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add container to main layout with alignment
        main_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Setup grid layout for the container
        self.layout = QGridLayout(container)
        self.layout.setSpacing(20)  # Keep consistent spacing between cards
        
        # Set the container to take 90% of the parent width
        container.setMaximumWidth(int(QApplication.primaryScreen().size().width() * 0.90))
        
        # Set equal margins for better spacing
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Force uniform column widths
        self.layout.setColumnMinimumWidth(0, 0)
        self.layout.setColumnMinimumWidth(1, 0)
        self.layout.setColumnMinimumWidth(2, 0)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)

class IndicesContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("NSE Indices", parent)
        
        # Create a stacked widget for multiple screens
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
        
        # Create screens and add cards
        for screen_index, screen_data in enumerate(indices_data):
            # Create a widget for this screen
            screen = QWidget()
            screen_layout = QGridLayout(screen)
            screen_layout.setSpacing(20)
            
            # Add cards to the screen
            for card_index, card_data in enumerate(screen_data):
                card = GlassmorphicCard(
                    card_data["title"],
                    card_data["value"],
                    card_data["change"]
                )
                row = card_index // 3
                col = card_index % 3
                screen_layout.addWidget(card, row, col)
            
            # Set equal column and row stretches
            for i in range(3):
                screen_layout.setColumnStretch(i, 1)
            for i in range(2):
                screen_layout.setRowStretch(i, 1)
            
            # Add screen to stacked widget
            self.screens_stack.addWidget(screen)
        
        # Add swipe navigation
        self.current_screen = 0
        self.screens_stack.installEventFilter(self)
        self.old_pos = None
        self.animation_in_progress = False  # Add flag to track animation state
    
    def eventFilter(self, obj, event):
        if obj == self.screens_stack:
            if event.type() == event.Type.MouseButtonPress:
                # Only start new swipe if no animation is in progress
                if not self.animation_in_progress:
                    self.old_pos = event.pos()
                return True
            
            elif event.type() == event.Type.MouseButtonRelease:
                if self.old_pos is not None and not self.animation_in_progress:
                    delta = event.pos().x() - self.old_pos.x()
                    if abs(delta) > 50:  # Reduced minimum swipe distance for better responsiveness
                        if delta > 0 and self.current_screen > 0:
                            self.change_screen(self.current_screen - 1)
                        elif delta < 0 and self.current_screen < self.screens_stack.count() - 1:
                            self.change_screen(self.current_screen + 1)
                    self.old_pos = None
                return True
            
        return super().eventFilter(obj, event)
    
    def change_screen(self, index):
        if index != self.current_screen and not self.animation_in_progress:
            # Set animation flag
            self.animation_in_progress = True
            
            # Animate screen change
            direction = 1 if index > self.current_screen else -1
            current_widget = self.screens_stack.currentWidget()
            new_widget = self.screens_stack.widget(index)
            
            if current_widget and new_widget:
                # Setup animation
                current_widget.show()
                new_widget.show()
                new_widget.raise_()
                
                screen_width = self.screens_stack.width()
                current_widget.move(0, 0)
                new_widget.move(direction * screen_width, 0)
                
                # Create animation group
                anim_group = QParallelAnimationGroup(self)
                
                # Current widget animation
                current_anim = QPropertyAnimation(current_widget, b"pos")
                current_anim.setDuration(200)  # Reduced duration for faster animation
                current_anim.setStartValue(QPoint(0, 0))
                current_anim.setEndValue(QPoint(-direction * screen_width, 0))
                current_anim.setEasingCurve(QEasingCurve.Type.OutQuad)  # Changed to simpler easing curve
                
                # New widget animation
                new_anim = QPropertyAnimation(new_widget, b"pos")
                new_anim.setDuration(200)  # Reduced duration for faster animation
                new_anim.setStartValue(QPoint(direction * screen_width, 0))
                new_anim.setEndValue(QPoint(0, 0))
                new_anim.setEasingCurve(QEasingCurve.Type.OutQuad)  # Changed to simpler easing curve
                
                # Add animations to group
                anim_group.addAnimation(current_anim)
                anim_group.addAnimation(new_anim)
                
                # Update current screen index
                self.current_screen = index
                
                # Reset animation flag when finished
                def on_animation_finished():
                    self.animation_in_progress = False
                    self.screens_stack.setCurrentIndex(index)
                
                anim_group.finished.connect(on_animation_finished)
                
                # Start animation
                anim_group.start()

class StocksContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("Top Stocks", parent)
        
        # Card data for Stocks page
        cards_data = [
            {"title": "Reliance", "value": "₹ 2,843.25", "change": "1.25%", "pos": (0, 0)},
            {"title": "TCS", "value": "₹ 3,576.50", "change": "0.75%", "pos": (0, 1)},
            {"title": "HDFC Bank", "value": "₹ 1,687.40", "change": "-0.45%", "pos": (0, 2)},
            {"title": "Infosys", "value": "₹ 1,523.15", "change": "1.15%", "pos": (1, 0)},
            {"title": "Bharti Airtel", "value": "₹ 945.30", "change": "0.65%", "pos": (1, 1)},
            {"title": "ITC", "value": "₹ 425.85", "change": "-0.25%", "pos": (1, 2)}
        ]
        
        # Create and add cards
        for card_data in cards_data:
            card = GlassmorphicCard(
                card_data["title"], 
                card_data["value"], 
                card_data["change"]
            )
            row, col = card_data["pos"]
            self.layout.addWidget(card, row, col)
            
        # Set column and row stretches to be equal
        for i in range(3):  # 3 columns
            self.layout.setColumnStretch(i, 1)
        for i in range(2):  # 2 rows
            self.layout.setRowStretch(i, 1)

class NewsContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("Market News", parent)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Create container widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Sample news data
        news_data = [
            {
                "title": "Market Rally Continues: Sensex, Nifty Hit New Highs",
                "description": "Indian markets continued their bullish trend with both Sensex and Nifty touching new all-time highs, driven by strong institutional buying and positive global cues.",
                "time": "2 hours ago"
            },
            {
                "title": "RBI Maintains Repo Rate, Focuses on Growth",
                "description": "The Reserve Bank of India kept the repo rate unchanged at 6.5% in its latest monetary policy meeting, maintaining its focus on supporting economic growth while keeping inflation in check.",
                "time": "4 hours ago"
            },
            {
                "title": "IT Sector Shows Strong Recovery",
                "description": "Major IT companies reported better-than-expected Q3 results, indicating a strong recovery in the technology sector. TCS and Infosys lead the gains.",
                "time": "6 hours ago"
            },
            {
                "title": "FII Investment Reaches 6-Month High",
                "description": "Foreign Institutional Investors (FIIs) have pumped in over ₹25,000 crore in Indian equities this month, marking the highest monthly inflow in the last six months.",
                "time": "8 hours ago"
            },
            {
                "title": "New IPOs Set to Hit Market",
                "description": "Several companies have filed their draft red herring prospectus (DRHP) with SEBI, indicating a busy season ahead for the primary market.",
                "time": "10 hours ago"
            }
        ]
        
        # Create and add news cards
        for news in news_data:
            card = NewsCard(
                news["title"],
                news["description"],
                news["time"]
            )
            scroll_layout.addWidget(card)
        
        # Add stretch to push cards to the top
        scroll_layout.addStretch()
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        
        # Add scroll area to main layout
        self.layout.addWidget(scroll_area, 0, 0, 1, 3)

class MainMenuButton(QFrame):
    def __init__(self, icon_text, title, parent=None):
        super().__init__(parent)
        self.setObjectName("menuButton")
        self.setStyleSheet("""
            QFrame#menuButton {
                background-color: rgba(40, 50, 80, 0.9);
                border-radius: 15px;
                padding: 10px;
            }
            QFrame#menuButton:hover {
                background-color: rgba(50, 60, 100, 0.9);
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        # Set fixed size
        self.setFixedSize(180, 180)
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon_label = QLabel(icon_text)
        icon_label.setFont(QFont("Segoe UI", 48))
        icon_label.setStyleSheet("color: white;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Store the title for reference
        self.title = title
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Store callback function
        self.click_callback = None
        
    def set_click_callback(self, callback):
        self.click_callback = callback
        
    def mousePressEvent(self, event):
        # Add pressed effect
        self.setStyleSheet("""
            QFrame#menuButton {
                background-color: rgba(60, 70, 110, 0.9);
                border-radius: 15px;
                padding: 10px;
            }
        """)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        # Restore normal style
        self.setStyleSheet("""
            QFrame#menuButton {
                background-color: rgba(40, 50, 80, 0.9);
                border-radius: 15px;
                padding: 10px;
            }
            QFrame#menuButton:hover {
                background-color: rgba(50, 60, 100, 0.9);
            }
        """)
        
        # Call the callback if it exists and cursor is still over the button
        if self.click_callback and self.rect().contains(event.pos()):
            self.click_callback()
            
        super().mouseReleaseEvent(event)

class MainMenuContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("Financial Dashboard", parent)
        
        # Create buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(30)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create only the indices button
        self.indices_button = MainMenuButton("📈", "NSE Indices")
        
        # Add button to layout
        buttons_layout.addWidget(self.indices_button)
        
        # Add buttons container to main layout
        self.layout.addWidget(buttons_container, 0, 0, 1, 3)
        
        # Add welcome message
        welcome_label = QLabel("Welcome to Financial Dashboard")
        welcome_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(welcome_label, 1, 0, 1, 3)
        
        # Add description
        desc_label = QLabel("Click on NSE Indices to view market data")
        desc_label.setFont(QFont("Segoe UI", 16))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(desc_label, 2, 0, 1, 3)

class GlassmorphicUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial Dashboard")
        
        # Set to fullscreen
        self.showFullScreen()
        
        # Initialize background attribute first
        self.background = None
        
        # Try to load the background image
        try:
            bg_path = resource_path("bg_blurlow.png")
            self.background = QPixmap(bg_path)
            if self.background.isNull():
                print(f"Failed to load background image from: {bg_path}")
                # Create a fallback background
                self.background = QPixmap(self.size())
                self.background.fill(QColor(20, 30, 50))
        except Exception as e:
            print(f"Error loading background: {e}")
            # Create a fallback background
            self.background = QPixmap(self.size())
            self.background.fill(QColor(20, 30, 50))
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 10, 20, 20)
        
        # Add stretch to push content to center
        self.main_layout.addStretch(1)
        
        # Center content container
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(15)
        
        # Title container
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel("NSE Indices")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label)
        
        center_layout.addLayout(title_layout)
        
        # Create and add indices content
        self.indices_content = IndicesContent()
        center_layout.addWidget(self.indices_content)
        
        self.main_layout.addWidget(center_container)
        
        # Add stretch to push content to center
        self.main_layout.addStretch(1)
        
        # For keyboard shortcut tracking
        self.key_sequence = ""
        self.exit_sequence = "yogi"
    
    def paintEvent(self, event):
        painter = QPainter(self)
        if hasattr(self, 'background') and self.background and not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        else:
            # Fallback to a solid color if background is not available
            painter.fillRect(self.rect(), QColor(20, 30, 50))
    
    def keyPressEvent(self, event):
        # Track key sequence for exit shortcut
        if event.key() >= Qt.Key.Key_A and event.key() <= Qt.Key.Key_Z:
            # Add the pressed key to the sequence
            self.key_sequence += chr(event.key()).lower()
            
            # Check if the sequence ends with the exit sequence
            if self.key_sequence.endswith(self.exit_sequence):
                self.close()
            
            # Keep only the last few characters to avoid memory buildup
            if len(self.key_sequence) > 10:
                self.key_sequence = self.key_sequence[-10:]
        
        # Handle escape key to exit fullscreen
        if event.key() == Qt.Key.Key_Escape:
            self.showNormal()
        
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = GlassmorphicUI()
    window.show()
    app.exec()