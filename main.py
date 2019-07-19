import sys
import re
import datetime

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import traceback

from modules.chapterList import ChapterListDownloader, ChapterListLoader
from modules.codec import MKCodec
from modules.settings import Settings
from ui.mangaDownloading import ThreadedMangaDownload
from ui.mangaLoading import ThreadedMangaLoad
from ui.search import ThreadedSearch
from ui.tree_gen import ThreadedTreeGenerate
from ui.web import ThreadedWebGenerate
from ui.popular import PopularPage
from ui.top10 import Top10List

from dialogs.main_window import Ui_MainWindow

from modules.html import HtmlManager

class Ui(QMainWindow, ThreadedSearch, ThreadedMangaLoad, ThreadedMangaDownload, ThreadedTreeGenerate, ThreadedWebGenerate, PopularPage, Top10List):
    def __init__(self, app : QApplication):
        super(Ui, self).__init__()
        # uic.loadUi('dialogs/main.ui', self)

        Ui_MainWindow().setupUi(self)

        self.app = app

        self.settings = Settings()
        self.dark_palette = QPalette()
        self.init_dark_palette()

        self.stack = self.findChild(QStackedWidget, 'dynamicStack')

        self.navbar = {
            'chapter': self.findChild(QAction, 'actionChapterView'),
            'download': self.findChild(QAction, 'actionDownloadsView'),
            'exit': self.findChild(QAction, 'actionExit'),
            'generate_tree': self.findChild(QAction, 'actionGenerate'),
            'keep_originals': self.findChild(QAction, 'actionKeep_originals'),
            'composite_jpg': self.findChild(QAction, 'actionCompositeJpg'),
            'startup_popular': self.findChild(QAction, 'actionLoadPopular'),
            'startup_top10': self.findChild(QAction, 'actionLoadTop10'),
            'composite_pdf': self.findChild(QAction, 'actionCompositePdf'),
            'dark_mode': self.findChild(QAction, 'actionDarkMode'),
            'documentation': self.findChild(QAction, 'actionDocumentation'),
            'about': self.findChild(QAction, 'actionAbout'),
        }
        self.navbar['chapter'].triggered.connect(lambda: self.stack.setCurrentIndex(2))
        self.navbar['download'].triggered.connect(lambda: self.stack.setCurrentIndex(3))
        self.navbar['exit'].triggered.connect(self.close)
        self.navbar['generate_tree'].triggered.connect(self.on_generate_clicked)
        self.navbar['about'].triggered.connect(lambda: QMessageBox.information(self, 'About', 'Author: mHaisham\nDescription: Supports download from mangakakalot.com, composition options and viewing the downloaded manga'))
        
        self.navbar['startup_popular'].setChecked(self.settings.settings['startup_popular'])
        self.navbar['startup_top10'].setChecked(self.settings.settings['startup_top10'])
        self.navbar['composite_jpg'].setChecked(self.settings.settings['composite_jpg'])
        self.navbar['composite_pdf'].setChecked(self.settings.settings['composite_pdf'])
        self.navbar['keep_originals'].setChecked(self.settings.settings['keep_originals'])
        self.navbar['dark_mode'].setChecked(self.settings.settings['dark_mode'])

        self.navbar['startup_popular'].triggered.connect(self.update_settings)
        self.navbar['startup_top10'].triggered.connect(self.update_settings)
        self.navbar['composite_jpg'].triggered.connect(self.update_settings)
        self.navbar['composite_pdf'].triggered.connect(self.update_settings)
        self.navbar['keep_originals'].triggered.connect(self.update_settings)
        self.navbar['dark_mode'].triggered.connect(self.set_theme)

        self.navigation = {
            'hot': self.findChild(QPushButton, 'hotNavButton'),
            'top10': self.findChild(QPushButton, 'top10NavButton'),
            'search': self.findChild(QPushButton, 'searchNavButton'),
            'direct': self.findChild(QPushButton, 'directNavButton'),
            'browser': self.findChild(QPushButton, 'viewFunButton')
        }
        
        self.navigation['hot'].clicked.connect(lambda : self.stack.setCurrentIndex(4))
        self.navigation['top10'].clicked.connect(lambda : self.stack.setCurrentIndex(5))
        self.navigation['search'].clicked.connect(lambda : self.stack.setCurrentIndex(0))
        self.navigation['direct'].clicked.connect(lambda : self.stack.setCurrentIndex(1))
        self.navigation['browser'].clicked.connect(self.on_browser_clicked)

        self.popular = {
            'previous_button': self.findChild(QPushButton, 'previousPopularButton'),
            'next_button': self.findChild(QPushButton, 'nextPopularButton'),
            'refresh_button': self.findChild(QPushButton, 'refreshPopularButton'),
            'pageno_label': self.findChild(QLabel, 'pagePopularLabel'),
            'page_spinbox': self.findChild(QSpinBox, 'selectPopularPageSpinBox'),
            'page_button': self.findChild(QPushButton, 'selectPopularPageButton'),
            'table': self.findChild(QListWidget, 'popularTableWidget'),
            'proceed_button': self.findChild(QPushButton, 'proceedPopularButton'),
            'progress': self.findChild(QProgressBar, 'popularProgressBar')
        }

        self.popular['progress'].hide()

        self.popular['refresh_button'].clicked.connect(self.on_refresh)
        self.popular['previous_button'].clicked.connect(self.on_previous_page)
        self.popular['page_button'].clicked.connect(self.on_custom_page_select)
        self.popular['next_button'].clicked.connect(self.on_next_page)
        self.popular['proceed_button'].clicked.connect(self.on_proceed_popular)

        self.top = {
            'list': self.findChild(QListWidget, 'top10ListWidget'),
            'refresh': self.findChild(QPushButton, 'refreshTopButton'),
            'next_button': self.findChild(QPushButton, 'nextTopButton')
        }

        self.top['refresh'].clicked.connect(self.on_top10_refresh)
        self.top['next_button'].clicked.connect(self.on_top10_next)

        self.search = {
            'input': self.findChild(QLineEdit, 'searchInputBox'),
            'search_button': self.findChild(QPushButton, 'mangaSearchButton'),
            'table': self.findChild(QTableWidget, 'searchResultTable'),
            'progress_bar': self.findChild(QProgressBar, 'searchProgressBar'),
            'next_button': self.findChild(QPushButton, 'searchNextButton')
        }


        self.search['progress_bar'].hide()
        self.search['search_button'].clicked.connect(self._search)
        self.search['next_button'].clicked.connect(self._search_to_manga_download)

        self.direct = {
            'input': self.findChild(QLineEdit, 'directDownloadInput'),
            'next_button': self.findChild(QPushButton, 'directNextButton'),
            'error_label': self.findChild(QLabel, 'directDownloadErrorLabel')
        }

        self.direct['next_button'].clicked.connect(self.on_direct_download)

        self.download = {
            'title': self.findChild(QLabel, 'mangaTitle'),
            'select_all': self.findChild(QPushButton, 'selectAllMangaButton'),
            'inverse': self.findChild(QPushButton, 'inverseSelectedMangaButton'),
            'list': self.findChild(QListWidget, 'chapterListWidget'),
            'progress_bar': self.findChild(QProgressBar, 'mangaDataLoadProgressBar'),
            'download_button': self.findChild(QPushButton, 'selectedMangaDownloadButton')
        }

        self.download['progress_bar'].hide()
        self.download['select_all'].clicked.connect(self.select_all)
        self.download['inverse'].clicked.connect(self.inverse_all)
        self.download['download_button'].clicked.connect(self.on_download_clicked)

        self.progress = {
            'title_label': self.findChild(QLabel, 'progressTitleLabel'),

            'total_label': self.findChild(QLabel, 'totalDownloadProgressLabel'),
            'total_progress': self.findChild(QProgressBar, 'totalDownloadProgressBar'),

            'chapter_label': self.findChild(QLabel, 'chapterDownloadProgressLabel'),
            'chapter_progress': self.findChild(QProgressBar, 'chapterDownloadProgressBar'),

            'page_label': self.findChild(QLabel, 'pageDownloadProgressLabel'),
            'page_progress': self.findChild(QProgressBar, 'pageDownloadProgressBar'),

            'composite_label': self.findChild(QLabel, 'compositingLabel')
        }
        if self.settings.settings['startup_popular']:
            self.on_refresh()
        if self.settings.settings['startup_top10']:
            self.on_top10_refresh()

        self.set_theme(save=False)
        self.download_resume_init()
        self.show()

    def on_direct_download(self):
        self.direct['input'].setEnabled(False)
        self.load_manga(self.direct['input'].text())

    def update_settings(self):
        self.settings.save_settings(
            self.navbar['startup_popular'].isChecked(),
            self.navbar['startup_top10'].isChecked(),
            self.navbar['composite_jpg'].isChecked(),
            self.navbar['composite_pdf'].isChecked(),
            self.navbar['keep_originals'].isChecked()
        )

    def init_dark_palette(self):
        self.dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.WindowText, Qt.white)
        self.dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        self.dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        self.dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        self.dark_palette.setColor(QPalette.Text, Qt.white)
        self.dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        self.dark_palette.setColor(QPalette.ButtonText, Qt.white)
        self.dark_palette.setColor(QPalette.BrightText, Qt.red)
        self.dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    def set_theme(self, save = True) -> None:
        is_dark = self.navbar['dark_mode'].isChecked()
        self.app.setPalette(self.dark_palette if is_dark else self.app.style().standardPalette())
        
        if save:
            self.settings.dark_mode_enabled(is_dark)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = Ui(app)
        app.exec_()
    except:
        with open(re.sub(r':', '-', str(datetime.datetime.now())) + '.txt', 'w') as f:
            f.write(traceback.format_exc())
