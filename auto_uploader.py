import concurrent.futures
import datetime
import functools
import http.server
import json
import os.path
import re
import shutil
import socket
import socketserver
import threading
import time
import urllib.parse

import pymediainfo
import wx

# Constants
MEDIA_DIR = 'media'
ARCHIVE_DIR = 'archive'
SERVER_IP = '192.168.4.89'
SERVER_PORT = 8000

COLOR_WHITE = (wx.Colour(255, 255, 255), wx.BLACK)
COLOR_GRAY = (wx.Colour(150, 150, 150), wx.BLACK)
COLOR_YELLOW = (wx.Colour(255, 215, 0), wx.BLACK)
COLOR_GREEN = (wx.Colour(173, 255, 47), wx.BLACK)
COLOR_RED = (wx.Colour(220, 100, 100), wx.BLACK)
COLOR_BLUE = (wx.Colour(135, 206, 250), wx.BLACK)


class AppView(wx.Frame):
    def __init__(self):
        super().__init__(None, style=wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX), size=(600, 550))
        self.SetIcon(wx.Icon('app.ico'))
        self.SetTitle('Auto Uploader')
        self.panel = wx.Panel(self)

        # Device box
        dev_box = wx.StaticBox(self.panel, label='Device Settings')
        dev_box_sizer = wx.StaticBoxSizer(dev_box, wx.HORIZONTAL)
        # Label of device IP address
        txt_dev_ip_addr = wx.StaticText(self.panel, label='IP Address:')
        dev_box_sizer.Add(txt_dev_ip_addr, proportion=0, flag=wx.EXPAND | wx.ALL, border=4)
        # Input of device IP address
        self.tc_dev_ip_addr = wx.TextCtrl(self.panel)
        dev_box_sizer.Add(self.tc_dev_ip_addr, proportion=1, flag=wx.EXPAND | wx.ALL, border=2)
        # Set button
        self.btn_dev_ip_addr = wx.Button(self.panel, label='OK')
        dev_box_sizer.Add(self.btn_dev_ip_addr, proportion=0, flag=wx.EXPAND | wx.ALL, border=1)

        # Automation box
        auto_box = wx.StaticBox(self.panel, label='Automation')
        auto_box_sizer = wx.StaticBoxSizer(auto_box, wx.HORIZONTAL)
        # Label of directory watch path
        txt_watch_path = wx.StaticText(self.panel, label='Watch Folder:')
        auto_box_sizer.Add(txt_watch_path, proportion=0, flag=wx.EXPAND | wx.ALL, border=4)
        # Input of directory watch path
        self.tc_watch_path = wx.TextCtrl(self.panel)
        auto_box_sizer.Add(self.tc_watch_path, proportion=1, flag=wx.EXPAND | wx.ALL, border=2)
        # Set button
        self.btn_watch_path = wx.Button(self.panel, label='OK')
        auto_box_sizer.Add(self.btn_watch_path, proportion=0, flag=wx.EXPAND | wx.ALL, border=1)

        # Control box
        ctrl_box = wx.StaticBox(self.panel, label='Device Control')
        ctrl_box_sizer = wx.StaticBoxSizer(ctrl_box, wx.HORIZONTAL)
        gbs = wx.GridBagSizer(vgap=2, hgap=2)
        # Button of show version
        self.btn_show_ver = wx.Button(self.panel, label='Show Version')
        gbs.Add(self.btn_show_ver, pos=(0, 0), flag=wx.EXPAND | wx.ALL)
        # Button of list video
        self.btn_list_video = wx.Button(self.panel, label='List Video')
        gbs.Add(self.btn_list_video, pos=(1, 0), flag=wx.EXPAND | wx.ALL)
        # Button of clear console
        self.btn_clear_console = wx.Button(self.panel, label='Clear Console')
        gbs.Add(self.btn_clear_console, pos=(2, 0), flag=wx.EXPAND | wx.ALL)
        # Button of upload video
        self.btn_upload_video = wx.Button(self.panel, label='Upload Video')
        gbs.Add(self.btn_upload_video, pos=(0, 1), flag=wx.EXPAND | wx.ALL)
        # Button of clear video
        self.btn_clear_video = wx.Button(self.panel, label='Clear Video')
        gbs.Add(self.btn_clear_video, pos=(1, 1), flag=wx.EXPAND | wx.ALL)
        # Button of clear first video
        self.btn_pop_video = wx.Button(self.panel, label='Pop Video')
        gbs.Add(self.btn_pop_video, pos=(2, 1), flag=wx.EXPAND | wx.ALL)
        # Button of start breath
        self.btn_start_breath = wx.Button(self.panel, label='Start Breath')
        gbs.Add(self.btn_start_breath, pos=(0, 2), flag=wx.EXPAND | wx.ALL)
        # Button of stop breath
        self.btn_stop_breath = wx.Button(self.panel, label='Stop Breath')
        gbs.Add(self.btn_stop_breath, pos=(1, 2), flag=wx.EXPAND | wx.ALL)
        # Button of start fan
        self.btn_start_fan = wx.Button(self.panel, label='Start Fan')
        gbs.Add(self.btn_start_fan, pos=(0, 3), flag=wx.EXPAND | wx.ALL)
        # Button of stop fan
        self.btn_stop_fan = wx.Button(self.panel, label='Stop Fan')
        gbs.Add(self.btn_stop_fan, pos=(1, 3), flag=wx.EXPAND | wx.ALL)
        # Button of reset device
        self.btn_reset_device = wx.Button(self.panel, label='Reset Device')
        gbs.Add(self.btn_reset_device, pos=(2, 3), flag=wx.EXPAND | wx.ALL)
        # Button of start service
        self.btn_start_service = wx.Button(self.panel, label='Start Service')
        gbs.Add(self.btn_start_service, pos=(0, 4), flag=wx.EXPAND | wx.ALL)
        # Button of stop service
        self.btn_stop_service = wx.Button(self.panel, label='Stop Service')
        gbs.Add(self.btn_stop_service, pos=(1, 4), flag=wx.EXPAND | wx.ALL)
        # Set growable column
        gbs.AddGrowableCol(4)
        ctrl_box_sizer.Add(gbs, proportion=1, flag=wx.EXPAND | wx.ALL, border=1)

        # Console
        self.console = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.VSCROLL | wx.TE_RICH)
        self.console.SetBackgroundColour(wx.BLACK)
        self.console.SetFont(wx.Font(9, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas'))

        # Create main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dev_box_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(auto_box_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(ctrl_box_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        sizer.Add(self.console, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.panel.SetSizer(sizer)


class FanControl:
    MSG_HEAD = b'\xf1\xf2\xf3'
    MSG_TAIL = b'\xf4\xf5\xf6'

    @staticmethod
    def get_checksum(b):
        return (sum(b) % 0x80).to_bytes(1, 'big')

    @staticmethod
    def wrap_message(msg):
        checksum = FanControl.get_checksum(msg)
        return FanControl.MSG_HEAD + msg + checksum + FanControl.MSG_TAIL

    @staticmethod
    def unwrap_message(msg):
        # Check message characteristics
        if len(msg) <= len(FanControl.MSG_HEAD) + len(FanControl.MSG_TAIL) + 1:
            raise Exception('message is too short')
        if msg[:3] != FanControl.MSG_HEAD:
            raise Exception('message has no standard head')
        if msg[-3:] != FanControl.MSG_TAIL:
            raise Exception('message has no standard tail')
        # Check message integrity
        data = msg[3:-4]
        checksum = msg[-4:-3]
        if FanControl.get_checksum(data) != checksum:
            raise Exception('message checksum is incorrect')
        return data

    @staticmethod
    def bounded_recv(s):
        bytes_read = b''
        while not bytes_read.endswith(FanControl.MSG_TAIL):
            bytes_read += s.recv(1)
        return bytes_read

    @staticmethod
    def simple_api(to_send, to_recv, ip_addr, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_addr, port))
            # Send request
            s.send(FanControl.wrap_message(to_send))
            # Receive response
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            if resp != to_recv:
                raise Exception('unexpected response')

    @staticmethod
    def show_version(ip_addr, port=8900):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_addr, port))
            # Send request
            s.send(FanControl.wrap_message(b'\x12\x00\x00'))
            # Receive response
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            # Check message characteristics
            if resp[0:1] != b'\x12':
                raise Exception('unexpected response')
            if resp[1] != len(resp) - 2:  # Exclude head byte and length byte
                raise Exception('incorrect response length')
            obj = json.loads(resp[2:].decode('ascii'))
            return obj

    @staticmethod
    def upload_video(server_ipaddr, server_port, web_path_to_file, local_path_to_file, ip_addr, port=8900):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_addr, port))
            # Send request
            web_path_to_file = urllib.parse.quote(web_path_to_file)
            filename = urllib.parse.quote(
                re.findall(r'([^/\\]+?)(\.[^.]*$|$)', local_path_to_file)[0][0]).encode('ascii')
            bytes_to_send = b'\x17\x00\x00\x01\x7b\x68\x74\x74\x70\x3a\x2f\x2f' + \
                            server_ipaddr.encode('ascii') + \
                            b'\x3a' + \
                            str(server_port).encode('ascii') + \
                            b'\x2f' + \
                            web_path_to_file.encode('ascii') + \
                            b'\x7d\x7b\x73\x69\x7a\x65\x3a' + \
                            os.path.getsize(local_path_to_file).to_bytes(4, 'big') + \
                            b'\x2c\x6e\x61\x6d\x65\x3a\x22' + \
                            filename + \
                            b'\x22\x2c\x74\x69\x6d\x65\x3a\x00\x00\x75\x30' \
                            b'\x22\x6c\x6f\x67\x49\x64\x22\x3a\x30\x30\x30\x2c\x22\x75\x69\x64\x22\x3a\x30\x30\x30' \
                            b'\x2c\x22\x73\x6f\x6e\x67\x22\x3a\x22' + \
                            filename + \
                            b'\x22\x7d'
            s.send(FanControl.wrap_message(bytes_to_send))
            # Receive response
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            # Check message
            if resp != b'\x17\x01\x01':
                raise Exception('unexpected response')
            # Receive progress
            while True:
                bytes_read = FanControl.bounded_recv(s)
                resp = FanControl.unwrap_message(bytes_read)
                if resp[0:1] != b'\x19':
                    raise Exception('unexpected response while reporting progress')
                if resp[1] != len(resp) - 2:
                    raise Exception('incorrect response length while reporting progress')
                perc = int(re.findall(r'"perc":"([0-9]+?)"', resp[2:].decode('ascii'))[0])
                yield perc
                if perc >= 100:
                    break

    @staticmethod
    def list_video(ip_addr, port=8900):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_addr, port))

            # Request to list all videos
            s.send(FanControl.wrap_message(b'\x00\x00\x00'))

            # Receive video list
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            # Check message head
            if resp[0:1] != b'\x00':
                raise Exception('unexpected response')
            if int.from_bytes(resp[1:3], 'big') != len(resp) - 3:
                raise Exception('incorrect response length')
            if int.from_bytes(resp[1:3], 'big') == 0:
                # No video
                return []
            return [i['name'] for i in json.loads(f"[{resp[3:].decode('ascii')}]")]

    @staticmethod
    def clear_video(ip_addr, port=8900):
        """
        Clear all videos

        :param ip_addr: IP address of target device
        :param port: port of target device
        :return: number of videos cleared by the operation (-1 means no operation)
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_addr, port))

            # Request to list all videos (S0)
            s.send(FanControl.wrap_message(b'\x00\x00\x00'))
            # Receive video list
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            # Check message head
            if resp[0:1] != b'\x00':
                raise Exception('unexpected response while listing video(s) (S0)')
            if int.from_bytes(resp[1:3], 'big') != len(resp) - 3:
                raise Exception('incorrect response length while listing video(s) (S0)')
            if int.from_bytes(resp[1:3], 'big') == 0:
                # No video to clear, skip
                return -1
            obj = json.loads(f"[{resp[3:].decode('ascii')}]")

            # Request to clear all videos (S1)
            cmd = b'\x01' + len(obj).to_bytes(1, 'big') + b'\x00\x00'
            s.send(FanControl.wrap_message(cmd))
            # Receive clearing response
            while True:
                bytes_read = FanControl.bounded_recv(s)
                resp = FanControl.unwrap_message(bytes_read)
                if resp == b'\x01\x01\x01':
                    break
                elif resp[0:1] != b'\x0d':
                    raise Exception('unexpected response while clearing video(s) (S1)')

            # Confirm, request to clear all videos again (S2)
            s.send(FanControl.wrap_message(cmd))
            # Receive clearing response
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            if resp != b'\x01\x01\x00':
                raise Exception('unexpected response while confirming by clearing video(s) again (S2)')
            return len(obj)

    @staticmethod
    def pop_video(ip_addr, port=8900):
        """
        Clear the first video (the earliest uploaded video)

        :param ip_addr: IP address of target device
        :param port: port of target device
        :return: number of videos remaining after the operation (-1 means no operation)
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_addr, port))

            # Request to list all videos (S0)
            s.send(FanControl.wrap_message(b'\x00\x00\x00'))
            # Receive video list
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            # Check message head
            if resp[0:1] != b'\x00':
                raise Exception('unexpected response while listing video(s) (S0)')
            if int.from_bytes(resp[1:3], 'big') != len(resp) - 3:
                raise Exception('incorrect response length while listing video(s) (S0)')
            if int.from_bytes(resp[1:3], 'big') == 0:
                # No video to clear, skip
                return -1
            obj = json.loads(f"[{resp[3:].decode('ascii')}]")
            prev_count = len(obj)

            # Request to clear the first video (S1)
            cmd = b'\x01\x01\x00\x00'
            s.send(FanControl.wrap_message(cmd))
            # Receive clearing response
            while True:
                bytes_read = FanControl.bounded_recv(s)
                resp = FanControl.unwrap_message(bytes_read)
                if resp == b'\x01\x01\x01':
                    break
                elif resp[0:1] != b'\x0d':
                    raise Exception('unexpected response while clearing the first video (S1)')

            # Confirm, request to list all videos again (S2)
            s.send(FanControl.wrap_message(b'\x00\x00\x00'))
            # Receive video list
            bytes_read = FanControl.bounded_recv(s)
            resp = FanControl.unwrap_message(bytes_read)
            # Check message head
            if resp[0:1] != b'\x00':
                raise Exception('unexpected response while confirming by listing video(s) again (S2)')
            if int.from_bytes(resp[1:3], 'big') != len(resp) - 3:
                raise Exception('incorrect response length while confirming by listing video(s) again (S2)')
            if int.from_bytes(resp[1:3], 'big') == 0:
                # No video
                count = 0
            else:
                obj = json.loads(f"[{resp[3:].decode('ascii')}]")
                count = len(obj)
            if prev_count - count != 1:
                raise Exception(f'incorrect number of cleared video(s), should be 1, but is {prev_count - count}')
            return count

    @staticmethod
    def start_breath(ip_addr, port=8900):
        FanControl.simple_api(b'\x0e\x01\x01', b'\x0e\x01\x01', ip_addr, port)

    @staticmethod
    def stop_breath(ip_addr, port=8900):
        FanControl.simple_api(b'\x0e\x01\x00', b'\x0e\x01\x01', ip_addr, port)

    @staticmethod
    def start_fan(ip_addr, port=8900):
        FanControl.simple_api(b'\x06\x01\x01', b'\x06\x01\x01', ip_addr, port)

    @staticmethod
    def stop_fan(ip_addr, port=8900):
        FanControl.simple_api(b'\x06\x01\x00', b'\x06\x01\x01', ip_addr, port)

    @staticmethod
    def restore_to_factory(ip_addr, port=8900):
        FanControl.simple_api(b'\x0f\x01\x00', b'\x0f\x01\x01', ip_addr, port)


