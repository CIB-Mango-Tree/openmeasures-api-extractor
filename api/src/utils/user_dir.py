from os import path, mkdir
from platformdirs import user_data_dir


def get_app_data_dir(name: str = "mango-tree-api-extractor") -> str:
    return path.join(user_data_dir(), name)


def initialize_user_dir_if_not_exists(dir: str) -> None:
    if path.isdir(dir):
        return

    mkdir(dir)
