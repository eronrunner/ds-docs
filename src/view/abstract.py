from abc import ABC, abstractmethod


def index_start_with_one(data):
    return tuple(i for i in range(1, len(data) + 1))


class View(ABC):

    @abstractmethod
    def render(self):
        raise NotImplementedError




