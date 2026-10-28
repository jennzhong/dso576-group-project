"""Streamlit UI for BUILD_SPEC.md; all metrics come from the M4/M5 backends."""
from pathlib import Path
import hashlib
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "member5-aggregations"))
import aggregation_functions as m5
import kpi_analysis as kpi

CAPPED = {"H-music", "iliekcomputers", "s_john_s"}


def section_heading(number, title):
    st.markdown(f'<div class="section-heading"><div class="eyebrow">{number} / OVERVIEW</div>'
                f'<h2>{title}</h2></div>', unsafe_allow_html=True)


def style_chart(figure):
    """Presentation only: preserve every trace and value from the backends."""
    figure.update_layout(
        template="plotly_white", paper_bgcolor="#fffef9", plot_bgcolor="#fffef9",
        font={"family": "Arial, sans-serif", "size": 11, "color": "#687267"},
        title={"font": {"family": "Georgia, serif", "size": 22, "color": "#263c30"}, "x": 0.04},
        colorway=["#355c4b", "#b88d70"],
        margin={"l": 45, "r": 24, "t": 65, "b": 40},
        legend={"orientation": "h", "y": -0.2, "title_text": ""},
        hoverlabel={"bgcolor": "#fffef9", "font_color": "#263c30"},
    )
    for index, trace in enumerate(figure.data):
        color = ["#355c4b", "#b88d70"][index % 2]
        if trace.type == "bar":
            trace.update(marker_color=color, marker_line_width=0)
        elif trace.type == "scatter":
            trace.update(line_color=color, marker_color=color, line_width=2)
    figure.update_xaxes(gridcolor="#edeee7", zeroline=False, linecolor="#dde0d5")
    figure.update_yaxes(gridcolor="#edeee7", zeroline=False)
    return figure


@st.cache_data(show_spinner=False)
def load_data():
    return kpi.load_listens()


@st.cache_data(show_spinner=False)
def selection_data(start, end, users):
    listens = kpi.filter_period(load_data(), start, end, users)
    if listens.empty:
        return {"listens": listens}
    pairs = kpi.pair_kpis(listens)
    artists = kpi.artist_kpis(listens)
    events = m5.build_artist_listen_events(listens)
    return {
        "listens": listens,
        "artists": artists,
        "headline": kpi.headline_kpis(listens, pairs, artists),
        "listeners": m5.build_listener_engagement(listens),
        "daily": m5.build_daily_activity(listens),
        "coverage": m5.build_audience_growth(listens),
        "engagement": m5.build_artist_engagement(events) if not events.empty else pd.DataFrame(),
        "monthly": m5.build_artist_monthly_growth(events) if not events.empty else pd.DataFrame(),
    }


@st.cache_data(show_spinner=False)
def detail_data(listens, artist_id):
    return kpi.artist_detail(listens, artist_id)


def listener_label(username):
    return f"{username} · capped" if username in CAPPED else username


def artist_labels(artists):
    duplicates = artists["display_name"].duplicated(keep=False)
    return {
        row.artist_id: (f"{row.display_name} ({row.artist_id[:8]})" if duplicate else row.display_name)
        for row, duplicate in zip(artists.itertuples(), duplicates)
    }


def number(value, decimals=0, percent=False):
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:.1%}" if percent else f"{value:,.{decimals}f}"


def display_table(frame, rates=(), percentages=(), decimals=None, dates=(), listeners=False):
    """Format backend values for display only; missing values stay explicit."""
    table = frame.copy()
    for column in rates:
        table[column] = table[column].map(lambda value: number(value, percent=True))
    for column in percentages:
        table[column] = table[column].map(lambda value: "n/a" if pd.isna(value) else f"{value:.1f}%")
    for column, places in (decimals or {}).items():
        table[column] = table[column].map(lambda value: number(value, places))
    for column in dates:
        table[column] = pd.to_datetime(table[column], utc=True).dt.strftime("%Y-%m-%d")
    if listeners:
        table["username"] = table["username"].map(listener_label)
    return table