def get_dev_ip_addr():
    return app_view.tc_dev_ip_addr.GetValue()


def set_dev_ip_addr(value):
    app_view.tc_dev_ip_addr.SetValue(value)


def get_watch_path():
    return app_view.tc_watch_path.GetValue()


def set_watch_path(value):
    app_view.tc_watch_path.SetValue(value)


def enable_non_service_button(value):
    app_view.tc_dev_ip_addr.Enable(value)
    app_view.btn_dev_ip_addr.Enable(value)
    app_view.tc_watch_path.Enable(value)
    app_view.btn_watch_path.Enable(value)
    app_view.btn_dev_ip_addr.Enable(value)
    app_view.btn_watch_path.Enable(value)
    app_view.btn_upload_video.Enable(value)
    app_view.btn_clear_video.Enable(value)
    app_view.btn_pop_video.Enable(value)
    app_view.btn_start_breath.Enable(value)
    app_view.btn_stop_breath.Enable(value)
    app_view.btn_reset_device.Enable(value)


def enable_service_button(value):
    app_view.btn_show_ver.Enable(value)
    app_view.btn_list_video.Enable(value)
    app_view.btn_clear_console.Enable(value)
    app_view.btn_start_fan.Enable(value)
    app_view.btn_stop_fan.Enable(value)
    app_view.btn_start_service.Enable(value)
    app_view.btn_stop_service.Enable(value)


