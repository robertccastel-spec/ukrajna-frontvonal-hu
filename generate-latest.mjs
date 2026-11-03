import fs from 'node:fs';
import { XMLParser } from 'fast-xml-parser';
import polygonClipping from 'polygon-clipping';

const UKRAINE_TOTAL_KM2 = 603628;
const THEATER = {minLon:22,maxLon:41,minLat:44,maxLat:53.5};
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36';

const cleanRing = (ring) => {
  if (!Array.isArray(ring) || ring.length < 3) return [];
  const out=[];
  for (const p of ring) {
    if (!Array.isArray(p) || p.length<2) continue;
    const lon=Math.round(Number(p[0])*1e5)/1e5, lat=Math.round(Number(p[1])*1e5)/1e5;
    if (!Number.isFinite(lon)||!Number.isFinite(lat)) continue;
    if (lon<THEATER.minLon||lon>THEATER.maxLon||lat<THEATER.minLat||lat>THEATER.maxLat) return [];
    if (!out.length || out.at(-1)[0]!==lon || out.at(-1)[1]!==lat) out.push([lon,lat]);
  }
  if (out.length<3) return [];
  if (out[0][0]!==out.at(-1)[0] || out[0][1]!==out.at(-1)[1]) out.push([...out[0]]);
  return out.length>=4?out:[];
};

function geomToPolys(g){
  if(!g)return[];
  if(g.type==='GeometryCollection'&&Array.isArray(g.geometries))return g.geometries.flatMap(geomToPolys);
  if(g.type==='Polygon'&&Array.isArray(g.coordinates)){const rings=g.coordinates.map(cleanRing).filter(r=>r.length>=4);return rings.length?[rings]:[];}
  if(g.type==='MultiPolygon'&&Array.isArray(g.coordinates))return g.coordinates.map(p=>p.map(cleanRing).filter(r=>r.length>=4)).filter(p=>p.length);
  return[];
}
const featurePolys=f=>geomToPolys(f.geometry);
const lname=s=>(s||'').toLowerCase();
function isOccupied(name,fill){
  const n=lname(name),f=lname(fill);
  if(['придністров','transnistria','салла','естоні','латві','курильськ','цхінвальськ','абхазія','пруссія','карелі','ічкерія','тузла'].some(x=>n.includes(x)))return false;
  return n.includes('geojson.status.occupied')||n.includes('geojson.territories.crimea')||n.includes('geojson.territories.ordlo')||n.includes('окупован')||n.includes('occupied')||n.includes('ордло')||n==='крим'||n.includes('зайняті ворогом')||f==='#a52714';
}
function isGrey(name,fill){const n=lname(name),f=lname(fill);return n.includes('geojson.status.unknown')||n.includes('unknown status')||n.includes('статус невідомий')||n.includes('під питанням')||n.includes('contested')||n.includes('contensed')||f==='#bcaaa4'||f==='#bdbdbd';}
function isCrimeaFeature(f){const n=lname(f.properties?.name);if(n.includes('кримськ')||n.includes('міст')||n.includes('bridge')||n.includes('airfield'))return false;return n.includes('geojson.territories.crimea')||n.includes('окупований крим')||n.includes('occupied crimea')||n==='крим';}
function isLaCrimea(p){const n=lname(p.name||p.description);return n.includes('республика крым')||n.includes('севастополь')||n.includes('occupied crimea')||n.includes('крым');}
function ringArea(ring){const R=6371.0072;let total=0;if(ring.length<3)return 0;for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length],lon1=a[0]*Math.PI/180,lat1=a[1]*Math.PI/180,lon2=b[0]*Math.PI/180,lat2=b[1]*Math.PI/180;total+=(lon2-lon1)*(2+Math.sin(lat1)+Math.sin(lat2));}return Math.abs(total*R*R/2);}
function area(mp){let t=0;for(const p of mp||[]){if(!p?.length)continue;let a=ringArea(p[0]);for(let i=1;i<p.length;i++)a-=ringArea(p[i]);t+=Math.max(0,a);}return t;}
const round1=n=>Math.round(n*10)/10;
const safeUnion=(mp)=>{if(!mp?.length)return[];return polygonClipping.union(mp);};