def artist_metrics(summary):
    fields = [
        ("Countable listens", "countable_listens", 0, False),
        ("Listeners", "unique_listeners", 0, False),
        ("Return rate", "return_rate", 1, True),
        ("Avg active days", "avg_active_days", 2, False),
        ("Distinct tracks", "distinct_tracks", 0, False),
        ("Return momentum", "return_momentum", 2, False),
    ]
    for col, (label, key, decimals, percent) in zip(st.columns(6), fields):
        col.metric(label, number(summary[key], decimals, percent))


def render_shortlist(data, shortlist, table_key):
    headline = data["headline"]
    section_heading("01", "Find artists listeners return to")
    fields = [
        ("Listeners", "listeners", False),
        ("Artists", "artists", False),
        ("Countable listens", "countable_listens", False),
        ("Listener–artist pairs", "listener_artist_pairs", False),
        ("Pair return rate", "pair_return_rate", True),
        ("Artists with a return", "pct_artists_with_return", True),
        ("Artists with momentum", "artists_with_momentum", False),
    ]
    for offset, columns in ((0, st.columns(4)), (4, st.columns(3))):
        for col, (label, key, percent) in zip(columns, fields[offset:]):
            col.metric(label, number(headline[key], percent=percent))
    st.caption("Cards describe the date/listener selection. Shortlist filters affect only the ranked table and artist picker.")
    st.markdown("#### Ranked artists")
    st.caption("Ranked by return rate, average active days, countable listens, then momentum. Select a row, then open Artist detail.")
    if shortlist.empty:
        st.info("No artists match these filters")
    else:
        columns = ["rank", "display_name", "countable_listens", "unique_listeners", "return_rate",
                   "avg_active_days", "distinct_tracks", "median_days_to_return", "return_momentum", "artist_id"]
        table = display_table(shortlist[columns], rates=("return_rate",),
                              decimals={"avg_active_days": 2, "median_days_to_return": 1, "return_momentum": 2})

        def select_row():
            rows = st.session_state[table_key]["selection"]["rows"]
            if rows:
                st.session_state["selected_artist"] = shortlist.iloc[rows[0]]["artist_id"]

        st.dataframe(table, hide_index=True, use_container_width=True, height=430,
                     key=table_key, on_select=select_row, selection_mode="single-row",
                     column_config={
                         "display_name": st.column_config.TextColumn("Artist"),
                         "artist_id": st.column_config.TextColumn("Artist ID", help="Stable identity used for selections; names can overlap."),
                     })
    st.caption(f"{len(shortlist)} of {len(data['artists'])} artists match the shortlist filters")


def render_artist(data, shortlist):
    section_heading("02", "Artist detail")
    if shortlist.empty:
        st.session_state.pop("selected_artist", None)
        st.info("No artist selected")
        return
    options = shortlist["artist_id"].tolist()
    if st.session_state.get("selected_artist") not in options:
        st.session_state["selected_artist"] = options[0]
    labels = artist_labels(shortlist)
    artist_id = st.selectbox("Artist", options, format_func=labels.get, key="selected_artist")
    detail = detail_data(data["listens"], artist_id)
    artist_metrics(detail.summary)
    st.caption(f"Artist ID: {artist_id} · First observed listen: {detail.summary['first_listen_utc']:%Y-%m-%d}")
    st.markdown("#### 30-day return and depth")
    st.caption("MBID-matched listens · all logged listens. These figures use each row's own MBID and exclude name-only identity matches.")
    if artist_id.startswith("name:"):
        st.info("n/a — no MBID")
    else:
        engagement = data["engagement"]
        match = engagement.loc[engagement["artist_mbid"] == artist_id] if not engagement.empty else engagement
        if match.empty:
            st.info("n/a — no MBID-matched listens in this selection")
        else:
            for col, (label, field) in zip(st.columns(3), [
                ("Return within 30 days", "return_rate_pct"),
                ("Listeners on 3+ days", "share_3plus_days_pct"),
                ("Listeners with 3+ tracks", "share_3plus_tracks_pct"),
            ]):
                col.metric(label, f"{match.iloc[0][field]:.1f}%")
        monthly = data["monthly"]
        monthly = monthly.loc[monthly["artist_mbid"] == artist_id] if not monthly.empty else monthly
        if not monthly.empty:
            figure = px.bar(monthly, x="month", y="total_listens", hover_data=["unique_listeners"],
                            title="Monthly listening for this artist", labels={"month": "Month (UTC)", "total_listens": "All logged listens"})
            st.plotly_chart(style_chart(figure), use_container_width=True, theme=None)
            st.caption("MBID-matched listens · all logged listens. Listeners: " +
                       ", ".join(detail.listeners["username"].map(listener_label)) +
                       ". Separate observation windows; this is listener evidence, not a market trend.")
    st.markdown("#### Listeners driving this artist")
    listener_columns = ["username", "countable_listens", "active_days", "days_to_return", "return_momentum"]
    st.dataframe(display_table(detail.listeners[listener_columns], listeners=True,
                              decimals={"days_to_return": 1, "return_momentum": 2}),
                 hide_index=True, use_container_width=True)
    st.markdown("#### Tracks")
    st.dataframe(display_table(detail.tracks, dates=("first_listen_utc", "last_listen_utc")).rename(
        columns={"first_listen_utc": "first_observed_listen", "last_listen_utc": "last_observed_listen"}),
        hide_index=True, use_container_width=True)


