#!/usr/bin/env python
# coding=utf-8

# <bitbar.title>Screenshot</bitbar.title>
# <bitbar.version>v2.0</bitbar.version>
# <bitbar.author>Jean-Francois Parent</bitbar.author>
# <bitbar.abouturl>https://github.com/jf-parent/bitbar-screenshot-to-gdrive</bitbar.abouturl>
# <bitbar.desc>Allows for screenshots to be uploaded to gdrive, saved, and added to the clipboard</bitbar.desc>
# <bitbar.dependencies>python</bitbar.dependencies>

"""
Modified from:
# <bitbar.author>Brandon Barker</bitbar.author>
# <bitbar.author.github>ProjectBarks</bitbar.author.github>
# <bitbar.abouturl>https://github.com/matryer/bitbar-plugins/blob/master/System/screenshot.1d.py</bitbar.abouturl>
"""

import os, subprocess, tempfile, hashlib, requests, sys, platform, time
from distutils.version import StrictVersion
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
# from IPython import embed

HERE = os.path.abspath(os.path.dirname(__file__))
SAVE_PATH = "~/Desktop"


def screenshot(path, copy_to_clipboard=False, show_cursor=False, show_errors=False, interactive=False,
               only_main_monitor=False, window_mode=False, open_in_preview=False, selection_mode=True,
               sounds=True, delay=5):
    params = ""
    if copy_to_clipboard:
        params += "-c "
    if show_cursor:
        params += "-C "
    if show_errors:
        params += "-d "
    if interactive:
        params += "-i "
    if only_main_monitor:
        params += "-m "
    if window_mode:
        params += "-o "
    if open_in_preview:
        params += "-P "
    if selection_mode:
        params += "-s "
    if sounds:
        params += "-x "
    if delay != 5 and delay >= 0:
        params += "-T {} ".format(delay)

    os.system("screencapture {} {}".format(params, path))
    return os.path.isfile(path)


def text_to_clipboard(output):
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode('utf-8'))


def notify(title, subtitle, message):
    command = "display notification \"{}\" with title \"{}\"".format(message, title)
    if len(subtitle) > 0:
        command += " subtitle \"{}\"".format(subtitle)
    os.system("osascript -e '{}'".format(command))


def upload_image(screenshot_path):
    gauth = GoogleAuth()

    # gauth.LocalWebserverAuth()
    HERE = os.path.abspath(os.path.dirname(__file__))
    credential_file_path = os.path.join(HERE, 'credentials.json')
    # credential_file_path = os.path.join(HERE, '..', 'credentials.json')
    gauth.LoadCredentialsFile(credential_file_path)

    drive = GoogleDrive(gauth)

    gfile = drive.CreateFile({
            'title': screenshot_path,
            'parents': [{"id": "0B55JGc_LEyB8QVhRcW1rMVdOa3M"}]
    })
    gfile.SetContentFile(screenshot_path);
    gfile.Upload()
    gfile.InsertPermission({
		'type': 'anyone',
		'value': 'anyone',
		'role': 'reader'
    })

    os.remove(screenshot_path)

    return gfile['alternateLink']


class Command(object):
    def __init__(self, title, name):
        self.title = title
        self.name = name

    def get_name(self):
        return self.name

    def get_description(self):
        return "{0} |bash={2} param1={1} terminal=false".format(self.title, self.name, os.path.realpath(__file__))

    def execute(self):
        raise Exception("Abstract Function")


class Upload(Command):
    def __init__(self):
        super(Upload, self).__init__("Upload Online", "upload")

    def execute(self):
        temp_path = tempfile.NamedTemporaryFile().name + ".png"
        if not screenshot(temp_path):
            exit()
        notify("Uploading Screenshot", "", "Your image is being uploaded online!")
        url = upload_image(temp_path)
        notify("Copied Screenshot", "", "Image URL copied to clipboard!")
        text_to_clipboard(url)


class Clipboard(Command):
    def __init__(self):
        super(Clipboard, self).__init__("Copy to Clipboard", "clipboard")

    def execute(self):
        temp_path = tempfile.NamedTemporaryFile().name + ".png"
        if not screenshot(temp_path):
            exit()
        os.system("osascript -e 'set the clipboard to POSIX file \"{}\"'".format(temp_path))
        notify("Copied Screenshot", "", "Image copied to clipboard!")


class SaveFile(Command):
    def __init__(self):
        super(SaveFile, self).__init__("Save to File", "save")

    def execute(self):
        temp_path = os.path.join(os.path.expanduser(SAVE_PATH), time.strftime("screenshot-%Y%m%d-%H%M%S.png"))
        parent = os.path.dirname(temp_path)
        if not os.path.isdir(parent):
            os.mkdir(parent)
        if not screenshot(temp_path):
            exit()
        os.system("open -R {0}".format(temp_path))


version = platform.mac_ver()[0]
if StrictVersion(version) < StrictVersion("10.9"):
    raise Exception("Mac OSX is too old!")

sub_commands = [Upload(), Clipboard(), SaveFile()]

if len(sys.argv) <= 1:
    print("📸")
    print("---")
    for sub_command in sub_commands:
        print(sub_command.get_description())
else:
    try:
        for sub_command in sub_commands:
            if sub_command.get_name() != sys.argv[1]:
                continue
            sub_command.execute()
    except Exception, e:
        notify("Error", "", str(e))
