from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Sequence

from belka.core.dataclasses_ import BaseDataclass


@dataclass
class MatchItems:
    old_key: str
    new_key: str = field(default=None)
    new_type: Any = field(default=None)


class Adapter:
    _include_only: list[MatchItems] = None
    _exclude: list[MatchItems] = None
    _convert: list[MatchItems] = None

    def _get_include_only(self, data: dict) -> dict:
        data: dict = data.copy()
        new_data: dict[str, Any] = dict()

        match_items_dict: dict[str, MatchItems] = dict()
        for item in self._include_only:
            match_items_dict[item.old_key] = item

        data_old_keys = set(data.keys())
        matches_old_keys = set(item.old_key for item in self._include_only)
        existing_old_keys = data_old_keys.intersection(matches_old_keys)

        for old_key in existing_old_keys:
            match = match_items_dict[old_key]

            new_value = data[old_key]
            new_data[match.old_key] = new_value

            if match.new_type is not None and new_value is not None:
                new_value = match.new_type(new_value)
                new_data[match.old_key] = new_value

            if match.new_key is not None:
                new_data.pop(match.old_key, None)
                new_data[match.new_key] = new_value

        return new_data

    def _get_exclude(self, data: dict) -> dict:
        data: dict = data.copy()

        data_old_keys = set(data.keys())
        not_allowed_old_keys = set(item.old_key for item in self._exclude)
        not_allowed_existing_keys = data_old_keys.intersection(not_allowed_old_keys)

        for old_key in not_allowed_existing_keys:
            data.pop(old_key)

        return data

    def _get_convert(self, data: dict) -> dict:
        data: dict = data.copy()
        new_data: dict[str, Any] = dict()
        match_items_dict: dict[str, MatchItems] = dict()

        for item in self._convert:
            match_items_dict[item.old_key] = item

        for old_key in data.keys():
            new_value = data[old_key]
            new_data[old_key] = new_value

            if match := match_items_dict.get(old_key):
                if match.new_type is not None and new_value is not None:
                    new_value = match.new_type(new_value)
                    new_data[match.old_key] = new_value

                if match.new_key is not None:
                    new_data.pop(match.old_key, None)
                    new_data[match.new_key] = new_value

        return new_data

    def _transform_one(self, data: dict | BaseDataclass) -> dict:
        if type(data) is dict:
            data: dict = data.copy()
        elif is_dataclass(data):
            data = asdict(data)
        else:
            # TODO: Добавить логирование!
            print('Error: Unknown type of "data"!')
            print(f"{data=}")
            raise RuntimeError('Error: Unknown type of "data"!')

        existing_keys = set(data.keys())
        for key in existing_keys:
            if data.get(key) is None:
                data.pop(key)

        if self._include_only is not None:
            return self._get_include_only(data=data)

        if self._exclude is not None:
            data = self._get_exclude(data=data)

        if self._convert is not None:
            data = self._get_convert(data=data)

        return data

    def to_dict(
        self, data: dict | BaseDataclass | Sequence[dict | BaseDataclass]
    ) -> dict | Sequence[dict]:
        if type(data) is dict:
            return self._transform_one(data=data)

        elif issubclass(type(data), Sequence):
            result_items: list = list()
            for item in data:
                result = self._transform_one(data=item)
                if result != {}:
                    result_items.append(result)

            return tuple(result_items)
