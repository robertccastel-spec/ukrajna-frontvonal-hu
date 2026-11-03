from pathlib import Path
import shutil
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
PACK = Path(__file__).resolve().parent

def read(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f'Hiányzó fájl: {p}')
    return p.read_text(encoding='utf-8')

def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')
    print('OK:', rel)

def replace_once(rel, old, new):
    s = read(rel)
    if new in s:
        print('Már módosítva:', rel)
        return
    if old not in s:
        raise SystemExit(f'Nem található a várt részlet ebben: {rel}')
    write(rel, s.replace(old, new, 1))

replace_once(
    'site/src/utils/language.ts',
    "export const SUPPORTED_LANGUAGES = ['en', 'ru', 'uk', 'de'] as const;",
    "export const SUPPORTED_LANGUAGES = ['en', 'ru', 'uk', 'de', 'hu'] as const;",
)

replace_once(
    'site/src/utils/provider.tsx',
    "import GB from 'country-flag-icons/react/3x2/GB';",
    "import GB from 'country-flag-icons/react/3x2/GB';\nimport HU from 'country-flag-icons/react/3x2/HU';",
)
replace_once(
    'site/src/utils/provider.tsx',
    "  de: { label: 'Deutsch', Flag: DE },",
    "  de: { label: 'Deutsch', Flag: DE },\n  hu: { label: 'Magyar', Flag: HU },",
)

replace_once(
    'site/src/utils/format.ts',
    "  de: (decade) => decade.replace(/s$/, 'er'),",
    "  de: (decade) => decade.replace(/s$/, 'er'),\n  hu: (decade) => decade,",
)

format_locale = 'site/src/utils/format-locale.ts'
s = read(format_locale)
if "  hu: {" not in s:
    marker = "  de: {\n"
    idx = s.find(marker)
    if idx < 0:
        raise SystemExit('Nem található a német blokk a format-locale.ts fájlban.')
    hu = """  hu: {
    AEC: 'Ázsia Kína nélkül',
    ROW: 'A világ többi része',
    OTHERS: 'Egyéb',
    SUN: 'Szovjetunió',
    YUG: 'Jugoszlávia',
    SCG: 'Szerbia és Montenegró',
    CSK: 'Csehszlovákia',
    DDR: 'NDK',
    ANT: 'Holland Antillák',
    ZA1: 'Dél-afrikai Vámunió',
    YMD: 'Dél-Jemen',
    PUS: 'Amerikai csendes-óceáni szigetek',
    PCI: 'Csendes-óceáni Gyámsági Terület',
    ATB: 'Brit Antarktiszi Terület',
    XK: 'Koszovó',
    XKX: 'Koszovó',
  },
"""
    write(format_locale, s[:idx] + hu + s[idx:])