def require_fan_lock(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        fan_lock.acquire()
        func(*args, **kwargs)
        fan_lock.release()

    return wrapper


def require_console_lock(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        console_lock.acquire()
        func(*args, **kwargs)
        console_lock.release()

    return wrapper


@require_console_lock
def write_to_console(fg, bg, message, end='\n'):
    app_view.console.SetDefaultStyle(wx.TextAttr(fg, bg))
    app_view.console.AppendText(f"{message}{end}")
    app_view.console.ShowPosition(app_view.console.GetLastPosition())


def append_if_not_exist(fg, bg, text, append_text=None):
    if append_text is None:
        append_text = text
    if not app_view.console.GetValue().endswith(text):
        write_to_console(fg, bg, append_text, end='')


def pretty_block(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        append_if_not_exist(*COLOR_GRAY, '\n\n', '\n')
        write_to_console(*COLOR_GRAY, f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] =====>")
        func(*args, **kwargs)
        write_to_console(*COLOR_GRAY, f'==============================', end='\n\n')

    return wrapper


def bind_events():
    app_view.btn_dev_ip_addr.Bind(wx.EVT_BUTTON, lambda evt: on_btn_dev_ip_addr())
    app_view.btn_watch_path.Bind(wx.EVT_BUTTON, lambda evt: on_btn_mon_path())
    app_view.btn_show_ver.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_show_ver))
    app_view.btn_list_video.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_list_video))
    app_view.btn_clear_console.Bind(wx.EVT_BUTTON, lambda evt: on_btn_clear_console())
    app_view.btn_upload_video.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_upload_video))
    app_view.btn_clear_video.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_clear_video))
    app_view.btn_pop_video.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_pop_video))
    app_view.btn_start_breath.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_start_breath))
    app_view.btn_stop_breath.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_stop_breath))
    app_view.btn_start_fan.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_start_fan))
    app_view.btn_stop_fan.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_stop_fan))
    app_view.btn_reset_device.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_reset_device))
    app_view.btn_start_service.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_start_service))
    app_view.btn_stop_service.Bind(wx.EVT_BUTTON, lambda evt: pool.submit(on_btn_stop_service))


