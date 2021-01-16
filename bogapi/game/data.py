from collections.abc import Iterable, Mapping
from typing import Any, Optional, Union

from bogapi.game.player import is_master


class Data(object):
    data_type = 'any'

    def __init__(self,
                 content=None,
                 public: bool = False,
                 allowed_pid: Optional[Iterable[int]] = None):
        self.content = content
        self._public = public
        self._allowed_pid = set(allowed_pid or [])

    @property
    def public(self) -> bool:
        return self._public

    @property
    def private(self) -> bool:
        return not self._public

    @property
    def allowed_pid(self) -> Iterable[int]:
        return list(self._allowed_pid)

    def to_dict(self) -> Mapping[str, Any]:
        return {
            'type': self.data_type,
            'content': self.content,
            'public': self.public,
            'allowed_pid': self.allowed_pid,
        }

    @classmethod
    def _type_check(cls, content):
        return

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]):
        content = payload.get('content')
        cls._type_check(content)
        if 'public' in payload and not isinstance(payload['public'], bool):
            raise TypeError('the attribute `public` is not boolean')
        public = payload.get('public', False)
        if 'allowed_pid' in payload:
            for pid in payload['allowed_pid']:
                if not isinstance(pid, int):
                    raise TypeError('the attribute `pid` is not integer')
        allowed_pid = payload.get('allowed_pid')
        return cls(content=content, public=public, allowed_pid=allowed_pid)

    def make_public(self):
        self._public = True

    def make_private(self):
        self._public = False

    def show_to(self, pid: Union[int, Iterable[int]]):
        if self.public:
            return
        if isinstance(pid, int):
            self._allowed_pid.add(pid)
        else:
            self._allowed_pid.update(pid)

    def hide_from(self, pid: Union[int, Iterable[int]]):
        if self.public:
            raise ValueError('the data is public')
        if isinstance(pid, int):
            self._allowed_pid.remove(pid)
        else:
            self._allowed_pid.difference_update(pid)

    def visible_by(self, pid: int) -> bool:
        return is_master(pid) or self.public or pid in self.allowed_pid


class NumericData(Data):
    data_type = 'numeric'

    def __init__(self, content: Union[int, float, complex], *args, **kwargs):
        super(NumericData, self).__init__(content, *args, **kwargs)

    @classmethod
    def _type_check(cls, content):
        if not isinstance(content, (int, float, complex)):
            raise TypeError('the attribute `content` is not numeric')

    def __iadd__(self, other):
        self.content += other

    def __isub__(self, other):
        self.content -= other

    def __imul__(self, other):
        self.content *= other

    def __itruediv__(self, other):
        self.content /= other

    def __ifloordiv__(self, other):
        self.content //= other

    def __imod__(self, other):
        self.content %= other


class StringData(Data):
    data_type = 'string'

    def __init__(self, content: str, *args, **kwargs):
        super(StringData, self).__init__(content, *args, **kwargs)

    @classmethod
    def _type_check(cls, content):
        if not isinstance(content, str):
            raise TypeError('the attribute `content` is not string')

    def __iadd__(self, other):
        self.content += other

    def __imul__(self, other):
        self.content *= other


def _get_data_from_dict(payload: Mapping[str, Any]) -> Data:
    data_type = payload['type']
    if data_type == NumericData.data_type:
        data = NumericData.from_dict(payload)
    elif data_type == StringData.data_type:
        data = StringData.from_dict(payload)
    elif data_type == Data.data_type:
        data = Data.from_dict(payload)
    else:
        raise ValueError('unknown data type: {}'.format(data_type))
    return data
