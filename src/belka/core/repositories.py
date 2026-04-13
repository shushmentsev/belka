from collections import defaultdict
from typing import Any, Generic, Iterable, List, Protocol, Sequence, TypeVar

from pydantic import UUID4
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from belka.core.adapters import Adapter
from belka.core.pagination.schemas import PaginationParams
from belka.core.database import Base
from belka.core.schemas import SchemaModel
from belka.core.specifications import Specification

Model = type[Base]
SchemaT = TypeVar("SchemaT")


def _get_hash_table(items: Iterable[dict]):
    hashes = defaultdict(list)
    for index, item in enumerate(items):
        calculated_hash = hash(None)
        if item is not None:
            calculated_hash = hash(frozenset(item.items()))
        hashes[calculated_hash].append(index)

    return hashes


def _get_new_entities(
    data: Sequence[dict],
    existing_entities: Sequence[SchemaModel | dict],
    comparison_adapter: Adapter,
) -> Sequence[dict]:

    data_for_hashing: list[dict] = [
        comparison_adapter.to_dict(data=item) for item in data
    ]

    existing_entities_for_hashing = []
    if len(existing_entities) > 0:
        first_entity = existing_entities[0]
        if isinstance(first_entity, SchemaModel):
            existing_entities_for_hashing: list[dict] = [
                comparison_adapter.to_dict(data=item.model_dump())
                for item in existing_entities
            ]
        elif type(first_entity) is dict:
            existing_entities_for_hashing: list[dict] = [
                comparison_adapter.to_dict(data=item) for item in existing_entities
            ]
        else:
            # TODO: Добавить логирование!!!
            print("Error: Unknown type of existing_entities!")

    data_hashes = _get_hash_table(data_for_hashing)
    existing_entities_hashes = _get_hash_table(existing_entities_for_hashing)

    new_hashes = data_hashes.keys() - existing_entities_hashes.keys()
    return [data[data_hashes[hash_value][0]] for hash_value in new_hashes]


class IRepository(Protocol[SchemaT]):
    async def execute_sql(
        self,
        sql_query: str,
        parameters: dict | None,
        result_schema: SchemaModel | None,
    ):
        raise NotImplementedError

    async def get_by_id(self, entity_id: UUID4 | int) -> SchemaT | None:
        raise NotImplementedError

    async def get_by_filters(
        self,
        filter_by: dict | None = None,
        specification: Any | None = None,
        pagination: Any | None = None,
        order_by: Any | None = None,
        select_data: Any | None = None,
        get_one_or_none: bool = False,
    ) -> Sequence[SchemaT]:
        raise NotImplementedError

    # Creates
    async def create(self, data: dict | None = None) -> UUID4 | int:
        raise NotImplementedError

    # TODO: Сделать "create" с общим интерфейсом???
    async def create_if_not_exists(
        self,
        data: dict = None,
        filter_by: dict = None,
        **params,
    ) -> UUID4 | int | None:
        raise NotImplementedError

    async def create_many(self, data: Sequence[dict]) -> List[UUID4 | int]:
        raise NotImplementedError

    async def create_many_if_not_exists(
        self,
        data: Sequence[dict],
        comparison_adapter: Any,
        filter_by: dict,
        specification: Any | None = None,
    ) -> List[UUID4 | int]:
        raise NotImplementedError

    # Updates
    async def update_by_id(self, entity_id: UUID4 | int, data: dict) -> UUID4 | int:
        raise NotImplementedError

    async def update_by_filters(
        self,
        data: dict,
        filter_by: dict,
        specification: Any | None = None,
    ):
        raise NotImplementedError

    # Deletes
    async def delete_by_id(self, entity_id: UUID4 | int) -> None:
        raise NotImplementedError

    async def delete_by_ids(self, entities_ids: List[UUID4]) -> None:
        raise NotImplementedError

    async def delete_by_filters(self, filter_by: dict | None = None) -> None:
        raise NotImplementedError

    # Other
    async def amount(self, **filter_by) -> int:
        raise NotImplementedError

    async def upsert(self, data: dict, **filter_by) -> UUID4 | int | dict:
        raise NotImplementedError


