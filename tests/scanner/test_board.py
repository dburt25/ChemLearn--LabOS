import pytest

from src.scanner.board import BoardSpec, generate_board_image

cv2 = pytest.importorskip("cv2")


def test_generate_board_image(tmp_path):
    if not hasattr(cv2, "aruco"):
        pytest.skip("cv2.aruco not available")
    spec = BoardSpec(
        family="aruco_4x4",
        rows=2,
        cols=2,
        marker_size_m=0.04,
        marker_spacing_m=0.01,
    )
    output = tmp_path / "board.png"
    generated = generate_board_image(spec, output, pixels_per_meter=1000)
    assert generated.exists()
    image = cv2.imread(str(generated), cv2.IMREAD_GRAYSCALE)
    assert image is not None
    assert image.shape[0] > 0
    assert image.shape[1] > 0
