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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.front_widget)
        
        # Set initial fixed size
        self.setFixedSize(590, 450)  # Increased width from 550 to 633 (15% more)
    
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        logo_label = QLabel()
        logo_path = resource_path(f"logos/unique_{hash(self.title) % 83 + 1}.png")
        fallback_logo_path = resource_path("logos/unique_1.png")
        
        logo_pixmap = None
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
        else:
            logo_pixmap = QPixmap(fallback_logo_path)

        logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_layout.addWidget(logo_label)
        
        title_layout.addSpacing(15)
        
        # Create a container for the title with fixed height
        title_container = QWidget()
        title_container.setFixedHeight(120)  # Increased from 100 to 120
        title_container_layout = QVBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 8, 0, 8)  # Increased padding
        title_container_layout.setSpacing(4)  # Increased spacing between lines
        
        # Format title with different font sizes for each line
        title_words = self.title.split()
        first_line = " ".join(title_words[:2])
        remaining_words = title_words[2:]
        
        # Base font size
        base_font_size = 24
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
        value_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        value_container_layout.addWidget(value_label)
        
        layout.addWidget(value_container)
        
        layout.addStretch()
        
        # Create a fixed-size container for the change
        change_container = QWidget()
        change_container.setFixedHeight(60)
        change_layout = QHBoxLayout(change_container)
        change_layout.setContentsMargins(0, 0, 0, 0)
        change_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        change_label = QLabel(f"{self.change}")
        change_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        change_label.setStyleSheet(f"color: {self.change_color}; font-weight: bold;")
        change_label.setMinimumWidth(160)
        
        arrow_label = QLabel()
        arrow_pixmap = QPixmap(resource_path("up_arrow.png" if self.change_value >= 0 else "down_arrow.png"))
        arrow_label.setPixmap(arrow_pixmap.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
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
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(container, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.layout = QGridLayout(container)
        self.layout.setSpacing(20)
        
        # Set container width to 95% of screen width
        screen_width = QApplication.primaryScreen().size().width()
        container.setFixedWidth(int(screen_width * 0.98))  # Increased from 0.90 to 0.95
        
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
        
        # Create page indicator container
        page_indicator_container = QWidget()
        page_indicator_layout = QHBoxLayout(page_indicator_container)
        page_indicator_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_indicator_layout.setSpacing(15)  # Space between dots
        
        # Create dots for each screen
        self.page_dots = []
        for i in range(9):  # 9 screens
            dot = QLabel()
            dot.setFixedSize(12, 12)  # Size of each dot
            dot.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.3);
                    border-radius: 6px;
                }
            """)
            page_indicator_layout.addWidget(dot)
            self.page_dots.append(dot)
        
        # Add page indicator below the screens stack
        self.layout.addWidget(page_indicator_container, 1, 0, 1, 3)
        
        # Update the first dot to show it's selected
        self.page_dots[0].setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 6px;
            }
        """)
        
        # NSE Indices data - 54 indices (9 screens × 6 cards)
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
        
        # Create all screens first
        self.screens = []
        self.cards = []
        
        for screen_data in self.indices_data:
            screen = QWidget()
            screen_layout = QGridLayout(screen)
            screen_layout.setSpacing(20)
            
            # Set fixed spacing for the grid
            screen_layout.setHorizontalSpacing(50)  # Increased spacing
            screen_layout.setVerticalSpacing(50)  # Increased spacing
            
            screen_cards = []
            
            # Create and add all cards for this screen
            for card_index, card_data in enumerate(screen_data):
                card = GlassmorphicCard(
                    card_data["title"],
                    card_data["value"],
                    card_data["change"]
                )
                row = card_index // 3
                col = card_index % 3
                screen_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)
                screen_cards.append(card)
            
            # Set equal column and row stretches
            for i in range(3):
                screen_layout.setColumnStretch(i, 1)
            for i in range(2):
                screen_layout.setRowStretch(i, 1)
            
            self.screens.append(screen)
            self.cards.append(screen_cards)
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
        
        # Create a mapping from index names to card positions
        self.index_map = {}
        for screen_idx, screen_data in enumerate(self.indices_data):
            for card_idx, card_data in enumerate(screen_data):
                self.index_map[card_data["title"]] = (screen_idx, card_idx)
    
    def update_card_data(self, index_name, value, change):
        if index_name in self.index_map:
            screen_idx, card_idx = self.index_map[index_name]
            if 0 <= screen_idx < len(self.cards) and 0 <= card_idx < len(self.cards[screen_idx]):
                self.cards[screen_idx][card_idx].update_data(value, change)
                print(f"Updated {index_name} with value: {value}, change: {change}")
    
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
    
    def change_screen(self, index):
        if index != self.current_screen and not self.animation_in_progress:
            self.animation_in_progress = True
            
            # Update page indicator dots
            self.page_dots[self.current_screen].setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.3);
                    border-radius: 6px;
                }
            """)
            self.page_dots[index].setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.9);
                    border-radius: 6px;
                }
            """)
            
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
                
                # Ensure both widgets are visible
                current_widget.show()
                new_widget.show()
                new_widget.raise_()
                
                # Set initial positions
                current_widget.move(zero_pos)
                new_widget.move(start_pos)
                
                # Create animation group for parallel animations
                anim_group = QParallelAnimationGroup(self)
                
                # Position animations with improved settings
                current_anim = QPropertyAnimation(current_widget, b"pos")
                current_anim.setDuration(800)  # Increased from 400ms to 800ms for much slower animation
                current_anim.setStartValue(zero_pos)
                current_anim.setEndValue(end_pos)
                current_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                
                new_anim = QPropertyAnimation(new_widget, b"pos")
                new_anim.setDuration(800)  # Increased from 400ms to 800ms for much slower animation
                new_anim.setStartValue(start_pos)
                new_anim.setEndValue(zero_pos)
                new_anim.setEasingCurve(QEasingCurve.Type.OutExpo)
                
                # Add animations to group
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
        
        # Force fullscreen flags
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Hide cursor for the entire application
        self.setCursor(Qt.CursorShape.BlankCursor)
        
        # Get screen dimensions
        self.screen = QApplication.primaryScreen().geometry()
        
        # Set initial dimensions
        self.updateDimensions()
        
        # Show the window
        self.show()
        self.hide_cursor_completely()
        
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
        
        self.center_container = QWidget()
        center_layout = QVBoxLayout(self.center_container)
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
    
    def hide_cursor_completely(self):
    # Hide cursor using Qt method
      self.setCursor(Qt.CursorShape.BlankCursor)
    
    # For Windows - additional method
      if sys.platform.startswith('win'):
        try:
            # Get the current cursor handle
            cursor_info = ctypes.c_int()
            ctypes.windll.user32.GetCursorInfo(ctypes.byref(cursor_info))
            # Hide the cursor
            ctypes.windll.user32.ShowCursor(False)
        except Exception as e:
            print(f"Error hiding Windows cursor: {e}")
    
    # For Linux - additional X11 method
      elif sys.platform.startswith('linux'):
        try:
            # Create an invisible cursor
            pixmap = QPixmap(1, 1)
            pixmap.fill(Qt.transparent)
            invisible_cursor = QCursor(pixmap)
            QApplication.setOverrideCursor(invisible_cursor)
            QApplication.changeOverrideCursor(invisible_cursor)
        except Exception as e:
            print(f"Error hiding Linux cursor: {e}")

    def enterEvent(self, event):
    # Hide cursor when mouse enters the window
      self.hide_cursor_completely()
      super().enterEvent(event)

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