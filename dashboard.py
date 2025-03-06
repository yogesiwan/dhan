from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                            QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, 
                            QFrame, QStackedWidget, QPushButton, QScrollArea)
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap, QIcon, QPen, QTransform, QKeyEvent
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
                padding: 15px;
            }
        """)
        
        # Make the card longer to accommodate percentage labels
        self.setMinimumHeight(180)  # Increased minimum height
        
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Title with icon - centered
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add appropriate icon based on title
        icon_label = QLabel()
        if "Nifty" in self.title:
            icon_label.setText("📈")
        elif "Bank" in self.title:
            icon_label.setText("🏦")
        elif "VIX" in self.title:
            icon_label.setText("📊")
        elif "Reliance" in self.title:
            icon_label.setText("🏭")
        elif "TCS" in self.title or "Infosys" in self.title:
            icon_label.setText("💻")
        elif "HDFC" in self.title:
            icon_label.setText("🏦")
        elif "Airtel" in self.title:
            icon_label.setText("📱")
        elif "ITC" in self.title:
            icon_label.setText("🏢")
        else:
            icon_label.setText("📊")
            
        icon_label.setFont(QFont("Segoe UI", 17))
        title_layout.addWidget(icon_label)
        
        # Title - make stock names 20% larger
        title_font_size = 17
        if any(stock in self.title for stock in ["Reliance", "TCS", "HDFC Bank", "Infosys", "Bharti Airtel", "ITC"]):
            title_font_size = int(title_font_size * 1.2)  # 20% larger for stock names
            
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", title_font_size, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        
        # Value - centered
        value_label = QLabel(self.value)
        value_label.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Change with icon and mini graph - keep original position
        change_layout = QHBoxLayout()
        
        change_icon = "↗" if self.change_value >= 0 else "↘"
        
        # Change label
        change_label = QLabel(f"{self.change} {change_icon}")
        change_label.setFont(QFont("Segoe UI", 14))
        change_label.setStyleSheet(f"color: {self.change_color};")
        change_layout.addWidget(change_label)
        
        # Add mini graph
        graph_widget = QFrame()
        graph_widget.setFixedSize(60, 20)
        graph_widget.setStyleSheet(f"background-color: transparent;")
        
        # Store change value for painting
        graph_widget.change_value = self.change_value
        graph_widget.change_color = self.change_color
        
        # Custom paint method for graph
        def paintEvent(event):
            painter = QPainter(graph_widget)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Set pen color based on change
            painter.setPen(QColor(self.change_color))
            
            # Draw mini graph
            width = graph_widget.width()
            height = graph_widget.height()
            mid_y = int(height / 2)  # Convert to int
            
            # Generate some random-looking but consistent points for the graph
            points = []
            
            # Start point
            points.append(QPoint(0, mid_y))
            
            # Generate middle points with some variation
            import random
            random.seed(abs(hash(self.title)))  # Use title as seed for consistent randomness
            
            num_points = 5
            for i in range(1, num_points):
                x = int(i * width / num_points)
                
                # Make the line trend up or down based on change value
                trend = -1 if self.change_value >= 0 else 1  # Negative because y-axis is inverted
                variation = random.randint(-3, 3)  # Small random variation
                
                # Calculate y with more pronounced trend at the end
                factor = (i / num_points) * abs(min(max(self.change_value, -10), 10)) / 2
                y = int(mid_y + trend * factor * height / 4 + variation)  # Convert to int
                
                points.append(QPoint(x, y))
            
            # End point - make it clearly up or down based on change
            end_y = int(mid_y - (height / 3)) if self.change_value >= 0 else int(mid_y + (height / 3))  # Convert to int
            points.append(QPoint(width, end_y))
            
            # Draw the line
            for i in range(1, len(points)):
                painter.drawLine(points[i-1], points[i])
        
        # Assign custom paint event
        graph_widget.paintEvent = paintEvent
        
        change_layout.addWidget(graph_widget)
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
        
        # Setup layout
        self.layout = QGridLayout(self)
        self.layout.setSpacing(15)

class IndicesContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("NSE Indices", parent)
        
        # Card data for Indices page
        cards_data = [
            {"title": "Nifty 50", "value": "₹ 25,426.25", "change": "0.79%", "pos": (0, 0)},
            {"title": "Fin Nifty", "value": "₹ 24,426.25", "change": "0.29%", "pos": (0, 1)},
            {"title": "Bank Nifty", "value": "₹ 51,460.25", "change": "0.08%", "pos": (0, 2)},
            {"title": "Nifty Midcap 50", "value": "₹ 15,426.25", "change": "0.79%", "pos": (1, 0)},
            {"title": "Nifty Smallcap 50", "value": "₹ 9,426.25", "change": "0.79%", "pos": (1, 1)},
            {"title": "India VIX", "value": "₹ 786.0", "change": "-0.79%", "pos": (1, 2)}
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
        
        # Create menu buttons
        self.indices_button = MainMenuButton("📈", "NSE Indices")
        self.stocks_button = MainMenuButton("💹", "Top Stocks")
        self.news_button = MainMenuButton("📰", "Market News")
        
        # Add buttons to layout
        buttons_layout.addWidget(self.indices_button)
        buttons_layout.addWidget(self.stocks_button)
        buttons_layout.addWidget(self.news_button)
        
        # Add buttons container to main layout
        self.layout.addWidget(buttons_container, 0, 0, 1, 3)
        
        # Add welcome message
        welcome_label = QLabel("Welcome to Financial Dashboard")
        welcome_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(welcome_label, 1, 0, 1, 3)
        
        # Add description
        desc_label = QLabel("Select an option above to view market data")
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
        
        # Use resource_path to load the image
        self.background = QPixmap(resource_path("bg_blurlow.png"))
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Top bar with time, title and temperature
        top_bar = QHBoxLayout()
        
        # Time with icon
        time_layout = QHBoxLayout()
        time_icon = QLabel("🕒")
        time_icon.setFont(QFont("Segoe UI", 17))
        time_icon.setStyleSheet("color: white;")
        time_layout.addWidget(time_icon)
        
        self.time_label = QLabel("12:45 PM")
        self.time_label.setObjectName("time_label")
        self.time_label.setFont(QFont("Segoe UI", 17))
        self.time_label.setStyleSheet("color: white;")
        time_layout.addWidget(self.time_label)
        
        top_bar.addLayout(time_layout)
        
        # Title container with icon - will be updated based on current content
        title_layout = QHBoxLayout()
        self.title_icon = QLabel("📊")
        self.title_icon.setFont(QFont("Segoe UI", 22))
        self.title_icon.setStyleSheet("color: white;")
        title_layout.addWidget(self.title_icon)
        
        self.title_label = QLabel("Financial Dashboard")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label, 1)
        
        top_bar.addLayout(title_layout, 1)
        
        # Temperature with icon
        temp_layout = QHBoxLayout()
        temp_icon = QLabel("☀️")
        temp_icon.setFont(QFont("Segoe UI", 17))
        temp_layout.addWidget(temp_icon)
        
        temp_label = QLabel("32°C")
        temp_label.setFont(QFont("Segoe UI", 17))
        temp_label.setStyleSheet("color: white;")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        temp_layout.addWidget(temp_label)
        
        top_bar.addLayout(temp_layout)
        
        self.main_layout.addLayout(top_bar)
        
        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        
        # Create content widgets
        self.main_menu_content = MainMenuContent()
        self.indices_content = IndicesContent()
        self.stocks_content = StocksContent()
        self.news_content = NewsContent()
        
        # Add content widgets to stack - main menu first
        self.content_stack.addWidget(self.main_menu_content)
        self.content_stack.addWidget(self.indices_content)
        self.content_stack.addWidget(self.stocks_content)
        self.content_stack.addWidget(self.news_content)
        
        # Set up button callbacks
        self.main_menu_content.indices_button.set_click_callback(lambda: self.navigate_to_page(1))
        self.main_menu_content.stocks_button.set_click_callback(lambda: self.navigate_to_page(2))
        self.main_menu_content.news_button.set_click_callback(lambda: self.navigate_to_page(3))
        
        # Add stacked widget to main layout
        self.main_layout.addWidget(self.content_stack)
        
        # Navigation dots layout
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nav_layout.setSpacing(10)
        
        # Initialize variables before setup_navigation
        self.current_page = 0
        self.total_pages = self.content_stack.count()
        self.animation_in_progress = False
        self.old_pos = None
        
        # Create navigation dots
        self.setup_navigation()
        
        # Add navigation layout to main layout
        self.main_layout.addLayout(self.nav_layout)
        
        # Add home button
        self.home_button = QPushButton("🏠 Home")
        self.home_button.setFixedSize(120, 40)
        self.home_button.setFont(QFont("Segoe UI", 12))
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.home_button.clicked.connect(self.go_home)
        
        home_layout = QHBoxLayout()
        home_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(self.home_button)
        self.main_layout.addLayout(home_layout)
        
        # Update time periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(60000)  # Update every minute
        
        # Initial time update
        self.update_time()
        
        # Update title based on current content
        self.update_title()
        
        # For keyboard shortcut tracking
        self.key_sequence = ""
        self.exit_sequence = "yogi"
        
        # # Add exit button
        # exit_button = QPushButton("❌ Exit")
        # exit_button.setFixedSize(80, 30)
        # exit_button.setFont(QFont("Segoe UI", 10))
        # exit_button.setStyleSheet("""
        #     QPushButton {
        #         background-color: rgba(255, 50, 50, 0.7);
        #         color: white;
        #         border: none;
        #         border-radius: 15px;
        #         padding: 5px;
        #     }
        #     QPushButton:hover {
        #         background-color: rgba(255, 50, 50, 0.9);
        #     }
        # """)
        # exit_button.clicked.connect(self.close)
        
        # Add exit button to top-right corner
        # exit_layout = QHBoxLayout()
        # exit_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        # exit_layout.addWidget(exit_button)
        
        # # Add exit layout to main layout
        # self.main_layout.insertLayout(0, exit_layout)
    
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
    
    def navigate_to_page(self, page_index):
        if not self.animation_in_progress and self.current_page != page_index:
            self.animate_page_change(page_index)
    
    def go_home(self):
        if not self.animation_in_progress and self.current_page != 0:
            self.animate_page_change(0)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background)
    
    def setup_navigation(self):
        # Create navigation dots
        for i in range(self.content_stack.count()):
            dot = QPushButton()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border-radius: 6px;
                    opacity: 0.5;
                }
                QPushButton:checked {
                    background-color: white;
                    opacity: 1.0;
                }
            """)
            dot.setCheckable(True)
            dot.setChecked(i == self.current_page)
            
            # Use a lambda with default arguments to avoid late binding issues
            dot.clicked.connect(lambda checked, idx=i: self.change_page(idx))
            
            self.nav_layout.addWidget(dot)
    
    def update_time(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm AP")
        self.time_label.setText(time_text)
    
    def update_title(self):
        current_content = self.content_stack.currentWidget()
        if isinstance(current_content, ContentWidget):
            self.title_label.setText(current_content.title)
            
            # Update icon based on title
            if "Indices" in current_content.title:
                self.title_icon.setText("📈")
            elif "Stocks" in current_content.title:
                self.title_icon.setText("💹")
            elif "News" in current_content.title:
                self.title_icon.setText("📰")
            else:
                self.title_icon.setText("📊")
    
    def update_navigation(self):
        # Update the navigation dots based on current page
        for i, dot in enumerate(self.find_children(self.nav_layout, QPushButton)):
            dot.setChecked(i == self.current_page)
    
    def find_children(self, layout, widget_type):
        """Helper method to find all children of a specific type in a layout"""
        children = []
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, widget_type):
                children.append(widget)
        return children
    
    def mousePressEvent(self, event):
        if not self.animation_in_progress:
            self.old_pos = event.pos()
    
    def mouseReleaseEvent(self, event):
        if self.old_pos is not None and not self.animation_in_progress:
            # Calculate the difference in x position
            dx = event.pos().x() - self.old_pos.x()
            
            # If the swipe distance is significant (reduced from 50 to 30 pixels for more responsive swipes)
            if abs(dx) > 30:
                if dx > 0:  # Swipe from left to right
                    new_page = max(0, self.current_page - 1)
                else:  # Swipe from right to left
                    new_page = min(self.total_pages - 1, self.current_page + 1)
                
                # Only animate if the page is changing
                if new_page != self.current_page:
                    self.animate_page_change(new_page)
            
            self.old_pos = None
    
    def change_page(self, page_index):
        if page_index != self.current_page and not self.animation_in_progress:
            self.animate_page_change(page_index)
    
    def animate_page_change(self, new_page):
        if new_page == self.current_page or self.animation_in_progress:
            return
            
        # Set animation in progress flag
        self.animation_in_progress = True
        
        # Initialize animation properties
        direction = 1 if new_page > self.current_page else -1
        current_widget = self.content_stack.widget(self.current_page)
        new_widget = self.content_stack.widget(new_page)
        
        # Make sure both widgets are in the stacked widget
        if current_widget and new_widget:
            # Prepare for animation - both widgets need to be visible
            current_widget.show()
            new_widget.show()
            
            # Ensure new widget is on top during animation
            new_widget.raise_()
            
            # Starting positions
            screen_width = self.width()
            current_widget.move(0, 0)
            new_widget.move(direction * screen_width, 0)
            
            # Create a parallel animation group for smoother synchronization
            animation_group = QParallelAnimationGroup(self)
            
            # Create animation for current widget
            current_anim = QPropertyAnimation(current_widget, b"pos", self)
            current_anim.setDuration(200)  # Faster animation
            current_anim.setStartValue(QPoint(0, 0))
            current_anim.setEndValue(QPoint(-direction * screen_width, 0))
            current_anim.setEasingCurve(QEasingCurve.Type.OutExpo)  # Smoother acceleration
            
            # Create animation for new widget
            new_anim = QPropertyAnimation(new_widget, b"pos", self)
            new_anim.setDuration(200)  # Faster animation
            new_anim.setStartValue(QPoint(direction * screen_width, 0))
            new_anim.setEndValue(QPoint(0, 0))
            
            # Add bounce effect at the last screen
            if new_page == self.total_pages - 1 or (new_page == 0 and self.current_page == self.total_pages - 1):
                new_anim.setEasingCurve(QEasingCurve.Type.OutBounce)  # Bounce effect
            else:
                new_anim.setEasingCurve(QEasingCurve.Type.OutExpo)  # Smooth acceleration
            
            # Add animations to the group
            animation_group.addAnimation(current_anim)
            animation_group.addAnimation(new_anim)
            
            # Update current page and navigation
            self.current_page = new_page
            self.update_navigation()
            
            # When animation finishes, update stacked widget and reset flag
            animation_group.finished.connect(self.on_animation_finished)
            
            # Start animations
            animation_group.start()
    
    def on_animation_finished(self):
        # Set current widget in stacked widget
        self.content_stack.setCurrentIndex(self.current_page)
        
        # Update title based on current content
        self.update_title()
        
        # Reset animation flag
        self.animation_in_progress = False

if __name__ == "__main__":
    app = QApplication([])
    window = GlassmorphicUI()
    window.show()
    app.exec()