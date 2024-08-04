import collections
import datetime
import json
import re
import uuid
from typing import Sequence, Any, Optional

from annotated_types import BaseMetadata, SLOTS, MinLen, MaxLen
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass
from pydantic_core import PydanticUndefined
from pydantic_core.core_schema import ValidationInfo

FIELD_TYPES = {
    "integer": int,
    "float": float,
    "text": str,
    "datetime": datetime.datetime,
    "boolean": bool,
    "json": dict,
    "list": list,
    "uuid": uuid.UUID,
}

DEFAULT_TYPE = "text"

FIELD_FACTORIES = {
    "auto": "auto",
    "manual": "manual"
}

DEFAULT_FACTORY = "manual"


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


@dataclass(frozen=True, **SLOTS)
class Choices(BaseMetadata):
    """
    List of choices for a field. The field value must be one of the choices.
    """

    choices: dict[str, Any]


def _attach_choices(field_info: 'FieldInfo', choices: Sequence[Choices]):
    if not field_info.metadata:
        field_info.metadata = [Choices(choices)]
    else:
        field_info.metadata.append(Choices(choices))
    return field_info


class FieldDetailHelper:

    @classmethod
    def get_field_hint(cls, field: 'FieldInfo') -> collections.OrderedDict[str, str]:
        generic_meta_cls = "<class 'pydantic._internal._fields._general_metadata_cls.<locals>._PydanticGeneralMetadata'>"
        hint = collections.OrderedDict({"required": "Required" if field.json_schema_extra.get("required") else "Optional"})
        hint["default"] = f"Default value: {cls.get_default(field)}"
        for info in field.metadata:
            if isinstance(info, MinLen):
                hint["min_length"] = f"Min length: {info.min_length}"
            elif isinstance(info, MaxLen):
                hint["max_length"] = f"Max length: {info.max_length}"
            elif str(type(info)) == generic_meta_cls and hasattr(info, "pattern"):
                hint["pattern"] = f"Pattern: {info.pattern}"
            elif isinstance(info, Choices):
                hint["choices"] = "Choices: " + ", ".join(list(info.choices.keys()))
        return hint

    @classmethod
    def get_default(cls, field: 'FieldInfo') -> Any:
        if field.default is not PydanticUndefined:
            return field.default
        return None

    @classmethod
    def get_types(cls, field: 'FieldInfo') -> tuple:
        annotated = field.annotation
        if hasattr(annotated, "__args__"):
            return annotated.__args__
        else:
            return (annotated, )


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


