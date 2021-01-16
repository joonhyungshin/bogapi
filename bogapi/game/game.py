from collections.abc import Iterable, Mapping
from typing import Any, Optional, Union

from bogapi.game.component import Component, RenderedComponent, _get_component_from_dict


class Game(object):
    def __init__(self):
        self._components = {}

    def add_component(self, component: Component, name: Optional[str] = None):
        self._components[name or component.name] = component

    def add_components(self, components: Union[Iterable[Component], Mapping[str, Component]]):
        for key in components:
            if isinstance(key, str):
                self.add_component(components[key], key)
            else:
                self.add_component(key)

    def render(self, pid: int = 0) -> Mapping[str, RenderedComponent]:
        rendered_components = {}
        for name in self._components:
            component = self._components[name]
            if component.visible_by(pid):
                rendered_components[name] = component.render(pid)
        return rendered_components

    def save_components_to_dict(self) -> Mapping[str, Mapping[str, Any]]:
        return {
            name: self._components[name].to_dict()
            for name in self._components
        }

    def load_components_from_dict(self, payload: Mapping[str, Mapping[str, Any]]):
        if set(self._components.keys()) != set(payload.keys()):
            raise ValueError('the game component names do not match')
        for name in self._components:
            self._components[name] = _get_component_from_dict(payload[name])

    def setup(self):
        raise NotImplementedError

    def __getattribute__(self, item):
        return self._components[item]
