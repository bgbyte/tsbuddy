try:
    from tsbuddy import private_repo
    IS_PRIVATE = True
except ImportError:
    private_repo = None
    IS_PRIVATE = False

## Commented out to improve startup speed. Drawback is importing the submodules will be slower when they are first used, and more verbose syntax, but it should speed up the initial loading of tsbuddy and the menu.
# from . import aos
# from . import extracttar
# from . import hmon
# from . import log_analyzer
# #from . import tsbuddy_menu # Avoid Python script import issue 
# from . import tslog2csv
# from . import utils

# __all__ = [
#     'aos',
#     'extracttar',
#     'hmon',
#     'log_analyzer',
#     #'tsbuddy_menu',
#     'tslog2csv',
#     'utils',
# ]