custom = 'site/scripts/cldr-custom-units.ts'
s = read(custom)
if "  hu: {" not in s:
    end = s.rfind('\n};')
    if end < 0:
        raise SystemExit('Nem található a CUSTOM_UNITS objektum vége.')
    hu = r'''
  hu: {
    short: {
      'event-launch': { displayName: 'indítás', perUnitPattern: '{0}/indítás', 'unitPattern-count-one': '{0} indítás', 'unitPattern-count-other': '{0} indítás' },
      'energy-terawatt-hour': { displayName: 'TWh', 'unitPattern-count-one': '{0} TWh', 'unitPattern-count-other': '{0} TWh' },
      'energy-kilowatt-hour': { displayName: 'kWh', 'unitPattern-count-one': '{0} kWh', 'unitPattern-count-other': '{0} kWh' },
      person: { displayName: 'fő', perUnitPattern: '{0}/fő', 'unitPattern-count-one': '{0} fő', 'unitPattern-count-other': '{0} fő' },
      'vehicle-car-per-1000-person': { displayName: 'autó / 1000 fő', 'unitPattern-count-one': '{0} autó / 1000 fő', 'unitPattern-count-other': '{0} autó / 1000 fő' },
    },
    long: {
      'event-launch': { displayName: 'indítás', perUnitPattern: '{0} indításonként', 'unitPattern-count-one': '{0} indítás', 'unitPattern-count-other': '{0} indítás' },
      'energy-terawatt-hour': { displayName: 'terawattóra', 'unitPattern-count-one': '{0} terawattóra', 'unitPattern-count-other': '{0} terawattóra' },
      'energy-kilowatt-hour': { displayName: 'kilowattóra', 'unitPattern-count-one': '{0} kilowattóra', 'unitPattern-count-other': '{0} kilowattóra' },
      person: { displayName: 'fő', perUnitPattern: '{0} főre', 'unitPattern-count-one': '{0} fő', 'unitPattern-count-other': '{0} fő' },
      'vehicle-car-per-1000-person': { displayName: 'személygépkocsi 1000 főre', 'unitPattern-count-one': '{0} személygépkocsi 1000 főre', 'unitPattern-count-other': '{0} személygépkocsi 1000 főre' },
    },
    narrow: {
      'event-launch': { displayName: 'ind.', perUnitPattern: '{0}/ind.', 'unitPattern-count-one': '{0} ind.', 'unitPattern-count-other': '{0} ind.' },
      'energy-terawatt-hour': { displayName: 'TWh', 'unitPattern-count-one': '{0} TWh', 'unitPattern-count-other': '{0} TWh' },
      'energy-kilowatt-hour': { displayName: 'kWh', 'unitPattern-count-one': '{0} kWh', 'unitPattern-count-other': '{0} kWh' },
      person: { displayName: 'fő', perUnitPattern: '{0}/fő', 'unitPattern-count-one': '{0} fő', 'unitPattern-count-other': '{0} fő' },
      'vehicle-car-per-1000-person': { displayName: 'autó/1e fő', 'unitPattern-count-one': '{0} autó/1e fő', 'unitPattern-count-other': '{0} autó/1e fő' },
    },
  },'''
    write(custom, s[:end] + hu + s[end:])

frontmap = 'site/src/projects/war-rf-ua/components/FrontlineMap.tsx'
s = read(frontmap)
if 'function preferHungarianMapLabels' not in s:
    anchor = "const decodedCache = new Map<string, FrontlineMapLayers>();"
    helper = r'''/** Prefer Hungarian place/road labels when the vector tiles expose OSM name:hu. */
function preferHungarianMapLabels(map: MapLibreMap): void {
  if (typeof document === 'undefined' || document.documentElement.lang !== 'hu') return;
  for (const layer of map.getStyle().layers ?? []) {
    if (layer.type !== 'symbol') continue;
    const current = map.getLayoutProperty(layer.id, 'text-field');
    if (current == null) continue;
    try {
      map.setLayoutProperty(layer.id, 'text-field', [
        'coalesce',
        ['get', 'name:hu'],
        ['get', 'name:latin'],
        ['get', 'name'],
      ]);
    } catch {
      // Some symbol layers are not name-based; leave them unchanged.
    }
  }
}

'''
    if anchor not in s:
        raise SystemExit('Nem található a FrontlineMap beszúrási pontja.')
    s = s.replace(anchor, helper + anchor, 1)
    old = "    map.on('load', () => {\n      const activeLayers = getDecodedLayers(historyRef.current, activeDateRef.current);"
    new = "    map.on('load', () => {\n      preferHungarianMapLabels(map);\n      const activeLayers = getDecodedLayers(historyRef.current, activeDateRef.current);"
    if old not in s:
        raise SystemExit('Nem található a MapLibre load blokk.')
    s = s.replace(old, new, 1)
    write(frontmap, s)

for rel in [
    'site/src/locales/common-hu.ts',
    'site/src/projects/war-rf-ua/locales/dict-hu.ts',
    'site/src/projects/war-rf-ua/locales/meta-hu.ts',
]:
    src = PACK / 'files' / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print('OK:', rel)
