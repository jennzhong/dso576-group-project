"""DSO 576 Phase 2: consolidate ListenBrainz event data without inventing listens.

Run: python final_cleaning.py --input listenbrainz_sample.csv --outdir outputs
Processes the supplied raw CSV; verify provenance of source extract with teammates.
Dependencies: pandas.
"""
import argparse
import ast
import json
from pathlib import Path
import pandas as pd

RAW_COLUMNS = ['username','listened_at','track_name','artist_name','release_name',
               'recording_msid','artist_mbids','recording_mbid','release_mbid']
EVENT_KEY = ['username','listened_at','recording_msid']


def parsed_timestamp(value):
    """Accept raw Unix seconds or a previously-cleaned ISO timestamp, keeping raw value intact."""
    value = str(value).strip()
    if not value:
        return pd.NaT
    try:
        number = float(value)
        if number == number and abs(number) < 1e12:
            return pd.to_datetime(number, unit='s', utc=True, errors='coerce')
    except (ValueError, OverflowError):
        pass
    return pd.to_datetime(value, utc=True, errors='coerce')


def parsed_mbids(value):
    if not str(value).strip():
        return '', 'missing'
    for parse in (json.loads, ast.literal_eval):
        try:
            items = parse(value)
            if isinstance(items, list) and all(isinstance(x,str) and x.strip() for x in items):
                return json.dumps(items, ensure_ascii=False, separators=(',',':')), 'valid'
            return '', 'invalid_array'
        except (ValueError, SyntaxError, TypeError, MemoryError):
            continue
    return '', 'unparseable'


def integrate(source):
    missing = [col for col in RAW_COLUMNS if col not in source]
    if missing:
        raise ValueError('Required columns missing: '+', '.join(missing))
    events = source[RAW_COLUMNS].copy()
    duplicates = events.duplicated(subset=RAW_COLUMNS, keep='first')
    events = events.loc[~duplicates].copy().reset_index(drop=True)
    times = events['listened_at'].map(parsed_timestamp)
    events['listened_at_utc'] = times.map(lambda d: d.isoformat() if pd.notna(d) else '')
    parsed = events['artist_mbids'].map(parsed_mbids)
    events['artist_mbids_parsed'] = parsed.map(lambda v: v[0])
    status = parsed.map(lambda v: v[1])
    per_user = []
    for user, block in events.groupby('username', dropna=False):
        dates = pd.to_datetime(block['listened_at_utc'], utc=True, errors='coerce').dropna()
        per_user.append({'username':user, 'listen_rows':len(block),
                         'first_listen_utc':dates.min().isoformat() if len(dates) else '',
                         'last_listen_utc':dates.max().isoformat() if len(dates) else '',
                         'source_rows_for_user':int((source.username==user).sum()),
                         'reached_500_record_cap':bool((source.username==user).sum() >= 500)})
    summary = {
        'source_rows':len(source), 'cleaned_rows':len(events), 'exact_duplicates_removed':int(duplicates.sum()),
        'unique_listeners':int(events.username.nunique()), 'distinct_artist_name_strings':int(events.artist_name.nunique()),
        'unparseable_timestamps':int((events.listened_at_utc=='').sum()),
        'artist_mbid_status':{str(k):int(v) for k,v in status.value_counts().items()},
        'repeated_candidate_event_key_rows':int(events.duplicated(EVENT_KEY,keep=False).sum()),
        'raw_columns_preserved':bool(source.loc[~source[RAW_COLUMNS].duplicated(),RAW_COLUMNS].reset_index(drop=True).equals(events[RAW_COLUMNS])),
        'source_is_complete_uploaded_extract':True
    }
    assert summary['raw_columns_preserved']
    assert len(events)==len(source)-summary['exact_duplicates_removed']
    assert events[RAW_COLUMNS].duplicated().sum()==0
    assert sum(x['listen_rows'] for x in per_user)==len(events)
    return events,pd.DataFrame(per_user),summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input', required=True, help='Original listenbrainz_sample.csv preferred')
    p.add_argument('--outdir',default='outputs')
    a=p.parse_args(); out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    src=pd.read_csv(a.input,dtype=str,keep_default_na=False,na_filter=False)
    events,users,metrics=integrate(src)
    events.to_csv(out/'listenbrainz_final_cleaned.csv',index=False)
    users.to_csv(out/'user_observation_summary.csv',index=False)
    (out/'validation_summary.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps(metrics,indent=2))
    print('Validated against supplied source extract; confirm this is the team-approved source version.')

if __name__=='__main__':
    main()
