
import os
import json
import re

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from modules.chapterList import ChapterListDownloader
from modules.internet import have_internet
from modules.settings import Settings

class ThreadedMangaDownload(object):
    def __init__(self):
        super().__init__()
        self.path = None

        self.downloader = ChapterListDownloader()
        self.downloader_thread = QThread()
        self.init_downloader_thread()
    
    def start_download_task(self, manga_title: str, chapter_list : list):
        if not have_internet():
            return

        manga_title = re.sub(r'[/\\:*"<>|\?]', '', manga_title)
        self.path = os.path.realpath(os.path.join(Settings.manga_save_path, manga_title))
        self.progress['composite_label'].setText('')
        self.progress['chapter_list'].hide()
        self.progress['open_button'].hide()
        self.stack.setCurrentIndex(3)

        self.downloader.manga_name = manga_title
        self.progress['title_label'].setText(manga_title)

        self.downloader.chapter_list = chapter_list
        self.downloader.compile_jpg = self.settings.settings['composite_jpg']
        self.downloader.compile_pdf = self.settings.settings['composite_pdf']
        self.downloader.keep_originals = self.settings.settings['keep_originals']

        self.downloader_thread.start()

    def init_downloader_thread(self):
        self.downloader.total_title_changed.connect(lambda text: self.progress['total_label'].setText(text))
        self.downloader.total_maximum_changed.connect(lambda i: self.progress['total_progress'].setMaximum(i))
        self.downloader.total_progress_changed.connect(lambda i: self.progress['total_progress'].setValue(i))

        self.downloader.chapter_title_changed.connect(lambda text: self.progress['chapter_label'].setText(text))
        self.downloader.chapter_maximum_changed.connect(lambda i: self.progress['chapter_progress'].setMaximum(i))
        self.downloader.chapter_progress_changed.connect(lambda i: self.progress['chapter_progress'].setValue(i))
        
        self.downloader.page_title_changed.connect(lambda text: self.progress['page_label'].setText(text))
        self.downloader.page_maximum_changed.connect(lambda i: self.progress['page_progress'].setMaximum(i / 1024))
        self.downloader.page_progress_changed.connect(lambda i: self.progress['page_progress'].setValue(i / 1024))

        self.downloader.composition_label_changed.connect(lambda text: self.progress['composite_label'].setText(text))

        self.downloader.moveToThread(self.downloader_thread)

        self.downloader.finished.connect(self.downloader_thread.exit)
        self.downloader.finished.connect(self.on_download_finished)

        self.downloader_thread.started.connect(self.downloader.download)

    def on_download_finished(self):
        self.progress['total_progress'].setValue(self.progress['total_progress'].maximum())
        self.progress['chapter_progress'].setValue(self.progress['chapter_progress'].maximum())
        self.progress['page_progress'].setValue(self.progress['page_progress'].maximum())

        self.progress['composite_label'].setText('Download Task Finished!')
        self.download['download_button'].setEnabled(True)
        self.progress['chapter_list'].show()
        self.progress['open_button'].show()

    def download_resume_init(self):
        if not os.path.exists(os.path.join(Settings.manga_save_path, Settings.download_log)):
            return

        manga_title = None
        chapter_list = None
        with open(os.path.join(Settings.manga_save_path, Settings.download_log)) as dlog:
            data = json.load(dlog)
            manga_title = data['name']
            chapter_list = data['list']

        final_list = []
        if type(chapter_list) == dict:
            final_list.append(chapter_list)
        elif type(chapter_list) == list:
            final_list = chapter_list
        else:
            os.remove(os.path.join(Settings.manga_save_path, Settings.download_log))
            return

        resume_query = QMessageBox.question(self, manga_title, 'Download of {0} {1} was not completed.\nWould you like to resume?'.format(len(final_list), 'chapter' if len(final_list) == 1 else 'chapters'))
        if resume_query == QMessageBox.Yes:
            self.start_download_task(manga_title, final_list)
        else:
            os.remove(os.path.join(Settings.manga_save_path, Settings.download_log))
            return

    def on_progress_open_clicked(self):
        os.startfile(self.path)