import pytest
from sqlalchemy import func

from belka.core.adapters import Adapter, MatchItems
from belka.core.pagination.schemas import PaginationParams
from tests.conftest import (
    Item,
    ItemAggSchema,
    ItemCountSchema,
    ItemRepository,
    ItemSchema,
    ItemValueGteSpec,
    TagRepository,
)


# -----------------------------
# execute_sql
# -----------------------------

async def test_execute_sql_returns_raw_rows_when_no_schema(
        item_repo: ItemRepository,
):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "x"})

    rows = await item_repo.execute_sql("SELECT id, name FROM items ORDER BY id")

    assert len(rows) == 2
    assert rows[0].name == "a"
    assert rows[1].name == "b"


async def test_execute_sql_validates_into_schema(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})

    rows = await item_repo.execute_sql(
        "SELECT id, name, value, category FROM items",
        result_schema=ItemSchema,
    )

    assert len(rows) == 1
    assert isinstance(rows[0], ItemSchema)
    assert rows[0].name == "a"


async def test_execute_sql_passes_parameters(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "x"})

    rows = await item_repo.execute_sql(
        "SELECT id, name, value, category FROM items WHERE name = :name",
        parameters={"name": "b"},
        result_schema=ItemSchema,
    )

    assert [r.name for r in rows] == ["b"]


# -----------------------------
# get_by_id
# -----------------------------

async def test_get_by_id_returns_schema_when_found(item_repo: ItemRepository):
    new_id = await item_repo.create({"name": "a", "value": 7, "category": "x"})

    result = await item_repo.get_by_id(entity_id=new_id)

    assert isinstance(result, ItemSchema)
    assert result.id == new_id
    assert result.name == "a"
    assert result.value == 7


async def test_get_by_id_returns_dict_when_model_uses_to_dict(
        tag_repo: TagRepository,
):
    new_id = await tag_repo.create({"title": "first"})

    result = await tag_repo.get_by_id(entity_id=new_id)

    assert result == {"id": new_id, "title": "first"}


async def test_get_by_id_returns_none_when_missing(item_repo: ItemRepository):
    assert await item_repo.get_by_id(entity_id=9999) is None


# -----------------------------
# get_by_filters
# -----------------------------

async def test_get_by_filters_no_args_returns_all(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    result = await item_repo.get_by_filters()

    assert len(result) == 2
    assert {r.name for r in result} == {"a", "b"}


async def test_get_by_filters_with_filter_by(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    result = await item_repo.get_by_filters(filter_by={"category": "y"})

    assert [r.name for r in result] == ["b"]


async def test_get_by_filters_with_specification(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 5, "category": "x"})
    await item_repo.create({"name": "b", "value": 10, "category": "x"})
    await item_repo.create({"name": "c", "value": 20, "category": "x"})

    result = await item_repo.get_by_filters(specification=ItemValueGteSpec(10))

    assert sorted(r.name for r in result) == ["b", "c"]


async def test_get_by_filters_with_pagination(item_repo: ItemRepository):
    for i in range(5):
        await item_repo.create({"name": f"n{i}", "value": i, "category": "x"})

    page1 = await item_repo.get_by_filters(
        pagination=PaginationParams(page=1, per_page=2),
    )
    page2 = await item_repo.get_by_filters(
        pagination=PaginationParams(page=2, per_page=2),
    )
    page3 = await item_repo.get_by_filters(
        pagination=PaginationParams(page=3, per_page=2),
    )

    assert [r.name for r in page1] == ["n0", "n1"]
    assert [r.name for r in page2] == ["n2", "n3"]
    assert [r.name for r in page3] == ["n4"]


async def test_get_by_filters_get_one_or_none_returns_single(
        item_repo: ItemRepository,
):
    new_id = await item_repo.create({"name": "a", "value": 1, "category": "x"})

    result = await item_repo.get_by_filters(
        filter_by={"id": new_id},
        get_one_or_none=True,
    )

    assert isinstance(result, ItemSchema)
    assert result.id == new_id


async def test_get_by_filters_get_one_or_none_returns_none_when_empty(
        item_repo: ItemRepository,
):
    result = await item_repo.get_by_filters(
        filter_by={"id": 9999},
        get_one_or_none=True,
    )
    assert result is None


async def test_get_by_filters_get_one_or_none_raises_when_many(
        item_repo: ItemRepository,
):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "x"})

    with pytest.raises(Exception, match=r"len\(result\) > 1"):
        await item_repo.get_by_filters(
            filter_by={"category": "x"},
            get_one_or_none=True,
        )


