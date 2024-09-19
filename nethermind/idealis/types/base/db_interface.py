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
        for field_name, field_type in self.__annotations__.items():  # type: ignore
            encode_field = getattr(self, field_name)

            if custom_parser and field_name in custom_parser:
                encode_field = custom_parser[field_name](encode_field)

            if json_fields and field_name in json_fields:
                return_cols.append(json_encoder(encode_field))
            else:
                return_cols.append(encode_field)

        return tuple(return_cols)

    def from_db_row(self, row: Sequence[Any]):
        for idx, (field_name, field_type) in enumerate(self.__annotations__):  # type: ignore
            setattr(self, field_name, row[idx])  # type: ignore
        return self
