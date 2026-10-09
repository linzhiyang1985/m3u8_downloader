import PySimpleGUI as sg
import pyperclip

from get_m3u8 import get_m3u8_and_next_page, parse_host
from fetch_ts_files_from_m3u8_list import FLAGS, backup_command, get_m3u8_file_content, download_m3u8

import configparser
from os import path
from threading import Thread
import time

sg.theme('LightBlue')
BOLD_FONT = ('Helvetica', 10, 'bold')
CLOSE_ATTEMPTED_EVENT = getattr(sg, 'WINDOW_CLOSE_ATTEMPTED_EVENT', '-WINDOW CLOSE ATTEMPTED-')


class M3u8Downloader:

    def __init__(self):
        self.window = None
        self.url_dir_pairs = []
        self.copy_paste_target = 'clipboard'
        self.cache1 = ''
        self.cache2 = ''
        # 表格数据行，等价于 toga Table 的 data: [[num, title, m3u8_url], ...]
        self.m3u8_list = []
        self._activate_download_thread_()

    def _activate_download_thread_(self):
        FLAGS['stop'] = False
        self.downloading = False
        self.exit_flag = False
        self.download_thread = Thread(target=self.download_thread_method)
        self.download_thread.start()

    ###### helpers ######

    def _refresh_table_(self):
        self.window['-TABLE-'].update(values=self.m3u8_list)

    def _append_log_(self, text):
        log = self.window['-LOG-']
        # disabled 状态下保证可写
        widget = log.Widget
        state = widget.cget('state')
        widget.configure(state='normal')
        log.update(value=log.get() + '\n' + text)
        widget.configure(state=state)

    ###### event handlers ######

    def clear_start_html_handler(self):
        self.window['-HTML-'].update('')
        self.window['-HTML-'].set_focus()

    def detect_handler(self):
        page_url = self.window['-HTML-'].get()
        if not page_url:
            self.window['-HTML-'].update(placeholder="Please input start html")
            self.window['-HTML-'].set_focus()
            return
        host = parse_host(page_url)
        self.m3u8_list.clear()
        self._refresh_table_()
        start_num = int(self.window['-START-NUM-'].get())
        while True:
            title, m3u8_url, link_next = get_m3u8_and_next_page(host, page_url)
            print(title)
            print(link_next)
            print(m3u8_url)
            self.m3u8_list.append([f"{(len(self.m3u8_list) + start_num):02d}", title, m3u8_url])
            if link_next:
                page_url = link_next
                self.window['-HTML-'].update(page_url)
            self._refresh_table_()
            self.window.refresh()
            if not link_next:
                break

    def renumber_handler(self):
        start_num = int(self.window['-START-NUM-'].get())
        for i, row in enumerate(self.m3u8_list):
            row[0] = f"{(i + start_num):02d}"
        self._refresh_table_()

    def save_settings_handler(self):
        self.save_settings()

    def get_m3u8_list(self):
        m3u8_list = [(row[0], row[1], row[2]) for row in self.m3u8_list]
        return m3u8_list

    def copy_handler(self):
        m3u8_list = self.get_m3u8_list()
        format_to_str = "\n".join([",".join(item) for item in m3u8_list])
        # copy to clipboard
        if self.copy_paste_target == 'clipboard':
            pyperclip.copy(format_to_str)
        elif self.copy_paste_target == 'cache1':
            self.cache1 = format_to_str
        elif self.copy_paste_target == 'cache2':
            self.cache2 = format_to_str

    def paste_handler(self):
        try:
            if self.copy_paste_target == 'clipboard':
                format_as_str = pyperclip.paste()
            elif self.copy_paste_target == 'cache1':
                format_as_str = self.cache1
            elif self.copy_paste_target == 'cache2':
                format_as_str = self.cache2
            if format_as_str:
                #self.m3u8_list.clear()
                m3u8_list = [tuple(item.split(',')) for item in format_as_str.splitlines()]
                for num, title, m3u8_url in m3u8_list:
                    self.m3u8_list.append([num, title, m3u8_url])
                self._refresh_table_()
        except Exception as ex:
            print(ex)

    def select_clipboard_handler(self):
        if self.window['-RD-CLIP-'].get():
            self.copy_paste_target = 'clipboard'

            self.window['-RD-CACHE1-'].update(False)
            self.window['-RD-CACHE2-'].update(False)

    def select_cache1_handler(self):
        if self.window['-RD-CACHE1-'].get():
            self.copy_paste_target = 'cache1'

            self.window['-RD-CLIP-'].update(False)
            self.window['-RD-CACHE2-'].update(False)

    def select_cache2_handler(self):
        if self.window['-RD-CACHE2-'].get():
            self.copy_paste_target = 'cache2'

            self.window['-RD-CLIP-'].update(False)
            self.window['-RD-CACHE1-'].update(False)

    def clear_handler(self):
        self.m3u8_list.clear()
        self._refresh_table_()

    def remove_row_handler(self, selected_rows):
        # 双击行 = 删除该行（等价于 toga Table 的 on_activate）
        for index in sorted(selected_rows or [], reverse=True):
            del self.m3u8_list[index]
        self._refresh_table_()

    def start_download_handler(self):
        ### Settings ###
        root_folder = self.window['-PATH-'].get()
        m3u8_list = self.get_m3u8_list()

        self.url_dir_pairs.clear()
        sep = '/' if root_folder else ''
        for num, _, m3u8_url in m3u8_list:
            self.url_dir_pairs.append((m3u8_url, f'{root_folder}{sep}{num}'))
        ######

        ### batch parse m3u8 ###
        for url, local_dir in self.url_dir_pairs:
            self._append_log_(f'>>> Preparing m3u8 {local_dir}')
            backup_command(url, local_dir, self.window['-FRAG-'].get(), self.window['-SKIP-'].get())
            if not path.exists(path.join(local_dir, 'm3u8.txt')):
                get_m3u8_file_content(url, local_dir)
            self._append_log_(f'<<< Prepared m3u8 {local_dir}')

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
                    try:
                        url, local_dir = self.url_dir_pairs[0]
                        self._append_log_(f">>> Downloading {local_dir}")
                        download_m3u8(url, local_dir,
                                      int(self.window['-FRAG-'].get()),
                                      int(self.window['-SKIP-'].get()))
                        done_count += 1
                        if FLAGS['stop']:
                            self._append_log_(f"<<< Stopped download of {local_dir} ({done_count}/{total})")
                            break
                        else:
                            self._append_log_(f"<<< Downloaded {local_dir} ({done_count}/{total})")
                            self.url_dir_pairs.remove((url, local_dir))
                    except Exception as ex:
                        print(f"Error downloading {local_dir}: {ex}")
                        continue

                self.downloading = False  # all files downloaded
                if FLAGS['stop']:
                    break
            else:
                time.sleep(1)

    def stop_download_handler(self):
        FLAGS['stop'] = True
        self.downloading = False
        self.url_dir_pairs.clear()
        self.download_thread.join()
        self._activate_download_thread_()

    def clear_log_handler(self):
        self.window['-LOG-'].update("<Download Log>\n")

    ###### settings ######

    def load_settings(self):
        ## load settings from file
        config = configparser.ConfigParser()
        if path.exists('settings.ini'):
            config.read('settings.ini', encoding='utf-8')
            self.window['-HTML-'].update(config.get('Settings', 'start_html'))
            self.window['-START-NUM-'].update(value=str(int(config.get('Settings', 'start_num'))))
            self.window['-PATH-'].update(config.get('Settings', 'local_path'))
            self.window['-FRAG-'].update(str(int(config.get('Settings', 'start_index'))))
            self.window['-SKIP-'].update(str(int(config.get('Settings', 'skip_count'))))

            for num in config.options('M3u8'):
                try:
                    title, m3u8_url = config.get('M3u8', num).split(',')
                    self.m3u8_list.append([num, title, m3u8_url])
                except Exception as ex:
                    print(ex)
                    continue
            self._refresh_table_()
        else:
            self.window['-HTML-'].update('')
            self.window['-START-NUM-'].update(value='1')
            self.window['-PATH-'].update('download')
            self.window['-FRAG-'].update('0')
            self.window['-SKIP-'].update('0')
            self.m3u8_list.clear()
            self._refresh_table_()

    def save_settings(self):
        config = configparser.ConfigParser()

        config.add_section('Settings')
        config.set('Settings', 'start_html', self.window['-HTML-'].get())
        config.set('Settings', 'start_num', str(int(self.window['-START-NUM-'].get())))
        config.set('Settings', 'local_path', self.window['-PATH-'].get())
        config.set('Settings', 'start_index', str(self.window['-FRAG-'].get()))
        config.set('Settings', 'skip_count', str(self.window['-SKIP-'].get()))

        config.add_section('M3u8')
        m3u8_list = self.get_m3u8_list()
        for num, title, m3u8_url in m3u8_list:
            config.set('M3u8', num, f'{title},{m3u8_url}')

        with open('settings.ini', 'w', encoding='utf-8') as f:
            config.write(f)

    def close_handler(self):
        self.save_settings()
        if self.download_thread.is_alive():
            FLAGS['stop'] = True
            self.downloading = False
            self.exit_flag = True
        self.download_thread.join()
        self.window.close()

    ###### UI ######

    def _build_ui_(self):
        # left: detect + m3u8 list
        left_layout = [
            [sg.Text("Detect m3u8", font=BOLD_FONT)],
            [sg.Text("Start html", size=(9, 1)),
             sg.Input(key='-HTML-', expand_x=True),
             sg.Button("X", key='-BTN-X-')],
            [sg.Text("Start Num", size=(9, 1)),
             sg.Spin([str(i) for i in range(1, 101)], initial_value='1',
                     key='-START-NUM-', size=(6, 1))],
            [sg.Button("Detect", key='-BTN-DETECT-'),
             sg.Button("Re-num", key='-BTN-RENUM-'),
             sg.Button("Save", key='-BTN-SAVE-')],
            [sg.HorizontalSeparator()],
            [sg.Text("M3u8 list", font=BOLD_FONT)],
            [sg.Button("Copy", key='-BTN-COPY-'),
             sg.Button("Paste", key='-BTN-PASTE-'),
             sg.Text('<=>'),
             sg.Radio('Clipboard', key='-RD-CLIP-', group_id='copy_target', default=True, enable_events=True),
             sg.Radio('Cache1', key='-RD-CACHE1-', group_id='copy_target', enable_events=True),
             sg.Radio('Cache2', key='-RD-CACHE2-', group_id='copy_target', enable_events=True)],
            [sg.Button("Clear", key='-BTN-CLEAR-', size=(8, 1))],
            [sg.Table(values=[], headings=['Num', 'Title', 'M3u8 Url'],
                      key='-TABLE-', enable_events=True,
                      auto_size_columns=True,
                      justification='left',
                      expand_x=True, expand_y=True)],
        ]

        # right: download settings + log
        right_layout = [
            [sg.Text("Download from m3u8 list", font=BOLD_FONT)],
            [sg.Text("Local root path:"), sg.Input(key='-PATH-', expand_x=True)],
            [sg.Text("Start fragment:"), sg.Spin([str(i) for i in range(0, 101)], key='-FRAG-', initial_value='0', size=(6, 1))],
            [sg.Text("Skip end fragments:"), sg.Spin([str(i) for i in range(0, 101)], key='-SKIP-', initial_value='0', size=(6, 1))],
            [sg.Button("Start download", key='-BTN-START-', font=BOLD_FONT),
             sg.Button("Stop download", key='-BTN-STOP-', font=BOLD_FONT)],
            [sg.HorizontalSeparator()],
            [sg.Text("Download log", font=BOLD_FONT),
             sg.Button("Clear log", key='-BTN-CLEARLOG-', size=(9, 1))],
            [sg.Multiline('<Download Log>', key='-LOG-', disabled=True,
                          size=(70, 18), autoscroll=True, expand_x=True, expand_y=True)],
        ]

        layout = [
            [sg.Column(left_layout, vertical_alignment='top',
                        expand_x=True, expand_y=True),
             sg.VSeparator(),
             sg.Column(right_layout, vertical_alignment='top',
                       expand_x=True, expand_y=True)],
        ]
        self.window = sg.Window('M3u8 Downloader', layout,
                                size=(1200, 600), resizable=True,
                                enable_close_attempted_event=True,
                                finalize=True)
        # 双击表格行删除（等价于 toga Table 的 on_activate）
        self.window['-TABLE-'].bind('<Double-Button-1>', '-DOUBLE')

    def main_loop(self):
        self._build_ui_()
        self.load_settings()
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, CLOSE_ATTEMPTED_EVENT):
                self.close_handler()
                break
            elif event == '-BTN-X-':
                self.clear_start_html_handler()
            elif event == '-BTN-DETECT-':
                self.detect_handler()
            elif event == '-BTN-RENUM-':
                self.renumber_handler()
            elif event == '-BTN-SAVE-':
                self.save_settings_handler()
            elif event == '-BTN-COPY-':
                self.copy_handler()
            elif event == '-BTN-PASTE-':
                self.paste_handler()
            elif event == '-RD-CLIP-':
                self.select_clipboard_handler()
            elif event == '-RD-CACHE1-':
                self.select_cache1_handler()
            elif event == '-RD-CACHE2-':
                self.select_cache2_handler()
            elif event == '-BTN-CLEAR-':
                self.clear_handler()
            elif event == '-TABLE--DOUBLE':
                self.remove_row_handler(values['-TABLE-'])
            elif event == '-BTN-START-':
                self.start_download_handler()
            elif event == '-BTN-STOP-':
                self.stop_download_handler()
            elif event == '-BTN-CLEARLOG-':
                self.clear_log_handler()


def main():
    app = M3u8Downloader()
    app.main_loop()


if __name__ == "__main__":
    main()
