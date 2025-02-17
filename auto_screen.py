"""Autoinput script for DEV environment"""
import time
import re
import sys
import json
import logging
import pathlib
import traceback
from os import sep
from os.path import dirname
import pyautogui # pylint: disable=import-error
import win32gui # type: ignore # pylint: disable=import-error


# timeouts
SEARCH_TMT = 3
APP_TMT = 60


# check environment
if getattr(sys, 'frozen', False):
    app_path = dirname(sys.executable)
    app_name = pathlib.Path(sys.executable).stem
    APP_RUNMODE = 'PROD'
    time.sleep(APP_TMT)
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
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bot - top
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        print(result)
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        
        if result == 1:
            #PrintWindow Succeeded
            im.save("test.png")
# run
w = WindowMgr()
while True:
    try:
        logger.info('Searching window')
        w.find_window_wildcard(WINDOW_TITLE_RGX)
        logger.info('Setting window foreground')
        w.set_foreground()
        time.sleep(SEARCH_TMT)
        logger.info('Save picture')
        w.get_window_pic()
        logger.info('Picture successfully saved')
        time.sleep(60)
    except Exception as ex: # pylint: disable=broad-exception-caught
        logger.warning('Window processing return exception - %s', str(ex))
        time.sleep(SEARCH_TMT)
