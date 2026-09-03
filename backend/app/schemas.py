from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class BrowserSessionIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=120)


class CountIn(BrowserSessionIn):
    code: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, ge=0, le=100_000)
    mode: str = "add"


class RecountIn(BrowserSessionIn):
    quantity: int = Field(ge=0, le=100_000)
    note: str = Field(default="", max_length=500)


class RecountRequestIn(BaseModel):
    skus: list[str] = Field(min_length=1)
    note: str = Field(default="", max_length=500)


class ApproveIn(BaseModel):
    skus: list[str] = Field(min_length=1)
    note: str = Field(default="", max_length=500)


class InventoryStartIn(BaseModel):
    label: str = Field(default="Inventário Geral", min_length=3, max_length=160)


class UserCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "OPERADOR"
    permissions: list[str] = []


class UserUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: str | None = None
    permissions: list[str] | None = None
    active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class ProviderIn(BaseModel):
    provider: str


class ScenarioIn(BaseModel):
    scenario: str
