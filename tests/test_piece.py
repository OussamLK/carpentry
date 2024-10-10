from solver import Piece


def test_parser():
    p_str = "23.5x44r"
    p = Piece.parse_piece(p_str)
    assert p.height == 23.5, f"piece `{
        p_str}` height should be 23.5 but is {p.height}"
    assert p.width == 44.0, f"piece `{
        p_str} width should be 44 but is {p.width}"
    assert p.can_rotate, f"piece `{p_str}` should be able to rotate"
