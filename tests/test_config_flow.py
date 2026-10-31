"""Configuration validation tests."""

from dataclasses import dataclass

import pytest

from custom_components.weekly_gate_scheduler.config_flow import (
    RelayValidationError,
    build_entry_data,
    is_duplicate_relay,
    validate_relay_entity,
)


GATE_RELAY = "select.example_gate_relay_mode"


@dataclass
class FakeState:
    state: str
    attributes: dict


class FakeStates:
    def __init__(self, values):
        self._values = values

    def get(self, entity_id):
        return self._values.get(entity_id)


class FakeHass:
    def __init__(self, values):
        self.states = FakeStates(values)


def valid_hass(entity_id=GATE_RELAY):
    return FakeHass(
        {
            entity_id: FakeState(
                "normal", {"options": ["normal", "hold_open", "hold_closed"]}
            )
        }
    )


def test_accepts_and_persists_selected_relay_entity():
    assert validate_relay_entity(valid_hass(), GATE_RELAY) == GATE_RELAY
    assert build_entry_data(GATE_RELAY) == {"relay_entity_id": GATE_RELAY}


@pytest.mark.parametrize(
    ("hass", "entity_id", "error_key"),
    [
        (FakeHass({}), GATE_RELAY, "entity_not_found"),
        (valid_hass("switch.gate"), "switch.gate", "not_select"),
        (
            FakeHass(
                {
                    GATE_RELAY: FakeState(
                        "normal", {"options": ["normal", "hold_closed"]}
                    )
                }
            ),
            GATE_RELAY,
            "missing_options",
        ),
    ],
)
def test_rejects_invalid_relay_entities(hass, entity_id, error_key):
    with pytest.raises(RelayValidationError) as exc:
        validate_relay_entity(hass, entity_id)
    assert exc.value.translation_key == error_key


def test_detects_duplicate_relay_configuration():
    entries = [
        {"data": {"relay_entity_id": "select.other_gate_relay_mode"}},
        {"data": {"relay_entity_id": GATE_RELAY}},
    ]
    assert is_duplicate_relay(entries, GATE_RELAY)
    assert not is_duplicate_relay(entries, "select.third_gate_relay_mode")


def test_configured_value_is_not_replaced_by_a_default():
    chosen = "select.example_relay_mode"
    assert validate_relay_entity(valid_hass(chosen), chosen) == chosen
    assert build_entry_data(chosen)["relay_entity_id"] == chosen
