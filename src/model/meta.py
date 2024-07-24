import datetime
import json
import re
import uuid
from typing import Sequence, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import ValidationError
from pydantic_core.core_schema import ValidationInfo


class ForeignKeyInfo(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    field_name: str
    fk_table_name: str
    fk_field_name: str
    fk_relate_name: str = Field(required=False)

    def __init__(self, field_name: str, fk_table_name: str, fk_field_name: str, fk_relate_name: str = None):
        super(BaseModel).__init__()
        self.field_name = field_name
        self.fk_table_name = fk_table_name
        self.fk_field_name = fk_field_name
        self.fk_relate_name = fk_relate_name

    def __str__(self):
        return f"ForeignKeyInfo(field_name={self.field_name}, fk_table_name={self.fk_table_name}, fk_field_name={self.fk_field_name})"


FIELD_TYPES = {
    "int": int,
    "integer": int,
    "float": float,
    "double": float,
    "str": str,
    "text": str,
    "date": datetime.date,
    "datetime": datetime.datetime,
    "bool": bool,
    "boolean": bool,
    "json": dict,
    "list": list,
    "array": list,
    "uuid": uuid.UUID,
}

FIELD_FACTORIES = ("auto", "manual")


def _attach_choices(field_info, value):
    setattr(field_info, "choices", value)
    return field_info


def auto_field_factory(field_type: str):
    if field_type in ("int", "integer"):
        return 0
    if field_type in ("float", "double"):
        return 0.0
    if field_type in ("str", "text"):
        return ""
    if field_type in ("bool", "boolean"):
        return False
    if field_type in ("date", "datetime"):
        return datetime.datetime.now()
    if field_type in ("uuid",):
        return str(uuid.uuid4())
    return None


class FieldInfo(BaseModel):

    field_name: str = Field(required=True, min_length=1, max_length=32, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    field_type: str = _attach_choices(Field(required=True, min_length=1, max_length=16), list(FIELD_TYPES.keys()))
    field_pattern: str = Field(required=False, default=None)
    field_min: int = Field(required=False)
    field_max: int = Field(required=False)
    field_alias: str = Field(required=False, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    field_factory: str = _attach_choices(Field(required=False, default="manual"), FIELD_FACTORIES)
    field_gt: float = Field(required=False, description="Greater than, applicable for numeric fields")
    field_lt: float = Field(required=False, description="Less than, applicable for numeric fields")
    field_ge: float = Field(required=False, description="Greater than or equal to, applicable for numeric fields")
    field_le: float = Field(required=False, description="Less than or equal to, applicable for numeric fields")
    field_decimal_places: int = Field(required=False, default=2)
    field_required: bool = Field(required=False, default=False)
    field_unique: bool = Field(required=False, default=False)
    field_default_value: Any = Field(required=False)

    @field_validator("field_default_value")
    def value(self, value, info: ValidationInfo) -> Optional[Any]:
        data = info.data
        if not data["field_type"]:
            raise ValueError("Field type is required")
        if not isinstance(value, FIELD_TYPES[data["field_type"]]):
            raise ValueError(f"Field Value {value} should be of type {FIELD_TYPES[data['field_type']]}")
        _t = FIELD_TYPES[data["field_type"]]

        if value is None:
            if data["field_factory"] == "auto":
                value = auto_field_factory(data["field_type"])
                if not isinstance(value, _t):
                    raise ValueError(f"Field Value {value} should be of type {_t}")
            else:
                if data["field_required"]:
                    raise ValueError(f"Field Value cannot be Null")
        elif _t == str:
            if data["field_min"] and len(value) < data["field_min"]:
                raise ValueError(f"Field value {value} should be greater than {data['field_min']}")
            if data["field_max"] and len(value) > data["field_max"]:
                raise ValueError(f"Field value {value} should be less than {data['field_max']}")
            if data["field_pattern"] and not re.match(data["field_pattern"], value):
                raise ValueError(f"Field value {value} should match pattern {data['field_pattern']}")
        elif _t in (int, float):
            if data["field_min"] and value < data["field_min"]:
                raise ValueError(f"Field value {value} should be greater than {data['field_min']}")
            if data["field_max"] and value > data["field_max"]:
                raise ValueError(f"Field value {value} should be less than {data['field_max']}")
            if data["field_gt"] and value <= data["field_gt"]:
                raise ValueError(f"Field value {value} should be greater than {data['field_gt']}")
            if data["field_lt"] and value >= data["field_lt"]:
                raise ValueError(f"Field value {value} should be less than {data['field_lt']}")
            if data["field_ge"] and value < data["field_ge"]:
                raise ValueError(f"Field value {value} should be greater than or equal to {data['field_ge']}")
            if data["field_le"] and value > data["field_le"]:
                raise ValueError(f"Field value {value} should be less than or equal to {data['field_le']}")
        elif _t == bool:
            if not isinstance(value, bool):
                raise ValueError(f"Field value {value} should be a boolean")
        elif _t == uuid.UUID:
            try:
                uuid.UUID(value, version=4)
            except ValueError:
                raise ValueError(f"Field value {value} should be a valid UUID")
        elif _t == datetime.datetime:
            if data["field_min"] and value < data["field_min"]:
                raise ValueError(f"Field value {value} should be greater than {data['field_min']}")
            if data["field_max"] and value > data["field_max"]:
                raise ValueError(f"Field value {value} should be less than {data['field_max']}")
        elif _t == datetime.date:
            if data["field_min"] and value < data["field_min"]:
                raise ValueError(f"Field value {value} should be greater than {data['field_min']}")
            if data["field_max"] and value > data["field_max"]:
                raise ValueError(f"Field value {value} should be less than {data['field_max']}")
        else:
            raise ValueError(f"Field type {_t} is not supported")

        return value

    @field_validator("field_type")
    def type(self, value) -> str:
        if value not in FIELD_TYPES:
            raise ValueError(f"Field type {value} is not supported")
        return value

    @field_validator("field_factory")
    def factory(self, value) -> str:
        if value is None:
            value = FieldInfo.field_factory.default
        elif value not in FIELD_FACTORIES:
            raise ValueError(f"Field factory {value} is not supported")
        return value

    def __str__(self):
        return f"FieldInfo(field_name={self.field_name}, field_type={self.field_type})"


class TableInfo(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    table_name: str
    table_fields: Optional[Sequence[FieldInfo]] = None

    def __str__(self):
        return f"TableInfo(table_name={self.table_name}, table_columns={self.table_fields})"


class DataSourceInfo(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    ds_name: str = Field(min_length=2, max_length=32)
    ds_type: str = Field(min_length=1, max_length=32)
    ds_host: str = Field(min_length=1, max_length=255)
    ds_port: int = Field(field_type="int", field_min=0, field_max=65535)
    ds_user: str = Field(min_length=1, max_length=64)
    ds_password: str = Field(min_length=1, max_length=512)

    def __str__(self):
        return f"DataSourceInfo(ds_name={self.ds_name}, ds_type={self.ds_type}, ds_host={self.ds_host}, ds_port={self.ds_port}, ds_user={self.ds_user}, ds_password={self.ds_password})"


class DatasourceDocs(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    ds_info: DataSourceInfo
    tables: dict[str, TableInfo]

    def __init__(self, datasource: DataSourceInfo):
        super().__init__()
        self.ds_info: DataSourceInfo = datasource
        self.tables: dict[str, TableInfo] = {}

    def __str__(self):
        return (
            f"DatasourceDocs(database_info={self.ds_info}, db_engine={self.db_engine})"
        )

    def add_table(self, table: TableInfo):
        self.tables[table.table_name] = table

    def add_field(self, table_name: str, field: FieldInfo):
        if table_name in self.tables:
            self.tables[table_name].table_fields.append(field)
        else:
            self.tables[table_name] = TableInfo(table_name, [field])


class DataSourceConfiguration:
    def __init__(self, docs: DatasourceDocs, db_engine=None):
        self.ds_docs: DatasourceDocs = docs
        self.db_engine = db_engine

    def __str__(self):
        return f"DataSourceConfiguration(database_info={self.ds_docs})"


def json_schema(to_path: str = "./schema"):
    schema_sources = (
        DataSourceInfo.model_json_schema(),
        FieldInfo.model_json_schema(),
        TableInfo.model_json_schema(),
        DatasourceDocs.model_json_schema(),
    )
    for schema in schema_sources:
        with open(to_path + f"/{schema['title']}.json", "w+") as f:
            f.write(json.dumps(schema, indent=2))

