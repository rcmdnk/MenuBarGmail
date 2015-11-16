# MenuBarGmail

Gmail notification in Menu Bar for Mac.

Unread messages of Gmail are checked and the number of unread messages
is shown in the menu bar.

Default setting checks only Inbox.
Multi-label can be set to be checked.

Short information of unread messages are shown in the menu.

New message notification is also available, too.

# Installation

With [Homebrew Cask](http://caskroom.io/), do:

    $ brew cask install rcmdnk/MenuBarGmail/menubargmail

Or download the app and install it in **/Applications** or **~/Applications**.

# Uninstall

Launch MenuBarGmail, and click **Uninstall** menu from menu bar icon.

This function will remove

* $HOME/.menubargmail_oauth
* $HOME/.menubargmail_settings
* $HOME/Library/LaunchAgents/menubargmail.plist
* $HOME/Library/Application Support/MenuBarGmail/

# Usage

When you start MenuBarGmail,
an authentication page will be open in a browser.
**Accept** it, then a following icon will appear in the menubar.

![MenuBarGmailMenuBarIcon.png](MenuBarGmailMenuBarIcon.png)

Following menus are available:

* About: Show information of MenuBarGmail.
* Account: Current account. Gmail page will be open by clicking this.
* Reconnect: Renew account authentication.
* Unread messages: Number and details of unread messages.
* Set checking interval: Set interval to check mails (Default is 60 sec).
* Set labels: Set labels (comma-separated) to be checked (Default is `Inbox`).
* Mail notification: Toggle if a notification is shown or not when the new message comes.
* Start at login: Toggle if starting at login or not.
* Uninstall: Uninstall MenuBarGmail.
* Quit: Quit MenuBarGmail.

# How to build

* Requirements
    * [rumps](https://github.com/jaredks/rumps)
    * [httplib2](https://github.com/jcgregorio/httplib2)
    * [oauth2client](https://github.com/google/oauth2client)
    * [google-api-python-client](https://github.com/google/google-api-python-client)
    * [py2app](https://pypi.python.org/pypi/py2app/)


    $ pip install rumps httplib2 oauth2client google-api-python-client py2app

In OS X 10.11 El Capitan, you may need to install pyobjc packages.

    $ pip install pyobjc-core pyobjc-framework-Accounts pyobjc-framework-AddressBook pyobjc-framework-AppleScriptKit pyobjc-framework-AppleScriptObjC pyobjc-framework-Automator pyobjc-framework-CFNetwork pyobjc-framework-CalendarStore pyobjc-framework-Cocoa pyobjc-framework-Collaboration pyobjc-framework-CoreData pyobjc-framework-CoreLocation pyobjc-framework-CoreText pyobjc-framework-CoreWLAN pyobjc-framework-DictionaryServices pyobjc-framework-DiskArbitration pyobjc-framework-EventKit pyobjc-framework-ExceptionHandling pyobjc-framework-FSEvents pyobjc-framework-InputMethodKit pyobjc-framework-InstallerPlugins pyobjc-framework-InstantMessage pyobjc-framework-LatentSemanticMapping pyobjc-framework-LaunchServices pyobjc-framework-OpenDirectory pyobjc-framework-PreferencePanes pyobjc-framework-PubSub pyobjc-framework-QTKit pyobjc-framework-Quartz pyobjc-framework-ScreenSaver pyobjc-framework-ScriptingBridge pyobjc-framework-SearchKit pyobjc-framework-ServiceManagement pyobjc-framework-Social pyobjc-framework-StoreKit pyobjc-framework-SyncServices pyobjc-framework-SystemConfiguration pyobjc-framework-WebKit

* Build

    $ python setup.py py2app

then, **MenuBarGmail.app** will appear in **./dist** directory.
