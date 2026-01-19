from src.scanner.pose import AnchorPose, PoseQualityGates, evaluate_pose_quality, reject_outlier_poses


def _pose_with_error(index, error):
    return AnchorPose(
        frame_index=index,
        rvec=[0.0, 0.0, 0.0],
        tvec=[0.0, 0.0, 0.0],
        reproj_err_px=error,
        camera_position_m=[0.0, 0.0, 0.0],
        camera_rotation_matrix=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )


def test_outlier_rejection_removes_large_error():
    poses = [_pose_with_error(i, err) for i, err in enumerate([0.5, 0.6, 5.0, 0.55])]
    filtered = reject_outlier_poses(poses, sigma=2.0)
    assert len(filtered) == 3
    assert all(p.reproj_err_px < 1.0 for p in filtered)


def test_pose_quality_gates():
    poses = [_pose_with_error(i, 0.5) for i in range(12)]
    gates = PoseQualityGates(min_frames_with_pose=10, max_mean_reproj_err_px=1.0)
    ok, summary = evaluate_pose_quality(poses, gates)
    assert ok is True
    assert summary["frames_with_pose"] == 12
