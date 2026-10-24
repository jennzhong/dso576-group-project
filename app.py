"""Streamlit dashboard for emerging artist discovery."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "member5-aggregations"))

import aggregation_functions as m5  # noqa: E402
import kpi_analysis as kpi  # noqa: E402

CAPPED_USERS = {"H-music", "iliekcomputers", "s_john_s"}


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    return kpi.load_listens()


@st.cache_data(show_spinner=False)
def calculate_shortlist(listens: pd.DataFrame, min_listens: int,
                        min_days: float, max_listeners: int | None,
                        mbid_status: str, excluded: tuple[str, ...]):
    pairs = kpi.pair_kpis(listens)
    artists = kpi.artist_kpis(listens)
    headline = kpi.headline_kpis(listens, pairs, artists)
    shortlist = kpi.apply_emerging_filter(
        artists, kpi.EmergingFilter(min_listens, min_days, max_listeners,
                                    mbid_status, excluded))
    return pairs, artists, headline, shortlist


def display_artist(artists: pd.DataFrame, artist_id: str) -> str:
    name = artists.loc[artists.artist_id.eq(artist_id), "display_name"]
    if name.empty:
        return artist_id
    duplicates = artists.display_name.eq(name.iloc[0]).sum() > 1
    return f"{name.iloc[0]} [{artist_id[:8]}]" if duplicates else str(name.iloc[0])


def fmt_rate(value) -> str:
    return "n/a" if pd.isna(value) else f"{value:.1%}"


def fmt_momentum(value) -> str:
    return "n/a" if pd.isna(value) else f"{value:.2f}"


def marked_user(username: str) -> str:
    return f"{username} · capped" if username in CAPPED_USERS else username


def main() -> None:
    st.set_page_config(page_title="Emerging Artist Discovery", layout="wide")
    st.title("Emerging Artist Discovery")
    st.caption("Shortlist artists by repeat engagement in the sampled ListenBrainz histories.")

    listens = load_data()
    first_day = listens.listen_day.min().date()
    last_day = listens.listen_day.max().date()
    user_options = sorted(listens.username.unique().tolist())
    labels = {user: marked_user(user) for user in user_options}

    with st.sidebar:
        st.header("Filters")
        date_range = st.date_input("UTC date range", value=(first_day, last_day),
                                   min_value=first_day, max_value=last_day)
        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start, end = date_range
        else:
            start = end = date_range
        selected_users = st.multiselect("Listeners", user_options,
                                        default=user_options,
                                        format_func=lambda x: labels[x])
        st.subheader("Shortlist filters")
        min_listens = st.number_input("Minimum countable listens", min_value=1,
                                      value=1, step=1)
        min_days = st.number_input("Minimum average active days", min_value=1.0,
                                   value=1.0, step=0.5)
        max_listeners = st.number_input("Maximum listeners (0 = no limit)",
                                        min_value=0, value=0, step=1)
        mbid_status = st.selectbox("MBID status", ["any", "mbid", "no_mbid"],
                                   format_func={"any": "Any", "mbid": "Has MBID",
                                                "no_mbid": "No MBID"}.get)

    period = kpi.filter_period(listens, start, end, selected_users)
    if period.empty:
        st.info("No listens in this period")
        return

    pairs, artists, headline, _ = calculate_shortlist(
        period, int(min_listens), float(min_days),
        int(max_listeners) if max_listeners else None, mbid_status, ())
    eligible = kpi.apply_emerging_filter(
        artists, kpi.EmergingFilter(int(min_listens), float(min_days),
                                    int(max_listeners) if max_listeners else None,
                                    mbid_status, ()))
    labels_by_id = {row.artist_id: display_artist(artists, row.artist_id)
                    for row in artists.itertuples()}
    with st.sidebar:
        exclude_labels = st.multiselect(
            "Exclude artists", options=artists.artist_id.tolist(),
            format_func=lambda artist_id: labels_by_id[artist_id],
            help="Choose established artists to remove from the shortlist.")
    if exclude_labels:
        shortlist = kpi.apply_emerging_filter(
            artists, kpi.EmergingFilter(int(min_listens), float(min_days),
                                        int(max_listeners) if max_listeners else None,
                                        mbid_status, tuple(exclude_labels)))
    else:
        shortlist = eligible

    st.session_state.setdefault("selected_artist_id", None)
    tabs = st.tabs(["Shortlist", "Artist detail", "Listeners"])

    with tabs[0]:
        st.subheader("Selection overview")
        kpis = [
            ("Listeners", headline["listeners"]), ("Artists", headline["artists"]),
            ("Countable listens", headline["countable_listens"]),
            ("Listener–artist pairs", headline["listener_artist_pairs"]),
            ("Pair return rate", fmt_rate(headline["pair_return_rate"])),
            ("Artists with a return", fmt_rate(headline["pct_artists_with_return"])),
            ("Artists with momentum", headline["artists_with_momentum"]),
        ]
        cols = st.columns(len(kpis))
        for col, (label, value) in zip(cols, kpis):
            col.metric(label, value)
        st.subheader("Ranked artist shortlist")
        st.caption("Return rate is the share of listener–artist pairs played on at least two distinct UTC days.")
        st.caption("Momentum is shown as n/a when there is not enough return history.")
        if shortlist.empty:
            st.info("No artists match these filters")
        else:
            table = shortlist.copy()
            table["display_name"] = table.artist_id.map(labels_by_id)
            table["return_rate"] = table.return_rate.map(fmt_rate)
            table["return_momentum"] = table.return_momentum.map(fmt_momentum)
            table = table[["rank", "display_name", "artist_id", "countable_listens",
                           "unique_listeners", "return_rate", "avg_active_days",
                           "distinct_tracks", "median_days_to_return", "return_momentum"]]
            event = st.dataframe(table, hide_index=True, width="stretch",
                                 on_select="rerun", selection_mode="single-row")
            selected = event.selection.rows
            if selected:
                st.session_state.selected_artist_id = shortlist.iloc[selected[0]].artist_id
            st.caption(f"{len(shortlist)} of {len(artists)} artists match the shortlist filters")

    with tabs[1]:
        st.subheader("Artist detail")
        if shortlist.empty:
            st.info("No artist selected")
        else:
            ids = shortlist.artist_id.tolist()
            selected_id = st.session_state.selected_artist_id
            if selected_id not in ids:
                selected_id = shortlist.iloc[0].artist_id
                st.session_state.selected_artist_id = selected_id
            if st.session_state.get("_last_selected_artist_id") != selected_id:
                st.session_state.artist_picker = selected_id
                st.session_state._last_selected_artist_id = selected_id
            artist_id = st.selectbox("Artist", ids,
                                     format_func=lambda x: labels_by_id[x],
                                     key="artist_picker")
            st.session_state.selected_artist_id = artist_id
            detail = kpi.artist_detail(period, artist_id)
            summary = detail.summary
            metrics = [
                ("Countable listens", int(summary.countable_listens)),
                ("Listeners", int(summary.unique_listeners)),
                ("Return rate", fmt_rate(summary.return_rate)),
                ("Average active days", f"{summary.avg_active_days:.1f}"),
                ("Distinct tracks", int(summary.distinct_tracks)),
                ("Return momentum", fmt_momentum(summary.return_momentum)),
            ]
            cols = st.columns(len(metrics))
            for col, (label, value) in zip(cols, metrics):
                col.metric(label, value)

            events = m5.build_artist_listen_events(period)
            if str(artist_id).startswith("name:"):
                st.caption("30-day return and monthly chart: n/a — no MBID")
            else:
                engagement = m5.build_artist_engagement(events)
                row = engagement.loc[engagement.artist_mbid.eq(artist_id)]
                if not row.empty:
                    vals = row.iloc[0]
                    artist_rows = period.loc[period.artist_id.eq(artist_id)]
                    borrowed_rows = artist_rows.artist_id_source.eq("key_mbid").sum()
                    m5_events = events.loc[events.artist_mbid.eq(artist_id), "listen_event_id"].nunique()
                    c1, c2, c3 = st.columns(3)
                    if borrowed_rows > len(artist_rows) / 2:
                        c1.metric("30-day return rate", "n/a")
                        c1.caption("Most M4 listens use a borrowed artist ID; M5 has no direct MBID match for them.")
                    else:
                        c1.metric("30-day return rate", f"{vals.return_rate_pct:.1f}%")
                    c1.caption(f"M5: {m5_events} MBID-matched artist events; M4 assigns {len(artist_rows)} listen rows.")
                    c2.metric("Listeners with 3+ active days", f"{vals.share_3plus_days_pct:.1f}%")
                    c3.metric("Listeners with 3+ tracks", f"{vals.share_3plus_tracks_pct:.1f}%")
                monthly = m5.build_artist_monthly_growth(events)
                monthly = monthly.loc[monthly.artist_mbid.eq(artist_id)]
                if not monthly.empty:
                    fig = px.bar(monthly, x="month", y="total_listens",
                                 hover_data={"unique_listeners": True, "month": True},
                                 labels={"month": "Month", "total_listens": "All logged listens"})
                    st.plotly_chart(fig, width="stretch")
                evidence_users = ", ".join(
                    marked_user(user) for user in detail.listeners.username.tolist())
                st.caption(
                    f"MBID-matched listens. M5 uses all logged listens. "
                    f"Listeners represented: {evidence_users or 'none'}. "
                    "These sampled histories are non-overlapping."
                )

            st.markdown("**Listeners**")
            listener_table = detail.listeners.copy()
            listener_table["username"] = listener_table.username.map(marked_user)
            listener_table["return_momentum"] = listener_table.return_momentum.map(fmt_momentum)
            listener_table = listener_table[["username", "countable_listens", "active_days",
                                             "days_to_return", "return_momentum"]]
            st.dataframe(listener_table, hide_index=True, width="stretch")
            st.markdown("**Tracks**")
            st.dataframe(detail.tracks, hide_index=True, width="stretch")

    with tabs[2]:
        st.subheader("Listener engagement")
        listener_stats = m5.build_listener_engagement(period)
        listener_stats["username"] = listener_stats.username.map(marked_user)
        listener_stats = listener_stats.rename(columns={"first_listen": "first_observed_listen",
                                                        "last_listen": "last_observed_listen"})
        listener_stats["first_observed_listen"] = pd.to_datetime(listener_stats.first_observed_listen).dt.strftime("%Y-%m-%d")
        listener_stats["last_observed_listen"] = pd.to_datetime(listener_stats.last_observed_listen).dt.strftime("%Y-%m-%d")
        st.dataframe(listener_stats[["username", "total_listens", "first_observed_listen",
                                     "last_observed_listen", "observation_days", "active_days",
                                     "unique_artists", "listens_per_active_day", "repeat_listen_pct"]],
                     hide_index=True, width="stretch")
        st.caption("First observed listen; last listen may be truncated for capped listeners. M5 totals include all logged listens.")
        daily = m5.build_daily_activity(period)
        for username in sorted(daily.username.unique()):
            user_daily = daily.loc[daily.username.eq(username)]
            with st.expander(marked_user(username), expanded=False):
                fig = px.line(user_daily, x="date", y=["total_listens", "unique_artists"],
                              labels={"date": "Date in this listener's window", "value": "Daily count",
                                      "variable": "Measure"})
                st.plotly_chart(fig, width="stretch")
        monthly_coverage = m5.build_audience_growth(period)
        if not monthly_coverage.empty:
            fig = px.bar(monthly_coverage, x="month", y="active_listeners",
                         labels={"month": "Month", "active_listeners": "Active listeners"},
                         title="Sampled listeners active per month")
            st.plotly_chart(fig, width="stretch")


if __name__ == "__main__":
    main()
