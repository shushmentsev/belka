from sqlalchemy import and_, or_, Select
from typing_extensions import Self

from belka.utils.sequences import unique_sequence


class Specification:
    _statement: Select = None

    # TODO: Переделать на _filters?
    _filter = None
    _models_for_join: list = list()
    _models_for_outerjoin: list = list()
    _models_for_join_onclause: list[dict] = list()

    def set_statement(self, statement: Select):
        self._statement = statement

    def is_satisfied(self):
        for model_for_join in self._models_for_join:
            self._statement = self._statement.join(model_for_join)

        for model_for_outerjoin in self._models_for_outerjoin:
            self._statement = self._statement.outerjoin(model_for_outerjoin)

        for model_for_join_onclause in self._models_for_join_onclause:
            self._statement = self._statement.join(**model_for_join_onclause)

        if self._filter is not None:
            return self._statement.filter(self._filter)

        return self._statement

    def __or__(self, other: Self) -> Self:
        self._models_for_join = list(
            unique_sequence(self._models_for_join + other._models_for_join),
        )
        self._models_for_outerjoin = list(
            unique_sequence(self._models_for_outerjoin + other._models_for_outerjoin),
        )
        self._models_for_join_onclause = list(
            unique_sequence(
                self._models_for_join_onclause + other._models_for_join_onclause
            ),
        )

        if (self._filter is not None) and (other._filter is not None):
            self._filter = or_(
                self._filter,
                other._filter,
            )
        elif self._filter is not None:
            self._filter = self._filter
        elif other._filter is not None:
            self._filter = other._filter
        else:
            self._filter = None

        return self

    def __and__(self, other: Self) -> Self:
        self._models_for_join = list(
            unique_sequence(self._models_for_join + other._models_for_join),
        )
        self._models_for_outerjoin = list(
            unique_sequence(self._models_for_outerjoin + other._models_for_outerjoin),
        )
        self._models_for_join_onclause = list(
            unique_sequence(
                self._models_for_join_onclause + other._models_for_join_onclause
            ),
        )

        if (self._filter is not None) and (other._filter is not None):
            self._filter = and_(
                self._filter,
                other._filter,
            )
        elif self._filter is not None:
            self._filter = self._filter
        elif other._filter is not None:
            self._filter = other._filter
        else:
            self._filter = None

        return self


def and_for_specifications(
        previous_specification: Specification | None,
        current_specification: Specification | None,
):
    if previous_specification is None:
        if current_specification is not None:
            return current_specification
        return None

    elif current_specification is None:
        if previous_specification is not None:
            return previous_specification
        return None

    else:
        previous_specification &= current_specification
        return previous_specification


def and_fof_specifications_with_condition(
        condition: bool,
        previous_specification: Specification,
        current_specification_false: Specification,
        current_specification_true: Specification,
):
    current_specification = current_specification_false
    if condition:
        current_specification = current_specification_true

    return and_for_specifications(
        previous_specification=previous_specification,
        current_specification=current_specification,
    )


def or_for_specifications(
        previous_specification: Specification | None,
        current_specification: Specification | None,
):
    if previous_specification is None:
        if current_specification is not None:
            return current_specification
        return None

    elif current_specification is None:
        if previous_specification is not None:
            return previous_specification
        return None

    elif previous_specification is not None:
        previous_specification |= current_specification
        return previous_specification
