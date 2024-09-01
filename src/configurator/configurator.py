import datetime
import json
import typing
from typing import Any

from pydantic_core import PydanticUndefined
from tabulate import tabulate

from src.model.meta import DataSourceInfo, TableInfo, FieldInfo, Choices, FIELD_TYPES
from src.view.TableView import TableView
from multipledispatch import dispatch

from src.view.abstract import index_start_with_one

NOT_SET = object()


RE_DATA_SOURCE_INFO = r"^.*-datasourceinfo-.*(.json)$"
RE_TABLE_INFO = r"^.*-tableinfo-.*(.json)$"

DATA_SOURCE_INFO_LABEL = "datasourceinfo"
TABLE_INFO_LABEL = "tableinfo"


def validate_boolean(value: Any) -> typing.Optional[bool]:
    if value is None or value is PydanticUndefined:
        return
    elif isinstance(value, (bool, int)):
        return bool(value)
    elif isinstance(value, str):
        return value.lower() == "true"
    else:
        raise ValueError(f"Invalid value: {value}")


class Configurator:

    model: 'BaseModel.__class__'  # type: ignore
    _obj: 'BaseModel'
    data: dict

    @classmethod
    def get_metadata(cls, field_name: str) -> list[Any]:
        return cls.model.model_fields[field_name].metadata

    @classmethod
    def get_choices(cls, field_name: str) -> dict[str, Any]:
        for meta, v in cls.model.get_extra(cls.model.model_fields[field_name]).items():
            if isinstance(v, Choices):
                return v.choices
        return {}

    @classmethod
    def get_default(cls, field_name: str) -> Any:
        field = cls.model.model_fields[field_name]
        return cls.model.get_default(field)

    @classmethod
    def get_hint(cls, field_name: str) -> str:
        if field_name not in cls.model.model_fields:
            raise ValueError(f"Field {field_name} is not exist")
        hint = cls.model.get_field_hint(cls.model.model_fields[field_name])
        hint_format = "\n"
        for _, hint_value in hint.items():
            hint_format += f"[{hint_value}]"
        hint_format += "\n"
        return hint_format

    @classmethod
    def get_types(cls, field_name: str) -> tuple:
        return cls.model.get_types(cls.model.model_fields[field_name])

    @classmethod
    def is_required(cls, field_name: str) -> bool:
        return cls.model.is_required(cls.model.model_fields[field_name])

    def get_unconfigured_fields(self):
        for field in self.__dict__:  # self.__dict__.keys()
            # typing.get_type_hints(Metadata)
            if self.__dict__[field] == NOT_SET:
                yield field

    def configure(self):
        raise NotImplementedError('Method not implemented')

    def display(self):
        raise NotImplementedError('Method not implemented')


