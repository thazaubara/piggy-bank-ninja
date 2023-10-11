ERROR = 1
WARN = 2
HIGHLIGHT = 3
INFO = 4
DEBUG = 5

# define 8 ANSI colors.
_black = '\033[30m'
_red = '\033[31m'
_green = '\033[32m'
_yellow = '\033[33m'
_blue = '\033[34m'
_magenta = '\033[35m'
_cyan = '\033[36m'
_white = '\033[37m'
_gray = '\033[37;2m'

# define ANSI decorations
_bold = '\033[1m'
_italic = '\033[3m'
_underline = '\033[4m'
_reverse = '\033[7m'

# ANSI reset
_reset = '\033[0m'

# internal variables
_loglevel = INFO
_nocolors = False
_severity_prefix = False

# log to file
_log_to_file = False
_logfile_name = "log.txt"

def log_to_file(enabled=True, filename="log.txt", clear=False):
    global _log_to_file, _logfile_name
    _log_to_file = enabled
    _logfile_name = filename
    if clear:
        with open(filename, "w") as file:
            pass


def set_loglevel(loglevel):
    global _loglevel
    warn(f"Loglevel set to: {get_loglevel_string(loglevel)}")
    _loglevel = loglevel

def get_loglevel_string(loglevel=_loglevel):
    if loglevel == ERROR:
        return "ERROR"
    elif loglevel == WARN:
        return "WARN"
    elif loglevel == HIGHLIGHT:
        return "HIGHLIGHT"
    elif loglevel == INFO:
        return "INFO"
    elif loglevel == DEBUG:
        return "DEBUG"

def set_nocolors(nocolors):
    global _nocolors
    _nocolors = nocolors

def error(message):
    _log(message, _red + _italic, ERROR)

def warn(message):
    _log(message, _yellow + _italic, WARN)

def highlight(message):
    _log(message, _blue + _italic, HIGHLIGHT)

def green(message):
    _log(message, _green, INFO)


def log(message, severity=None):
    pass

    color = _reset

    # to support old logger style
    if severity is not None:
        oldloggerinfo = " [old logger!]"
        numspaces = 80 - len(message) - len(oldloggerinfo)
        message += numspaces * " " + oldloggerinfo
    if severity == ERROR:
        color = _red
    elif severity == WARN:
        color = _yellow
    elif severity == HIGHLIGHT:
        color = _blue
    elif severity == DEBUG:
        color = _gray + _italic
    else:
        severity = INFO

    _log(message, color, severity)


def debug(message):
    _log(message, _gray + _italic, DEBUG)

def _log(message, color, severity=INFO):
    if severity > _loglevel:
        return

    if _severity_prefix:
        if severity == ERROR:
            message = "[ERR] " + message
        elif severity == WARN:
            message = "[WRN] " + message
        elif severity == HIGHLIGHT:
            message = "[!!!] " + message
        elif severity == DEBUG:
            message = "[DBG] " + message
        else:
            message = "[   ] " + message

    if _nocolors:
        print(message)
    else:
        print(f"{color}{message}{_reset}")

    if _log_to_file:
        with open(_logfile_name, "a") as file:
            file.write(str(message) + "\n")


def greeting():
    string = """
       welcome to the mighty              ________________  _____ 
  _______   _   __ _  ___  ______ __     / __/ __/_  __/ / / / _ \\
 / __/ -_) (_) /  ' \/ _ \/ __/ // /    _\ \/ _/  / / / /_/ / ___/
/_/  \__/ (_) /_/_/_/\___/_/  \_, /    /___/___/ /_/  \____/_/    
-----------------------------/___/--------------------------------
    """
    log(string)
