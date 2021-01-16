from typing import Any, Dict, Iterable, Mapping, Optional, Union

from bogapi.game.data import Data, _get_data_from_dict
from bogapi.game.player import is_master


class RenderedComponent(object):
    def __init__(self,
                 name: str,
                 data: Mapping[str, Any],
                 position: Optional[str]):
        self.name = name
        self.data = dict(data)
        self.position = position

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'data': self.data,
            'position': self.position
        }


class Component(object):
    component_type = 'base'

    def __init__(self,
                 name: str,
                 data: Mapping[str, Data],
                 position: Optional[str] = None,
                 public: bool = True,
                 allowed_pid: Optional[Iterable[int]] = None):
        self._name = name
        self._public = public
        self._allowed_pid = set(allowed_pid or [])
        self._position = position
        self._data = dict(data)

    @property
    def name(self) -> str:
        return self._name

    @property
    def position(self) -> Optional[str]:
        return self._position

    @property
    def public(self) -> bool:
        return self._public

    @property
    def private(self) -> bool:
        return not self._public

    @property
    def allowed_pid(self) -> Iterable[int]:
        return list(self._allowed_pid)

    @property
    def data(self) -> Dict[str, Data]:
        return self._data

    def __getitem__(self, item):
        return self._data[item]

    def own_by(self, pid: Union[int, Iterable[int]]):
        for name in self.data:
            self.data[name].make_private()
            self.data[name].show_to(pid)

    def make_public(self):
        self._public = True

    def make_private(self):
        self._public = False

    def set_position(self, position: Optional[str]):
        self._position = position

    def show_to(self, pid: Union[int, Iterable[int]]):
        if self.public:
            return
        if isinstance(pid, int):
            self._allowed_pid.add(pid)
        else:
            self._allowed_pid.update(pid)

    def hide_from(self, pid: Union[int, Iterable[int]]):
        if self.public:
            raise ValueError('the component is public')
        if isinstance(pid, int):
            self._allowed_pid.remove(pid)
        else:
            self._allowed_pid.difference_update(pid)

    def visible_by(self, pid: int) -> bool:
        return is_master(pid) or self.public or pid in self.allowed_pid

    def render(self, pid: int = 0) -> RenderedComponent:
        if not self.visible_by(pid):
            raise ValueError('the component is not visible by PID {}'.format(pid))
        return RenderedComponent(
            name=self.name,
            data={
                key: self.data[key].content
                for key in self.data
                if self.data[key].visible_by(pid)
            },
            position=self.position,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'position': self.position,
            'data': {
                key: self.data[key].to_dict()
                for key in self.data
            }
        }

    @classmethod
    def _get_attributes_from_dict(cls, payload: Mapping[str, Any]):
        if 'name' not in payload or not isinstance(payload['name'], str):
            raise TypeError('the attribute `name` is not string')
        name = payload['name']
        if 'data' not in payload:
            raise TypeError('the component has no data')
        data_dict = payload['data']
        for key in data_dict:
            if not isinstance(key, str):
                raise TypeError('data key is not string')
        data = {
            key: _get_data_from_dict(data_dict[key])
            for key in data_dict
        }
        if 'position' in payload and not isinstance(payload['position'], str):
            raise TypeError('the attribute `position` is not string')
        position = payload.get('position')
        if 'public' in payload and not isinstance(payload['public'], bool):
            raise TypeError('the attribute `public` is not boolean')
        public = payload.get('public', True)
        if 'allowed_pid' in payload:
            for pid in payload['allowed_pid']:
                if not isinstance(pid, int):
                    raise TypeError('the attribute `pid` is not integer')
        allowed_pid = payload.get('allowed_pid')
        return name, data, position, public, allowed_pid

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]):
        name, data, position, public, allowed_pid = cls._get_attributes_from_dict(payload)
        return cls(name=name, data=data, position=position, public=public, allowed_pid=allowed_pid)


class SimpleComponent(Component):
    component_type = 'simple'

    def __init__(self, name: str, content=None, *args, **kwargs):
        data = content if isinstance(content, Data) else Data(content)
        super(SimpleComponent, self).__init__(name, {'content': data}, *args, **kwargs)

    def show_content(self):
        self.data['content'].make_public()

    @property
    def content(self):
        return self.data['content'].content

    def set_content(self, content):
        self.data['content'].content = content

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]):
        name, data, position, public, allowed_pid = cls._get_attributes_from_dict(payload)
        if len(data) != 1:
            raise ValueError('a simple component should have only one data')
        for key in data:
            if key != 'content':
                raise ValueError('a simple component should have data `content`')
        return cls(name=name, content=data['content'],
                   position=position, public=public, allowed_pid=allowed_pid)


class SimpleCard(SimpleComponent):
    component_type = 'simple_card'

    def flip(self):
        data = self.data['content']
        if data.public:
            data.make_private()
        else:
            data.make_public()


class TwoSidedCard(Component):
    component_type = 'two_sided_card'

    def __init__(self, name: str, front=None, back=None, *args, **kwargs):
        data = {
            'front': front if isinstance(front, Data) else Data(front, public=True),
            'back': back if isinstance(back, Data) else Data(back, public=False),
        }
        super(TwoSidedCard, self).__init__(name, data, *args, **kwargs)

    def flip(self):
        front = self.data['front']
        back = self.data['back']
        if front.public and back.private:
            front.make_private()
            back.make_public()
        elif front.private and back.public:
            front.make_public()
            back.make_private()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]):
        name, data, position, public, allowed_pid = cls._get_attributes_from_dict(payload)
        if len(data) != 2:
            raise ValueError('a two-sided card should have exactly two data')
        for key in data:
            if key not in ['front', 'back']:
                raise ValueError('a two-sided card should have data `front` and `back`')
        return cls(name=name, front=data['front'], back=data['back'],
                   position=position, public=public, allowed_pid=allowed_pid)


def _get_component_from_dict(payload: Mapping[str, Any]) -> Component:
    component_type = payload['type']
    if component_type == SimpleComponent.component_type:
        component = SimpleComponent.from_dict(payload)
    elif component_type == SimpleCard.component_type:
        component = SimpleCard.from_dict(payload)
    elif component_type == TwoSidedCard.component_type:
        component = TwoSidedCard.from_dict(payload)
    elif component_type == Component.component_type:
        component = Component.from_dict(payload)
    else:
        raise ValueError('unknown component type: {}'.format(component_type))
    return component
