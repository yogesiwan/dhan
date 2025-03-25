import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QScrollArea, QLabel, QFrame, 
                             QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPalette, QFont, QLinearGradient, QBrush, QPainter
from PyQt5.QtWidgets import QScroller, QScrollerProperties
from PyQt5.QtCore import QRect

class StockCard(QFrame):
    def __init__(self, title, price, change, is_positive=True):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("stockCard")
        self.setStyleSheet("""
            QFrame#stockCard {
                background-color: rgba(50, 50, 80, 180);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        
        # Price
        price_label = QLabel(f"₹ {price}")
        price_label.setFont(QFont("Arial", 18, QFont.Bold))
        price_label.setStyleSheet("color: white;")
        
        # Change percentage with arrow
        arrow = "↑" if is_positive else "↓"
        color = "rgb(100, 220, 100)" if is_positive else "rgb(220, 100, 100)"
        change_label = QLabel(f"{change}% {arrow}")
        change_label.setFont(QFont("Arial", 12))
        change_label.setStyleSheet(f"color: {color};")
        
        # Add a placeholder for the chart
        chart_placeholder = QLabel("Chart Placeholder")
        chart_placeholder.setMinimumHeight(50)
        chart_placeholder.setStyleSheet(f"background-color: {color}; border-radius: 5px; color: transparent;")
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(price_label)
        layout.addWidget(change_label)
        layout.addWidget(chart_placeholder)
        
        # Set fixed size for the card
        self.setFixedSize(600, 400)

class NSEIndicesDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(100, 50, 150, 200))  # Purple-ish at top
        gradient.setColorAt(1, QColor(50, 50, 150, 200))   # Blue-ish at bottom
        
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Time
        time_label = QLabel("12:45 PM")
        time_label.setFont(QFont("Arial", 16))
        time_label.setStyleSheet("color: white;")
        
        # Title
        title_label = QLabel("NSE Indices")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Temperature
        temp_label = QLabel("☀️ 32°C")
        temp_label.setFont(QFont("Arial", 16))
        temp_label.setStyleSheet("color: white;")
        temp_label.setAlignment(Qt.AlignRight)
        
        header_layout.addWidget(time_label)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(temp_label)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)
        
        # Create a horizontal scrollable container
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable vertical scrolling
        scroll_area.setStyleSheet("""
            QScrollArea { 
                background: transparent; 
                border: none; 
            }
            QScrollBar:horizontal {
                height: 10px;
                background: rgba(255, 255, 255, 30);
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 100);
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                height: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # Container widget for all cards
        scroll_container = QWidget()
        scroll_container.setStyleSheet("background: transparent;")
        
        # Use a vertical layout to stack rows
        container_layout = QVBoxLayout(scroll_container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # Sample stock data
        stocks = [
            {"title": "Nifty 50", "price": "25,426.25", "change": "0.79", "positive": True},
            {"title": "Fin Nifty", "price": "24,426.25", "change": "0.29", "positive": True},
            {"title": "Bank Nifty", "price": "51,460.25", "change": "0.08", "positive": True},
            {"title": "Nifty Midcap 50", "price": "15,426.25", "change": "0.79", "positive": True},
            {"title": "Nifty Smallcap 50", "price": "9,426.25", "change": "0.79", "positive": True},
            {"title": "India VIX", "price": "14.65", "change": "0.79", "positive": False},
        ]
        
        # Add more stocks to test multiple rows
        for i in range(6, 50):
            stocks.append({
                "title": f"Index {i+1}", 
                "price": f"{i*1000+425}.25", 
                "change": "0.50", 
                "positive": i % 2 == 0
            })
        
        # Number of rows to display
        num_rows = 2
        
        # Create rows of cards
        for row in range(num_rows):
            # Create a horizontal layout for each row
            row_layout = QHBoxLayout()
            row_layout.setSpacing(20)
            
            # Add cards to this row
            start_idx = row * (len(stocks) // num_rows)
            end_idx = min((row + 1) * (len(stocks) // num_rows), len(stocks))
            
            for i in range(start_idx, end_idx):
                stock = stocks[i]
                card = StockCard(stock["title"], stock["price"], stock["change"], stock["positive"])
                row_layout.addWidget(card)
            
            # Add the row to the container
            container_layout.addLayout(row_layout)
        
        # Set a fixed height for the scroll area based on the number of rows
        card_height = 660
        spacing = 20
        total_height = (card_height * num_rows) + (spacing * (num_rows + 1))
        scroll_area.setFixedHeight(total_height)
        
        scroll_area.setWidget(scroll_container)
        main_layout.addWidget(scroll_area)
        
        # Enable smooth scrolling
        scroller = QScroller.scroller(scroll_area)
        scroller.grabGesture(scroll_area, QScroller.LeftMouseButtonGesture)
        # Use both gestures
        # scroller.grabGesture(scroll_area, QScroller.LeftMouseButtonGesture)
        scroller.grabGesture(scroll_area, QScroller.TouchGesture)
        
        # Configure the scroller properties for smooth scrolling
        properties = QScrollerProperties()
     # Modify these values for smoother trackpad scrolling
        properties.setScrollMetric(QScrollerProperties.DecelerationFactor, 1)   # Increase for more momentum
        properties.setScrollMetric(QScrollerProperties.DragStartDistance, 0.015)  # Increase this
        properties.setScrollMetric(QScrollerProperties.MinimumVelocity, 0.05)     # Lower minimum velocity
        # properties.setScrollMetric(QScrollerProperties.PixelPerMeter, 2000)       # Control scroll speed
        scroller.setScrollerProperties(properties)
        
        # Navigation buttons (placeholder)
        nav_layout = QHBoxLayout()
        home_btn = QLabel("🏠")
        home_btn.setStyleSheet("color: white; font-size: 24px;")
        nav_layout.addWidget(home_btn)
        nav_layout.addStretch()
        
        # App switcher (placeholder)
        app_switcher = QLabel("◻️◻️\n◻️◻️")
        app_switcher.setStyleSheet("color: white;")
        app_switcher.setAlignment(Qt.AlignRight)
        nav_layout.addWidget(app_switcher)
        
        main_layout.addLayout(nav_layout)
        
        # Set window properties
        self.setWindowTitle('NSE Indices Dashboard')
        self.setGeometry(0, 0, 1920, 1080)  # Full HD resolution
        self.showMaximized()  # Start maximized
        
    def paintEvent(self, event):
        # This ensures the gradient gets updated when the window is resized
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(100, 50, 150, 200))
        gradient.setColorAt(1, QColor(50, 50, 150, 200))
        painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # You could update layout here if needed

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = NSEIndicesDashboard()
    sys.exit(app.exec_())
