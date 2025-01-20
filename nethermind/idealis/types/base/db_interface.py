from typing import Any, Callable, Sequence


class DataclassDBInterface:
    def db_tuple(
        self,
        json_encoder: Callable[[Any], Any] | None = None,
        json_fields: set[str] | None = None,
        custom_parser: dict[str, Callable] | None = None,
    ) -> tuple:
        """
        Convert the dataclass to a tuple for insertion into the database.  Values are ordered indentically to the
        definition order of the dataclass members.  If json_fields is provided, the fields in the set will be converted
        to Jsonb objects.

        :param json_encoder: {callable to encode json fields into DB}
        :param json_fields: {fields to wrap as Jsonb}
        :param custom_parser: {field_name: callable}
        :return: (Any, ...)
        """

        if json_fields and json_encoder is None:
            raise ValueError("Json Encoder param required for json dataclass fields")

        return_cols = []
        for field_name, field_type in self.__annotations__.items():  # type: ignore  # pylint: disable=unused-variable
            encode_field = getattr(self, field_name)

            if custom_parser and field_name in custom_parser:
                encode_field = custom_parser[field_name](encode_field)

            if json_fields and field_name in json_fields:
                return_cols.append(json_encoder(encode_field))  # type: ignore
            else:
                return_cols.append(encode_field)

        return tuple(return_cols)

    @classmethod
    def from_db_row(
        cls,
        row: Sequence[Any],
        json_fields: set[str] | None = None,
        json_decoder: Callable[[Any], Any] | None = None,
        custom_parser: dict[str, Callable] | None = None,
        convert_bytes: bool = False,
    ):
        """
        Convert a SELECT * result into a python Dataclass

        :param row:  Row from SELECT * query
        :param json_fields:  Set of fields to parse as JSON
        :param json_decoder:  JSON Decoder to use for parsing JSON fields
        :param custom_parser:  Custom parser for fields.  Maps field_name -> parse_function
        :param convert_bytes:  Convert bytearrays & memoryviews to immutable bytes

        >>> import json
        >>> from decimal import Decimal
        >>> from dataclasses import dataclass
        >>> from nethermind.idealis.types.base import DataclassDBInterface
        >>> @dataclass
        ... class TestClass(DataclassDBInterface):
        ...     field1: int
        ...     field2: dict[str, str]
        ...     field3: list[str]
        ...     field4: list[bytes]
        ...
        >>> TestClass.from_db_row(
        ...     (Decimal(12345), '{"a": 12, "b": 22}', '0x1234,0x5678', [bytearray(b'1234')]),
        ...     json_fields={'field2'},
        ...     json_decoder=json.loads,
        ...     custom_parser={
        ...         'field1': lambda b: int(b),
        ...         'field3': lambda b: b.split(',')
        ...     },
        ...     convert_bytes=True
        ... )
        TestClass(field1=12345, field2={'a': 12, 'b': 22}, field3=['0x1234', '0x5678'], field4=[b'1234'])

        """

        def _convert_bytes(value: Any) -> Any:
            if isinstance(value, (bytearray, memoryview)):
                return bytes(value)
            if isinstance(value, list):
                return [_convert_bytes(v) for v in value]
            if isinstance(value, dict):
                return {_convert_bytes(k): _convert_bytes(v) for k, v in value.items()}
            if isinstance(value, tuple):
                return tuple(_convert_bytes(v) for v in value)
            if isinstance(value, set):
                return {_convert_bytes(v) for v in value}
            return value

        if json_fields and json_decoder is None:
            raise ValueError("No JSON Decoder provided...")

        formatted_row = []

        for idx, (field_name, field_type) in enumerate(cls.__annotations__.items()):
            value = _convert_bytes(row[idx]) if convert_bytes else row[idx]

            if custom_parser and field_name in custom_parser:
                value = custom_parser[field_name](value)
            if json_fields and field_name in json_fields:
                value = json_decoder(value)
            formatted_row.append(value)

        return cls(*formatted_row)