def on_btn_dev_ip_addr():
    global dev_ip_addr
    dev_ip_addr = get_dev_ip_addr()
    write_to_console(*COLOR_WHITE, f'Set device IP to {dev_ip_addr}')


def on_btn_mon_path():
    global watch_path
    watch_path = get_watch_path()
    write_to_console(*COLOR_WHITE, f'Set monitor path to {watch_path}')


@require_fan_lock
@pretty_block
def on_btn_show_ver():
    try:
        write_to_console(*COLOR_BLUE, 'Started to fetch version info...')
        resp = FanControl.show_version(dev_ip_addr)
        write_to_console(*COLOR_WHITE, 'Version:')
        write_to_console(*COLOR_WHITE, f" - FPGA: {resp['FPGA']}")
        write_to_console(*COLOR_WHITE, f" - ARM: {resp['ARM']}")
        write_to_console(*COLOR_WHITE, f" - MCU: {resp['MCU']}")
        write_to_console(*COLOR_GREEN, 'Successfully fetched version info')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to fetch version info:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@require_fan_lock
@pretty_block
def on_btn_list_video():
    try:
        write_to_console(*COLOR_BLUE, 'Started to list videos...')
        names = FanControl.list_video(dev_ip_addr)
        if len(names) == 0:
            write_to_console(*COLOR_WHITE, 'No video to list')
        else:
            write_to_console(*COLOR_WHITE, f'Found {len(names)} videos:')
            for name in names:
                write_to_console(*COLOR_WHITE, f' - {name}')
        write_to_console(*COLOR_GREEN, 'Successfully listed videos')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to list videos:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


