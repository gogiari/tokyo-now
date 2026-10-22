"""Google Places(New)로 리뷰 수·영업시간·임시휴업을 받아 data.json 갱신. 키 없으면 아무것도 안 바꿈."""
import json, math, os, sys, urllib.request, datetime
KEY=os.environ.get("GOOGLE_PLACES_API_KEY")
if not KEY: print("no key, skip"); sys.exit(0)
D=json.load(open("data.json")); P=D["places"]
DAYS=["sun","mon","tue","wed","thu","fri","sat"]
def call(body):
    r=urllib.request.Request("https://places.googleapis.com/v1/places:searchText",json.dumps(body).encode(),
      {"Content-Type":"application/json","X-Goog-Api-Key":KEY,
       "X-Goog-FieldMask":"places.id,places.userRatingCount,places.rating,places.businessStatus,places.regularOpeningHours"})
    return json.load(urllib.request.urlopen(r,timeout=20)).get("places",[])
def hours(o):
    if not o or "periods" not in o: return None
    h={d:[] for d in DAYS}
    for p in o["periods"]:
        a=p["open"]; c=p.get("close")
        if not c: return {d:[["00:00","24:00"]] for d in DAYS+["holiday"]}
        oh=a["hour"]*60+a["minute"]; ch=c["hour"]*60+c["minute"]
        if c["day"]!=a["day"] or ch<=oh: ch+=1440
        h[DAYS[a["day"]]].append(["%02d:%02d"%divmod(oh,60),"%02d:%02d"%divmod(ch,60)])
    h["holiday"]=None; return h
ok=0
for p in P:
    try:
        res=call({"textQuery":p.get("ja") or p["ko"],"languageCode":"ja",
          "locationBias":{"circle":{"center":{"latitude":p["lat"],"longitude":p["lng"]},"radius":300}}})
        if not res: continue
        g=res[0]; p["g"]=g.get("userRatingCount"); p["gr"]=g.get("rating")
        hw=hours(g.get("regularOpeningHours"))
        if hw: p["h"]=hw
        p["tc"]=g.get("businessStatus")=="CLOSED_TEMPORARILY" or None
        ok+=1
    except Exception as e: print(p["ko"],e)
if ok<len(P)//2: print("too many failures, keep old data"); sys.exit(1)
for k in {p["k"] for p in P}:
    c=[p for p in P if p["k"]==k]; m=max(math.log1p(p.get("g") or 0) for p in c) or 1
    for p in c: p["s"]=round(100*math.log1p(p.get("g") or 0)/m,1)
    for i,p in enumerate(sorted(c,key=lambda p:-p["s"])): p["r"]=i+1
D["updated"]=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="minutes")
D["source"]="google_places"
json.dump(D,open("data.json","w"),ensure_ascii=False); print("updated",ok,"/",len(P))
