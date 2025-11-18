from os import path, mkdir
from platformdirs import user_data_dir


def get_app_data_dir(name: str = "mango-tree-api-extractor-backend") -> str:
    return path.join(user_data_dir(), name)


def initialize_user_dir_if_not_exists(dir: str) -> None:
    print(f"checking for dir: {dir}")
    if path.isdir(dir):
        return

    mkdir(dir)


initialize_user_dir_if_not_exists(get_app_data_dir())
