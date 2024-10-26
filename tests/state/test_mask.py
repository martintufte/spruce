from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.state.mask import get_piece_mask


def test_get_piece_mask() -> None:
    for cube_size in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        for piece in (Piece.center, Piece.edge, Piece.corner):
            mask = get_piece_mask(piece=piece, cube_size=cube_size)
            assert mask.size == 6 * cube_size**2
