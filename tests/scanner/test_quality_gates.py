from scanner.quality_gates import QualityGateConfig, evaluate_quality_gates


def test_quality_gates_pass():
    errors = [1.0] * 12
    config = QualityGateConfig(min_frames_with_pose=10, max_mean_reproj_err_px=2.0, max_p95_reproj_err_px=4.0)

    passed, reason, stats = evaluate_quality_gates(errors, config)

    assert passed is True
    assert reason is None
    assert stats.accepted_frame_count == 12


def test_quality_gates_fail_on_mean():
    errors = [5.0] * 12
    config = QualityGateConfig(min_frames_with_pose=10, max_mean_reproj_err_px=2.0, max_p95_reproj_err_px=4.0)

    passed, reason, _ = evaluate_quality_gates(errors, config)

    assert passed is False
    assert reason == "mean_reproj_error"
