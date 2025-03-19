from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                            QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, 
                            QFrame, QStackedWidget, QSizePolicy, QWIDGETSIZE_MAX)
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap, QPen, QTransform, QKeyEvent, QPainterPath
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QRectF, pyqtProperty, QTimer, pyqtSignal, QObject

from PyQt5.QtGui import QCursor
import os
import sys
import math
import json
import paho.mqtt.client as mqtt
import ssl
import time
import threading
import ctypes

# MQTT Configuration``
BROKER_URL = "mqtts://mqtt.dhan.co"
CONFIG_MQTT_CLIENT_ID = "mqtt-12x"
CONFIG_MQTT_USERNAME = "device"
CONFIG_MQTT_PASSWORD = "device"
STOCKDOCK_CONFIG_TOPIC = "stockdock/screen/nse-indices"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class MQTTClient(QObject):
    data_received = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = mqtt.Client(client_id=CONFIG_MQTT_CLIENT_ID, clean_session=True)
        self.client.username_pw_set(CONFIG_MQTT_USERNAME, CONFIG_MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Extract host and port from MQTT URL
        url = BROKER_URL.replace("mqtts://", "")
        self.host = url
        self.port = 8443  # Using port 8443 as specified
        
        # Set up TLS
        self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        self.client.tls_insecure_set(False)
        
        self.is_connected = False
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.connect)
        
        # Add update timer for 2-second intervals
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.request_update)
        
    def connect(self):
        try:
            if not self.is_connected:
                print(f"Connecting to MQTT broker at {self.host}:{self.port}")
                self.client.connect(self.host, self.port, 60)
                self.client.loop_start()
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            if not self.reconnect_timer.isActive():
                self.reconnect_timer.start(5000)  # Try to reconnect every 5 seconds
    
    def request_update(self):
        if self.is_connected:
            # Re-subscribe to trigger an update
            self.client.unsubscribe(STOCKDOCK_CONFIG_TOPIC)
            self.client.subscribe(STOCKDOCK_CONFIG_TOPIC)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            self.is_connected = True
            self.reconnect_timer.stop()
            client.subscribe(STOCKDOCK_CONFIG_TOPIC)
            # Start the update timer when connected
            self.update_timer.start(2000)  # 2000 ms = 2 seconds
        else:
            print(f"Failed to connect to MQTT broker with code {rc}")
            self.is_connected = False
            if not self.reconnect_timer.isActive():
                self.reconnect_timer.start(5000)
    
    def disconnect(self):
        self.update_timer.stop()  # Stop the update timer
        self.client.loop_stop()
        self.client.disconnect()
        self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with code {rc}")
        self.is_connected = False
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start(5000)
    
    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            if isinstance(data, list):
                self.data_received.emit(data)
                print(f"Received data with {len(data)} items")
            else:
                print(f"Unexpected data format: {type(data)}")
        except Exception as e:
            print(f"Error processing message: {e}")