async def test_get_by_filters_with_order_by(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 30, "category": "x"})
    await item_repo.create({"name": "b", "value": 10, "category": "x"})
    await item_repo.create({"name": "c", "value": 20, "category": "x"})

    result = await item_repo.get_by_filters(order_by=Item.value)

    assert [r.value for r in result] == [10, 20, 30]


async def test_get_by_filters_with_select_data_on_scalar_raises(
        item_repo: ItemRepository,
):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})

    # Фиксируем текущее поведение: select_data=Item.name возвращает
    # строки, на которых .to_dict()/.to_schema() кидает AttributeError,
    # и try/except в list() его не ловит (ловится только
    # NotImplementedError). TODO: починить продовый код, чтобы
    # скалярная выборка работала, и обновить этот тест.
    with pytest.raises(AttributeError):
        await item_repo.get_by_filters(select_data=Item.name)


# -----------------------------
# aggregate
# -----------------------------

async def test_aggregate_single_row_when_group_by_none(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    result = await item_repo.aggregate(
        select_data=func.count(Item.id).label("total"),
        result_schema=ItemCountSchema,
    )

    assert isinstance(result, ItemCountSchema)
    assert result.total == 2


async def test_aggregate_with_group_by(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 5, "category": "x"})
    await item_repo.create({"name": "b", "value": 7, "category": "x"})
    await item_repo.create({"name": "c", "value": 3, "category": "y"})

    result = await item_repo.aggregate(
        select_data=(Item.category, func.sum(Item.value).label("total")),
        result_schema=ItemAggSchema,
        group_by=Item.category,
        order_by=Item.category,
    )

    assert [(r.category, r.total) for r in result] == [("x", 12), ("y", 3)]


async def test_aggregate_with_specification(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 5, "category": "x"})
    await item_repo.create({"name": "b", "value": 15, "category": "x"})
    await item_repo.create({"name": "c", "value": 25, "category": "y"})

    result = await item_repo.aggregate(
        select_data=(Item.category, func.sum(Item.value).label("total")),
        result_schema=ItemAggSchema,
        group_by=Item.category,
        order_by=Item.category,
        specification=ItemValueGteSpec(10),
    )

    assert [(r.category, r.total) for r in result] == [("x", 15), ("y", 25)]


# -----------------------------
# create
# -----------------------------

async def test_create_returns_id_and_persists(item_repo: ItemRepository):
    new_id = await item_repo.create({"name": "a", "value": 1, "category": "x"})

    assert isinstance(new_id, int)
    fetched = await item_repo.get_by_id(entity_id=new_id)
    assert fetched.name == "a"


async def test_create_with_no_data_uses_defaults(item_repo: ItemRepository):
    new_id = await item_repo.create()

    fetched = await item_repo.get_by_id(entity_id=new_id)
    assert fetched.name == ""
    assert fetched.value == 0
    assert fetched.category == "default"


# -----------------------------
# create_if_not_exists
# -----------------------------

async def test_create_if_not_exists_creates_when_absent(item_repo: ItemRepository):
    new_id = await item_repo.create_if_not_exists(
        data={"name": "a", "value": 1, "category": "x"},
        filter_by={"name": "a"},
    )

    assert isinstance(new_id, int)
    assert await item_repo.amount() == 1