async function getJson(url,headers={}){
  const r=await fetch(url,{headers:{'User-Agent':UA,...headers}});
  if(!r.ok)throw new Error('HTTP '+r.status+' '+url);
  return r.json();
}
async function getText(url,headers={}){
  const r=await fetch(url,{headers:{'User-Agent':UA,...headers}});
  if(!r.ok)throw new Error('HTTP '+r.status+' '+url);
  return r.text();
}

const meta=await getJson('https://lostarmour.info/panel/next/api/public/map/kml-meta',{Referer:'https://lostarmour.info/map'});
const date=meta?.date;
if(!date)throw new Error('LostArmour latest date missing');

const hist=await getJson('https://deepstatemap.live/api/history/public');
const candidates=(hist||[]).filter(x=>x?.createdAt?.slice(0,10)<=date).sort((a,b)=>a.createdAt.localeCompare(b.createdAt));
const rev=candidates.at(-1);
if(!rev?.id)throw new Error('DeepState revision missing');

const [dsGeo,laKml]=await Promise.all([
  getJson('https://deepstatemap.live/api/history/'+rev.id+'/geojson'),
  getText('https://lostarmour.info/mapinfo/kml/'+date+'.kml',{Referer:'https://lostarmour.info/map'})
]);

const dsOcc=[], dsGrey=[], dsCrimea=[];
for(const f of dsGeo.features||[]){
  const name=f.properties?.name, fill=f.properties?.fill;
  if(isCrimeaFeature(f))dsCrimea.push(...featurePolys(f));
  if(isOccupied(name,fill))dsOcc.push(...featurePolys(f));
  else if(isGrey(name,fill))dsGrey.push(...featurePolys(f));
}
const dsOccupied=safeUnion(dsOcc), dsGreyUnion=dsGrey.length?safeUnion(dsGrey):[], dsCrimeaUnion=dsCrimea.length?safeUnion(dsCrimea):[];

const parser=new XMLParser({ignoreAttributes:false,attributeNamePrefix:'@_'});
const doc=parser.parse(laKml);
let marks=doc?.kml?.Document?.Folder?.Placemark||[];
if(!Array.isArray(marks))marks=[marks];
const la=[];
for(const p of marks){
  const cs=(p?.Polygon?.outerBoundaryIs?.LinearRing?.coordinates||'').trim();
  if(!p?.Polygon||cs.length<=100||isLaCrimea(p))continue;
  const ring=cleanRing(cs.split(/\s+/).map(pair=>pair.split(',').slice(0,2).map(Number)));
  if(ring.length>=4)la.push([ring]);
}
la.push(...dsCrimea);
const laUnion=safeUnion(la);
let consensus=polygonClipping.intersection(laUnion,dsOccupied);
if(dsCrimeaUnion.length)consensus=safeUnion([...consensus,...dsCrimeaUnion]);
const xor=polygonClipping.xor(laUnion,dsOccupied);
let disputed=safeUnion([...(xor||[]),...(dsGreyUnion||[])]);
let dsFront=safeUnion([...(dsOccupied||[]),...(dsGreyUnion||[])]);

const summary={
  latestDate:date,totalUkraineKm2:UKRAINE_TOTAL_KM2,
  consensusRfKm2:round1(area(consensus)),
  disputedKm2:round1(area(disputed)),
  consensusUaKm2:0,
  dsOccupiedKm2:round1(area(dsOccupied)),
  dsGreyKm2:round1(area(dsGreyUnion)),
  laClaimedKm2:round1(area(laUnion))
};
summary.consensusUaKm2=round1(Math.max(0,UKRAINE_TOTAL_KM2-summary.consensusRfKm2-summary.disputedKm2));

fs.mkdirSync('_site/data',{recursive:true});
fs.writeFileSync('_site/data/latest.json',JSON.stringify({date,summary,layers:{consensusRf:consensus,disputed,deepstate:dsFront,lostarmour:laUnion}}));
console.log('Kész:',date,summary);
