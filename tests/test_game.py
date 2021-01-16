from unittest import TestCase

from bogapi.game import Component, SimpleComponent, Game, NumericData


class RockScissorPaper(Game):
    def __init__(self):
        self.moves = [
            SimpleComponent('move1'),
            SimpleComponent('move2')
        ]
        self.board = Component('board', data={
            'score1': NumericData(0, public=True),
            'score2': NumericData(0, public=True)
        })
        self.moves[0].own_by(1)
        self.moves[1].own_by(2)
        super(RockScissorPaper, self).__init__()

    def setup(self):
        self.add_components([self.moves[0], self.moves[1], self.board])

    def verify_move(self, pid, move) -> bool:
        if pid not in [1, 2] or move not in [0, 1, 2]:
            return False
        return self.moves[pid - 1].content is None

    def apply_move(self, pid, move):
        component = self.moves[pid - 1]
        other = self.moves[2 - pid]
        if component.content is None:
            component.set_content(move)
            if other.content is not None:
                other_move = other.content
                if (move + 1) % 3 == other_move:
                    self.board.data['score{}'.format(pid)].content += 1
                elif (other_move + 1) % 3 == move:
                    self.board.data['score{}'.format(3 - pid)].content += 1
                component.set_content(None)
                other.set_content(None)

    def move_candidates(self, pid):
        if self.verify_move(pid, 0):
            return [0, 1, 2]
        else:
            return []


class TestSimpleGames(TestCase):
    def test_rock_scissor_paper(self):
        game = RockScissorPaper()
        game.setup()
        self.assertTrue(game.verify_move(1, 0))
        game.apply_move(1, 0)
        state = game.render(2)
        self.assertDictEqual(state['move1'].data, {})
        self.assertFalse(game.verify_move(1, 1))
        self.assertListEqual(list(game.move_candidates(1)), [])
        self.assertListEqual(list(game.move_candidates(2)), [0, 1, 2])
        game.apply_move(2, 1)
        self.assertEqual(game.board.data['score1'].content, 1)
        self.assertEqual(game.board.data['score2'].content, 0)