class FieldInfo(BaseModel, FieldDetailHelper):

    field_name: str = Field(required=True, min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    field_type: str = _attach_choices(Field(required=True, min_length=1, max_length=16, default=DEFAULT_TYPE),
                                      dict([(k, k) for k, _ in FIELD_TYPES.items()]))
    field_pattern: Optional[str] = Field(required=False, default=None)
    field_min_length: Optional[int] = Field(required=False)
    field_max_length: Optional[int] = Field(required=False)
    field_alias: Optional[str] = Field(required=False, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    field_factory: Optional[str] = _attach_choices(Field(required=False, default=FIELD_FACTORIES[DEFAULT_FACTORY]), FIELD_FACTORIES)
    field_gt: Optional[float] = Field(required=False, description="Greater than, applicable for numeric fields")
    field_lt: Optional[float] = Field(required=False, description="Less than, applicable for numeric fields")
    field_ge: Optional[float] = Field(required=False, description="Greater than or equal to, applicable for numeric fields")
    field_le: Optional[float] = Field(required=False, description="Less than or equal to, applicable for numeric fields")
    field_decimal_places: Optional[int] = Field(required=False, ge=0, le=10, default=2)
    field_required: Optional[bool] = Field(required=False, default=False)
    field_unique: Optional[bool] = Field(required=False, default=False)
    field_default_value: Any = Field(required=False)

    @field_validator("field_default_value")
    def value(cls, value, info: ValidationInfo) -> Optional[Any]:
        data = info.data
        if "field_type" not in data:
            raise ValueError("Field type is required")
        if not isinstance(value, FIELD_TYPES[data["field_type"]]):
            raise ValueError(f"Field Value {value} should be of type {str(FIELD_TYPES[data['field_type']])}")
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
            if "field_min_length" in data and len(value) < data["field_min_length"]:
                raise ValueError(f"Field value {value} should be greater than {data['field_min_length']}")
            if "field_max_length" in data and len(value) > data["field_max_length"]:
                raise ValueError(f"Field value {value} should be less than {data['field_max_length']}")
            if "field_pattern" in data and not re.match(data["field_pattern"], value):
                raise ValueError(f"Field value {value} should match pattern {data['field_pattern']}")
        elif _t in (int, float):
            cls._check_number(value, data)
        elif _t == bool:
            if not isinstance(value, bool):
                raise ValueError(f"Field value {value} should be a boolean")
        elif _t == uuid.UUID:
            try:
                uuid.UUID(value, version=4)
            except ValueError:
                raise ValueError(f"Field value {value} should be a valid UUID")
        elif _t == datetime.datetime:
            if isinstance(value, int):
                try:
                    datetime.datetime.utcfromtimestamp(value / 1000)
                except ValueError:
                    raise ValueError(f"Field value {value} should be a valid utc timestamp in milliseconds")

            cls._check_number(value, data)

        else:
            raise ValueError(f"Field type {_t} is not supported")

        return value

    @classmethod
    def _check_number(cls, value, data):
        (low, low_expr), (high, high_expr) = cls._range_number(data)
        if high is not None and low is not None and not eval(f"{value}{low_expr} or {value}{high_expr}"):
            raise ValueError(f"Field value {value} should be between {low_expr} and {high_expr}")
        elif high and low is None and not eval(f"{value}{high_expr}"):
            raise ValueError(f"Field value {value} should be {high_expr}")
        elif high is None and low and not eval(f"{value}{low_expr}"):
            raise ValueError(f"Field value {value} should be {low_expr}")

    @classmethod
    def _range_number(cls, data):
        ge = data.get("field_ge")
        gt = data.get("field_gt")
        if ge is not None and gt is not None:
            if ge <= gt:
                high = ge
                high_eq = True
            else:
                high = gt
                high_eq = False
        else:
            if ge:
                high = ge
                high_eq = True
            else:
                high = gt
                high_eq = False
        le = data.get("field_le")
        lt = data.get("field_lt")
        if le is not None and lt is not None:
            if le >= lt:
                low = le
                low_eq = True
            else:
                low = lt
                low_eq = False
        else:
            if le:
                low = le
                low_eq = True
            else:
                low = lt
                low_eq = False

        if high:
            if high_eq:
                high_expr = f"<={high}"
            else:
                high_expr = f"<{high}"
        else:
            high_expr = None
        if low:
            if low_eq:
                low_expr = f">={low}"
            else:
                low_expr = f">{low}"
        else:
            low_expr = None

        return (low, low_expr), (high, high_expr)

    @field_validator("field_type")
    def type(cls, value) -> str:
        if value not in FIELD_TYPES:
            raise ValueError(f"Field type {value} is not supported")
        return value

    @field_validator("field_factory")
    def factory(cls, value) -> str:
        if value is None:
            value = FieldInfo.model_fields["field_factory"].default
        elif value not in FIELD_FACTORIES:
            raise ValueError(f"Field factory {value} is not supported")
        return value

    def __str__(self):
        return f"FieldInfo(field_name={self.field_name}, field_type={self.field_type})"

print("FIELDSSS", FieldInfo.model_fields)

class TableInfo(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    table_name: str = Field(pattern="^[a-zA-Z][a-zA-Z0-9_]*$", min_length=1, max_length=64)
    table_fields: Optional[Sequence[FieldInfo]] = None

    def __str__(self):
        return f"TableInfo(table_name={self.table_name}, table_columns={self.table_fields})"


DATA_SOURCE_TYPES = {
    "mysql": "mysql",
    "mssql": "mssql",
    "sqlite": "sqlite",
    "postgresql": "postgresql",
    "oracle": "oracle",
}


class DataSourceInfo(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    ds_name: str = Field(min_length=2, max_length=32, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    ds_type: str = _attach_choices(Field(min_length=1, max_length=32), DATA_SOURCE_TYPES)
    ds_host: str = Field(min_length=1, max_length=512)
    ds_port: int = Field(field_type="int", min_length=0, max_length=65535)
    ds_user: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
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
