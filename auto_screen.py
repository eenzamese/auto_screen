"""Autoinput script for DEV environment"""
import time
import re
import sys
import os
import json
import logging
import pathlib
import hashlib
import traceback
from os import sep
from os.path import dirname
import pyautogui # pylint: disable=import-error
import win32gui # type: ignore # pylint: disable=import-error


# timeouts
SEARCH_TMT = 10
APP_TMT = 60
APP_TMT_START = 300

# check environment
if getattr(sys, 'frozen', False):
    app_path = dirname(sys.executable)
    app_name = pathlib.Path(sys.executable).stem
    APP_RUNMODE = 'PROD'
    time.sleep(APP_TMT_START)
else:
    app_path = dirname(__file__)
    app_name = pathlib.Path(__file__).stem
    APP_RUNMODE = 'PREPROD'


# logging settings
LOG_START_TIME = re.sub(r"\W+", "_", str(time.ctime()))
LOG_FMT_STRING = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILENAME = f'{app_path}{sep}{app_name}_{LOG_START_TIME}.log'
log_handlers = [logging.StreamHandler()]

if APP_RUNMODE == 'PROD':
    log_handlers.append(logging.FileHandler(LOG_FILENAME))

logger = logging.getLogger(APP_RUNMODE)
logging.basicConfig(format=LOG_FMT_STRING,
                    datefmt='%d.%m.%Y %H:%M:%S',
                    level=logging.INFO, # NOTSET/DEBUG/INFO/WARNING/ERROR/CRITICAL
                    handlers=log_handlers)


# load configuration
CONFIG_PATH = f'{app_path}{sep}auto_screen.config'
logger.info('Configurations file is %s', CONFIG_PATH)


# inputs
try:
    logger.info('Loading config file')
    with open(CONFIG_PATH, 'r', encoding="UTF-8") as file:
        file_content = file.read()
        logger.debug('Configurations content is %s', file_content)
        conf_data = json.loads(file_content)
    logger.info('Configuration file loads successfully')
except Exception as ex: # pylint: disable=broad-exception-caught
    logger.critical('Config problems with exception %s', str(ex))
    sys.exit('Config problems')
    

# load configs
WINDOW_TITLE_CONTENT = conf_data['WINDOW_TITLE_CONTENT']
print(WINDOW_TITLE_CONTENT)
WINDOW_TITLE_RGX = f".*{WINDOW_TITLE_CONTENT}.*"
INPUT = conf_data['INPUT']


# windows processing class
# thanks luc from stackoverflow (stackoverflow.com/users/117092/luc)
class WindowMgr:
    """Encapsulates some calls to the winapi for window management"""

    def __init__(self):
        """Constructor"""
        self._handle = None

    def find_window(self, class_name, window_name=None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

    def get_window_pic(self):
        """put the window in the foreground"""
        hwnd = self._handle
        x, y, x1, y1 = win32gui.GetClientRect(hwnd)
        x, y = win32gui.ClientToScreen(hwnd, (x, y))
        x1, y1 = win32gui.ClientToScreen(hwnd, (x1 - x, y1 - y))
        im = pyautogui.screenshot(region=(x, y, x1, y1))
        print(type(im))
        im_hash = hashlib.md5(im.tobytes()).hexdigest()
        print(im_hash)
        return(im_hash)

# run
w = WindowMgr()
md5pic_old = None
flag = 0
while True:
    try:
        logger.info('Searching window')
        print(WINDOW_TITLE_RGX)
        w.find_window_wildcard(WINDOW_TITLE_RGX)
        logger.info('Setting window foreground')
        w.set_foreground()
        logger.info('Saving picture')
        md5pic_new = w.get_window_pic()
        logger.info('md5pic_new %s', str(md5pic_new))
        if md5pic_new != md5pic_old:
            logger.info('Hash differ')
            logger.info('md5pic_new %s', str(md5pic_new))
            logger.info('md5pic_old %s', str(md5pic_old))
            md5pic_old = md5pic_new
            logger.info('flag on hash differ %s', flag)
            flag = 0
            logger.info('flag on hash differ set %s', flag)
        else:
            logger.info('flag on hash same %s', flag)
            flag+=1
            logger.info('flag on hash same set %s', flag)
        if flag > 3:
            os.system("shutdown /r")
        logger.info('Picture successfully saved')
        time.sleep(60)
    except Exception as ex: # pylint: disable=broad-exception-caught
        logger.warning('Window processing return exception - %s', str(ex))
        time.sleep(SEARCH_TMT)
