from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class SchemaModel(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True


class ApiModel(BaseModel):
    class Config:
        alias_generator = to_camel
        from_attributes = True
        populate_by_name = True


class RequestModel(ApiModel):
    def model_dump(self, *, exclude_unset: bool = True, **kwargs):
        return super().model_dump(exclude_unset=exclude_unset, **kwargs)


class ResponseModel(ApiModel):
    pass
