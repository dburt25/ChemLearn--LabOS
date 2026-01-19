from scanner.board import BoardSpec, MarkerFamily


def test_board_spec_serialization_round_trip():
    spec = BoardSpec(
        family=MarkerFamily.ARUCO_4X4,
        rows=4,
        cols=6,
        marker_size_m=0.02,
        marker_spacing_m=0.005,
        board_id="board-test",
    )
    payload = spec.to_dict()
    restored = BoardSpec.from_dict(payload)
    assert restored == spec
