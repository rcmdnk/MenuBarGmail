#!/usr/bin/env python
"""
menubargmail: Gmail notification in Menu bar,

requirement: rumps (https://github.com/jaredks/rumps),
             httplib2, oauth2client, google-api-python-client
"""

__prog__ = "MenuBarGmail"
__author__ = "rcmdnk"
__copyright__ = "Copyright (c) 2015 rcmdnk"
__credits__ = ["rcmdnk"]
__license__ = "MIT"
__version__ = "v0.0.5"
__date__ = "16/Nov/2015"
__maintainer__ = "rcmdnk"
__email__ = "rcmdnk@gmail.com"
__status__ = "Prototype"

import os
import sys
import re
import httplib2
import webbrowser
import urllib
import BaseHTTPServer
import rumps
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser
from oauth2client.client import OAuth2WebServerFlow
from apiclient.discovery import build
from apiclient import errors


DEBUG = False
MAILS_MAX_GET = 10
MAILS_MAX_SHOW = 10
AUTHENTICATION_FILE = os.environ['HOME'] + '/.menubargmail_oauth'
SETTING_FILE = os.environ['HOME'] + '/.menubargmail_settings'
PLIST_FILE = os.environ['HOME'] + '/Library/LaunchAgents/menubargmail.plist'
GOOGLE_CLIENT_ID = '401979756927-453hrgvmgjik9tqqq744s6pg7762hfel'\
    '.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'sso7NdujDxkT92bxK2u-RPGi'
MENU_BAR_ICON = 'MenuBarGmailMenuBarIcon.png'


class MenuBarGmail(rumps.App):
    def __init__(self):
        # Set default values
        rumps.debug_mode(DEBUG)
        self.mails_max_get = MAILS_MAX_GET
        self.mails_max_show = MAILS_MAX_SHOW
        self.authentication_file = AUTHENTICATION_FILE
        self.setting_file = SETTING_FILE
        self.plist_file = PLIST_FILE
        self.google_client_id = GOOGLE_CLIENT_ID
        self.google_client_secret = GOOGLE_CLIENT_SECRET
        self.menu_bar_icon = MENU_BAR_ICON

        # Read settings
        self.settings = {}
        self.read_settings()

        # Application setup
        super(MenuBarGmail, self).__init__(type(self).__name__, title=None,
                                           icon=self.menu_bar_icon)
        self.menu = [
            'About',
            None,
            'Account',
            'Reconnect',
            'Unread messages',
            'Set checking interval',
            'Set labels',
            'Set filter',
            'Mail notification',
            'Start at login',
            None,
            'Uninstall',
            None,
        ]

        # Other class variables
        self.address = ''
        self.address = ''
        self.messages = {}
        self.service = None
        self.is_first = True

        if 'notification' in self.settings\
                and self.settings['notification'] == '1':
            self.menu['Mail notification'].state = True
        else:
            self.menu['Mail notification'].state = False
        if 'startatlogin' in self.settings\
                and self.settings['startatlogin'] == '1':
            self.menu['Start at login'].state = True
        else:
            self.menu['Start at login'].state = False

        # Set and start get_messages
        self.get_messages_timer = rumps.Timer(self.get_messages,
                                              int(self.settings['interval'])
                                              if 'interval' in self.settings
                                              else 60)
        self.get_messages_timer.start()

    @rumps.clicked('About')
    def about(self, sender):
        rumps.alert(title="%s" % __prog__,
                    message="Gmail notification in Menu bar.\n"
                    + "Version %s\n" % __version__
                    + "%s" % __copyright__)

    @rumps.clicked('Account')
    def account(self, sender):
        self.open_gmail()

    @rumps.clicked('Reconnect')
    def recoonect(self, sender):
        self.build_service(True)
        if self.get_messages_timer.is_alive():
            self.get_messages_timer.stop()
        self.get_messages_timer.start()

    @rumps.clicked('Set checking interval')
    def set_interval(self, sender):
        # Need to stop timer job, otherwise interval can not be changed.
        if self.get_messages_timer.is_alive():
            self.get_messages_timer.stop()
        response = rumps.Window('Set checking interval (s)',
                                default_text=str(
                                    self.get_messages_timer.interval),
                                dimensions=(100, 20)).run()
        if response.clicked:
            self.get_messages_timer.interval = int(response.text)
            self.settings['interval'] = response.text
            self.write_settings()

        self.get_messages_timer.start()

    @rumps.clicked('Set labels')
    def set_labels(self, sender):
        response = rumps.Window('Set labels (comma-separeted list).\n'
                                'If "labels" is empty and filter is not set,'
                                ' INBOX is checked.',
                                default_text=self.settings['labels']
                                if 'labels' in self.settings else '',
                                dimensions=(400, 20)).run()
        if response.clicked:
            self.settings['labels'] = response.text.upper()
            self.write_settings()

            if self.get_messages_timer.is_alive():
                self.get_messages_timer.stop()
            self.get_messages_timer.start()

    @rumps.clicked('Set filter')
    def set_filter(self, sender):
        response = rumps.Window('Set filter.\n'
                                'e.g. "newer_than:1w"'
                                ' for mails within a week\n'
                                'ref:'
                                'https://support.google.com/mail/answer/7190',
                                default_text=self.settings['filter']
                                if 'filter' in self.settings else '',
                                dimensions=(400, 20)).run()
        if response.clicked:
            self.settings['filter'] = response.text.upper()
            self.write_settings()

            if self.get_messages_timer.is_alive():
                self.get_messages_timer.stop()
            self.get_messages_timer.start()

    @rumps.clicked('Mail notification')
    def mail_notification(self, sender):
        sender.state = not sender.state
        self.settings['notification'] = str(sender.state)
        self.write_settings()

    @rumps.clicked('Start at login')
    def set_startup(self, sender):
        sender.state = not sender.state
        if sender.state == 0:
            if os.path.exists(self.plist_file):
                os.system('launchctl unload %s' % self.plist_file)
                os.remove(self.plist_file)
        else:
            plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"'''\
''' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>Label</key>
        <string>menubargmail</string>
        <key>ProgramArguments</key>
        <array>
            <string>''' + self.get_exe() + '''</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
