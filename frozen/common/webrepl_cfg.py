try:
    from secrets import WEBREPL_PASS as PASS
except ImportError:
    PASS = 'CHANGEME'     # WebREPL: 4 a 9 caracteres