class SQLAlchemyRepository(Generic[SchemaT]):
    _model: Model

    def __init__(self, session: AsyncSession):
        self._session = session

    async def execute_sql(
        self,
        sql_query: str,
        parameters: dict | None = None,
        result_schema: SchemaModel | None = None,
    ):
        res = await self._session.execute(text(sql_query), parameters)

        if result_schema is None:
            return res.all()

        rows = res.mappings()
        return [result_schema.model_validate(row) for row in rows]

    # TODO: Заменить метод "get" на "get_by_id"
    async def get(self, entity_id: UUID4 | int) -> SchemaT | None:
        stmt = select(self._model).filter_by(id=entity_id)

        result = None
        res = await self._session.execute(stmt)
        res = res.scalar_one_or_none()

        try:
            result = res.to_dict() if res else None
        except NotImplementedError:
            pass

        try:
            result = res.to_schema() if res else None
        except NotImplementedError:
            pass

        return result

    # TODO: Заменить метод "get" на "get_by_id"
    async def get_by_id(self, entity_id: UUID4 | int) -> SchemaT | None:
        return await self.get(entity_id=entity_id)

    # TODO: Заменить метод "list" на "get_by_filters"
    async def list(
        self,
        specification: Specification | None = None,
        pagination: PaginationParams | None = None,
        order_by: Any | None = None,
        select_data: Any | None = None,
        **filter_by,
    ) -> List[SchemaT]:
        if order_by is None:
            if select_data is None:
                order_by = self._model.id

        if select_data is None:
            select_data = self._model

        stmt = select(select_data).filter_by(**filter_by).order_by(order_by)

        if specification is not None:
            specification.set_statement(stmt)
            stmt = specification.is_satisfied()

        if pagination:
            stmt = stmt.limit(
                pagination.per_page,
            ).offset(max(0, (pagination.page - 1) * pagination.per_page))

        res = await self._session.execute(stmt)
        rows = res.scalars().unique().all()

        result: list = list()
        try:
            result = [row.to_dict() for row in rows]
        except NotImplementedError:
            print("to_dict not implemented")
            pass

        try:
            result = [row.to_schema() for row in rows]
        except NotImplementedError:
            pass

        # TODO: Возвращать сам объект, а не список, если len(rows) == 1?
        # TODO: А если не нашлось объектов?
        return result

    async def get_by_filters(
        self,
        filter_by: dict | None = None,
        specification: Specification | None = None,
        pagination: PaginationParams | None = None,
        order_by: Any | None = None,
        select_data: Any = None,
        get_one_or_none: bool = False,
    ) -> List[SchemaT] | SchemaT | None:
        filter_by = {} if filter_by is None else filter_by
        result = await self.list(
            specification=specification,
            pagination=pagination,
            order_by=order_by,
            select_data=select_data,
            **filter_by,
        )
        if not get_one_or_none:
            return result

        if len(result) > 1:
            raise Exception(
                f'Error in "get_by_filters": len(result) > 1 | {filter_by=}'
            )

        if len(result) == 1:
            return result[0]

        return None

    async def aggregate(
        self,
        select_data: Any,
        result_schema: SchemaModel,
        filter_by: dict | None = None,
        specification: Specification | None = None,
        pagination: PaginationParams | None = None,
        group_by: Any | None = None,
        order_by: Any | None = None,
    ):
        filter_by = {} if filter_by is None else filter_by

        if type(select_data) in [tuple, list]:
            stmt = select(*select_data)
        else:
            stmt = select(select_data)

        if isinstance(group_by, (list, tuple)):
            stmt = stmt.filter_by(**filter_by).group_by(*group_by).order_by(order_by)
        else:
            stmt = stmt.filter_by(**filter_by).group_by(group_by).order_by(order_by)

        if specification is not None:
            specification.set_statement(stmt)
            stmt = specification.is_satisfied()

        if pagination:
            stmt = stmt.limit(
                pagination.per_page,
            ).offset(max(0, (pagination.page - 1) * pagination.per_page))

        res = await self._session.execute(stmt)
        rows = res.unique().all()

        one_row_result = False
        # if type(select_data) in [sum]:
        #     one_row_result = True

        if group_by is None:
            one_row_result = True

        if one_row_result:
            return result_schema.model_validate(rows[0])

        return [result_schema.model_validate(row._asdict()) for row in rows]

    # TODO: Заменить метод "add" на "create"
    async def add(self, data: dict | None = None) -> UUID4 | int:
        data = dict() if (data is None) else data

        model = self._model(**data)
        self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)

        return model.id

    async def create(self, data: dict | None = None) -> UUID4 | int:
        return await self.add(data=data)

    async def create_if_not_exists(
        self,
        data: dict = None,
        filter_by: dict = None,
        specification: Specification = None,
    ) -> UUID4 | int | None:
        result: list[dict] = await self.get_by_filters(
            filter_by=filter_by,
            specification=specification,
        )

        if len(result) == 0:
            return await self.create(data=data)

    async def create_many(self, data: Sequence[dict]) -> Sequence[UUID4 | int] | None:
        if len(data) > 0:
            stmt = insert(self._model).returning(self._model.id)
            res = await self._session.execute(stmt, data)
            await self._session.flush()
            return res.scalars().all()

    # TODO: Подумать над возвращаемыми значениями!
    # TODO: Добавить в интерфейс "comparison_adapter"
    async def create_many_if_not_exists(
        self,
        data: Sequence[dict],
        comparison_adapter: Adapter,
        filter_by: dict = None,
        specification: Specification = None,
    ) -> Sequence[UUID4 | int] | None:
        if len(data) > 0:
            existing_entities: Sequence[dict] = await self.get_by_filters(
                filter_by=filter_by,
                specification=specification,
            )

            new_entities: Sequence[dict] = _get_new_entities(
                data=data,
                existing_entities=existing_entities,
                comparison_adapter=comparison_adapter,
            )
            return await self.create_many(data=new_entities)

    # TODO: Заменить метод "update" на метод "update_by_id"
    async def update(self, entity_id: UUID4, data: dict) -> UUID4 | int:
        stmt = select(self._model).filter_by(id=entity_id)
        res = await self._session.execute(stmt)

        model = res.scalar_one_or_none()

        if model is None:
            return

        for key, value in data.items():
            setattr(model, key, value)

        return model.id

    async def update_by_id(self, entity_id: UUID4, data: dict) -> UUID4 | int:
        return await self.update(
            entity_id=entity_id,
            data=data,
        )

    # Альтернатива update без select запроса, в теории быстрее
    async def sql_update_by_id(self, entity_id: UUID4, data: dict) -> UUID4 | int:
        stmt = (
            update(self._model)
            .filter_by(id=entity_id)
            .values(data)
            .returning(self._model.id)
        )
        await self._session.execute(stmt)

    async def bulk_update(self, data: Sequence[dict]):
        await self._session.execute(update(self._model), data)
        await self._session.flush()

    # TODO: Подумать над возвращаемым или возвращаемыми типами
    async def update_by_filters(
        self,
        data: dict,
        filter_by: dict | None = None,
        specification: Specification | None = None,
    ):
        stmt = select(self._model)

        if (filter_by is not None) and (filter_by != {}):
            stmt = stmt.filter_by(**filter_by)

        if specification is not None:
            specification.set_statement(stmt)
            stmt = specification.is_satisfied()

        res = await self._session.execute(stmt)
        for row in res.scalars().all():
            for key, value in data.items():
                setattr(row, key, value)

    # TODO: Заменить метод "delete" на метод "delete_by_id"
    async def delete(self, entity_id: UUID4):
        stmt = delete(self._model).filter_by(id=entity_id)
        await self._session.execute(stmt)

    async def delete_by_id(self, entity_id: UUID4):
        await self.delete(
            entity_id=entity_id,
        )

    async def delete_by_ids(self, entities_ids: List[UUID4]):
        filter_ = self._model.id.in_(entities_ids)
        stmt = delete(self._model).filter(filter_)
        await self._session.execute(stmt)

    async def delete_by_filters(
        self,
        filter_by: dict | None = None,
        specification: Specification | None = None,
    ):
        if filter_by is None and specification is None:
            raise

        filter_by = filter_by if filter_by is not None else {}
        stmt = delete(self._model).filter_by(**filter_by)

        if specification is not None:
            specification.set_statement(stmt)
            stmt = specification.is_satisfied()
        await self._session.execute(stmt)

    # Other
    # TODO: Переделать интерфейс на "filter_by" в виде словаря
    async def amount(
        self,
        specification: Specification | None = None,
        **filter_by,
    ) -> int:
        stmt = select(func.count()).select_from(self._model).filter_by(**filter_by)
        if specification is not None:
            specification.set_statement(stmt)
            stmt = specification.is_satisfied()

        res = await self._session.execute(stmt)
        return res.scalar_one()

    async def upsert(self, data: dict, **filter_by) -> UUID4 | int:
        stmt = select(self._model).filter_by(**filter_by)
        res = await self._session.execute(stmt)
        model = res.scalar()

        if model is None:
            data = dict() if (data is None) else data

            model = self._model(**data)
            self._session.add(model)

            await self._session.flush()
            await self._session.refresh(model)
            return model.id

        for key, value in data.items():
            setattr(model, key, value)

        return model.id
