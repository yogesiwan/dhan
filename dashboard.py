from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QGridLayout, 
                            QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, 
                            QFrame, QStackedWidget, QPushButton)
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap, QIcon
from PyQt6.QtCore import Qt, QTime, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint, QParallelAnimationGroup
import os
import sys

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
                background-color: rgba(40, 50, 80, 0.7);
                border-radius: 10px;
                padding: 15px;
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
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        layout.addWidget(value_label)
        
        # Change with icon
        change_color = "green" if not change.startswith("-") else "red"
        change_icon = "↗" if not change.startswith("-") else "↘"
        
        change_label = QLabel(f"{change} {change_icon}")
        change_label.setFont(QFont("Segoe UI", 12))
        change_label.setStyleSheet(f"color: {change_color};")
        layout.addWidget(change_label)

class PageContainer(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        # Use resource_path to load the image
        self.background = QPixmap(resource_path("bg_blurlow.png"))
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Top bar with time, title and temperature
        top_bar = QHBoxLayout()
        
        # Time
        self.time_label = QLabel("12:45 PM")
        self.time_label.setObjectName("time_label")
        self.time_label.setFont(QFont("Segoe UI", 14))
        self.time_label.setStyleSheet("color: white;")
        top_bar.addWidget(self.time_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_label, 1)
        
        # Temperature
        temp_label = QLabel("☀️ 32°C")
        temp_label.setFont(QFont("Segoe UI", 14))
        temp_label.setStyleSheet("color: white;")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_bar.addWidget(temp_label)
        
        self.main_layout.addLayout(top_bar)
        
        # Grid layout for cards - to be filled by subclasses
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.main_layout.addLayout(self.grid_layout)
        
        # Navigation dots
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.nav_layout)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background)
        
    def update_time(self):
        current_time = QTime.currentTime()
        time_text = current_time.toString("hh:mm AP")
        self.time_label.setText(time_text)

class IndicesPage(PageContainer):
    def __init__(self, parent=None):
        super().__init__("NSE Indices", parent)
        
        # Card data for Indices page
        cards_data = [
            {"title": "Nifty 50", "value": "₹ 25,426.25", "change": "0.79%", "pos": (0, 0)},
            {"title": "Fin Nifty", "value": "₹ 24,426.25", "change": "0.29%", "pos": (0, 1)},
            {"title": "Bank Nifty", "value": "₹ 51,460.25", "change": "0.08%", "pos": (0, 2)},
            {"title": "Nifty Midcap 50", "value": "₹ 15,426.25", "change": "0.79%", "pos": (1, 0)},
            {"title": "Nifty Smallcap 50", "value": "₹ 9,426.25", "change": "0.79%", "pos": (1, 1)},
            {"title": "India VIX", "value": "₹", "change": "-0.79%", "pos": (1, 2)}
        ]
        
        # Create and add cards
        for card_data in cards_data:
            card = GlassmorphicCard(
                card_data["title"], 
                card_data["value"], 
                card_data["change"]
            )
            row, col = card_data["pos"]
            self.grid_layout.addWidget(card, row, col)

class StocksPage(PageContainer):
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
            self.grid_layout.addWidget(card, row, col)

class GlassmorphicUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial Dashboard")
        self.setGeometry(100, 100, 960, 580)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create stacked widget for page transitions
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.indices_page = IndicesPage()
        self.stocks_page = StocksPage()
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.indices_page)
        self.stacked_widget.addWidget(self.stocks_page)
        
        # Add navigation dots to each page
        self.setup_navigation()
        
        main_layout.addWidget(self.stacked_widget)
        
        # Add swipe functionality
        self.old_pos = None
        self.current_page = 0
        self.total_pages = self.stacked_widget.count()
        
        # Animation in progress flag
        self.animation_in_progress = False
        
        # Update time periodically
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(60000)  # Update every minute
        
        # Initial time update
        self.update_time()
    
    def setup_navigation(self):
        # Create navigation dots for both pages
        for page_idx in range(self.stacked_widget.count()):
            for i in range(self.stacked_widget.count()):
                page = self.stacked_widget.widget(page_idx)
                
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
                dot.setChecked(i == page_idx)
                
                # Use a lambda with default arguments to avoid late binding issues
                dot.clicked.connect(lambda checked, idx=i: self.change_page(idx))
                
                page.nav_layout.addWidget(dot)
    
    def update_time(self):
        current_page = self.stacked_widget.currentWidget()
        if isinstance(current_page, PageContainer):
            current_page.update_time()
    
    def update_navigation(self):
        # Update the navigation dots based on current page
        for page_idx in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(page_idx)
            for i, dot in enumerate(self.find_children(page.nav_layout, QPushButton)):
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
            
            # If the swipe distance is significant (more than 50 pixels)
            if abs(dx) > 50:
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
        # Set animation in progress flag
        self.animation_in_progress = True
        
        # Initialize animation properties
        direction = 1 if new_page > self.current_page else -1
        current_widget = self.stacked_widget.widget(self.current_page)
        new_widget = self.stacked_widget.widget(new_page)
        
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
            animation_group = QParallelAnimationGroup()
            
            # Create animation for current widget
            current_anim = QPropertyAnimation(current_widget, b"pos")
            current_anim.setDuration(450)  # Longer, smoother animation
            current_anim.setStartValue(QPoint(0, 0))
            current_anim.setEndValue(QPoint(-direction * screen_width, 0))
            current_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)  # Smoother curve
            
            # Create animation for new widget
            new_anim = QPropertyAnimation(new_widget, b"pos")
            new_anim.setDuration(450)  # Longer, smoother animation
            new_anim.setStartValue(QPoint(direction * screen_width, 0))
            new_anim.setEndValue(QPoint(0, 0))
            new_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)  # Smoother curve
            
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
        self.stacked_widget.setCurrentIndex(self.current_page)
        
        # Reset animation flag
        self.animation_in_progress = False

if __name__ == "__main__":
    app = QApplication([])
    window = GlassmorphicUI()
    window.show()
    app.exec()