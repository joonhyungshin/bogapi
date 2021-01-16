from unittest import TestCase

from bogapi.game import SimpleCard, Game


class RockScissorPaper(Game):
    def setup(self):
        move0 = SimpleCard('move0', None)
        move1 = SimpleCard('move1', None)
        self.add_component(move0)
        self.add_component(move1)


class TestSimpleGames(TestCase):
    def test_rock_scissor_paper(self):
        pass
