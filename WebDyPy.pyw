import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QIcon, QKeySequence

# --- FUNKCE PRO CESTY (POTŘEBNÉ PRO PYINSTALLER) ---
def resource_path(relative_path):
    """ Získá absolutní cestu ke zdroji, funguje pro vývoj i pro PyInstaller """
    try:
        # PyInstaller vytvoří dočasnou složku a uloží cestu do _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- KONFIGURACE PROHLÍŽEČE ---
APP_TITLE = "WebDyPy"
DEFAULT_URL = "https://www.google.com"
SEARCH_ENGINE_URL = "https://www.google.com/search?q="
ICON_SIZE = 18
HOME_ICON_FONT_SIZE = 22
ICON = resource_path("webdypy_icon.ico")

# DPI nastavení pro moderní monitory
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# --- TŘÍDA PROHLÍŽEČE ---
class CustomWebEngineView(QWebEngineView):
    def __init__(self, main_window, *args, **kwargs):
        super(CustomWebEngineView, self).__init__(*args, **kwargs)
        self.main_window = main_window

    def contextMenuEvent(self, event):
        menu = self.page().createStandardContextMenu()
        actions = menu.actions()
        hit_test = self.page().contextMenuData()

        if hit_test.linkUrl().isValid():
            new_tab_action = QAction("Otevřít odkaz v novém panelu", self)
            new_tab_action.triggered.connect(lambda: self.main_window.add_new_tab(hit_test.linkUrl()))
            if actions:
                menu.insertAction(actions[0] if actions else None, new_tab_action)
            else:
                menu.addAction(new_tab_action)
            menu.addSeparator()
        
        menu.exec_(event.globalPos())

# --- HLAVNÍ OKNO ---
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle(APP_TITLE) 
        # Nastavení ikony okna pomocí cesty z resource_path
        self.setWindowIcon(QIcon(ICON))
        self.setStyleSheet("QMainWindow { background-color: white; }")


        # --- Lišta s taby ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setMovable(True) 
        self.tabs.tabBar().setExpanding(True)
        self.tabs.tabBar().setElideMode(Qt.ElideRight)
        
        self.tabs.setStyleSheet("""
            QTabBar::tab { font-size: 13px; padding: 10px 20px; min-width: 150px; background: #e8eaed; border: 1px solid #d1d1d1; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
            QTabBar::tab:selected { background: white; font-weight: bold; border-bottom: 2px solid white; }
            QTabBar::tab:hover:not(:selected) { background: #f1f3f4; }
            QTabWidget::pane { border: none; }
            QTabBar { background: #f1f3f4; qproperty-drawBase: 0; }
        """)

        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.clicked.connect(lambda: self.add_new_tab())
        self.add_tab_button.setStyleSheet("QToolButton { font-size: 20px; background: transparent; border: none; padding: 0 15px; color: #5f6368; } QToolButton:hover { color: #1a73e8; background: #e8eaed; border-radius: 15px; }")
        self.tabs.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # --- Navigační lišta ---
        self.navbar = QToolBar("Navigace")
        self.navbar.setIconSize(QSize(ICON_SIZE, ICON_SIZE)) 
        self.navbar.setMovable(False)
        self.navbar.setStyleSheet("background: white; padding: 5px; border-bottom: 1px solid #dee2e6;")
        self.addToolBar(Qt.TopToolBarArea, self.navbar)

        self.back_btn = QAction(self.style().standardIcon(QStyle.SP_ArrowBack), 'Zpět', self)
        self.back_btn.triggered.connect(lambda: self.get_current_browser().back())
        self.navbar.addAction(self.back_btn)

        self.forward_btn = QAction(self.style().standardIcon(QStyle.SP_ArrowForward), 'Vpřed', self)
        self.forward_btn.triggered.connect(lambda: self.get_current_browser().forward())
        self.navbar.addAction(self.forward_btn)

        self.reload_btn = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), 'Obnovit', self)
        self.reload_btn.triggered.connect(lambda: self.get_current_browser().reload())
        self.navbar.addAction(self.reload_btn)

        self.home_btn = QAction('⌂', self) 
        self.home_btn.triggered.connect(self.navigate_home)
        self.navbar.addAction(self.home_btn)
        self.navbar.widgetForAction(self.home_btn).setStyleSheet(f"font-size: {HOME_ICON_FONT_SIZE}px; font-weight: bold; margin-right: 5px; color: #5f6368;")


        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet("QLineEdit { font-size: 14px; padding: 8px 15px; border-radius: 18px; border: 1px solid #dfe1e5; background: #f1f3f4; color: black; } QLineEdit:focus { background: white; border: 1px solid #1a73e8; }")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        # --- Uspořádání ---
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(container)


        # Klávesové zkratky
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(lambda: self.add_new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("F5"), self).activated.connect(lambda: self.get_current_browser().reload())

        self.add_new_tab(QUrl(DEFAULT_URL), 'Domů')
        self.showMaximized()

    # --- LOGIKA FUNKCÍ ---
    def get_current_browser(self): 
        return self.tabs.currentWidget()

    def add_new_tab(self, qurl=None, label="Nový panel"):
        if qurl is None: 
            qurl = QUrl(DEFAULT_URL)
        
        browser = CustomWebEngineView(self)
        browser.setUrl(qurl)
        
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda qurl, b=browser: self.update_urlbar(qurl, b))
        browser.loadFinished.connect(lambda _, b=browser: self.update_title(b))
        browser.iconChanged.connect(lambda icon, b=browser: self.update_tab_icon(b, icon))


    def update_tab_icon(self, browser, icon):
        index = self.tabs.indexOf(browser)
        if index != -1: self.tabs.setTabIcon(index, icon)

    def update_title(self, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            title = browser.page().title()
            self.tabs.setTabText(index, (title[:25] + '...') if len(title) > 25 else title)

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            self.get_current_browser().setUrl(QUrl(DEFAULT_URL))
            return
        browser = self.tabs.widget(i)
        self.tabs.removeTab(i)
        browser.deleteLater()

    def current_tab_changed(self, i):
        if i != -1:
            browser = self.tabs.widget(i)
            if browser: self.update_urlbar(browser.url(), browser)

    def update_urlbar(self, q, browser=None):
        if browser != self.get_current_browser(): return
        self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

    def navigate_home(self): 
        self.get_current_browser().setUrl(QUrl(DEFAULT_URL))

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text: return
        
        if "." not in text and "localhost" not in text and ":" not in text:
            qurl = QUrl(f"{SEARCH_ENGINE_URL}{text}")
        elif not text.startswith(("http://", "https://", "file://")):
            qurl = QUrl("http://" + text)
        else:
            qurl = QUrl(text)
        self.get_current_browser().setUrl(qurl)

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON)) 
    app.setApplicationName(APP_TITLE)

    window = MainWindow()
    sys.exit(app.exec_())
#WebDyPy 1.0 by Daniell291 2025-2026. created with help from youtube and AI