def on_btn_clear_console():
    app_view.console.SetValue('')


@pretty_block
def on_btn_upload_video():
    try:
        write_to_console(*COLOR_BLUE, 'Started to upload videos...')

        # Disable all buttons
        enable_non_service_button(False)
        enable_service_button(False)

        if not os.path.exists(MEDIA_DIR):
            os.mkdir(MEDIA_DIR)
            write_to_console(*COLOR_WHITE, f'Created media folder "{MEDIA_DIR}"')
        elif not os.path.isdir(MEDIA_DIR):
            raise Exception(f'"{MEDIA_DIR}" is not a folder')
        upload_count = 0
        for filename in os.listdir(MEDIA_DIR):
            full_path = os.path.join(MEDIA_DIR, filename)
            if not os.path.isfile(full_path):
                continue
            write_to_console(*COLOR_WHITE, f'[{upload_count + 1}] Uploading "{filename}"...', end='')
            perc_count = 0
            for perc in FanControl.upload_video(server_ipaddr='192.168.4.89',
                                                server_port=SERVER_PORT,
                                                web_path_to_file=f'{MEDIA_DIR}/{filename}',
                                                local_path_to_file=full_path,
                                                ip_addr=dev_ip_addr):
                if perc >= 100:
                    # Progress is completed
                    if perc_count > 0:
                        # Non-first progress is completed
                        write_to_console(*COLOR_WHITE, f'{perc}%')
                else:
                    # Progress is uncompleted
                    write_to_console(*COLOR_WHITE, f'{perc}%...', end='')
                perc_count += 1
            append_if_not_exist(*COLOR_WHITE, '\n')
            if perc_count != 1:
                write_to_console(*COLOR_WHITE, f'[{upload_count + 1}] Uploaded "{filename}"')
            else:
                write_to_console(*COLOR_WHITE, f'[{upload_count + 1}] "{filename}" already exists')
            upload_count += 1
        write_to_console(*COLOR_GREEN, f'Successfully uploaded {upload_count} videos')
        if upload_count == 0:
            write_to_console(*COLOR_YELLOW, f'Please put videos in "{MEDIA_DIR}" folder')
    except Exception as e:
        append_if_not_exist(*COLOR_WHITE, '\n')
        write_to_console(*COLOR_RED, f'Failed to upload videos:')
        write_to_console(*COLOR_RED, f' - {str(e)}')
    finally:
        # Enable all buttons
        enable_non_service_button(True)
        enable_service_button(True)


