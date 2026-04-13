import inspect

from sqlalchemy.exc import InterfaceError


class UnitOfWork:
    _session = None

    def __init__(self, database_session=None):
        if database_session is not None:
            self._session = database_session

    def _init_repos(self, session):
        for cls in inspect.getmro(type(self)):
            annotations = cls.__dict__.get("__annotations__", {})
            for name, repo_cls in annotations.items():
                if name.startswith("_"):
                    continue
                setattr(self, name, repo_cls(session))

    async def __aenter__(self):
        if self._session is None:
            raise RuntimeError(
                "session must be provided via __init__ or set by subclass"
            )

        self._init_repos(self._session)

    async def __aexit__(self, *args):
        # await self.rollback()
        try:
            await self._session.close()
        except InterfaceError:
            pass
        self._session = None

    async def commit(self):
        await self._session.commit()

    async def flush(self):
        await self._session.flush()

    async def rollback(self):
        await self._session.rollback()
