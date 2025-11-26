from labos.modules.spectroscopy import (
    IRResult,
    NMRResult,
    analyze_ir_spectrum,
    analyze_nmr_spectrum,
)


def test_analyze_nmr_spectrum_detects_aromatic_peak():
    spectrum = [(1.2, 0.1), (7.1, 0.9)]

    result = analyze_nmr_spectrum(spectrum)

    assert isinstance(result, NMRResult)
    assert result.peaks, "Expected at least one detected peak"
    assert any(peak["annotation"] == "within aromatic window" for peak in result.peaks)
    assert result.integration_suggestions
    assert result.notes


def test_analyze_ir_spectrum_detects_carbonyl_hint_from_mapping():
    spectrum = {"wavenumber": [1705.0, 2900.0], "absorbance": [0.8, 0.4]}

    result = analyze_ir_spectrum(spectrum, params={"threshold": 0.5})

    assert isinstance(result, IRResult)
    assert result.peaks, "Expected at least one detected band"
    assert any("carbonyl" in hint.lower() for hint in result.functional_group_hints)
    assert result.notes