def render_listeners(data):
    section_heading("03", "Understand the listeners behind the sample")
    st.caption("All logged listens. Each listener has a different observation window; a capped history is truncated, not an end of engagement.")
    columns = ["username", "total_listens", "first_listen", "last_listen", "observation_days", "active_days",
               "unique_artists", "listens_per_active_day", "repeat_listen_pct"]
    table = display_table(data["listeners"][columns], listeners=True,
                          percentages=("repeat_listen_pct",), decimals={"listens_per_active_day": 2},
                          dates=("first_listen", "last_listen"))
    table = table.rename(columns={"first_listen": "first_observed_listen", "last_listen": "last_observed_listen"})
    st.dataframe(table, hide_index=True, use_container_width=True)
    users = data["listeners"]["username"].tolist()
    user = st.selectbox("Daily activity listener", [None] + users,
                        format_func=lambda value: "All selected listeners" if value is None else listener_label(value))
    for username in users if user is None else [user]:
        daily = data["daily"].loc[data["daily"]["username"] == username]
        figure = px.line(daily, x="date", y=["total_listens", "unique_artists"], markers=True,
                         title=listener_label(username), labels={"date": "Date (UTC)", "value": "Count", "variable": "Metric"})
        st.plotly_chart(style_chart(figure), use_container_width=True, theme=None)
        st.caption("All logged listens · each chart uses this listener's own dates. Only observed days are plotted; lines connect observations.")
    coverage = px.bar(data["coverage"], x="month", y="active_listeners", title="Sampled listeners active per month",
                      labels={"month": "Month (UTC)", "active_listeners": "Sampled listeners"})
    coverage.update_yaxes(dtick=1)
    st.plotly_chart(style_chart(coverage), use_container_width=True, theme=None)
    st.caption("Observation coverage across the sample, not audience growth or a market trend.")


