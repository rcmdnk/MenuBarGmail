# MenuBarGmail
Gmail notification in Menu Bar for Mac

# Installation

With [Homebrew Cask](http://caskroom.io/), do:

    $ brew cask install rcmdnk/MenuBarGmail/menubargmail

Or download the app and install it in **/Applications** or **~/Applications**.

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
