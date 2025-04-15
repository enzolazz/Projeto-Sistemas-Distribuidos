from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Tupla(_message.Message):
    __slots__ = ("chave", "valor", "versao")
    CHAVE_FIELD_NUMBER: _ClassVar[int]
    VALOR_FIELD_NUMBER: _ClassVar[int]
    VERSAO_FIELD_NUMBER: _ClassVar[int]
    chave: str
    valor: str
    versao: int
    def __init__(self, chave: _Optional[str] = ..., valor: _Optional[str] = ..., versao: _Optional[int] = ...) -> None: ...

class ChaveValor(_message.Message):
    __slots__ = ("chave", "valor")
    CHAVE_FIELD_NUMBER: _ClassVar[int]
    VALOR_FIELD_NUMBER: _ClassVar[int]
    chave: str
    valor: str
    def __init__(self, chave: _Optional[str] = ..., valor: _Optional[str] = ...) -> None: ...

class ChaveVersao(_message.Message):
    __slots__ = ("chave", "versao")
    CHAVE_FIELD_NUMBER: _ClassVar[int]
    VERSAO_FIELD_NUMBER: _ClassVar[int]
    chave: str
    versao: int
    def __init__(self, chave: _Optional[str] = ..., versao: _Optional[int] = ...) -> None: ...

class Versao(_message.Message):
    __slots__ = ("versao",)
    VERSAO_FIELD_NUMBER: _ClassVar[int]
    versao: int
    def __init__(self, versao: _Optional[int] = ...) -> None: ...
