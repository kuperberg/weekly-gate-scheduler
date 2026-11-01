from custom_components.weekly_gate_scheduler.frontend import resource_url


def test_resource_url_is_versioned_and_stable():
    assert resource_url("0.1.7") == "/weekly_gate_scheduler/weekly-gate-scheduler-card.js?v=0.1.7"


def test_resource_url_rejects_unsafe_version():
    try:
        resource_url("0.1.0?bad=1")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe version accepted")
