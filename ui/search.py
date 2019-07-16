from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from modules.codec import MKCodec


class ThreadedSearch(object):
    def __init__(self):
        super().__init__()

        self.codec = MKCodec()
        self.search_thread = QThread()
        self._init_search_thread()
        
    def _init_search_thread(self):
        self.codec.progress.connect(self._on_search_progress)
        self.codec.maximum.connect(self._set_search_maximum)

        self.codec.moveToThread(self.search_thread)

        self.codec.finished.connect(self.search_thread.quit)
        self.codec.finished.connect(self._on_search_finished)

        self.search_thread.started.connect(self.codec.search)

    def _search(self):

        # disable controls
        self.search['input'].setEnabled(False)
        self.search['search_button'].setEnabled(False)

        self.codec.keyword = self.codec.search_prefix + self.search['input'].text()

        self.search_thread.start()

    def _on_search_progress(self, i):
        self.search['progress_bar'].setValue(i)

    def _set_search_maximum(self, i):
        self.search['progress_bar'].setMaximum(i)
        self.search['progress_bar'].show()

    def _on_search_finished(self):

        # fill table
        self.search['table'].setRowCount(len(self.codec.search_result))
        for i in range(len(self.codec.search_result)):
            manga = self.codec.search_result[i]

            self.search['table'].setItem(i, 0, QTableWidgetItem(manga['name']))
            self.search['table'].setItem(i, 1, QTableWidgetItem(manga['last_chapter']))

        # enable controls
        self.search['input'].setEnabled(True)
        self.search['search_button'].setEnabled(True)
        self.search['progress_bar'].hide()
        print('search done')