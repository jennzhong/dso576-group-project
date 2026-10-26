
import pandas as pd, json, sys
sys.path.insert(0,'.')
import kpi_analysis as k
df = pd.read_csv('listenbrainz_final_cleaned.csv', dtype=str, keep_default_na=False, na_values=[''])
df['t'] = pd.to_datetime(df['listened_at_utc'], utc=True, format='ISO8601')
df = df.sort_values(['username','t'], kind='stable')
gap = df.groupby(['username','recording_msid'])['t'].diff().dt.total_seconds()
df = df[~(gap < 60)]
print('countable', len(df))
name = df['artist_name'].str.strip()
ph = {'unknown','[unknown]','unknown artist','n/a','none','null','-'}
df = df[name.notna() & ~name.str.casefold().isin(ph)]
print('artist listens', len(df))
L = k.load_listens()
rows = k.countable_artist_listens(L)
rows = rows.assign(day=rows['listened_at_utc'].dt.date)
p = rows.groupby(['artist_id','username'])['day'].nunique()
print('pairs', len(p), 'returned', (p>=2).sum(), 'rate', round((p>=2).mean(),4))
df['day']=df['t'].dt.date
p2 = df.groupby([df['artist_name'].str.strip().str.casefold(),'username'])['day'].nunique()
print('name-only pairs', len(p2), 'rate', round((p2>=2).mean(),4))
pk = k.pair_kpis(L)
ret = pk[pk.returned]
print('returned pairs', len(ret), 'days_to_return==1:', (ret.days_to_return==1).sum())
shallow=[]
for (a,u),g in rows.groupby(['artist_id','username']):
    days = sorted(g['day'].unique())
    if len(days)!=2: continue
    d1=g[g.day==days[0]]['listened_at_utc'].max(); d2=g[g.day==days[1]]['listened_at_utc'].min()
    h=(d2-d1).total_seconds()/3600
    if h<3: shallow.append((a,u,len(g),round(h,2)))
print('2-day pairs whose "return" is <3h after previous listen (one session across UTC midnight):', len(shallow))
for s in shallow[:15]: print(s)
    t=g['listened_at_utc'].sort_values()
    return (t.diff().dt.total_seconds()/3600 >= hrs).any()
for hrs in (3,8,24):
    r = rows.groupby(['artist_id','username']).apply(lambda g: ret_gap(g,hrs))
    print(f'return = gap >= {hrs}h: rate', round(r.mean(),4), r.sum())
