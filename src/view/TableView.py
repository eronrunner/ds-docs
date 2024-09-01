from typing import Optional, Sequence, Any, Union, Iterable

from tabulate import tabulate

from src.view.abstract import View


class TableView(View):

    def __init__(self, headers: Union[str, Iterable] = None, data: Optional[Iterable[Any]] = None):
        self.headers = headers
        self.data = [data] if isinstance(data, str) else data

    def render(self, fmt="rounded_grid", show_index=False):
        return tabulate(
                            tabular_data=self.data,
                            showindex=show_index,
                            headers=self.headers,
                            tablefmt=fmt,
                            numalign="center",
                            stralign="left",
                            missingval="N/A"
                        )