</dict>
</plist>'''
            with open(self.plist_file, 'w') as f:
                f.write(plist)

        self.settings['startatlogin'] = str(sender.state)
        self.write_settings()

    @rumps.clicked('Uninstall')
    def uninstall(self, sender):
        ret = rumps.alert("Do you want to uninstall MenuBarGmail?",
                          ok="OK", cancel="Cancel")
        if ret == 1:
            if os.path.exists(self.plist_file):
                os.system('launchctl unload %s' % self.plist_file)
                os.remove(self.plist_file)
            os.system('rm -f %s %s' % (self.authentication_file,
                                       self.setting_file))
            os.system('rm -rf "%s/%s"' %
                      (os.environ['HOME'],
                       '/Library/Application Support/MenuBarGmail'))
            app = self.get_app()
            if app != "":
                os.system('rm -rf "%s"' % app)
            else:
                print "%s is not in App" % self.get_exe()
            rumps.quit_application()

    def get_messages(self, sender):
        try:
            # Get service
            if self.service is None:
                self.service = self.build_service()

            # Set labels
            is_inbox_only = True
            labels = []
            if 'labels' in self.settings and self.settings['labels'] != '':
                for l in self.settings['labels'].split(','):
                    labels.append(l.strip())
                    if l != "INBOX":
                        is_inbox_only = False
            elif 'filter' not in self.settings\
                    or self.settings['filter'].strip() == '':
                labels.append("INBOX")

            if not is_inbox_only:
                # Get labelIds
                label_name_id = {x['name'].upper().replace('/', '-'): x['id']
                                 for x in self.service.users()
                                 .labels().list(userId='me')
                                 .execute()['labels']}
            else:
                label_name_id = {'INBOX': 'INBOX', 'None': None}
            labels = [x for x in labels
                      if x.replace('/', '-') in label_name_id]
            if len(labels) == 0:
                labels.append("None")

            # Get message ids
            query = 'label:unread ' + (self.settings['filter']
                                       if 'filter' in self.settings else '')
            ids = {}
            is_new = False
            for l in labels:
                response = self.service.users().messages().list(
                    userId='me', labelIds=label_name_id[l.replace('/', '-')],
                    q=query).execute()
                ids[l] = []
                if 'messages' in response:
                    ids[l].extend([x['id'] for x in response['messages']])

                while 'nextPageToken' in response:
                    page_token = response['nextPageToken']
                    response = self.service.users().messages().list(
                        userId='me',
                        labelIds=label_name_id[l.replace('/', '-')],
                        q=query, pageToken=page_token).execute()
                    ids[l].extend([x['id'] for x in response['messages']])

                if l not in self.messages:
                    self.messages[l] = {}
                if ids[l] != self.messages[l].keys():
                    is_new = True

                # Remove read messages' id
                self.messages[l] = {k: v for k, v
                                    in self.messages[l].items()
                                    if k in ids[l]}

            removed = [x for x in self.messages.keys() if x not in labels]
            if len(removed) > 0:
                is_new = True
                for l in removed:
                    del self.messages[l]

            if not is_new:
                # No new message
                return

            # Check total number of messages
            # Remove duplication in different labels
            all_ids = []
            for l in labels:
                all_ids += ids[l]
            all_ids = list(set(all_ids))

            # Set menu's title
            um_menu = self.menu['Unread messages']
            um_menu.title = 'Unread messages: %d' % len(all_ids)

            # Set menubar icon's title
            if len(all_ids) == 0:
                self.title = ''
            else:
                self.title = '%d' % len(all_ids)
            # Reset menu bar icon after title is put,
            # to adjust the width.
            self.icon = self.menu_bar_icon

            # Get message contents
            n_get = 0
            for l in labels:
                for i in ids[l]:
                    if i not in self.messages[l].keys()\
                            or 'Subject' not in self.messages[l][i]:
                        is_new = True if i not in self.messages[l].keys()\
                            else False
                        self.messages[l][i] = {}
                        if n_get >= self.mails_max_get:
                            continue
                        n_get += 1
                        message = self.service.users().messages().get(
                            userId='me', id=i).execute()
                        for x in message['payload']['headers']:
                            if x['name'] == 'Subject':
                                self.messages[l][i]['Subject'] = x['value']
                            elif x['name'] == 'Date':
                                self.messages[l][i]['Date'] =\
                                    x['value'].split(" +")[0]
                            elif x['name'] == 'From':
                                self.messages[l][i]['From'] = x['value']
                            if 'Subject' in self.messages[l][i]\
                                    and 'Date' in self.messages[l][i]\
                                    and 'From' in self.messages[l][i]:
                                break
                        self.messages[l][i]['labelIds'] = message['labelIds']
                        self.messages[l][i]['snippet'] = message['snippet']

                        # Popup notification
                        if is_new and not self.is_first\
                                and self.menu['Mail notification'].state:
                            rumps.notification(
                                title='Mail from %s' %
                                self.messages[l][i]['From'],
                                subtitle=self.messages[l][i]['Subject'],
                                message=self.messages[l][i]['snippet'])

            self.is_first = False

            # Get contents
            if um_menu._menu is not None:
                um_menu.clear()
            for l in labels:
                if len(labels) > 1:
                    # Set each labels' menu
                    um_menu.add(l)
                    um_menu[l].title = '%s: %d' % (l, len(ids[l]))
                for v in sorted([x for x in self.messages[l].values()
                                 if 'Subject' in x],
                                key=lambda x: x['Date']):
                    if len(labels) > 1:
                        if len(um_menu[l]) < self.mails_max_show:
                            um_menu[l].add(
                                rumps.MenuItem(
                                    '%s %s\n%s:  %s' % (
                                        v['Date'], v['From'], v['Subject'],
                                        v['snippet']),
                                    callback=lambda x: self.open_gmail(l)))

                    else:
                        if len(um_menu) < self.mails_max_show:
                            um_menu.add(rumps.MenuItem(
                                '%s %s\n%s:  %s' % (
                                    v['Date'], v['From'], v['Subject'],
                                    v['snippet']),
                                callback=lambda x: self.open_gmail(l)))

        except errors.HttpError, error:
            print 'An error occurred: %s' % error
        except:
            print 'Unexpected error:', sys.exc_info()[0]

    def read_settings(self):
        if not os.path.exists(self.setting_file):
            return
        with open(self.setting_file, 'r') as f:
            for line in f:
                l = re.sub(r' *#.*', '', line).strip()
                if l == '':
                    continue
                l = l.split('=')
                if len(l) < 2:
                    continue
                if l[0] == 'labels':
                    self.settings[l[0]] = l[1].upper()
                else:
                    self.settings[l[0]] = l[1]

    def write_settings(self):
        with open(self.setting_file, 'w') as f:
            for (k, v) in self.settings.items():
                f.write('%s=%s\n' % (k, v))

    def build_service(self, rebuild=False):
        storage = Storage(os.path.expanduser(self.authentication_file))
        credentials = storage.get()

        if rebuild or credentials is None or credentials.invalid:
            credentials = self.authentication(storage)

        http = httplib2.Http()
        http = credentials.authorize(http)

        service = build('gmail', 'v1', http=http)

        prof = service.users().getProfile(userId='me').execute()
        self.address = prof['emailAddress']
        self.menu['Account'].title = 'Account: %s' % self.address

        return service

    def authentication(self, storage):
        return run_flow(
            OAuth2WebServerFlow(
                client_id=self.google_client_id,
                client_secret=self.google_client_secret,
                scope=['https://www.googleapis.com/auth/gmail.readonly']),
            storage, argparser.parse_args([]))

    def open_gmail(self, label=''):
        url = 'https://mail.google.com'
        if label != '':
            url += '/mail/u/0/#label/' + urllib.quote(label.encode('utf-8'))
        webbrowser.open(url)

    def get_exe(self):
        exe = os.path.abspath(__file__)
        if exe.find('Contents/Resources/') != -1:
            name, ext = os.path.splitext(exe)
            if ext == ".py":
                exe = name
            exe = exe.replace("Resources", "MacOS")
        return exe

    def get_app(self):
        exe = self.get_exe()
        if exe.find('Contents/MacOS/') == -1:
            # Not in app
            return ""
        else:
            return os.path.dirname(exe).replace("/Contents/MacOS", "")


if __name__ == '__main__':
    MenuBarGmail().run()
