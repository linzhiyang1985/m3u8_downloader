from toga import MainWindow, Label, Button, Box, TextInput, MultilineTextInput, SplitContainer, NumberInput
import toga
import pyperclip

from get_m3u8 import get_m3u8_and_next_page, parse_host
from fetch_ts_files_from_m3u8_list import FLAGS, backup_command, get_m3u8_file_content, download_m3u8

from toga.constants import COLUMN, ROW

from typing import TypeAlias
from pathlib import Path
IconContentT: TypeAlias = str | Path | toga.Icon

from toga.app import AppStartupMethod, OnRunningHandler, OnExitHandler
from toga.documents import Document

import configparser
from os import path
from threading import Thread
import time

class M3u8Downloader(toga.App):

    def __init__(self,
        formal_name: str | None = None,
        app_id: str | None = None,
        app_name: str | None = None,
        *,
        icon: IconContentT | None = None,
        author: str | None = None,
        version: str | None = None,
        home_page: str | None = None,
        description: str | None = None,
        startup: AppStartupMethod | None = None,
        document_types: list[type[Document]] | None = None,
        on_running: OnRunningHandler | None = None,
        on_exit: OnExitHandler | None = None,
        ):
        super().__init__(
            formal_name=formal_name,
            app_id=app_id,
            app_name=app_name,
            icon=icon,
            author=author,
            version=version,
            home_page=home_page,
            description=description,
            startup=startup,
            document_types=document_types,
            on_running=on_running,
            on_exit=on_exit)
        self.main_window = None
        self.url_dir_pairs = []
        self._activate_download_thread_()

    def _activate_download_thread_(self):
        FLAGS['stop'] = False
        self.downloading = False
        self.exit_flag = False
        self.download_thread = Thread(target=self.download_thread_method)
        self.download_thread.start()

    def clear_start_html_handler(self, widget):
        self.html_input.value = ""

    def detect_handler(self, widget):
        page_url = self.html_input.value
        if not page_url:
            self.html_input.placeholder = "Please input start html"
            self.html_input.focus()
            return
        host = parse_host(page_url)
        self.m3u8_table.data.clear()
        start_num = int(self.start_num_input.value)
        while True:
            title, m3u8_url, link_next = get_m3u8_and_next_page(host, page_url)
            print(title)
            print(link_next)
            print(m3u8_url)
            self.m3u8_table.data.append((f"{(len(self.m3u8_table.data)+start_num):02d}", title, m3u8_url))
            if link_next:
                page_url = link_next
                self.html_input.value = page_url
            else:
                break
    
    def get_m3u8_list(self):
        m3u8_list = [(row.num, row.title, row.m3u8_url) for row in self.m3u8_table.data]
        return m3u8_list

    def copy_handler(self, widget):
        m3u8_list = self.get_m3u8_list()
        format_to_str = "\n".join([",".join(item) for item in m3u8_list])
        # copy to clipboard
        pyperclip.copy(format_to_str)

    def paste_handler(self, widget):
        try:
            format_as_str = pyperclip.paste()
            if format_as_str:
                #self.m3u8_table.data.clear()
                m3u8_list = [tuple(item.split(',')) for item in format_as_str.splitlines()]
                for num, title, m3u8_url in m3u8_list:
                    self.m3u8_table.data.append((num, title, m3u8_url))
        except Exception as ex:
            print(ex)

    def clear_handler(self, widget):
        self.m3u8_table.data.clear()        

    def remove_row_handler(self, widget, row):
        self.m3u8_table.data.remove(row)

    def start_download_handler(self, widget):
        ### Settings ###
        root_folder = self.local_path_input.value
        m3u8_list = self.get_m3u8_list()

        self.url_dir_pairs.clear()
        for num, _, m3u8_url in m3u8_list:
            self.url_dir_pairs.append((m3u8_url, f'{root_folder}{'/' if root_folder else ''}{num}'))
        ######

        ### batch parse m3u8 ###
        for url, local_dir in self.url_dir_pairs:
            self.download_log.value += f'>>> Preparing m3u8 {local_dir}\n'
            backup_command(url, local_dir, self.start_fragment_index_input.value, self.skip_count_input.value)
            if not path.exists(path.join(local_dir, 'm3u8.txt')):
                get_m3u8_file_content(url, local_dir)
            self.download_log.value += f'<<< Prepared m3u8 {local_dir}\n'

        ### Download ###
        self.downloading = True
        ######

    def download_thread_method(self):
        while True:
            if self.exit_flag:
                break
            
            if self.downloading and self.url_dir_pairs:
                # can do download
                total = len(self.url_dir_pairs)
                done_count = 0
                while self.url_dir_pairs:
                    url, path = self.url_dir_pairs[0]
                    self.download_log.value += f">>> Downloading {path}\n"
                    download_m3u8(url, path, int(self.start_fragment_index_input.value), int(self.skip_count_input.value))
                    done_count += 1
                    if FLAGS['stop']:
                        self.download_log.value += f"<<< Stopped download of {path} ({done_count}/{total})\n"
                        break
                    else:
                        self.download_log.value += f"<<< Downloaded {path} ({done_count}/{total})\n"
                        self.url_dir_pairs.remove((url, path))
                
                self.downloading = False # all files downloaded
                if FLAGS['stop']:
                    break
            else:
                time.sleep(1)

    def stop_download_handler(self, widget):
        FLAGS['stop'] = True
        self.downloading = False
        self.url_dir_pairs.clear()
        self.download_thread.join()
        self._activate_download_thread_()

    def clear_log_handler(self, widget):
        self.download_log.value = "<Download Log>\n"
    
    def load_settings(self):
        ## load settings from file
        config = configparser.ConfigParser()
        if path.exists('settings.ini'):
            config.read('settings.ini', encoding='utf-8')
            self.html_input.value = config.get('Settings', 'start_html')
            self.start_num_input.value = int(config.get('Settings', 'start_num'))
            self.local_path_input.value = config.get('Settings', 'local_path')
            self.start_fragment_index_input.value = int(config.get('Settings', 'start_index'))
            self.skip_count_input.value = int(config.get('Settings', 'skip_count'))
            
            for num in config.options('M3u8'):
                try:
                    title, m3u8_url = config.get('M3u8', num).split(',')
                    self.m3u8_table.data.append((num, title, m3u8_url))
                except Exception as ex:
                    print(ex)
                    continue
        else:
            self.html_input.value = ''
            self.start_num_input.value = 1
            self.local_path_input.value = 'download'
            self.start_fragment_index_input.value = 0
            self.skip_count_input.value = 0
            self.m3u8_table.data.clear()

    def save_settings(self):
        config = configparser.ConfigParser()

        config.add_section('Settings')
        config.set('Settings', 'start_html', self.html_input.value)
        config.set('Settings', 'start_num', str(int(self.start_num_input.value)))
        config.set('Settings', 'local_path', self.local_path_input.value)
        config.set('Settings', 'start_index', str(self.start_fragment_index_input.value))
        config.set('Settings', 'skip_count', str(self.skip_count_input.value))

        config.add_section('M3u8')
        m3u8_list = self.get_m3u8_list()
        for num, title, m3u8_url in m3u8_list:
            config.set('M3u8', num, f'{title},{m3u8_url}')
        
        with open('settings.ini', 'w', encoding='utf-8') as f:
            config.write(f)

    def close_handler(self, widget):
        self.save_settings()
        if self.download_thread.is_alive():
            FLAGS['stop'] = True
            self.downloading = False
            self.exit_flag = True
        self.download_thread.join()
        self.main_window.close()

    def startup(self):
        row1 = Box(children=[
            Label("Detect m3u8", font_weight="bold")
        ])

        self.html_input = TextInput(flex=1)
        row2 = Box(direction=ROW, gap=10, children=[
            Label("Start html"),
            self.html_input,
            Button("X", on_press = self.clear_start_html_handler)
        ])

        self.start_num_input = NumberInput(value=1, flex=1, min=1, max=100)
        row3 = Box(direction=ROW, gap=10, children=[
            Label("Start Num"),
            self.start_num_input
        ])

        row4 = Box(children=[
            Button("Detect", on_press = self.detect_handler)
        ])
        
        detect_box = Box(direction=COLUMN, gap=10, height=150, children=[
            row1,
            row2,
            row3,
            row4
        ])
        ######
        self.m3u8_table = toga.Table(columns=["Num", "Title", "M3u8 Url"], data=[], flex=1)
        self.m3u8_table.on_activate = self.remove_row_handler

        row5 = Box(gap=10, children=[
            Button("Copy", on_press = self.copy_handler),
            Button("Paste", on_press = self.paste_handler),
            Button("Clear", on_press = self.clear_handler)
        ])

        m3u8_box = Box(direction=COLUMN, gap=10, flex=1, children=[
            Label("M3u8 list", font_weight="bold"),
            row5,
            self.m3u8_table
        ])

        left_box = Box(direction=COLUMN, gap=10, children=[
            detect_box,
            toga.Divider(),
            m3u8_box
        ])

        ####
        self.local_path_input = TextInput(flex=1)
        row6 = Box(direction=ROW, gap=10, children=[
            Label("Local root path:"),
            self.local_path_input
        ])

        ###
        self.start_fragment_index_input = NumberInput(flex=1)
        row7 = Box(direction=ROW, gap=10, children=[
            Label("Start fragment:"),
            self.start_fragment_index_input
        ])

        ###
        self.skip_count_input = NumberInput(flex=1)
        row8 = Box(direction=ROW, gap=10, children=[
            Label("Skip end fragments:"),
            self.skip_count_input
        ])

        ###
        download_setting_box = Box(direction=COLUMN, gap=10, children=[
            row6,
            row7,
            row8
        ])
        
        button_box = Box(direction=ROW, gap=10, children=[
            Button("Start download", font_weight="bold", on_press = self.start_download_handler),
            Button("Stop download", font_weight="bold", on_press = self.stop_download_handler)
        ])
        
        ###
        self.download_log = MultilineTextInput(readonly=True, flex=1)
        self.download_log.value = "<Download Log>\n"
        log_box = Box(direction=COLUMN, gap=10, children=[
            Label("Download log", font_weight="bold"),
            Button("Clear log", width=100, on_press = self.clear_log_handler),
            self.download_log
        ])
        ###
        right_box = Box(direction=COLUMN, gap=10, children=[
            Label("Download from m3u8 list", font_weight="bold"),
            download_setting_box,
            button_box,
            toga.Divider(),
            log_box
        ])
        ###
        split = SplitContainer()
        split.content = [(left_box, 1), (right_box, 2)]

        ###
        self.load_settings()
        self.main_window = MainWindow()
        self.main_window.size = (1200, 600)
        self.main_window.title = 'M3u8 Downloader'
        self.main_window.on_close = self.close_handler
        self.main_window.content = split
        self.main_window.show()


def main():
    return M3u8Downloader("App", "ent.tool.downloader.m3u8")

if __name__ == "__main__":
    main().main_loop()
