from os import listdir
from os.path import isfile, join


def ls_all_files_in_directory(directory: str) -> [str]:
    for f in listdir(directory):
        if isfile(join(directory, f)):
            yield directory, f


def ls_all_directories_in_directory(directory: str) -> [str]:
    for f in listdir(directory):
        if not isfile(join(directory, f)):
            yield directory, f


def is_file(file: str) -> bool:
    return isfile(file)


def is_directory(directory: str) -> bool:
    return not isfile(directory)
