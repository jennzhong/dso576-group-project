"""Exercise the Streamlit app with the canonical data and real widget changes."""
from pathlib import Path
from datetime import date

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def app():
    result = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not result.exception
    return result


def widget(elements, label):
    return next(element for element in elements if element.label == label)


def test_default_cards_and_capped_listeners():
    at = app()
    assert [tab.label for tab in at.tabs] == ["Shortlist", "Artist detail", "Listeners"]
    assert [metric.value for metric in at.tabs[0].metric[:4]] == ["5", "669", "1,882", "677"]
    assert at.tabs[0].dataframe[0].value.iloc[0]["display_name"] == "Arthrn"
    listeners = at.tabs[2].dataframe[0].value["username"]
    assert len(listeners) == 5
    assert listeners.str.endswith("· capped").sum() == 3
    assert any("n/a" in set(table.value.get("return_momentum", [])) for table in at.dataframe)


def test_shortlist_filters_do_not_change_cards_or_listeners():
    at = app()
    widget(at.number_input, "Min avg active days").set_value(2.0).run()
    assert not at.exception
    assert len(at.tabs[0].dataframe[0].value) == 168
    assert at.tabs[0].metric[1].value == "669"
    assert len(at.tabs[2].dataframe[0].value) == 5


def test_empty_listener_selection_is_handled_in_every_tab():
    at = app()
    widget(at.multiselect, "Listeners").set_value([]).run()
    assert not at.exception
    assert len([info for info in at.info if info.value == "No listens in this period"]) == 3
    assert not at.dataframe


def test_period_without_observations_is_handled_in_every_tab():
    at = app()
    widget(at.date_input, "Date range (UTC)").set_value((date(2021, 1, 1), date(2021, 1, 31))).run()
    assert not at.exception
    assert len([info for info in at.info if info.value == "No listens in this period"]) == 3
    assert not at.dataframe


def test_empty_shortlist_keeps_listener_view_available():
    at = app()
    widget(at.number_input, "Min listens").set_value(10000).run()
    assert not at.exception
    assert "No artists match these filters" in [info.value for info in at.info]
    assert "No artist selected" in [info.value for info in at.info]
    assert len(at.tabs[2].dataframe[0].value) == 5


def test_name_only_artists_and_selection_fallback():
    at = app()
    widget(at.selectbox, "MBID status").set_value("no_mbid").run()
    assert not at.exception
    selected = at.session_state["selected_artist"]
    assert selected.startswith("name:")
    assert "n/a — no MBID" in [info.value for info in at.info]
    widget(at.multiselect, "Exclude artists").set_value([selected]).run()
    assert not at.exception
    assert at.session_state["selected_artist"] != selected
    assert selected not in set(at.tabs[0].dataframe[0].value["artist_id"])


def test_listener_filter_changes_all_tab_data():
    at = app()
    widget(at.multiselect, "Listeners").set_value(["H-music"]).run()
    assert not at.exception
    assert at.tabs[0].metric[0].value == "1"
    assert at.tabs[2].dataframe[0].value["username"].tolist() == ["H-music · capped"]
    assert at.tabs[1].dataframe[0].value["username"].tolist() == ["H-music · capped"]
