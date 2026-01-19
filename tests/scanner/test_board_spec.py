from scanner.board import BoardSpec, MarkerFamily


def test_board_spec_round_trip():
    spec = BoardSpec(
        family=MarkerFamily.ARUCO_4X4,
        rows=3,
        cols=5,
        marker_size_m=0.02,
        marker_spacing_m=0.005,
        origin_definition="board_center",
        board_id="unit-test",
    )
    payload = spec.to_dict()
    rehydrated = BoardSpec.from_dict(payload)

    assert rehydrated == spec
    assert rehydrated.board_center_m == (spec.board_width_m / 2.0, spec.board_height_m / 2.0, 0.0)