class DatasourceInfoConfigurator(Configurator):

    model = DataSourceInfo

    def __init__(
        self,
        ds_name=NOT_SET,
        ds_type=NOT_SET,
        ds_host=NOT_SET,
        ds_port=NOT_SET,
        ds_user=NOT_SET,
        ds_password=NOT_SET
    ):
        self.ds_name = ds_name
        self.ds_type = ds_type
        self.ds_host = ds_host
        self.ds_port = ds_port
        self.ds_user = ds_user
        self.ds_password = ds_password
        self._obj = None

    @dispatch()
    def configure(self):
        self._obj = self.model(
            ds_name=self.ds_name,
            ds_type=self.ds_type,
            ds_host=self.ds_host,
            ds_port=self.ds_port,
            ds_user=self.ds_user,
            ds_password=self.ds_password,
        )
        self.data = self._obj.model_dump()
        return self._obj

    @dispatch(dict)
    def configure(self, datasource_info: dict):
        self._obj = self.model(**datasource_info)
        self.data = datasource_info
        self.ds_name = self._obj.ds_name
        self.ds_type = self._obj.ds_type
        self.ds_host = self._obj.ds_host
        self.ds_port = self._obj.ds_port
        self.ds_user = self._obj.ds_user
        self.ds_password = self._obj.ds_password
        return self._obj

    def set_ds_name(self, name: str):
        self.ds_name = name
        return self

    def set_ds_type(self, type: str):
        self.ds_type = type
        return self

    def set_ds_host(self, host: str):
        self.ds_host = host if host else None
        return self

    def set_ds_port(self, port: int):
        self.ds_port = int(port) if isinstance(port, (int, float, str)) else None
        return self

    def set_ds_user(self, user: str):
        self.ds_user = user if user else None
        return self

    def set_ds_password(self, password: str):
        self.ds_password = password if password else None
        return self

    def validate(self, json_data: dict):
        self._obj = self.model(**json_data)
        return self

    def show_table(self, fmt="rounded_grid", show_index=False) -> str:
        """
        Table view of the DataSourceInfo object
        :return: String only, so want to show it, use a function to print it
        """
        if self._obj:
            print(self.data)
            view = TableView("keys", data=[self.data])
            return view.render(fmt=fmt, show_index=show_index)

    def __str__(self):
        print(self.ds_host if self.ds_host is not None else "None", type(self.ds_host))
        return f"DatasourceInfoConfigurator(ds_name={self.ds_name}, ds_type={self.ds_type}, ds_host={str(self.ds_host)}, ds_port={self.ds_port}, ds_user={self.ds_user}, ds_password={self.ds_password})"


class TableInfoConfigurator(Configurator):

    model = TableInfo

    def __init__(self, table_name=NOT_SET, table_fields=NOT_SET):
        self.table_name = table_name
        self.table_fields = table_fields

    @dispatch()
    def configure(self) -> 'BaseModel':
        self._obj = self.model(table_name=self.table_name, table_fields=self.table_fields)
        self.data = self._obj.model_dump()
        return self._obj

    @dispatch(dict)
    def configure(self, table_info: dict) -> 'BaseModel':
        self._obj = self.model(**table_info)
        self.data = table_info
        self.table_name = self._obj.table_name
        self.table_fields = self._obj.table_fields
        return self._obj

    def set_table_name(self, name: str):
        self.table_name = name
        return self

    def set_table_fields(self, fields: [FieldInfo]):
        self.table_fields = fields
        return self

    def add_table_field(self, field: FieldInfo):
        if self.table_fields:
            self.table_fields.append(field)
        else:
            self.table_fields = [field]
        return self

    def validate(self, json_data: dict):
        self.model(**json_data)
        return self

    def show_table(self, fmt="rounded_grid", show_index=False, show_details=True) -> str:
        """
        Table view of the TableInfo object
        :return: String only, so want to show it, use a function to print it
        """
        if self._obj:
            view = TableView([*self.data.keys()], data=[[self.table_name, "|".join(map(lambda x: x.field_name, self._obj.table_fields))]])
            table_view = view.render(fmt=fmt, show_index=False)
            if (fields_data := self.data.get("table_fields")) and show_details:
                field_view = TableView("keys", fields_data)
                table_view += f"\n{field_view.render(fmt=fmt, show_index=index_start_with_one(field_view.data) if show_index else False)}"
            return table_view


