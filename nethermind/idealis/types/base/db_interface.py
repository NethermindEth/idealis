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
    ):
        """
        Convert a SELECT * result into a python Dataclass

        :param row:  Row from SELECT * query
        :param json_fields:  Set of fields to parse as JSON
        :param json_decoder:  JSON Decoder to use for parsing JSON fields
        :param custom_parser:  Custom parser for fields.  Maps field_name -> parse_function

        >>> import json
        >>> from decimal import Decimal
        >>> from dataclasses import dataclass
        >>> from nethermind.idealis.types.base import DataclassDBInterface
        >>> @dataclass
        ... class TestClass(DataclassDBInterface):
        ...     field1: int
        ...     field2: dict[str, str]
        ...     field3: list[str]
        ...
        >>> TestClass.from_db_row(
        ...     (Decimal(12345), '{"a": 12, "b": 22}', '0x1234,0x5678'),
        ...     json_fields={'field2'},
        ...     json_decoder=json.loads,
        ...     custom_parser={
        ...         'field1': lambda b: int(b),
        ...         'field3': lambda b: b.split(',')
        ...     }
        ... )
        TestClass(field1=12345, field2={'a': 12, 'b': 22}, field3=['0x1234', '0x5678'])

        """

        if json_fields and json_decoder is None:
            raise ValueError("No JSON Decoder provided...")

        formatted_row = []

        for idx, (field_name, field_type) in enumerate(cls.__annotations__.items()):
            value = row[idx]
            if custom_parser and field_name in custom_parser:
                value = custom_parser[field_name](value)
            if json_fields and field_name in json_fields:
                value = json_decoder(value)
            formatted_row.append(value)

        return cls(*formatted_row)
