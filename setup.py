"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['MenuBarGmail.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
    },
    'iconfile': 'MenuBarGmail.icns',
    'resources': [
        'MenuBarGmailMenuBarIcon.png',
        'MenuBarGmailMenuBarIconForDark.png',
        'cacerts.txt'],
    'packages': ['rumps']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
