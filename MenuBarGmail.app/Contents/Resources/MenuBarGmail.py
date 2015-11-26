#!/usr/bin/env python
"""
Gmail notification in Menu bar.

requirement: rumps (https://github.com/jaredks/rumps),
             httplib2, oauth2client, google-api-python-client
Worked with python 2.7
"""

import os
import sys
import re
import argparse
import base64
import dateutil.parser
import webbrowser
import urllib
import httplib2
import BaseHTTPServer
import rumps
from email.mime.text import MIMEText
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser
from oauth2client.client import OAuth2WebServerFlow
from apiclient.discovery import build
from apiclient import errors

__prog__ = os.path.basename(__file__)
__description__ = __doc__
__author__ = 'rcmdnk'
__copyright__ = 'Copyright (c) 2015 rcmdnk'
__credits__ = ['rcmdnk']
__license__ = 'MIT'
__version__ = 'v0.0.9'
__date__ = '23/Nov/2015'
__maintainer__ = 'rcmdnk'
__email__ = 'rcmdnk@gmail.com'
__status__ = 'Prototype'

DEBUG = True
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
    def __init__(self, autostart=True):
        # Set default values
        self.debug_mode = DEBUG
        rumps.debug_mode(self.debug_mode)
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
            'Check now',
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
        self.message_contents = {}
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
        self.get_messages_timer = rumps.Timer(self.get_messages_wrapper,
                                              int(self.settings['interval'])
                                              if 'interval' in self.settings
                                              else 60)
        if autostart:
            self.start()

    @rumps.clicked('About')
    def about(self, sender):
        rumps.alert(title='%s' % __prog__,
                    message='Gmail notification in Menu bar.\n'
                    + 'Version %s\n' % __version__
                    + '%s' % __copyright__)

    @rumps.clicked('Account')
    def account(self, sender):
        self.open_gmail()

    @rumps.clicked('Check now')
    def check_now(self, sender):
        self.get_messages()

    @rumps.clicked('Reconnect')
    def recoonect(self, sender):
        self.build_service(True)
        self.restart()

    @rumps.clicked('Set checking interval')
    def set_interval(self, sender):
        # Need to stop timer job, otherwise interval can not be changed.
        self.stop()
        response = rumps.Window('Set checking interval (s)',
                                default_text=str(
                                    self.get_messages_timer.interval),
                                dimensions=(100, 20)).run()
        if response.clicked:
            self.get_messages_timer.interval = int(response.text)
            self.settings['interval'] = response.text
            self.write_settings()

        self.start()

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

            self.restart()

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

            self.restart()

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
        ret = rumps.alert('Do you want to uninstall MenuBarGmail?',
                          ok='OK', cancel='Cancel')
        if ret == 1:
            self.remove_me()

    def get_messages_wrapper(self, sender):
        self.get_messages()

    def get_messages(self, commandline=False):
        try:
            # Set labels
            is_inbox_only = True
            labels = []
            if 'labels' in self.settings and self.settings['labels'] != '':
                for l in self.settings['labels'].split(','):
                    labels.append(l.strip())
                    if l != 'INBOX':
                        is_inbox_only = False
            elif 'filter' not in self.settings\
                    or self.settings['filter'].strip() == '':
                labels.append('INBOX')

            if not is_inbox_only:
                # Get labelIds
                label_name_id = {x['name'].upper().replace('/', '-'): x['id']
                                 for x in self.get_service().users()
                                 .labels().list(userId='me')
                                 .execute()['labels']}
            else:
                label_name_id = {'INBOX': 'INBOX', 'None': None}
            labels = [x for x in labels
                      if x.replace('/', '-') in label_name_id]
            if len(labels) == 0:
                labels.append('None')

            # Get message ids
            query = 'label:unread ' + (self.settings['filter']
                                       if 'filter' in self.settings else '')
            ids = {}
            is_new = False
            for l in labels:
                response = self.get_service().users().messages().list(
                    userId='me', labelIds=label_name_id[l.replace('/', '-')],
                    q=query).execute()
                ids[l] = []
                if 'messages' in response:
                    ids[l].extend([x['id'] for x in response['messages']])

                while 'nextPageToken' in response:
                    page_token = response['nextPageToken']
                    response = self.get_service().users().messages().list(
                        userId='me',
                        labelIds=label_name_id[l.replace('/', '-')],
                        q=query, pageToken=page_token).execute()
                    ids[l].extend([x['id'] for x in response['messages']])

                if l not in self.messages:
                    self.messages[l] = []
                if ids[l] != self.messages[l]:
                    is_new = True

                # Remove read messages' id
                self.messages[l] = ids[l]

            removed = [x for x in self.messages if x not in labels]
            if len(removed) > 0:
                is_new = True
                for l in removed:
                    del self.messages[l]

            # No change
            if not is_new:
                # No new message
                return

            # Check total number of messages
            # Remove duplication in different labels
            all_ids = []
            for l in labels:
                all_ids += ids[l]
            all_ids = list(set(all_ids))

            self.message_contents = {
                k: v for k, v in self.message_contents.items()
                if k in all_ids}

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
            for i in all_ids:
                if i in self.message_contents\
                        and 'Subject' in self.message_contents[i]:
                    continue
                is_new = True if i not in self.message_contents\
                    else False
                self.message_contents[i] = {}
                if n_get >= self.mails_max_get:
                    continue
                n_get += 1
                message = self.get_service().users().messages().get(
                    userId='me', id=i).execute()

                for k in ['labelIds', 'snippet', 'threadId']:
                    self.message_contents[i][k] = message[k]

                for x in message['payload']['headers']:
                    if x['name'] == 'Subject':
                        self.message_contents[i]['Subject'] = x['value']
                    elif x['name'] == 'Date':
                        self.message_contents[i]['Date'] =\
                            x['value'].split(', ')[1].split(' +')[0]
                    elif x['name'] == 'From':
                        self.message_contents[i]['FromName'] =\
                            self.get_address_name(x['value'])
                        self.message_contents[i]['From'] = x['value']
                    elif x['name'] in ['Subject', 'To', 'Cc', 'Bcc',
                                       'In-Reply-To', 'References']:
                        self.message_contents[i][x['name']] = x['value']

                for k in ['To', 'Cc']:
                    if k not in self.message_contents[i]:
                        self.message_contents[i][k] = ''

                body = None
                if 'parts' in message['payload']:
                    for p in message['payload']['parts']:
                        if 'body' in p and 'data' in p['body']:
                            body = p['body']['data']
                            break
                    if body is None and 'body' in message['payload']\
                            and 'data' in message['payload']['body']:
                        body = message['payload']['body']['data']
                    if body is not None:
                        self.message_contents[i]['body']\
                            = base64.urlsafe_b64decode(body.encode('UTF-8'))
                if body is None:
                    self.message_contents[i]['body'] = message['snippet']

                # Popup notification
                if is_new and not self.is_first\
                        and self.menu['Mail notification'].state:
                    rumps.notification(
                        title='Mail from %s' %
                        self.message_contents[i]['FromName'],
                        subtitle=self.message_contents[i]['Subject'],
                        message=self.message_contents[i]['snippet'])

            self.is_first = False

            # Get contents
            if um_menu._menu is not None:
                um_menu.clear()
            for l in labels:
                threadIds = []
                if len(labels) > 1:
                    # Set each labels' menu
                    um_menu.add(rumps.MenuItem(
                        l,
                        callback=lambda x, y=l: self.open_gmail(y)))
                    um_menu[l].title = '%s: %d' % (l, len(ids[l]))
                for i in sorted([i for i in self.messages[l]
                                 if 'Subject' in self.message_contents[i]],
                                key=lambda x: dateutil.parser.parse(
                                    self.message_contents[x]['Date'])
                                .isoformat(),
                                reverse=True):
                    v = self.message_contents[i]
                    if v['threadId'] in threadIds:
                        continue
                    threadIds.append(v['threadId'])
                    title = '%s %s | %s' % (v['Date'], v['FromName'],
                                            v['Subject'])
                    title = title[0:80]
                    if len(labels) > 1:
                        m = um_menu[l]
                    else:
                        m = um_menu
                    if len(m) < self.mails_max_show:
                        m.add(
                            rumps.MenuItem(
                                l+str(i),
                                callback=lambda x, y=l, z=i:
                                self.show_mail(y, z)))
                        m[l+str(i)].title = title
                        m[l+str(i)].add(rumps.MenuItem(
                            l+str(i)+'snippet',
                            callback=lambda x, y=l, z=i: self.show_mail(y, z)))
                        m[l+str(i)][l+str(i)+'snippet'].title = v['snippet']

            if commandline or self.debug_mode:
                print ''
                print 'labels: %s' % (self.settings['labels']
                                      if 'labels' in self.settings else '')
                print 'filter: %s' % (self.settings['filter']
                                      if 'filter' in self.settings else '')
                print 'Total number of unread messages: %d\n' % len(all_ids)
                for l in labels:
                    if len(labels) > 1:
                        print '%d messages for %s' % (len(ids[l]), l)
                        for i in um_menu[l].values():
                            print '%s\n' % i.title
                    else:
                        for i in um_menu.values():
                            print '%s\n' % i.title

        except errors.HttpError, error:
            print '[ERROR] %s: %s' % (sys._getframe().f_code.co_name, error)
        except:
            print '[ERROR] %s: %s' % (sys._getframe().f_code.co_name,
                                      sys.exc_info()[0])

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
                scope=['https://www.googleapis.com/auth/gmail.modify']),
            storage, argparser.parse_args([]))

    def open_gmail(self, label=''):
        url = 'https://mail.google.com'
        if label != '':
            url += '/mail/u/0/#label/' + urllib.quote(label.encode('utf-8'))
        webbrowser.open(url)

    def show_mail(self, label, msg_id):
        # rumps.alert(title='From %s\n%s' % (sender, date),
        #             message=subject + '\n\n' + message)
        v = self.message_contents[msg_id]
        w = rumps.Window(message=v['Subject']+'\n\n'+v['snippet'],
                         title="From %s\n%s" % (v['From'], v['Date']),
                         dimensions=(0, 0),
                         ok="Cancel",
                         cancel="Open in browser")
        w.add_button("Mark as read")
        w.add_button("Reply")
        response = w.run()
        if response.clicked == 0:
            self.open_gmail(label)
        elif response.clicked == 2:
            self.mark_as_read(msg_id)
        elif response.clicked == 3:
            self.reply(msg_id)

    def get_exe(self):
        exe = os.path.abspath(__file__)
        if exe.find('Contents/Resources/') != -1:
            name, ext = os.path.splitext(exe)
            if ext == '.py':
                exe = name
            exe = exe.replace('Resources', 'MacOS')
        return exe

    def get_app(self):
        exe = self.get_exe()
        if exe.find('Contents/MacOS/') == -1:
            # Not in app
            return ''
        else:
            return os.path.dirname(exe).replace('/Contents/MacOS', '')

    def reset(self):
        if os.path.exists(self.plist_file):
            os.system('launchctl unload %s' % self.plist_file)
            os.remove(self.plist_file)
        os.system('rm -f %s %s' % (self.authentication_file,
                                   self.setting_file))
        os.system('rm -rf "%s/%s"' %
                  (os.environ['HOME'],
                   '/Library/Application Support/MenuBarGmail'))

    def remove_me(self):
        self.reset()
        app = self.get_app()
        if app != "":
            os.system('rm -rf "%s"' % app)
        else:
            print '%s is not in App' % self.get_exe()

    def start(self):
        self.get_messages_timer.start()

    def stop(self):
        if self.get_messages_timer.is_alive():
            self.get_messages_timer.stop()

    def restart(self):
        self.stop()
        self.start()

    def get_service(self):
        if self.service is None:
            self.service = self.build_service()
        return self.service

    def remove_labels(self, msg_id, labels):
        if type(labels) == str:
            labels = [labels]
        msg_labels = {"addLabelIds": [], "removeLabelIds": labels}
        try:
            self.get_service().users().messages().modify(
                userId='me', id=msg_id,
                body=msg_labels).execute()
        except errors.HttpError, error:
            print '[ERROR] %s: %s' % (sys._getframe().f_code.co_name, error)
        except:
            print '[ERROR] %s: %s' % (sys._getframe().f_code.co_name,
                                      sys.exc_info()[0])

    def mark_as_read(self, msg_id):
        self.remove_labels(msg_id, 'UNREAD')
        self.get_messages()

    def get_address_name(self, address):
            return re.sub(r' *<.*> *', '', address)

    def get_address(self, address):
        try:
            return re.search(r'(?<=<).*(?=>)', address).group()
        except:
            return address

    def reply(self, msg_id):
        v = self.message_contents[msg_id]
        to = self.get_address(v['From'])
        cc_tmp = []
        cc_tmp += v['To'].split(',') if v['To'] != '' else []
        cc_tmp += v['Cc'].split(',') if v['Cc'] != '' else []
        cc = []
        for a in cc_tmp:
            if a.lower() not in [to.lower(), self.address.lower()]:
                cc.append(self.get_address(a))

        body = ''
        for l in v['body'].split('\n'):
            body += '> ' + l + '\n'

        w = rumps.Window('To: %s\n' % to
                         + 'Cc: %s\n' % ','.join(cc)
                         + 'From: %s\n' % self.address,
                         default_text=body,
                         dimensions=(500, 500),
                         ok="Cancel",
                         cancel="Send")
        w.add_button('Save')
        response = w.run()
        if response.clicked == 1:
            pass
        elif response.clicked in [0, 2]:
            message = MIMEText(response.text)
            message['to'] = to
            message['cc'] = ''.join(cc)
            message['from'] = self.address
            message['subject'] = 'Re: ' + v['Subject']
            m = {'raw': base64.urlsafe_b64encode(message.as_string())}

            try:
                if response.clicked == 1:
                    self.service.users().messages().send(userId='me',
                                                         body=m).execute()

                elif response.clicked == 2:
                    self.service.users().drafts()\
                        .create(userId='me', body={'message': m}).execute()
            except errors.HttpError, error:
                print '[ERROR] %s: %s' % (sys._getframe().f_code.co_name,
                                          error)
            except:
                print '[ERROR] %s: %s' % (sys._getframe().f_code.co_name,
                                          sys.exc_info()[0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=__prog__,
        formatter_class=argparse.RawTextHelpFormatter,
        description=__description__)
    parser.add_argument('-u', '--uninstall', action='store_true',
                        dest='uninstall',
                        default=False, help='Uninstall %s' % __prog__)
    parser.add_argument('-r', '--reset', action='store_true', dest='reset',
                        default=False, help='Reset settings')
    parser.add_argument('-c', '--commandline', action='store_true',
                        dest='commandline',
                        default=False, help='Check mails once in command line')
    args = parser.parse_args()
    app = MenuBarGmail(not (args.uninstall or args.reset or args.commandline))
    if args.uninstall:
        app.remove_me()
    elif args.reset:
        app.reset()
    elif args.commandline:
        app.get_messages(True)
    else:
        app.run()