class FieldInfoConfigurator(Configurator):

    model = FieldInfo

    def __init__(
        self,
        field_name=NOT_SET,
        field_type=NOT_SET,
        field_pattern=NOT_SET,
        field_min_length=NOT_SET,
        field_max_length=NOT_SET,
        field_alias=NOT_SET,
        field_factory=NOT_SET,
        field_gt=NOT_SET,
        field_lt=NOT_SET,
        field_ge=NOT_SET,
        field_le=NOT_SET,
        field_decimal_places=NOT_SET,
        field_required=NOT_SET,
        field_unique=NOT_SET,
        field_default_value=NOT_SET,
    ):
        self.field_name = field_name
        self.field_type = field_type
        self.field_pattern = field_pattern
        self.field_min_length = field_min_length
        self.field_max_length = field_max_length
        self.field_alias = field_alias
        self.field_factory = field_factory
        self.field_gt = field_gt
        self.field_lt = field_lt
        self.field_ge = field_ge
        self.field_le = field_le
        self.field_decimal_places = field_decimal_places
        self.field_required = field_required
        self.field_unique = field_unique
        self.field_default_value = field_default_value

    @dispatch()
    def configure(self):
        self._obj = self.model(
            field_name=self.field_name,
            field_type=self.field_type,
            field_pattern=self.field_pattern,
            field_min_length=self.field_min_length,
            field_max_length=self.field_max_length,
            field_alias=self.field_alias,
            field_factory=self.field_factory,
            field_gt=self.field_gt,
            field_lt=self.field_lt,
            field_ge=self.field_ge,
            field_le=self.field_le,
            field_decimal_places=self.field_decimal_places,
            field_required=self.field_required,
            field_unique=self.field_unique,
            field_default_value=self.field_default_value,
        )
        self.data = self._obj.model_dump()
        return self._obj

    @dispatch(dict)
    def configure(self, field_info: dict):
        self._obj = self.model(**field_info)
        self.data = field_info
        self.field_name = self._obj.field_name
        self.field_type = self._obj.field_type
        self.field_pattern = self._obj.field_pattern
        self.field_min_length = self._obj.field_min_length
        self.field_max_length = self._obj.field_max_length
        self.field_alias = self._obj.field_alias
        self.field_factory = self._obj.field_factory
        self.field_gt = self._obj.field_gt
        self.field_lt = self._obj.field_lt
        self.field_ge = self._obj.field_ge
        self.field_le = self._obj.field_le
        self.field_decimal_places = self._obj.field_decimal_places
        self.field_required = self._obj.field_required
        self.field_unique = self._obj.field_unique
        self.field_default_value = self._obj.field_default_value
        return self._obj

    def set_field_name(self, name: str):
        self.field_name = name
        return self

    def set_field_type(self, type: str):
        self.field_type = type
        return self

    def set_field_pattern(self, pattern: str):
        self.field_pattern = pattern if pattern else None
        return self

    def set_field_min_length(self, min: int):
        self.field_min_length = int(min) if isinstance(min, (int, float, str)) else None
        return self

    def set_field_max_length(self, max: int):
        self.field_max_length = int(max) if isinstance(max, (int, float, str)) else None
        return self

    def set_field_alias(self, alias: str):
        self.field_alias = alias if alias else None
        return self

    def set_field_factory(self, factory: str):
        self.field_factory = factory if factory else None
        return self

    def set_field_gt(self, gt: float):
        self.field_gt = float(gt) if isinstance(gt, (int, float, str)) else None
        return self

    def set_field_lt(self, lt: float):
        self.field_lt = int(lt) if isinstance(lt, (int, float, str)) else None
        return self

    def set_field_ge(self, ge: float):
        self.field_ge = int(ge) if isinstance(ge, (int, float, str)) else None
        return self

    def set_field_le(self, le: float):
        self.field_le = int(le) if isinstance(le, (int, float, str)) else None
        return self

    def set_field_decimal_places(self, decimal_places: int):
        self.field_decimal_places = int(decimal_places) if isinstance(decimal_places, (int, float, str)) else None
        return self

    def set_field_required(self, required: bool | str | int):
        self.field_required = validate_boolean(required)
        return self

    def set_field_unique(self, unique: bool):
        self.field_unique = validate_boolean(unique)
        return self

    def set_field_default_value(self, default_value):
        _type = FIELD_TYPES.get(self.field_type)
        if default_value and _type != datetime.datetime:
            default_value = _type(default_value)
        self.field_default_value = default_value
        return self

    def show_table(self, fmt="rounded_grid", show_index=False) -> str:
        """
        Table view of the FieldInfo object
        :return: String only, so want to show it, use a function to print it
        """
        if self._obj:
            view = TableView("keys", data=self.data)
            return view.render(fmt=fmt, show_index=show_index)