@pretty_block
def on_btn_clear_video():
    try:
        write_to_console(*COLOR_BLUE, 'Started to clear videos...')
        num_video_cleared = FanControl.clear_video(dev_ip_addr)
        if num_video_cleared == -1:
            write_to_console(*COLOR_WHITE, 'No video to clear')
        else:
            write_to_console(*COLOR_WHITE, f'Cleared {num_video_cleared} videos')
        write_to_console(*COLOR_GREEN, 'Successfully cleared videos')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to clear all videos:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@pretty_block
def on_btn_pop_video():
    try:
        write_to_console(*COLOR_BLUE, 'Started to pop videos...')
        num_video_remained = FanControl.pop_video(dev_ip_addr)
        if num_video_remained == -1:
            write_to_console(*COLOR_WHITE, 'No video to pop')
        else:
            write_to_console(*COLOR_WHITE,
                             f'Popped the first video and {num_video_remained} videos remain')
        write_to_console(*COLOR_GREEN, 'Successfully popped videos')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to pop videos:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@pretty_block
def on_btn_start_breath():
    try:
        write_to_console(*COLOR_BLUE, 'Started to enable breath...')
        FanControl.start_breath(dev_ip_addr)
        write_to_console(*COLOR_GREEN, 'Successfully enabled breath')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to enable breath:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@pretty_block