async def test_create_if_not_exists_returns_none_when_present(
        item_repo: ItemRepository,
):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})

    result = await item_repo.create_if_not_exists(
        data={"name": "a", "value": 99, "category": "y"},
        filter_by={"name": "a"},
    )

    assert result is None
    assert await item_repo.amount() == 1


# -----------------------------
# create_many
# -----------------------------

async def test_create_many_inserts_all_and_returns_ids(item_repo: ItemRepository):
    ids = await item_repo.create_many(
        [
            {"name": "a", "value": 1, "category": "x"},
            {"name": "b", "value": 2, "category": "y"},
        ],
    )

    assert len(ids) == 2
    assert await item_repo.amount() == 2


async def test_create_many_with_empty_list_returns_none(item_repo: ItemRepository):
    result = await item_repo.create_many([])

    assert result is None
    assert await item_repo.amount() == 0


# -----------------------------
# create_many_if_not_exists
# -----------------------------

class _NameAdapter(Adapter):
    _include_only = [MatchItems(old_key="name")]


async def test_create_many_if_not_exists_inserts_only_new(
        item_repo: ItemRepository,
):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})

    await item_repo.create_many_if_not_exists(
        data=[
            {"name": "a", "value": 11, "category": "x"},  # дубль по name
            {"name": "b", "value": 22, "category": "y"},  # новый
        ],
        comparison_adapter=_NameAdapter(),
        filter_by={},
    )

    all_items = await item_repo.get_by_filters(order_by=Item.name)
    assert [i.name for i in all_items] == ["a", "b"]


async def test_create_many_if_not_exists_with_empty_list_does_nothing(
        item_repo: ItemRepository,
):
    result = await item_repo.create_many_if_not_exists(
        data=[],
        comparison_adapter=_NameAdapter(),
        filter_by={},
    )

    assert result is None
    assert await item_repo.amount() == 0


# -----------------------------
# update_by_id
# -----------------------------

async def test_update_by_id_updates_fields_and_returns_id(
        item_repo: ItemRepository,
):
    new_id = await item_repo.create({"name": "a", "value": 1, "category": "x"})

    returned = await item_repo.update_by_id(
        entity_id=new_id,
        data={"name": "b", "value": 99},
    )
    assert returned == new_id

    fetched = await item_repo.get_by_id(entity_id=new_id)
    assert fetched.name == "b"
    assert fetched.value == 99


async def test_update_by_id_returns_none_when_missing(item_repo: ItemRepository):
    result = await item_repo.update_by_id(entity_id=9999, data={"name": "x"})
    assert result is None


# -----------------------------
# sql_update_by_id
# -----------------------------

async def test_sql_update_by_id_updates_without_select(item_repo: ItemRepository):
    new_id = await item_repo.create({"name": "a", "value": 1, "category": "x"})

    await item_repo.sql_update_by_id(entity_id=new_id, data={"value": 42})

    fetched = await item_repo.get_by_id(entity_id=new_id)
    assert fetched.value == 42


# -----------------------------
# bulk_update
# -----------------------------

async def test_bulk_update_applies_changes_for_each_row(item_repo: ItemRepository):
    id1 = await item_repo.create({"name": "a", "value": 1, "category": "x"})
    id2 = await item_repo.create({"name": "b", "value": 2, "category": "x"})

    await item_repo.bulk_update(
        [
            {"id": id1, "value": 100},
            {"id": id2, "value": 200},
        ],
    )

    assert (await item_repo.get_by_id(id1)).value == 100
    assert (await item_repo.get_by_id(id2)).value == 200


# -----------------------------
# update_by_filters
# -----------------------------

