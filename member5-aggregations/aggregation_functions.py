"""Reusable aggregation functions for ListenBrainz analysis."""

from pathlib import Path
import json

import pandas as pd


def build_audience_growth(df):
    """
    Create a monthly audience-growth dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned listening-event data containing username and listened_at_utc.

    Returns
    -------
    pandas.DataFrame
        One row per calendar month with active, new, and cumulative
        observed-listener metrics.
    """
    required_columns = {'username', 'listened_at_utc'}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    data = df.loc[:, ['username', 'listened_at_utc']].copy()
    data['listened_at_utc'] = pd.to_datetime(data['listened_at_utc'], utc=True, errors='coerce')
    data = data.dropna(subset=['username', 'listened_at_utc'])
    data['month'] = data['listened_at_utc'].dt.tz_localize(None).dt.to_period('M').dt.to_timestamp()
    active = data.groupby('month')['username'].nunique().rename('active_listeners')
    first_month = data.groupby('username')['month'].min()
    new = first_month.value_counts().sort_index().rename('new_listeners')
    calendar = pd.date_range(start=data['month'].min(), end=data['month'].max(), freq='MS')
    result = pd.DataFrame(index=calendar).join(active).join(new).fillna(0).astype({'active_listeners': 'int64', 'new_listeners': 'int64'})
    result.index.name = 'month'
    result = result.reset_index()
    result['cumulative_listeners'] = result['new_listeners'].cumsum()
    result['listener_change'] = result['active_listeners'].diff()
    result['listener_growth_pct'] = result['active_listeners'].pct_change(fill_method=None).mul(100).replace([float('inf'), float('-inf')], pd.NA)
    return result


def build_listener_engagement(df):
    """
    Create one row per listener with engagement metrics.
    """
    required_columns = {'username', 'listened_at_utc', 'artist_name', 'track_name', 'release_name'}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    data = df.copy()
    data['listened_at_utc'] = pd.to_datetime(data['listened_at_utc'], utc=True, errors='coerce')
    data = data.dropna(subset=['username', 'listened_at_utc'])
    data['listen_date'] = data['listened_at_utc'].dt.date
    engagement = data.groupby('username', as_index=False).agg(first_listen=('listened_at_utc', 'min'), last_listen=('listened_at_utc', 'max'), total_listens=('username', 'size'), active_days=('listen_date', 'nunique'), unique_artists=('artist_name', 'nunique'), unique_tracks=('track_name', 'nunique'), unique_releases=('release_name', 'nunique'))
    engagement['observation_days'] = (engagement['last_listen'].dt.normalize() - engagement['first_listen'].dt.normalize()).dt.days + 1
    engagement['listens_per_active_day'] = (engagement['total_listens'] / engagement['active_days']).round(2)
    engagement['repeat_listens'] = engagement['total_listens'] - engagement['unique_tracks']
    engagement['repeat_listen_pct'] = (engagement['repeat_listens'] / engagement['total_listens'] * 100).round(2)
    return engagement.sort_values('total_listens', ascending=False).reset_index(drop=True)


def build_daily_activity(df):
    """
    Create daily listening metrics for each user.
    """
    required_columns = {'username', 'listened_at_utc', 'artist_name', 'track_name', 'release_name'}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    data = df.copy()
    data['listened_at_utc'] = pd.to_datetime(data['listened_at_utc'], utc=True, errors='coerce')
    data = data.dropna(subset=['username', 'listened_at_utc'])
    data['date'] = data['listened_at_utc'].dt.tz_localize(None).dt.normalize()
    daily = data.groupby(['date', 'username'], as_index=False).agg(total_listens=('username', 'size'), unique_artists=('artist_name', 'nunique'), unique_tracks=('track_name', 'nunique'), unique_releases=('release_name', 'nunique')).sort_values(['date', 'username']).reset_index(drop=True)
    return daily


def build_artist_performance(df):
    """
    Create chart-ready performance metrics for each artist.
    """
    required_columns = {'username', 'listened_at_utc', 'artist_name', 'track_name', 'release_name'}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    data = df.copy()
    data['listened_at_utc'] = pd.to_datetime(data['listened_at_utc'], utc=True, errors='coerce')
    data = data.dropna(subset=['username', 'artist_name', 'listened_at_utc'])
    data['listen_date'] = data['listened_at_utc'].dt.date
    artist_performance = data.groupby('artist_name', as_index=False).agg(total_listens=('artist_name', 'size'), unique_listeners=('username', 'nunique'), unique_tracks=('track_name', 'nunique'), unique_releases=('release_name', 'nunique'), active_days=('listen_date', 'nunique'), first_listen=('listened_at_utc', 'min'), last_listen=('listened_at_utc', 'max'))
    artist_performance['listens_per_listener'] = (artist_performance['total_listens'] / artist_performance['unique_listeners']).round(2)
    artist_performance['listen_share_pct'] = (artist_performance['total_listens'] / artist_performance['total_listens'].sum() * 100).round(2)
    return artist_performance.sort_values(['total_listens', 'artist_name'], ascending=[False, True]).reset_index(drop=True)

