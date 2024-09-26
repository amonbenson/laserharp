from appdirs import AppDirs

_dirs = AppDirs("laserharp")

DATA_DIR = _dirs.user_data_dir
CONFIG_DIR = _dirs.user_config_dir
CACHE_DIR = _dirs.user_cache_dir
STATE_DIR = _dirs.user_state_dir
LOG_DIR = _dirs.user_log_dir