class GlassmorphicCard(QFrame):
    def __init__(self, title, value, change, parent=None):
        super().__init__(parent)
        self.setObjectName("glassmorphicCard")
        
        self.setStyleSheet("""
            QFrame#glassmorphicCard {
                background-color: rgba(40, 50, 80, 0.5);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        # Set a fixed size policy to prevent layout changes
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
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
        self.setup_front_side()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 20, 0)
        main_layout.addWidget(self.front_widget)
        
        # Set initial fixed size
        self.setFixedSize(470, 290)  # Increased width from 550 to 633 (15% more)
    
    def update_data(self, value, change):
        self.value = value
        self.change = change
        
        try:
            self.change_value = float(change.strip('%').replace(',', '.'))
        except ValueError:
            self.change_value = 0
            
        self.change_color = "green" if self.change_value >= 0 else "red"
        
        # Recreate the front widget with new data
        self.front_widget.deleteLater()
        self.front_widget = QWidget()
        self.setup_front_side()
        self.layout().addWidget(self.front_widget)
    
    def setup_front_side(self):
        layout = QVBoxLayout(self.front_widget)
        layout.setContentsMargins(20, 20, 20,10)
        layout.setSpacing(0)
        
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        logo_label = QLabel()
        logo_path = f"logos/unique_{hash(self.title) % 83 + 1}.png"
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_layout.addWidget(logo_label)
        
        title_layout.addSpacing(5)
        
        # Create a container for the title with fixed height
        title_container = QWidget()
        title_container.setFixedHeight(100)  # Increased from 100 to 120
        title_container_layout = QVBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 8, 0, 30)  # Increased padding
        title_container_layout.setSpacing(3)  # Increased spacing between lines
        
        # Format title with different font sizes for each line
        title_words = self.title.split()
        first_line = " ".join(title_words[:3])
        remaining_words = title_words[3:]
        
        # Base font size
        base_font_size = 22
        if any(stock in self.title for stock in ["Reliance", "TCS", "HDFC Bank", "Infosys", "Bharti Airtel", "ITC"]):
            base_font_size = int(base_font_size * 1.2)
        
        # First line (largest font)
        first_line_label = QLabel(first_line)
        first_line_label.setFont(QFont("Segoe UI", base_font_size, QFont.Weight.Bold))
        first_line_label.setStyleSheet("color: white;")
        first_line_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        first_line_label.setMinimumHeight(int(base_font_size * 1.8))  # Increased height multiplier
        title_container_layout.addWidget(first_line_label)
        
        # Second line (if exists, smaller font)
        if len(remaining_words) > 0:
            second_line = " ".join(remaining_words[:2])
            second_line_label = QLabel(second_line)
            second_font_size = int(base_font_size * 0.85)
            second_line_label.setFont(QFont("Segoe UI", second_font_size, QFont.Weight.Bold))
            second_line_label.setStyleSheet("color: white;")
            second_line_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            second_line_label.setMinimumHeight(int(second_font_size * 1.8))  # Increased height multiplier
            title_container_layout.addWidget(second_line_label)
            
            # Third line (if exists, smallest font)
            if len(remaining_words) > 2:
                third_line = " ".join(remaining_words[2:])
                third_line_label = QLabel(third_line)
                third_font_size = int(base_font_size * 0.7)
                third_line_label.setFont(QFont("Segoe UI", third_font_size, QFont.Weight.Bold))
                third_line_label.setStyleSheet("color: white;")
                third_line_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                third_line_label.setMinimumHeight(int(third_font_size * 1.8))  # Increased height multiplier
                title_container_layout.addWidget(third_line_label)
        
        title_container_layout.addStretch()
        title_layout.addWidget(title_container)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        layout.addSpacing(40)
        
        # Create a fixed-size container for the value
        value_container = QWidget()
        value_container.setFixedHeight(70)
        
        value_container_layout = QVBoxLayout(value_container)
        value_container_layout.setContentsMargins(0, 0, 0, 0)
        
        value_label = QLabel(self.value)
        value_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        value_container_layout.addWidget(value_label)
        
        layout.addWidget(value_container)
        
        layout.addStretch()
        
        # Create a fixed-size container for the change
        change_container = QWidget()
        change_container.setFixedHeight(60)
        change_layout = QHBoxLayout(change_container)
        change_layout.setContentsMargins(0, 15, 0, 0)
        change_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        change_label = QLabel(f"{self.change}")
        change_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        change_label.setStyleSheet(f"color: {self.change_color}; font-weight: bold;")
        change_label.setMinimumWidth(100)
        
        arrow_label = QLabel()
        arrow_pixmap = QPixmap(resource_path("up_arrow.png" if self.change_value >= 0 else "down_arrow.png"))
        arrow_label.setPixmap(arrow_pixmap.scaled(27, 27, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        change_layout.addWidget(change_label)
        change_layout.addWidget(arrow_label)
        change_layout.addStretch()
        
        layout.addWidget(change_container)

class ContentWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container.setFixedHeight(680)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 50)  # Changed from (0, 0, 100, 50) to center the container
        
        main_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.layout = QGridLayout(container)
        self.layout.setSpacing(10)
        
        # Set container width to 95% of screen width
        screen_width = QApplication.primaryScreen().size().width()
        container.setFixedWidth(int(screen_width * 0.95))  # Changed from 1 to 0.95 to prevent overflow
        
        self.layout.setColumnMinimumWidth(0, 0)
        self.layout.setColumnMinimumWidth(1, 0)
        self.layout.setColumnMinimumWidth(2, 0)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)

class IndicesContent(ContentWidget):
    def __init__(self, parent=None):
        super().__init__("SE Indices", parent)
        
        # Add scroll state management
        self.is_scrolling = False
        self.is_animating = False
        self.scroll_velocity = 0
        self.last_x = 0
        self.last_time = 0
        self.last_scroll_pos = 0
        self.scroll_threshold = 2
        self.last_valid_x = 0
        self.scroll_start_x = None
        
        # NSE Indices data - 54 indices
        self.indices_data = [
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
        
        # Create a main container widget that will hold everything
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        self.main_container.setStyleSheet("""
            QWidget#mainContainer {
                background: transparent;
            }
        """)
        
        # Add main container to the layout with proper stretching
        self.layout.addWidget(self.main_container, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        
        # Create a scroll area
        scroll_area = QWidget()
        scroll_area.setObjectName("scrollArea")
        scroll_area.setStyleSheet("""
            QWidget#scrollArea {
                background: transparent;
            }
        """)
        
        # Create the container for cards with proper spacing
        self.scroll_container = QWidget()
        self.scroll_container.setObjectName("scrollContainer")
        self.scroll_container.setStyleSheet("""
            QWidget#scrollContainer {
                background: transparent;
            }
        """)
        
        # Create main layout for the scroll area
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a container for scroll area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)  # Remove bottom margin that was for dots
        content_layout.setSpacing(0)  # Remove spacing that was for dots
        
        content_layout.addWidget(scroll_area)
        
        # Create layout for the scroll area
        scroll_area_layout = QHBoxLayout(scroll_area)
        scroll_area_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area_layout.setSpacing(0)
        scroll_area_layout.addWidget(self.scroll_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Create grid layout for the cards with proper spacing
        scroll_layout = QGridLayout(self.scroll_container)
        scroll_layout.setContentsMargins(50, 20, 50, 20)  # Margins around the grid
        scroll_layout.setHorizontalSpacing(50)  # Space between cards horizontally
        scroll_layout.setVerticalSpacing(70)    # Space between cards vertically
        
        main_layout.addWidget(content_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Initialize cards list
        self.cards = []
        
        # Calculate dimensions
        cards_per_row = 3
        total_rows = 2
        total_cards = sum(len(screen) for screen in self.indices_data)
        total_columns = math.ceil(total_cards / (total_rows * cards_per_row))
        
        # Calculate container width to fit all cards
        card_width = 470  # Width of each card
        card_height = 290  # Height of each card
        horizontal_spacing = 50  # Space between cards horizontally
        vertical_spacing = 70    # Space between cards vertically
        
        # Calculate the width needed for one screen (3x2 grid)
        screen_width = (card_width * cards_per_row) + (horizontal_spacing * (cards_per_row - 1)) + 100
        
        # Calculate total width needed for all cards
        total_width = (screen_width * total_columns)
        self.scroll_container.setFixedWidth(total_width)
        
        # Create and add all cards
        card_index = 0
        for screen_data in self.indices_data:
            screen_cards = []
            for card_data in screen_data:
                card = GlassmorphicCard(
                    card_data["title"],
                    card_data["value"],
                    card_data["change"]
                )
                
                # Calculate position in the grid
                absolute_index = card_index
                row = (absolute_index % (cards_per_row * total_rows)) // cards_per_row
                col = absolute_index // (cards_per_row * total_rows) * cards_per_row + (absolute_index % cards_per_row)
                
                scroll_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)
                screen_cards.append(card)
                card_index += 1
            
            self.cards.append(screen_cards)
        
        # Create a mapping from index names to card positions
        self.index_map = {}
        card_index = 0
        for screen_idx, screen_data in enumerate(self.indices_data):
            for card_idx, card_data in enumerate(screen_data):
                self.index_map[card_data["title"]] = (screen_idx, card_idx)
                card_index += 1
        
        # Add scrolling animation properties
        self.scroll_animation = QPropertyAnimation(self.scroll_container, b"pos")
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.scroll_animation.setDuration(500)  # 500ms duration
        
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.update_inertial_scroll)
        self.scroll_timer.setInterval(16)  # 60 FPS
        
        # Enable smooth scrolling
        self.scroll_container.installEventFilter(self)
        
        # Set fixed dimensions for the scroll area to match original design
        scroll_area.setFixedHeight(680)  # Height to fit 2 rows of cards
        scroll_area.setFixedWidth(screen_width)  # Width to fit 3 cards
        
        # Add these new instance variables for better scroll control
        self.last_scroll_pos = 0
        self.scroll_threshold = 2  # Minimum pixels to move before updating position
        self.is_animating = False
        self.last_valid_x = 0
    
    def reset_scroll_state(self):
        """Reset all scrolling-related states"""
        self.is_scrolling = False
        self.is_animating = False
        self.scroll_velocity = 0
        self.scroll_start_x = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self.scroll_timer.isActive():
            self.scroll_timer.stop()
        if self.scroll_animation.state() == QPropertyAnimation.State.Running:
            self.scroll_animation.stop()
    
    def check_scroll_bounds(self, new_x):
        """Check if the new position is within valid bounds"""
        min_x = -self.scroll_container.width() + self.width()
        return min_x <= new_x <= 0, min_x
    
    def eventFilter(self, obj, event):
        if obj == self.scroll_container:
            if event.type() == event.Type.MouseButtonPress:
                try:
                    self.reset_scroll_state()
                    self.scroll_start_x = event.pos().x()
                    self.last_x = event.pos().x()
                    self.last_time = time.time()
                    self.is_scrolling = True
                    self.last_valid_x = self.scroll_container.pos().x()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                except Exception as e:
                    print(f"Error in mouse press event: {e}")
                    self.reset_scroll_state()
                return True
            
            elif event.type() == event.Type.MouseMove and self.is_scrolling:
                try:
                    if self.scroll_start_x is not None:
                        current_time = time.time()
                        delta_time = max(current_time - self.last_time, 0.001)
                        
                        current_x = event.pos().x()
                        delta = current_x - self.last_x
                        
                        # Reduced threshold for higher sensitivity
                        if abs(delta) < 2:  # Reduced from 3
                            return True
                        
                        try:
                            raw_velocity = delta / delta_time
                            max_velocity = 4600  # Increased from 4000 (15% more)
                            self.scroll_velocity = max(min(raw_velocity, max_velocity), -max_velocity)
                        except ZeroDivisionError:
                            self.scroll_velocity = 0
                        
                        current_pos = self.scroll_container.pos().x()
                        new_x = current_pos + (delta * 1.15)  # Increased movement by 15%
                        
                        is_within_bounds, min_x = self.check_scroll_bounds(new_x)
                        if not is_within_bounds:
                            if new_x < min_x:
                                resistance = (min_x - new_x) * 0.4
                                new_x = min_x + resistance
                            else:
                                resistance = new_x * 0.4
                                new_x = resistance
                        
                        # Enhanced smoothing
                        smoothing_factor = 0.82  # Slightly reduced for more responsive feel
                        smoothed_x = (smoothing_factor * new_x) + ((1 - smoothing_factor) * current_pos)
                        
                        # Only update if movement is significant
                        if abs(smoothed_x - self.last_scroll_pos) >= 2:  # Reduced from 3
                            rounded_x = round(smoothed_x * 2) / 2
                            self.scroll_container.move(int(rounded_x), self.scroll_container.pos().y())
                            self.last_scroll_pos = smoothed_x
                            self.last_valid_x = rounded_x
                        
                        self.last_x = current_x
                        self.last_time = current_time
                        
                except Exception as e:
                    print(f"Error in mouse move event: {e}")
                    self.scroll_container.move(self.last_valid_x, self.scroll_container.pos().y())
                    self.reset_scroll_state()
                return True
            
            elif event.type() == event.Type.MouseButtonRelease:
                try:
                    if self.is_scrolling:
                        self.is_scrolling = False
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                        
                        # Adjusted velocity threshold and maximum
                        if abs(self.scroll_velocity) > 350:  # Reduced from 400 for earlier activation
                            if self.scroll_velocity > 0:
                                self.scroll_velocity = min(self.scroll_velocity, 2875)  # Increased from 2500 (15% more)
                            else:
                                self.scroll_velocity = max(self.scroll_velocity, -2875)  # Increased from -2500 (15% more)
                            self.start_inertial_scroll()
                        
                        self.scroll_start_x = None
                except Exception as e:
                    print(f"Error in mouse release event: {e}")
                    self.reset_scroll_state()
                return True
            
        return super().eventFilter(obj, event)
    
    def start_inertial_scroll(self):
        if not self.is_animating:
            self.is_animating = True
            self.scroll_timer.start()
    
    def update_inertial_scroll(self):
        try:
            if abs(self.scroll_velocity) < 35 or not self.is_animating:  # Reduced from 40 for longer scroll
                self.scroll_timer.stop()
                self.is_animating = False
                return
            
            friction = 0.94  # Reduced friction for longer scroll
            self.scroll_velocity *= friction
            
            delta = self.scroll_velocity * (self.scroll_timer.interval() / 1000.0)
            current_x = self.scroll_container.pos().x()
            new_x = current_x + (delta * 1.15)  # Increased movement by 15%
            
            is_within_bounds, min_x = self.check_scroll_bounds(new_x)
            if not is_within_bounds:
                if new_x < min_x:
                    new_x = min_x
                else:
                    new_x = 0
                self.scroll_velocity = 0
                self.scroll_timer.stop()
                self.is_animating = False
            
            # Only update if movement is significant
            if abs(new_x - self.last_scroll_pos) >= 2:  # Reduced from 3
                rounded_x = round(new_x * 2) / 2
                self.scroll_container.move(int(rounded_x), self.scroll_container.pos().y())
                self.last_scroll_pos = new_x
                self.last_valid_x = rounded_x
            
        except Exception as e:
            print(f"Error in inertial scroll: {e}")
            self.scroll_timer.stop()
            self.is_animating = False
            self.scroll_container.move(self.last_valid_x, self.scroll_container.pos().y())
    
    def update_card_data(self, index_name, value, change):
        if index_name in self.index_map:
            screen_idx, card_idx = self.index_map[index_name]
            if 0 <= screen_idx < len(self.cards) and 0 <= card_idx < len(self.cards[screen_idx]):
                self.cards[screen_idx][card_idx].update_data(value, change)
                print(f"Updated {index_name} with value: {value}, change: {change}")

class GlassmorphicUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial Dashboard")
        
        # Force fullscreen flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Get screen dimensions
        self.screen = QApplication.primaryScreen().geometry()
        
        # Set initial dimensions
        self.updateDimensions()
        
        # Show the window
        self.show()
        
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
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_layout.addStretch(5)
        
        self.center_container = QWidget()
        center_layout = QVBoxLayout(self.center_container)
        center_layout.setContentsMargins(0, 15, 0, 0)
        center_layout.setSpacing(0)
        
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
        
        self.main_layout.addWidget(self.center_container)
        
        self.main_layout.addStretch(13)
        
        self.key_sequence = ""
        self.exit_sequence = "yogi"
        self.minimize_sequence = "min"
        
        # Define mapping between index IDs and display names
        self.index_id_to_name = {
            "IDX-I-1": "Nifty 50",
            "IDX-I-2": "Nifty Bank",
            "IDX-I-3": "Nifty IT",
            "IDX-I-4": "Nifty Auto",
            "IDX-I-5": "Nifty FMCG",
            "IDX-I-6": "Nifty Pharma",
            "IDX-I-7": "Nifty Metal",
            "IDX-I-8": "Nifty Media",
            "IDX-I-9": "Nifty Realty",
            "IDX-I-10": "Nifty PSU Bank",
            "IDX-I-11": "Nifty Private Bank",
            "IDX-I-12": "Nifty Energy",
            "IDX-I-13": "Nifty Financial Services",
            "IDX-I-14": "Nifty Consumer Durables",
            "IDX-I-15": "Nifty Oil & Gas",
            "IDX-I-16": "Nifty Healthcare",
            "IDX-I-17": "Nifty PSE",
            "IDX-I-18": "Nifty Infrastructure",
            "IDX-I-19": "Nifty MNC",
            "IDX-I-20": "Nifty Services Sector",
            "IDX-I-21": "Nifty India Digital",
            "IDX-I-22": "Nifty India Consumption",
            "IDX-I-23": "Nifty CPSE",
            "IDX-I-24": "Nifty India Manufacturing",
            "IDX-I-25": "Nifty Midcap 50",
            "IDX-I-26": "Nifty Midcap 100",
            "IDX-I-27": "Nifty Smallcap 50",
            "IDX-I-28": "Nifty Smallcap 100",
            "IDX-I-29": "Nifty Midcap Liquid 15",
            "IDX-I-30": "Nifty India Defence",
            "IDX-I-31": "Nifty Alpha 50",
            "IDX-I-32": "Nifty50 Value 20",
            "IDX-I-33": "Nifty50 Equal Weight",
            "IDX-I-34": "Nifty100 Equal Weight",
            "IDX-I-35": "Nifty100 Low Volatility 30",
            "IDX-I-36": "Nifty Alpha Low-Volatility 30",
            "IDX-I-37": "Nifty200 Quality 30",
            "IDX-I-38": "Nifty100 Quality 30",
            "IDX-I-39": "Nifty50 Dividend Points",
            "IDX-I-40": "Nifty Dividend Opportunities 50",
            "IDX-I-41": "Nifty Growth Sectors 15",
            "IDX-I-42": "Nifty100 ESG",
            "IDX-I-43": "Nifty100 Enhanced ESG",
            "IDX-I-44": "Nifty200 Momentum 30",
            "IDX-I-45": "Nifty Commodities",
            "IDX-I-46": "Nifty India Manufacturing",
            "IDX-I-47": "Nifty Microcap 250",
            "IDX-I-48": "Nifty Total Market",
            "IDX-I-49": "Nifty500 Value 50",
            "IDX-I-50": "Nifty Next 50",
            "IDX-I-51": "Nifty100 Liquid 15",
            "IDX-I-52": "Nifty MidSmallcap 400",
            "IDX-I-53": "Nifty200 Alpha 30",
            "IDX-I-54": "India VIX"
        }
        
        # Initialize MQTT client
        self.mqtt_client = MQTTClient(self)
        self.mqtt_client.data_received.connect(self.handle_mqtt_data)
        
        # Connect to MQTT broker after a short delay to ensure UI is fully loaded
        QTimer.singleShot(1000, self.mqtt_client.connect)
    
    def handle_mqtt_data(self, data):
        try:
            # Process the received MQTT data and update the UI
            if isinstance(data, list):
                for item in data:
                    if 'key' in item and 'ltp' in item and 'p_ch' in item:
                        index_id = item['key']
                        if index_id in self.index_id_to_name:
                            index_name = self.index_id_to_name[index_id]
                            value = f"₹ {item['ltp']:,.2f}"
                            change = f"{item['p_ch']:.2f}%"
                            self.indices_content.update_card_data(index_name, value, change)
                            print(f"Updated {index_name} with value: {value}, change: {change}")
        except Exception as e:
            print(f"Error handling MQTT data: {e}")
    
    def updateDimensions(self):
        # Simplified method - always use normal orientation
        self.setGeometry(0, 0, self.screen.width(), self.screen.height())
        self.setFixedSize(self.screen.width(), self.screen.height())
    
    def minimizeWindow(self):
        self.showMinimized()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        if hasattr(self, 'background') and self.background and not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        else:
            painter.fillRect(self.rect(), QColor(20, 30, 50))
    
    def keyPressEvent(self, event):
        if event.key() >= Qt.Key.Key_A and event.key() <= Qt.Key.Key_Z:
            char = chr(event.key()).lower()
            self.key_sequence += char
            
            # Check for minimize sequence
            if self.key_sequence.endswith(self.minimize_sequence):
                self.minimizeWindow()
            
            # Check for exit sequence
            if self.key_sequence.endswith(self.exit_sequence):
                # Disconnect MQTT client before closing
                self.mqtt_client.disconnect()
                self.close()
            
            if len(self.key_sequence) > 10:
                self.key_sequence = self.key_sequence[-10:]
        
        if event.key() == Qt.Key.Key_Escape:
            self.showNormal()
        
        super().keyPressEvent(event)
    
    def enterEvent(self, event):
        super().enterEvent(event)  # Just call parent method

    def closeEvent(self, event):
        # Disconnect MQTT client when closing the application
        self.mqtt_client.disconnect()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = GlassmorphicUI()
    window.show()  # Make sure window is shown
    window.raise_()  # Bring to front
    app.exec()