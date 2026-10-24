import pandas as pd, numpy as np
O="C:/Users/user/Music/Datathon/data/processed/followme/"
r=pd.read_csv(O+"observed_sea_links.csv"); na=pd.read_csv(O+"observed_links_noaccess_coverage.csv")
noacc=set(na.id)
v=r[r.rtl_served].copy(); v["ratio"]=v.median_min/v.rtl_median_min
v["bin"]=pd.cut(v.distance_km,[0,5,10,20,40,200])
print(v.groupby("bin",observed=True).agg(n=("ratio","size"),med=("ratio","median"),obs=("median_min","median"),rtl=("rtl_median_min","median")))
print("ratio<0.5",(v.ratio<.5).mean(),"0.5-1",((v.ratio>=.5)&(v.ratio<1)).mean(),">=1",(v.ratio>=1).mean(),"pearson log",np.corrcoef(np.log(v.median_min),np.log(v.rtl_median_min))[0,1])
print(r.trips_per_day.describe(), r.groupby("speed_class").size())
print("links with partner having access:")
c=r[r.touches_no_access_origin]
partner_ok=c[~(c.from_island_id.isin(noacc)&c.to_island_id.isin(noacc))]
print(len(c),len(partner_ok))
# for each covered no-access island: best link tpd and whether any partner is access island
rows=[]
for i in na[na.covered].id:
    s=r[((r.from_island_id==i)|(r.to_island_id==i))]
    p=set(s.from_island_id)|set(s.to_island_id); p.discard(i)
    out=s[s.from_island_id==i]
    rows.append((i,len(s),s.trips_per_day.max(),len(p-noacc),len(p&noacc)))
d=pd.DataFrame(rows,columns=["id","links","maxtpd","partners_access","partners_noaccess"])
d=d.merge(na,on="id"); print((d.partners_access>0).sum(), d[d.partners_access>0]["pop"].sum()); print((d.maxtpd<1).sum()); print(d.sort_values("pop",ascending=False).head(10).to_string())
print(d[d.partners_access==0].to_string())
print("dep hours weekday/weekend ratio", (r.tpd_weekend/r.tpd_weekday).median())
print(r.vessels.describe(), (r.speed_class=="fast").mean())
