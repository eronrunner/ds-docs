import datetime
import typing
from typing import Any

from src.model.meta import DataSourceInfo, TableInfo, FieldInfo, Choices, FIELD_TYPES

NOT_SET = object()


class Configurator:

    model: 'BaseModel'

    @classmethod
    def get_metadata(cls, field_name: str) -> list[Any]:
        return cls.model.model_fields[field_name].metadata

    @classmethod
    def get_choices(cls, field_name: str) -> dict[str, Any]:
        for meta in cls.get_metadata(field_name):
            if isinstance(meta, Choices):
                return meta.choices
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
        print("GET UNCONFIGURED FIELDS", list(self.__dict__.keys()))
        for field in self.__dict__:  # self.__dict__.keys()
            # typing.get_type_hints(Metadata)
            print("Field HINT", field, typing.get_type_hints(self.model))
            if self.__dict__[field] == NOT_SET:
                yield field

    def configure(self):
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

    def configure(self):
        return DataSourceInfo(
            ds_name=self.ds_name,
            ds_type=self.ds_type,
            ds_host=self.ds_host,
            ds_port=self.ds_port,
            ds_user=self.ds_user,
            ds_password=self.ds_password,
        )

    def set_ds_name(self, name: str):
        self.ds_name = name
        return self

    def set_ds_type(self, type: str):
        self.ds_type = type
        return self

    def set_ds_host(self, host: str):
        self.ds_host = host
        return self

    def set_ds_port(self, port: str):
        self.ds_port = port
        return self

    def set_ds_user(self, user: str):
        self.ds_user = user
        return self

    def set_ds_password(self, password: str):
        self.ds_password = password
        return self


class TableInfoConfigurator(Configurator):

    model = TableInfo

    def __init__(self, table_name=NOT_SET, table_fields=NOT_SET):
        self.table_name = table_name
        self.table_fields = table_fields

    def configure(self):
        return TableInfo(table_name=self.table_name, table_fields=self.table_fields)

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

    def configure(self):
        return FieldInfo(
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

    def set_field_name(self, name: str):
        self.field_name = name
        return self

    def set_field_type(self, type: str):
        self.field_type = type
        return self

    def set_field_pattern(self, pattern: str):
        self.field_pattern = pattern
        return self

    def set_field_min_length(self, min: int):
        self.field_min_length = min if min is None else int(min)
        return self

    def set_field_max_length(self, max: int):
        self.field_max_length = max if max is None else int(max)
        return self

    def set_field_alias(self, alias: str):
        self.field_alias = alias
        return self

    def set_field_factory(self, factory: str):
        self.field_factory = factory
        return self

    def set_field_gt(self, gt: float):
        self.field_gt = gt if gt is None else float(gt)
        return self

    def set_field_lt(self, lt: float):
        self.field_lt = lt if lt is None else float(lt)
        return self

    def set_field_ge(self, ge: float):
        self.field_ge = ge if ge is None else float(ge)
        return self

    def set_field_le(self, le: float):
        self.field_le = le if le is None else float(le)
        return self

    def set_field_decimal_places(self, decimal_places: int):
        self.field_decimal_places = decimal_places if decimal_places is None else int(decimal_places)
        return self

    def set_field_required(self, required: bool | str | int):
        if isinstance(required, (bool, int)):
            self.field_required = bool(required)
        elif isinstance(required, str):
            self.field_required = required.lower() == "true"
        else:
            raise ValueError(f"Invalid value for required: {required}")
        return self

    def set_field_unique(self, unique: bool):
        self.field_unique = unique
        return self

    def set_field_default_value(self, default_value):
        _type = FIELD_TYPES.get(self.field_type)
        if _type != datetime.datetime:
            print("SET FIELD DEFAULT VALUE", default_value, _type, self.field_type, type(default_value))
            default_value = _type(default_value)
        self.field_default_value = default_value
        return self