def generate_outputs(input_path, output_dir):
    """
    Generate and save all chart-ready aggregation datasets.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    listens = pd.read_csv(input_path)
    artist_events = build_artist_listen_events(listens)

    outputs = {
        "audience_growth.csv": build_audience_growth(listens),
        "listener_engagement.csv": build_listener_engagement(listens),
        "daily_listener_activity.csv": build_daily_activity(listens),
        "artist_performance.csv": build_artist_performance(listens),
        "artist_monthly_growth.csv": build_artist_monthly_growth(artist_events),
        "artist_engagement.csv": build_artist_engagement(artist_events)
    }

    for filename, table in outputs.items():
        output_path = output_dir / filename
        table.to_csv(output_path, index=False)
        print(f"Saved: {output_path}")


def parse_artist_mbids(value):
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def build_artist_listen_events(df):
    """
    Create one row per listening event and resolved artist MBID.

    A multi-artist listen produces multiple rows, one for each artist MBID.
    """
    required_columns = {'username', 'listened_at_utc', 'track_name', 'artist_name', 'recording_mbid', 'artist_mbids_parsed'}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    data = df.loc[:, list(required_columns)].copy()
    data['listen_event_id'] = data.index
    data['listened_at_utc'] = pd.to_datetime(data['listened_at_utc'], utc=True, errors='coerce')
    data['artist_mbid'] = data['artist_mbids_parsed'].apply(parse_artist_mbids)
    data = data.explode('artist_mbid')
    data = data.dropna(subset=['username', 'listened_at_utc', 'artist_mbid'])
    data = data.drop_duplicates(subset=['listen_event_id', 'artist_mbid'])
    data['date'] = data['listened_at_utc'].dt.tz_localize(None).dt.normalize()
    data['month'] = data['listened_at_utc'].dt.tz_localize(None).dt.to_period('M').dt.to_timestamp()
    return data.sort_values(['listened_at_utc', 'artist_mbid']).reset_index(drop=True)


def build_artist_monthly_growth(artist_events):
    """
    Create monthly audience metrics for each resolved artist MBID.
    """
    required_columns = {'artist_mbid', 'artist_name', 'username', 'track_name', 'listen_event_id', 'month'}
    missing_columns = required_columns.difference(artist_events.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    monthly = artist_events.groupby(['artist_mbid', 'month'], as_index=False).agg(artist_credit=('artist_name', lambda values: values.mode().iloc[0]), unique_listeners=('username', 'nunique'), total_listens=('listen_event_id', 'nunique'), unique_tracks=('track_name', 'nunique')).sort_values(['artist_mbid', 'month']).reset_index(drop=True)
    monthly['previous_month'] = monthly.groupby('artist_mbid')['month'].shift()
    monthly['previous_unique_listeners'] = monthly.groupby('artist_mbid')['unique_listeners'].shift()
    expected_previous_month = monthly['month'] - pd.offsets.MonthBegin(1)
    monthly['has_consecutive_month'] = monthly['previous_month'].eq(expected_previous_month)
    monthly['listener_change'] = (monthly['unique_listeners'] - monthly['previous_unique_listeners']).where(monthly['has_consecutive_month'])
    monthly['listener_growth_pct'] = (monthly['listener_change'] / monthly['previous_unique_listeners'] * 100).where(monthly['has_consecutive_month'] & monthly['previous_unique_listeners'].gt(0)).round(2)
    return monthly


def build_artist_engagement(artist_events):
    """
    Create listener-engagement metrics for each artist MBID.
    """
    required_columns = {'artist_mbid', 'artist_name', 'username', 'recording_mbid', 'listen_event_id', 'listened_at_utc', 'date'}
    missing_columns = required_columns.difference(artist_events.columns)
    if missing_columns:
        raise ValueError(f'Missing required columns: {sorted(missing_columns)}')
    listener_artist = artist_events.groupby(['artist_mbid', 'username'], as_index=False).agg(artist_credit=('artist_name', lambda values: values.mode().iloc[0]), first_listen=('listened_at_utc', 'min'), last_listen=('listened_at_utc', 'max'), total_listens=('listen_event_id', 'nunique'), listening_days=('date', 'nunique'), unique_tracks=('recording_mbid', 'nunique'))
    event_returns = artist_events.merge(listener_artist[['artist_mbid', 'username', 'first_listen']], on=['artist_mbid', 'username'], how='left', validate='many_to_one')
    event_returns['returned_within_30_days'] = event_returns['listened_at_utc'].gt(event_returns['first_listen']) & event_returns['listened_at_utc'].le(event_returns['first_listen'] + pd.Timedelta(days=30))
    return_flags = event_returns.groupby(['artist_mbid', 'username'], as_index=False)['returned_within_30_days'].any()
    listener_artist = listener_artist.merge(return_flags, on=['artist_mbid', 'username'], how='left', validate='one_to_one')
    listener_artist['has_3plus_days'] = listener_artist['listening_days'] >= 3
    listener_artist['has_3plus_tracks'] = listener_artist['unique_tracks'] >= 3
    engagement = listener_artist.groupby('artist_mbid', as_index=False).agg(artist_credit=('artist_credit', lambda values: values.mode().iloc[0]), unique_listeners=('username', 'nunique'), returned_listeners=('returned_within_30_days', 'sum'), listeners_3plus_days=('has_3plus_days', 'sum'), listeners_3plus_tracks=('has_3plus_tracks', 'sum'), median_listening_days=('listening_days', 'median'), median_tracks_played=('unique_tracks', 'median'))
    engagement['return_rate_pct'] = (engagement['returned_listeners'] / engagement['unique_listeners'] * 100).round(2)
    engagement['share_3plus_days_pct'] = (engagement['listeners_3plus_days'] / engagement['unique_listeners'] * 100).round(2)
    engagement['share_3plus_tracks_pct'] = (engagement['listeners_3plus_tracks'] / engagement['unique_listeners'] * 100).round(2)
    return engagement.sort_values(['unique_listeners', 'return_rate_pct'], ascending=[False, False]).reset_index(drop=True)


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    generate_outputs(
        input_path=project_dir / "listenbrainz_final_cleaned.csv",
        output_dir=script_dir / "outputs"
    )