async def test_update_by_filters_with_filter_by(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    await item_repo.update_by_filters(
        data={"value": 50},
        filter_by={"category": "x"},
    )

    items = {i.name: i.value for i in await item_repo.get_by_filters()}
    assert items == {"a": 50, "b": 2}


async def test_update_by_filters_with_specification(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 5, "category": "x"})
    await item_repo.create({"name": "b", "value": 15, "category": "x"})

    await item_repo.update_by_filters(
        data={"category": "high"},
        specification=ItemValueGteSpec(10),
    )

    items = {i.name: i.category for i in await item_repo.get_by_filters()}
    assert items == {"a": "x", "b": "high"}


async def test_update_by_filters_no_filters_updates_all(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    await item_repo.update_by_filters(data={"category": "z"})

    cats = {i.category for i in await item_repo.get_by_filters()}
    assert cats == {"z"}


# -----------------------------
# delete_by_id / delete_by_ids / delete_by_filters
# -----------------------------

async def test_delete_by_id_removes_row(item_repo: ItemRepository):
    new_id = await item_repo.create({"name": "a", "value": 1, "category": "x"})

    await item_repo.delete_by_id(entity_id=new_id)

    assert await item_repo.get_by_id(entity_id=new_id) is None


async def test_delete_by_ids_removes_listed_only(item_repo: ItemRepository):
    id1 = await item_repo.create({"name": "a", "value": 1, "category": "x"})
    id2 = await item_repo.create({"name": "b", "value": 2, "category": "x"})
    id3 = await item_repo.create({"name": "c", "value": 3, "category": "x"})

    await item_repo.delete_by_ids(entities_ids=[id1, id3])

    remaining = [i.id for i in await item_repo.get_by_filters()]
    assert remaining == [id2]


async def test_delete_by_filters_raises_when_no_filters_and_no_spec(
        item_repo: ItemRepository,
):
    # В коде стоит голый `raise` без объекта — это RuntimeError.
    # TODO: Когда продовый код починят на осмысленное исключение —
    # обновить этот тест.
    with pytest.raises(RuntimeError):
        await item_repo.delete_by_filters()


async def test_delete_by_filters_with_filter_by(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    await item_repo.delete_by_filters(filter_by={"category": "x"})

    remaining = [i.name for i in await item_repo.get_by_filters()]
    assert remaining == ["b"]


async def test_delete_by_filters_with_specification(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 5, "category": "x"})
    await item_repo.create({"name": "b", "value": 15, "category": "x"})

    await item_repo.delete_by_filters(specification=ItemValueGteSpec(10))

    remaining = [i.name for i in await item_repo.get_by_filters()]
    assert remaining == ["a"]


# -----------------------------
# amount
# -----------------------------

async def test_amount_without_filters_counts_all(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    assert await item_repo.amount() == 2


async def test_amount_with_filter_by(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 1, "category": "x"})
    await item_repo.create({"name": "b", "value": 2, "category": "y"})

    assert await item_repo.amount(category="x") == 1


async def test_amount_with_specification(item_repo: ItemRepository):
    await item_repo.create({"name": "a", "value": 5, "category": "x"})
    await item_repo.create({"name": "b", "value": 15, "category": "x"})
    await item_repo.create({"name": "c", "value": 25, "category": "x"})

    assert await item_repo.amount(specification=ItemValueGteSpec(10)) == 2


# -----------------------------
# upsert
# -----------------------------

async def test_upsert_inserts_when_missing_returns_id(item_repo: ItemRepository):
    new_id = await item_repo.upsert(
        data={"name": "a", "value": 1, "category": "x"},
        name="a",
    )

    assert isinstance(new_id, int)
    fetched = await item_repo.get_by_id(entity_id=new_id)
    assert fetched.name == "a"


async def test_upsert_updates_when_present_returns_id(item_repo: ItemRepository):
    existing_id = await item_repo.create(
        {"name": "a", "value": 1, "category": "x"},
    )

    returned = await item_repo.upsert(
        data={"value": 99, "category": "y"},
        name="a",
    )

    assert returned == existing_id
    fetched = await item_repo.get_by_id(entity_id=existing_id)
    assert fetched.value == 99
    assert fetched.category == "y"
    assert await item_repo.amount() == 1