def on_btn_stop_breath():
    try:
        write_to_console(*COLOR_BLUE, 'Started to disable breath...')
        FanControl.stop_breath(dev_ip_addr)
        write_to_console(*COLOR_GREEN, 'Successfully disabled breath')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to disable breath:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@require_fan_lock
@pretty_block
def on_btn_start_fan():
    try:
        write_to_console(*COLOR_BLUE, 'Started to enable fan...')
        FanControl.start_fan(dev_ip_addr)
        write_to_console(*COLOR_GREEN, 'Successfully enabled fan')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to enable fan:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@require_fan_lock
@pretty_block
def on_btn_stop_fan():
    try:
        write_to_console(*COLOR_BLUE, 'Started to disable fan...')
        FanControl.stop_fan(dev_ip_addr)
        write_to_console(*COLOR_GREEN, 'Successfully disabled fan')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to disable fan:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


@pretty_block
def on_btn_reset_device():
    try:
        write_to_console(*COLOR_BLUE, 'Started to reset device...')
        FanControl.restore_to_factory(dev_ip_addr)
        write_to_console(*COLOR_GREEN, 'Successfully reset device')
    except Exception as e:
        write_to_console(*COLOR_RED, f'Failed to reset device:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


def on_btn_start_service():
    # Start service async
    global service_thread
    service_thread = threading.Thread(target=service_worker, args=(), daemon=True)
    service_thread.start()


def on_btn_stop_service():
    global service_status
    if not service_status:
        return
    service_status = False
    write_to_console(*COLOR_BLUE, 'Requested to stop automation service...')


def web_server_worker():
    try:
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(('0.0.0.0', SERVER_PORT), handler) as httpd:
            write_to_console(*COLOR_GREEN, f'Web server started at http://127.0.0.1:{SERVER_PORT}/')
            httpd.serve_forever()
    except Exception as e:
        write_to_console(*COLOR_RED, 'General failure in web server:')
        write_to_console(*COLOR_RED, f' - {str(e)}')


def service_worker():
    global service_status
    try:
        service_status = True
        detected_file_names = []
        detected_file_durations = []
        on_device_file_durations = []
        next_pop_time = 0

        write_to_console(*COLOR_GREEN, 'Automation service started')

        if not os.path.exists(watch_path):
            os.mkdir(watch_path)
            write_to_console(*COLOR_GREEN, f'Created watch folder "{watch_path}"')
        elif not os.path.isdir(watch_path):
            raise Exception(f'"{watch_path}" is not a folder')
        archive_path = os.path.join(watch_path, ARCHIVE_DIR)
        if not os.path.exists(archive_path):
            os.mkdir(archive_path)
            write_to_console(*COLOR_GREEN, f'Created archive folder "{archive_path}"')
        elif not os.path.isdir(archive_path):
            raise Exception(f'"{archive_path}" is not a folder')

        # Disable buttons
        enable_non_service_button(False)

        # Scan watch folder
        file_count = 0
        for filename in os.listdir(watch_path):
            full_path = os.path.join(watch_path, filename)
            if not os.path.isfile(full_path):
                continue
            file_count += 1

        if file_count == 0:
            # Clear all videos
            write_to_console(*COLOR_BLUE, 'Found 0 video in watch folder, started to clear all videos on device...')
            num_video_cleared = FanControl.clear_video(dev_ip_addr)
            write_to_console(*COLOR_GREEN, f'Successfully cleared {max(0, num_video_cleared)} videos on device')
        else:
            # Mark videos on device
            write_to_console(*COLOR_BLUE,
                             f'Found {file_count} videos in watch folder, started to reduce the number of videos on '
                             f'device to one...')
            num_videos_on_device = len(FanControl.list_video(dev_ip_addr))
            while num_videos_on_device > 1:
                num_videos_on_device = FanControl.pop_video(dev_ip_addr)
            if num_videos_on_device == 1:
                on_device_file_durations.append(-1)
            write_to_console(*COLOR_GREEN,
                             f'Reduced the number of videos on device to one')

        # Service loop
        write_to_console(*COLOR_BLUE, f'Started to watch "{watch_path}" folder...')
        while service_status:
            fan_lock.acquire()

            # Enqueue all new files
            for filename in os.listdir(watch_path):
                full_path = os.path.join(watch_path, filename)
                if not os.path.isfile(full_path) or filename in detected_file_names:
                    continue
                detected_file_names.append(filename)
                duration = int(pymediainfo.MediaInfo.parse(full_path).tracks[0].duration / 1000)
                detected_file_durations.append(duration)
                write_to_console(*COLOR_GREEN, f'Found new file "{filename}", duration {duration} seconds')

            # Dequeue and upload until no available video or device gets full
            while len(detected_file_names) > 0 and (len(on_device_file_durations) < 2):
                filename = detected_file_names.pop(0)
                duration = detected_file_durations.pop(0)
                full_path = os.path.join(watch_path, filename)
                if not os.path.exists(full_path):
                    continue
                write_to_console(*COLOR_BLUE, f'Uploading "{filename}...', end='')
                perc_count = 0
                for perc in FanControl.upload_video(server_ipaddr=SERVER_IP,
                                                    server_port=SERVER_PORT,
                                                    web_path_to_file=f'{watch_path}/{filename}',
                                                    local_path_to_file=full_path,
                                                    ip_addr=dev_ip_addr):
                    if perc >= 100:
                        # Progress is completed
                        if perc_count > 0:
                            # Non-first progress is completed
                            write_to_console(*COLOR_BLUE, f'{perc}%', end='')
                    else:
                        # Progress is uncompleted
                        write_to_console(*COLOR_BLUE, f'{perc}%...', end='')
                    perc_count += 1
                append_if_not_exist(*COLOR_BLUE, '\n')
                if perc_count == 1:
                    raise Exception(f'"{filename}" already exists on device')
                on_device_file_durations.append(duration)
                if len(on_device_file_durations) == 1:
                    next_pop_time = time.time() + duration + 10
                    write_to_console(*COLOR_GREEN, f'Uploaded "{filename}" as the first video, '
                                                   f'will pop it after {duration + 10} seconds')
                else:
                    write_to_console(*COLOR_GREEN, f'Uploaded "{filename}" as the second video, will pend to play')
                shutil.move(full_path, os.path.join(archive_path, filename))
                write_to_console(*COLOR_GREEN, f'Archived "{filename}" to "{archive_path}" folder')

            # Pop video and play the next video
            while len(on_device_file_durations) >= 2 and time.time() >= next_pop_time:
                write_to_console(*COLOR_BLUE, 'Started to pop the first video...')
                # Pop the first video
                FanControl.pop_video(dev_ip_addr)
                on_device_file_durations.pop(0)
                # Calculate next pop time
                next_pop_time = time.time() + on_device_file_durations[0]

                write_to_console(*COLOR_GREEN, f'Popped the first video and proceeded to the second video, '
                                               f'will pop it after {on_device_file_durations[0]} seconds')

            fan_lock.release()
            time.sleep(1)
    except Exception as e:
        write_to_console(*COLOR_RED, 'General failure in auto upload service:')
        write_to_console(*COLOR_RED, f' - {str(e)}')
    finally:
        if fan_lock.locked():
            fan_lock.release()
        # Enable buttons
        enable_non_service_button(True)
        write_to_console(*COLOR_GREEN, 'Stopped automation service')


if __name__ == '__main__':
    # Start GUI
    app = wx.App()
    app_view = AppView()

    # Locks
    console_lock = threading.Lock()
    fan_lock = threading.Lock()

    # Configure GUI
    dev_ip_addr = '192.168.4.1'
    watch_path = 'auto_upload'
    set_dev_ip_addr(dev_ip_addr)
    set_watch_path(watch_path)
    bind_events()
    app_view.Show()

    # Start web server async
    web_server_thread = threading.Thread(target=web_server_worker, args=(),
                                         daemon=True)
    web_server_thread.start()

    # Create network operation thread pool
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    # Create service thread
    service_status = False
    service_thread = None

    # Start GUI event loop
    app.MainLoop()

    # Kill everything
    os.kill(os.getpid(), 0)
