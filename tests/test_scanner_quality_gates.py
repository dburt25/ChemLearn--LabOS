from scanner.quality_gates import QualityGateConfig, evaluate_quality_gates


def test_quality_gates_pass():
    config = QualityGateConfig(min_frames_with_pose=10, max_mean_reproj_err_px=2.0, max_p95_reproj_err_px=4.0)
    errors = [1.2] * 12
    result = evaluate_quality_gates(errors, config)
    assert result.passed
    assert result.failure_reasons == []


def test_quality_gates_fail_on_reproj():
    config = QualityGateConfig(min_frames_with_pose=5, max_mean_reproj_err_px=2.0, max_p95_reproj_err_px=4.0)
    errors = [1.0, 2.0, 3.0, 5.5, 6.0]
    result = evaluate_quality_gates(errors, config)
    assert not result.passed
    assert "max_mean_reproj_err_px" in result.failure_reasons or "max_p95_reproj_err_px" in result.failure_reasons
