from typing import Optional, Sequence, Any, Union

from tabulate import tabulate

from src.view.abstract import View


class TableView(View):

    def __init__(self, headers: Union[str, Sequence] = None, data: Optional[Sequence[Any]] = None):
        self.data = data if not isinstance(data, Sequence) else [data]
        self.headers = headers

    def render(self, fmt="rounded_grid", show_index=False):
        return tabulate(self.data, showindex=show_index,  headers=self.headers, tablefmt=fmt)