def main():
    st.set_page_config(page_title="Emerging Artist Discovery", page_icon="🎵", layout="wide", initial_sidebar_state="expanded")
    st.markdown(f"<style>{(ROOT / 'dashboard.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    listens = load_data()
    first = listens["listened_at_utc"].min().date()
    last = listens["listened_at_utc"].max().date()
    all_users = sorted(listens["username"].unique())
    with st.sidebar:
        st.markdown('''<div class="atlas-brand"><span class="atlas-mark">✳</span>
            <span class="atlas-wordmark">DISCOVERY<br>ATLAS</span></div>
            <div class="atlas-edition">LISTENBRAINZ · DSO 576</div>
            <div class="atlas-nav-label">EXPLORE THE SAMPLE</div>''', unsafe_allow_html=True)
        st.markdown(f'''<div class="atlas-footer"><strong>A smaller sample. A closer listen.</strong><br>
            {first:%Y}–{last:%Y} · Historical listening records<br>Repeat engagement, not popularity.</div>''', unsafe_allow_html=True)
    st.markdown('''<div class="research-masthead"><span>RESEARCH DASHBOARD / LISTENING BEHAVIOR</span>
        <span>DSO 576 &nbsp; / &nbsp; PHASE 3</span></div>''', unsafe_allow_html=True)
    st.markdown(f'''<div class="atlas-hero"><div><div class="eyebrow">EMERGING ARTISTS · REPEAT ENGAGEMENT</div>
        <h1>Emerging Artist <em>Discovery.</em></h1>
        <p class="hero-description">Discover artists through repeat engagement, active listening days, and return momentum.</p></div>
        <div class="atlas-coverage"><strong>{first:%Y} — {last:%Y}</strong><small>DATA COVERAGE · UTC</small></div></div>''', unsafe_allow_html=True)
    st.info("Small sample: 5 listeners observed in different periods. Results describe these listeners, not artist popularity. Capped histories are truncated.")
    with st.container(border=True, key="filter-toolbar"):
        period_col, listener_col = st.columns([1.1, 2.4], gap="large")
        with period_col:
            dates = st.date_input("Date range (UTC)", value=(first, last), min_value=first, max_value=last, format="YYYY-MM-DD")
        with listener_col:
            users = st.multiselect("Listeners", all_users, default=all_users, format_func=listener_label)
        st.caption("Dates and listeners apply to every tab.")
    shortlist_panel = st.expander("Shortlist filters", expanded=False)
    with shortlist_panel:
        st.caption("Apply to ranked artists and the artist picker only.")
        controls = st.columns(4)
        with controls[0]:
            min_listens = st.number_input("Min listens", min_value=1, value=1, step=1)
        with controls[1]:
            min_days = st.number_input("Min avg active days", min_value=1.0, value=1.0, step=0.5)
        with controls[2]:
            max_listeners = st.number_input("Max listeners", min_value=1, max_value=len(all_users), value=len(all_users))
            limit = st.checkbox("Limit maximum listeners", value=False)
        with controls[3]:
            mbid_status = st.selectbox("MBID status", ["any", "mbid", "no_mbid"],
                                       format_func={"any": "Any", "mbid": "Has MBID", "no_mbid": "No MBID"}.get)
    tabs = st.tabs(["Shortlist", "Artist detail", "Listeners"])
    if len(dates) != 2:
        for tab in tabs:
            tab.info("Select a start and end date")
        return
    data = selection_data(dates[0], dates[1], tuple(sorted(users)))
    if data["listens"].empty:
        for tab in tabs:
            tab.info("No listens in this period")
        return
    artists = data["artists"]
    labels = artist_labels(artists)
    with shortlist_panel:
        excluded = st.multiselect("Exclude artists", artists["artist_id"].tolist(), format_func=labels.get)
        st.caption("Emerging means the curator's shortlist criteria and exclude list; no popularity metadata is available.")
    shortlist = kpi.apply_emerging_filter(artists, kpi.EmergingFilter(
        min_listens=int(min_listens), min_avg_active_days=float(min_days),
        max_listeners=int(max_listeners) if limit else None, mbid_status=mbid_status,
        exclude_artist_ids=tuple(excluded)))
    fingerprint = repr((dates, users, min_listens, min_days, limit, max_listeners, mbid_status, excluded))
    table_key = "shortlist_" + hashlib.sha256(fingerprint.encode()).hexdigest()[:12]
    with tabs[0]:
        render_shortlist(data, shortlist, table_key)
    with tabs[1]:
        render_artist(data, shortlist)
    with tabs[2]:
        render_listeners(data)
    with st.expander("Metric definitions and data notes"):
        st.markdown("""
        - **Return rate:** share of listener–artist pairs with listens on at least two distinct UTC days.
        - **Return momentum:** late-window return listening compared with that listener's activity baseline; `n/a` means insufficient evidence.
        - **Countable listens:** suspected double-scrobbles are excluded by M4. M5 charts show all logged listens.
        - **Identity:** stable MBID or a normalized-name fallback. Missing MBIDs do not remove artists from the shortlist.
        - **First observed listen** describes this extract, not a listener's true first play.
        - **Capped:** H-music, iliekcomputers, and s_john_s reached the 500-listen extraction cap.
        """)


if __name__ == "__main__":
    main()
