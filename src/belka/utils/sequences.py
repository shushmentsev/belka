from typing import Sequence


def equal_parts(items, n):
    """Разделение списка на n максимально равных частей"""
    return [items[i::n] for i in range(n)]


def chunkify(items: Sequence, n):
    """Разбиение списка на подсписки по n элементов"""
    return [items[i: i + n] for i in range(0, len(items), n)]


def unique_sequence(items: Sequence) -> Sequence:
    unique_items = []
    for x in items:
        if x not in unique_items:
            unique_items.append(x)
    return unique_items


def merge_lists_dicts_by_key(
    dicts_1: list[dict],
    dicts_2: list[dict],
    key: str,
) -> list[dict]:
    """Объединение двух списков словарей в один по заданному ключу"""
    dict_1 = dict((obj[key], obj) for obj in dicts_1)
    dict_2 = dict((obj[key], obj) for obj in dicts_2)

    return [
        dict_1.get(key, dict()) | dict_2.get(key, dict())
        for key in set(list(dict_1.keys()) + list(dict_2.keys()))
    ]
