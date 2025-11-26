import pytest

from labos.api.adapters import (
    DummyPropertyPredictor,
    DummySpectrumPredictor,
    get_default_property_predictor,
    get_default_spectrum_predictor,
)
from labos.api.interfaces import ExternalPropertyPredictor, ExternalSpectrumPredictor, PropertyRequest, SpectrumRequest


_NOT_IMPLEMENTED_MESSAGE = "External integration not implemented in Phase 2.5.3."


def test_dummy_predictors_are_subclasses():
    assert issubclass(DummySpectrumPredictor, ExternalSpectrumPredictor)
    assert issubclass(DummyPropertyPredictor, ExternalPropertyPredictor)


@pytest.mark.parametrize(
    "predictor_cls, payload, method_name",
    [
        (DummySpectrumPredictor, SpectrumRequest("MS", [0.1, 0.2]), "predict_spectrum"),
        (
            DummyPropertyPredictor,
            PropertyRequest("CCO", ["logP", "pKa"]),
            "predict_properties",
        ),
    ],
)
def test_predict_methods_raise_not_implemented(predictor_cls, payload, method_name):
    predictor = predictor_cls()

    with pytest.raises(NotImplementedError, match=_NOT_IMPLEMENTED_MESSAGE):
        getattr(predictor, method_name)(payload)


@pytest.mark.parametrize("predictor_cls", [DummySpectrumPredictor, DummyPropertyPredictor])
def test_generic_predict_raises_not_implemented(predictor_cls):
    predictor = predictor_cls()

    with pytest.raises(NotImplementedError, match=_NOT_IMPLEMENTED_MESSAGE):
        predictor.predict(inputs={"feature": 1.0})


@pytest.mark.parametrize("predictor_cls", [DummySpectrumPredictor, DummyPropertyPredictor])
def test_close_raises_not_implemented(predictor_cls):
    predictor = predictor_cls()

    with pytest.raises(NotImplementedError, match=_NOT_IMPLEMENTED_MESSAGE):
        predictor.close()


@pytest.mark.parametrize(
    "factory, expected_type",
    [
        (get_default_spectrum_predictor, DummySpectrumPredictor),
        (get_default_property_predictor, DummyPropertyPredictor),
    ],
)
def test_default_factories_return_stub(factory, expected_type):
    predictor = factory()
    assert isinstance(predictor, expected_type)
