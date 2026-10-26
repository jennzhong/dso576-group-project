# Run from the repo root: python audit/toy_return_rate.py
import pandas as pd, json, sys
sys.path.insert(0,'.')
import kpi_analysis as k
def r(u,t,trk,art,msid,mb=None):
    return dict(username=u,listened_at='0',track_name=trk,artist_name=art,release_name='r',recording_msid=msid,
        artist_mbids='',recording_mbid='',release_mbid='',listened_at_utc=t,artist_mbids_parsed=json.dumps([mb] if mb else []))
toy = pd.DataFrame([
 r('A','2026-09-01T10:00:00Z','s1','X','m1'),
 r('A','2026-09-03T10:00:00Z','s2','X','m2'),          # A returns to X on a 2nd day -> returned
 r('A','2026-09-01T11:00:00Z','s3','Y','m3'),
 r('A','2026-09-01T11:00:30Z','s3','Y','m3'),          # double-scrobble (30 s) -> not countable
 r('B','2026-09-01T23:50:00Z','s4','Z','m4'),
 r('B','2026-09-02T00:05:00Z','s5','Z','m5'),          # same session crosses UTC midnight -> counts as 2 days
])
L = k.derive_columns(toy)
p = k.pair_kpis(L); a = k.artist_kpis(L)
print(p[['artist_id','username','countable_listens','active_days','returned']])
print('pair_return_rate =', k.headline_kpis(L,p,a)['pair_return_rate'])
