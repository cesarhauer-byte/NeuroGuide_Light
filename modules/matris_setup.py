"""
Multidimensionell Viktmatris – matris_setup.py
Skapar och hanterar matris.db med korrelationer mellan neuropsykologiska
variabler baserade på publicerad forskning.
"""
import sqlite3, os
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), 'matris.db')

# ─── TEST-FAMILJER (aldrig korsförstärkning inom samma familj) ────────────────
TESTFAMILJER = [
    {"ravlt_total", "ravlt_dr", "ravlt_igenkanning"},
    {"bvmt_total", "bvmt_dr", "bvmt_igenkanning"},
    {"rcft_kopia", "rcft_dr"},
    {"tmt_a", "tmt_b", "tmt_ba_kvot"},
    {"sifferrep_fram", "sifferrep_bak"},
    {"mta_hoger", "mta_vanster"},
]

def ar_giltig_korrelation(k1, k2):
    if k1 == k2:
        return False
    for f in TESTFAMILJER:
        if k1 in f and k2 in f:
            return False
    return True

# ─── VARIABELDEFINITIONER ─────────────────────────────────────────────────────
# (id, kod, namn, kategori, kognitiv_doman, hjarn_struktur, hjarn_lateralitet,
#  lokalisation_vikt, patologi_riktning, referens)
VARIABLER = [
    (1,  'ravlt_total',       'RAVLT Total',               'episodiskt_minne',        'episodiskt_minne/inlärning',           'hippocampus, entorhinalcortex',                'vänster dominant',          8.5, 'lågt', 'Milner 1972; Cohen & Eichenbaum 1993'),
    (2,  'ravlt_dr',          'RAVLT Fördröjd ÅG',         'episodiskt_minne',        'episodiskt_minne/konsolidering',       'hippocampus CA1, subiculum',                   'bilateral, vänster dominant',9.5, 'lågt', 'Squire 1992; Eichenbaum 2000'),
    (3,  'ravlt_igenkanning', 'RAVLT Igenkänning',         'episodiskt_minne',        'episodiskt_minne/igenkänning',         'perirhinal cortex, hippocampus',               'bilateral',                 7.0, 'lågt', 'Brown & Aggleton 2001'),
    (4,  'bvmt_total',        'BVMT-R Total',              'visuospatialt_minne',     'visuospatialt_minne/inlärning',        'hippocampus höger, parietallob',               'höger dominant',            8.0, 'lågt', 'Smith & Milner 1981; Benedict 1997'),
    (5,  'bvmt_dr',           'BVMT-R Fördröjd ÅG',       'visuospatialt_minne',     'visuospatialt_minne/konsolidering',    'hippocampus höger, parahippocampal',           'höger dominant',            9.0, 'lågt', 'Benedict 1997; Milner 1968'),
    (6,  'rcft_dr',           'RCFT Fördröjd ÅG',         'visuospatialt_minne',     'visuospatialt_minne/komplex',          'hippocampus höger, frontal-parietal',          'höger dominant',            8.0, 'lågt', 'Meyers & Meyers 1995'),
    (7,  'rcft_kopia',        'RCFT Kopia',                'visuospatial_konstruktion','visuospatial_konstruktion',           'parietallob höger, occipital',                 'höger dominant',            7.5, 'lågt', 'Meyers & Meyers 1995'),
    (8,  'tmt_a',             'TMT-A',                     'psykomotorisk_hastighet', 'psykomotorisk_hastighet/uppmärksamhet','anteriora cingulate, thalamus, striatum',      'bilateral',                 6.0, 'lågt', 'Reitan 1958; Arbuthnott & Frank 2000'),
    (9,  'tmt_b',             'TMT-B',                     'exekutivt',               'exekutivt/kognitiv_flexibilitet',      'DLPFC bilateral, anteriora cingulate',         'bilateral, höger dominant', 8.0, 'lågt', 'Stuss et al 2001; Yamamoto et al 2022'),
    (10, 'tmt_ba_kvot',       'TMT B/A-kvot',              'exekutivt',               'exekutivt/set-shifting',               'DLPFC, anterior cingulate',                    'bilateral',                 8.5, 'högt', 'Zakzanis et al 2005'),
    (11, 'fas_total',         'FAS Total',                 'exekutivt',               'exekutivt/fonemiskt_ordflöde',         'inferior frontal vänster (Broca), DLPFC',      'vänster dominant',          8.5, 'lågt', 'Benton 1968; Henry & Crawford 2004'),
    (12, 'djurnamn',          'Djurnamn',                  'semantiskt_minne',        'semantiskt_minne/ordflöde',            'anteriora temporalloben vänster',              'vänster dominant',          8.0, 'lågt', 'Hodges & Patterson 1995'),
    (13, 'block_design',      'Blockmönster',              'visuospatial_konstruktion','visuospatial_konstruktion',           'parietallob höger, occipital-parietal',        'höger dominant',            8.5, 'lågt', 'Lezak 2004; Milner 1965'),
    (14, 'kodning',           'Kodning',                   'psykomotorisk_hastighet', 'psykomotorisk_hastighet/arbetsminne',  'striatum, thalamus, prefrontal',               'bilateral',                 6.5, 'lågt', 'Joy et al 2003'),
    (15, 'sifferrep_fram',    'Sifferrep. Framlänges',     'arbetsminne',             'arbetsminne/uppmärksamhet',            'DLPFC bilateral, parietallob',                 'bilateral',                 6.0, 'lågt', 'Wechsler 1997'),
    (16, 'sifferrep_bak',     'Sifferrep. Baklänges',      'arbetsminne',             'arbetsminne/manipulation',             'DLPFC bilateral, inferior parietal',           'bilateral, vänster',        7.0, 'lågt', 'Wechsler 1997'),
    (17, 'likheter',          'Likheter',                  'verbal_abstraktion',      'verbal_abstraktion/semantik',          'temporallob vänster, frontal',                 'vänster dominant',          6.5, 'lågt', 'Lezak 2004'),
    (18, 'information',       'Information',               'semantiskt_minne',        'semantiskt_minne/kristalliserad',      'temporallob vänster, neocortex',               'vänster dominant',          5.5, 'lågt', 'Lezak 2004'),
    (19, 'mta_hoger',         'MTA Höger',                 'struktur',                'struktur/hippocampusatrofi',            'hippocampus höger, entorhinalcortex',          'höger',                    10.0, 'högt', 'Scheltens 1992; Jack et al 1999'),
    (20, 'mta_vanster',       'MTA Vänster',               'struktur',                'struktur/hippocampusatrofi',            'hippocampus vänster, entorhinalcortex',        'vänster',                  10.0, 'högt', 'Scheltens 1992; Jack et al 1999'),
    (21, 'gca',               'GCA',                       'struktur',                'struktur/global_kortikal_atrofi',      'cortex diffust',                               'bilateral',                 7.0, 'högt', 'Pasquier et al 1996'),
    (22, 'koedam',            'Koedam',                    'struktur',                'struktur/parietal_occipital_atrofi',   'parietallob, precuneus, occipital',            'bilateral',                 9.0, 'högt', 'Koedam et al 2011'),
    (23, 'fazekas',           'Fazekas',                   'struktur',                'struktur/vitsubstans',                 'vit substans, periventrikulärt',               'bilateral',                 7.5, 'högt', 'Fazekas et al 1987'),
]

# ─── KORRELATIONSDEFINITIONER ─────────────────────────────────────────────────
# (var1_kod, var2_kod, vikt, riktning, evidensnivå, mekanism, referens)
KORRELATIONER_DEF = [
    # Starka (7–10) ────────────────────────────────────────────────────────────
    ('ravlt_dr',     'bvmt_dr',        7.5, 'positiv', 1,
     'Båda mäter fördröjt episodiskt minne; delar hippocampusberoende; r≈0.45–0.55',
     'Lezak 2004; Strauss et al 2006'),
    ('ravlt_dr',     'mta_vanster',    9.0, 'negativ', 1,
     'RAVLT primärt vänster hippocampus; direkt strukturellt-funktionellt samband',
     'Scheltens 1992; Jack et al 1999'),
    ('ravlt_total',  'mta_vanster',    7.5, 'negativ', 1,
     'Inlärningskapacitet hippocampusberoende; vänster dominant vid verbal inlärning',
     'Jack et al 1999; Scoville & Milner 1957'),
    ('bvmt_dr',      'mta_hoger',      9.0, 'negativ', 1,
     'BVMT primärt höger hippocampus; spegelbilden av RAVLT-MTA vänster',
     'Benedict 1997; Milner 1968'),
    ('bvmt_total',   'mta_hoger',      7.5, 'negativ', 1,
     'Visuospatialt inlärning höger hippocampusberoende',
     'Benedict 1997; Smith & Milner 1981'),
    ('tmt_b',        'fas_total',      7.0, 'positiv', 1,
     'Båda frontalt beroende; exekutiv komponent (kognitiv flexibilitet + initieringsförmåga) gemensam',
     'Henry & Crawford 2004; Stuss et al 2001'),
    ('tmt_b',        'mta_vanster',    7.5, 'negativ', 1,
     'TMT-B korrelerar med hippocampusvolym; frontohippocampalt nätverk; rho=0.823, p=0.003',
     'Yamamoto et al 2022; Bohbot et al 2004'),
    ('tmt_b',        'sifferrep_bak',  7.0, 'positiv', 1,
     'Båda kräver simultankapacitet och central executive; DLPFC gemensam komponent',
     'Stuss et al 2001; Baddeley 2007'),
    ('block_design',  'bvmt_total',    7.5, 'positiv', 1,
     'Visuospatial konstruktionsförmåga gemensam; parietallob höger delade substrat',
     'Lezak 2004; Milner 1965'),
    ('block_design',  'koedam',        8.0, 'negativ', 1,
     'Koedam mäter parietal/precuneus atrofi; Block_design parietal-occipitalt beroende',
     'Whitwell et al 2007; Koedam et al 2011'),
    ('rcft_dr',       'bvmt_dr',       8.0, 'positiv', 1,
     'Båda visuospatialt fördröjt minne; höger hippocampus och posterior parietallob',
     'Meyers & Meyers 1995; Benedict 1997'),
    ('rcft_kopia',    'block_design',  7.5, 'positiv', 1,
     'Konstruktiv förmåga gemensam; parietal-occipital substrat; visuospatial organisering',
     'Lezak 2004; Meyers & Meyers 1995'),
    ('rcft_kopia',    'koedam',        7.0, 'negativ', 1,
     'Parietallob höger; Koedam mäter parietal-occipital atrofi som underminerar konstruktionsförmåga',
     'Koedam et al 2011; Whitwell et al 2007'),
    ('kodning',       'tmt_a',         7.0, 'positiv', 1,
     'Psykomotorisk hastighet gemensam komponent; striatum och subkortikalt nätverk',
     'Joy et al 2003; Arbuthnott & Frank 2000'),
    ('likheter',      'information',   7.5, 'positiv', 1,
     'Båda kristalliserad/semantisk intelligens; temporal vänster + neocortex gemensam',
     'Lezak 2004; Cattell 1971'),
    ('likheter',      'fas_total',     6.5, 'positiv', 1,
     'Verbal förmåga; frontal-temporal vänster gemensam; språklig abstraktion och produktion',
     'Henry & Crawford 2004; Lezak 2004'),
    ('koedam',        'bvmt_total',    7.0, 'negativ', 1,
     'Parietallob höger stöder visuospatialt minne; Koedam-atrofi underminerar BVMT',
     'Koedam et al 2011; Smith & Milner 1981'),
    ('koedam',        'rcft_dr',       6.5, 'negativ', 1,
     'Parietal-hippocampal koppling för visuospatialt minne; Koedam-atrofi påverkar båda',
     'Whitwell et al 2007; Meyers & Meyers 1995'),
    # Måttliga (4–6.9) ─────────────────────────────────────────────────────────
    ('fazekas',       'tmt_b',         6.5, 'negativ', 1,
     'Vitsubstans stör frontostriatala kopplingar; exekutivt nätverk känsligt för WMH',
     'Prins et al 2005; de Groot et al 2000'),
    ('fazekas',       'kodning',       6.5, 'negativ', 1,
     'Vitsubstans underminerar psykomotorisk snabbhet; subcortikala kopplingar',
     'Prins et al 2005; Longstreth et al 1996'),
    ('fazekas',       'tmt_a',         6.0, 'negativ', 1,
     'Vitsubstans och psykomotorisk hastighet; thalamo-cortikala banor',
     'Prins et al 2005'),
    ('fazekas',       'sifferrep_bak', 5.0, 'negativ', 2,
     'Vitsubstans stör frontal arbetsminneskapacitet; central executive',
     'Prins et al 2005; Breteler et al 1994'),
    ('gca',           'ravlt_dr',      6.0, 'negativ', 2,
     'Global atrofi inkluderar temporalt; indirekt hippocampuspåverkan vid diffus kortikalt bortfall',
     'Pasquier et al 1996; Pearlson et al 1992'),
    ('gca',           'tmt_b',         5.0, 'negativ', 2,
     'Diffus kortikal atrofi påverkar frontala nätverk exekutivt',
     'Pasquier et al 1996'),
    ('gca',           'block_design',  4.0, 'negativ', 2,
     'Kortikal atrofi inkluderar parietalt; visuospatial konstruktion påverkas',
     'Pasquier et al 1996'),
    ('gca',           'fas_total',     4.0, 'negativ', 2,
     'Diffus atrofi inkluderar frontalt; ordflöde påverkas',
     'Pasquier et al 1996'),
    ('gca',           'tmt_a',         4.5, 'negativ', 2,
     'Global atrofi och psykomotorisk hastighet; subcortikala banor påverkas',
     'Pasquier et al 1996'),
    ('ravlt_total',   'tmt_b',         5.0, 'positiv', 2,
     'Indirekt: båda nedsatta vid AD; frontohippocampalt nätverk delvis gemensam',
     'Goverover et al 2005; Baudic et al 2006'),
    ('fas_total',     'sifferrep_bak', 5.5, 'positiv', 2,
     'Frontal exekutiv komponent gemensam; DLPFC inferior frontal vänster',
     'Benton 1968; Baddeley 2007'),
    ('bvmt_total',    'sifferrep_fram', 4.5, 'positiv', 3,
     'Visuospatialt arbetsminne; partiell överlappning visuell buffer',
     'Baddeley 2007; Wechsler 1997'),
    ('tmt_a',         'sifferrep_fram', 5.0, 'positiv', 2,
     'Uppmärksamhetskomponent gemensam; kortvarig kapacitet',
     'Reitan 1958; Wechsler 1997'),
    ('djurnamn',      'ravlt_total',   6.5, 'positiv', 2,
     'Semantiskt + episodiskt minne; anterior temporal vänster och hippocampus delvis gemensam',
     'Hodges & Patterson 1995; Garrard et al 2005'),
    ('djurnamn',      'likheter',      6.0, 'positiv', 2,
     'Temporal vänster; semantisk förmåga gemensam komponent',
     'Hodges & Patterson 1995; Lezak 2004'),
    ('djurnamn',      'information',   5.5, 'positiv', 2,
     'Semantisk kunskap och temporal vänster gemensam substrat',
     'Hodges & Patterson 1995'),
    ('fas_total',     'tmt_a',         5.5, 'positiv', 2,
     'Frontalt initieringskomponent; men TMT-A mer subkortikalt/motoriskt',
     'Henry & Crawford 2004; Reitan 1958'),
    ('block_design',  'rcft_dr',       5.5, 'positiv', 2,
     'Visuospatial komponent; partiellt överlapp konstruktion och visuospatialt minne',
     'Lezak 2004; Meyers & Meyers 1995'),
    ('ravlt_dr',      'mta_hoger',     6.5, 'negativ', 2,
     'Bilateral hippocampus; RAVLT vänster dominant men höger bidrar till konsolidering',
     'Jack et al 1999; Squire 1992'),
    ('sifferrep_bak', 'tmt_a',         4.5, 'positiv', 2,
     'Arbetsminne och processhastighet; partiellt överlapp frontalt',
     'Wechsler 1997; Reitan 1958'),
    # Svaga (1–3.9) ────────────────────────────────────────────────────────────
    ('ravlt_dr',      'block_design',  3.0, 'positiv', 3,
     'Olika modaliteter; svag korrelation; skilda neurala substrat',
     'Lezak 2004'),
    ('fas_total',     'bvmt_dr',       2.5, 'positiv', 3,
     'Olika system; minimalt överlapp; frontal vs hippocampal höger',
     'Lezak 2004'),
    ('tmt_b',         'mta_hoger',     5.0, 'negativ', 2,
     'TMT-B korrelerar med total hippocampusvolym; höger delvis',
     'Yamamoto et al 2022'),
]

# ─── DIAGNOSMÖNSTER ──────────────────────────────────────────────────────────
# (diagnos, var_id, forvantat_varde, diagnostisk_vikt, sensitivitet, specificitet)
DIAGNOS_MONSTER = [
    # Alzheimers sjukdom (AD)
    ('AD', 2,  'lågt',  9.5, 0.88, 0.85),  # ravlt_dr
    ('AD', 1,  'lågt',  8.0, 0.80, 0.75),  # ravlt_total
    ('AD', 5,  'lågt',  8.0, 0.75, 0.72),  # bvmt_dr
    ('AD', 20, 'högt',  9.0, 0.85, 0.80),  # mta_vanster
    ('AD', 19, 'högt',  8.5, 0.83, 0.78),  # mta_hoger
    ('AD', 21, 'högt',  6.0, 0.65, 0.60),  # gca
    ('AD', 3,  'lågt',  7.5, 0.72, 0.68),  # ravlt_igenkanning
    ('AD', 12, 'lågt',  6.0, 0.65, 0.70),  # djurnamn (semantisk atrofi)
    # DLB – Demens med Lewykroppar
    ('DLB', 13, 'lågt',  9.0, 0.78, 0.82),  # block_design
    ('DLB', 4,  'lågt',  8.0, 0.72, 0.75),  # bvmt_total
    ('DLB', 7,  'lågt',  7.5, 0.68, 0.70),  # rcft_kopia
    ('DLB', 22, 'högt',  8.5, 0.70, 0.85),  # koedam
    ('DLB', 6,  'lågt',  7.0, 0.65, 0.72),  # rcft_dr
    # bvFTD – beteendevariant frontotemporal demens
    ('bvFTD', 11, 'lågt',  8.5, 0.75, 0.80),  # fas_total
    ('bvFTD', 9,  'lågt',  8.5, 0.80, 0.78),  # tmt_b
    ('bvFTD', 10, 'högt',  8.0, 0.72, 0.82),  # tmt_ba_kvot
    ('bvFTD', 16, 'lågt',  6.5, 0.65, 0.70),  # sifferrep_bak
    ('bvFTD', 17, 'lågt',  5.5, 0.60, 0.65),  # likheter
    # Vaskulär demens (VaD)
    ('VaD', 8,  'lågt',  7.0, 0.68, 0.65),  # tmt_a
    ('VaD', 14, 'lågt',  7.0, 0.65, 0.65),  # kodning
    ('VaD', 23, 'högt',  8.5, 0.75, 0.70),  # fazekas
    ('VaD', 9,  'lågt',  7.0, 0.70, 0.65),  # tmt_b
    ('VaD', 21, 'högt',  6.5, 0.65, 0.60),  # gca
    ('VaD', 16, 'lågt',  6.0, 0.60, 0.62),  # sifferrep_bak
]

# ─── MAPPNING: variabelkod → T-poäng-nyckel i testresultat ───────────────────
KOD_TILL_TSCORE = {
    'ravlt_total':      'ravlt_total_t',
    'ravlt_dr':         'ravlt_dr_t',
    'ravlt_igenkanning': None,
    'bvmt_total':       'bvmt_total_t',
    'bvmt_dr':          'bvmt_dr_t',
    'rcft_dr':          'rcft_30min_t',
    'rcft_kopia':       'rcft_kop_t',
    'tmt_a':            'tmt_a_t',
    'tmt_b':            'tmt_b_t',
    'tmt_ba_kvot':      'tmt_ba_kvot',   # kvot, ej T-poäng
    'fas_total':        'fas_t',
    'djurnamn':         'djur_t',
    'block_design':     'block_t',
    'kodning':          'kod_t',
    'sifferrep_fram':   None,
    'sifferrep_bak':    'siff_t',
    'likheter':         'lik_t',
    'information':      'info_t',
    'mta_hoger':        None,            # bilddiagnostik
    'mta_vanster':      None,
    'gca':              None,
    'koedam':           None,
    'fazekas':          None,
}

BILD_TILL_KOD = {
    'mta_h':    ('mta_hoger',   4.0),
    'mta_v':    ('mta_vanster', 4.0),
    'gca':      ('gca',         3.0),
    'koedam':   ('koedam',      3.0),
    'fazekas':  ('fazekas',     3.0),
}


# ─── DATABAS-OPERATIONER ──────────────────────────────────────────────────────

def skapa_databas():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
    DROP TABLE IF EXISTS variabler;
    DROP TABLE IF EXISTS korrelationsmatris;
    DROP TABLE IF EXISTS diagnos_matrismonster;

    CREATE TABLE variabler (
        id                INTEGER PRIMARY KEY,
        kod               TEXT UNIQUE NOT NULL,
        namn              TEXT,
        kategori          TEXT,
        kognitiv_doman    TEXT,
        hjarn_struktur    TEXT,
        hjarn_lateralitet TEXT,
        lokalisation_vikt REAL,
        patologi_riktning TEXT DEFAULT 'lågt',
        referens          TEXT
    );

    CREATE TABLE korrelationsmatris (
        var1_id     INTEGER,
        var2_id     INTEGER,
        vikt        REAL,
        riktning    TEXT DEFAULT 'positiv',
        evidensniva INTEGER DEFAULT 2,
        mekanism    TEXT,
        referens    TEXT,
        PRIMARY KEY (var1_id, var2_id)
    );

    CREATE TABLE diagnos_matrismonster (
        diagnos           TEXT,
        var_id            INTEGER,
        forvantat_varde   TEXT,
        diagnostisk_vikt  REAL,
        sensitivitet      REAL,
        specificitet      REAL,
        PRIMARY KEY (diagnos, var_id)
    );
    """)

    c.executemany("INSERT INTO variabler VALUES (?,?,?,?,?,?,?,?,?,?)", VARIABLER)

    kod_till_id = {v[1]: v[0] for v in VARIABLER}
    rader = []
    for (k1, k2, vikt, riktning, evidens, mekanism, ref) in KORRELATIONER_DEF:
        if k1 not in kod_till_id or k2 not in kod_till_id:
            continue
        if not ar_giltig_korrelation(k1, k2):
            continue
        id1, id2 = kod_till_id[k1], kod_till_id[k2]
        rader.append((id1, id2, vikt, riktning, evidens, mekanism, ref))
        rader.append((id2, id1, vikt, riktning, evidens, mekanism, ref))

    c.executemany("INSERT OR REPLACE INTO korrelationsmatris VALUES (?,?,?,?,?,?,?)", rader)
    c.executemany("INSERT INTO diagnos_matrismonster VALUES (?,?,?,?,?,?)", DIAGNOS_MONSTER)

    conn.commit()
    conn.close()
    print(f"matris.db skapad: {len(VARIABLER)} variabler, {len(rader)//2} korrelationspar")


def hamta_matrisdata():
    """Returnerar all statisk matrisdata för frontend-visualisering, inkl. korrelationsdetaljer."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    variabler = c.execute(
        "SELECT id,kod,namn,kategori,hjarn_struktur,lokalisation_vikt,patologi_riktning FROM variabler ORDER BY id"
    ).fetchall()
    korrelationer = c.execute(
        "SELECT var1_id,var2_id,vikt,mekanism,referens FROM korrelationsmatris"
    ).fetchall()
    conn.close()

    n = len(variabler)
    matris = [[0.0] * n for _ in range(n)]
    id_till_idx = {v[0]: i for i, v in enumerate(variabler)}

    for i, v in enumerate(variabler):
        matris[i][i] = v[5]  # diagonal = lokalisation_vikt

    korr_detalj = {}
    for (id1, id2, vikt, mekanism, referens) in korrelationer:
        i = id_till_idx.get(id1)
        j = id_till_idx.get(id2)
        if i is None or j is None:
            continue
        matris[i][j] = vikt
        # Spara detaljer för övre triangeln (i < j) för 3D-tooltip
        if i < j:
            korr_detalj[f"{i}_{j}"] = {
                'mekanism': mekanism or '',
                'referens':  referens  or '',
            }

    return {
        'variabler': [{'id': v[0], 'kod': v[1], 'namn': v[2], 'kategori': v[3],
                       'hjarn_struktur': v[4], 'lokalisation_vikt': v[5],
                       'patologi_riktning': v[6]} for v in variabler],
        'matris': matris,
        'korr_detalj': korr_detalj,
        'n': n,
    }


def uppdatera_vikt(var1_id, var2_id, ny_vikt):
    """Uppdaterar en korrelationsvikt i databasen (båda riktningarna)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE korrelationsmatris SET vikt=? WHERE var1_id=? AND var2_id=?",
                     (ny_vikt, var1_id, var2_id))
        conn.execute("UPDATE korrelationsmatris SET vikt=? WHERE var1_id=? AND var2_id=?",
                     (ny_vikt, var2_id, var1_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ─── HUVUDBERÄKNING ───────────────────────────────────────────────────────────

def berakna_avvikelse(varde, patologi_riktning="lågt"):
    """
    Avvikelsegrad 0.0–1.0. Normalt resultat ger alltid 0.0.
    Endast patologiska värden ger aktivering.
    """
    if patologi_riktning == "lågt":
        if varde is None: return 0.0
        if varde >= 40: return 0.0      # NORMALT = NOLL
        if varde >= 39: return 0.03
        if varde >= 37: return 0.10
        if varde >= 35: return 0.25
        if varde >= 33: return 0.40
        if varde >= 30: return 0.60
        if varde >= 27: return 0.75
        if varde >= 25: return 0.85
        return 1.0
    elif patologi_riktning == "högt":
        if varde is None: return 0.0
        if varde <= 0: return 0.0       # NORMALT = NOLL
        if varde == 1: return 0.20
        if varde == 2: return 0.55
        if varde == 3: return 0.85
        return 1.0
    return 0.0


def berakna_matrisaktivering(tscorer: dict, bilddiagnostik: dict, alder: int) -> dict:
    """
    Beräknar matrisaktivering för patientdata.
    tscorer:       dict med T-poäng-nycklar (t.ex. ravlt_dr_t: 28.0)
    bilddiagnostik: dict med råvärden (mta_h, mta_v, gca, koedam, fazekas)
    alder:         patientålder
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    var_rows = c.execute("SELECT id,kod,namn,hjarn_struktur,lokalisation_vikt,patologi_riktning FROM variabler").fetchall()
    variabler = {v[1]: {'id':v[0],'kod':v[1],'namn':v[2],'hjarn_struktur':v[3],
                        'lokalisation_vikt':v[4],'patologi_riktning':v[5]} for v in var_rows}

    korr_rows = c.execute("SELECT var1_id,var2_id,vikt,mekanism,referens FROM korrelationsmatris").fetchall()
    korr_lookup = {(r[0], r[1]): {'vikt':r[2],'mekanism':r[3],'referens':r[4]} for r in korr_rows}

    diag_rows = c.execute(
        "SELECT diagnos,var_id,forvantat_varde,diagnostisk_vikt,sensitivitet,specificitet FROM diagnos_matrismonster"
    ).fetchall()
    conn.close()

    # ─── Steg 1: avvikelse per variabel (inkl normala = 0.0) ─────────────────
    avvikelser = {}  # kod → avvikelse (0.0–1.0), alla mätta variabler
    gematta = set()  # alla koder vars värde faktiskt matades in

    for kod, var in variabler.items():
        tscore_key = KOD_TILL_TSCORE.get(kod)

        if tscore_key == 'tmt_ba_kvot':
            kvot = tscorer.get('tmt_ba_kvot')
            if kvot is not None:
                gematta.add(kod)
                avvikelser[kod] = min(1.0, max(0.0, (kvot - 3.0) / 3.0)) if kvot > 3.0 else 0.0

        elif var['patologi_riktning'] == 'lågt' and tscore_key:
            t = tscorer.get(tscore_key)
            if t is not None:
                gematta.add(kod)
                avvikelser[kod] = berakna_avvikelse(t, 'lågt')

        elif var['patologi_riktning'] == 'högt':
            for fk, (vkod, max_v) in BILD_TILL_KOD.items():
                if vkod == kod:
                    v = bilddiagnostik.get(fk)
                    if v is not None:
                        try:
                            gematta.add(kod)
                            avvikelser[kod] = berakna_avvikelse(float(v), 'högt')
                        except (TypeError, ValueError):
                            pass
                    break

    # ─── Steg 2: struktur aktivering ─────────────────────────────────────────
    # Normalt resultat (avv=0.0) bidrar inte och förstärker inte
    struktur_aktivering = defaultdict(float)
    forstarkta_par_raw = []

    for kod1, avv1 in avvikelser.items():
        if avv1 == 0.0:
            continue  # NORMALT = BIDRAR INTE
        var1 = variabler[kod1]
        s1 = var1['hjarn_struktur']

        # Direktbidrag
        struktur_aktivering[s1] += avv1 * var1['lokalisation_vikt']

        # Förstärkning via korrelationer – BÅDA måste vara patologiska
        for kod2, avv2 in avvikelser.items():
            if kod1 == kod2 or avv2 == 0.0:
                continue  # En normal = ingen förstärkning
            korr = korr_lookup.get((var1['id'], variabler[kod2]['id']))
            if korr is None:
                continue

            forstarkn = avv1 * avv2 * korr['vikt']  # skala 0–10
            var2 = variabler[kod2]
            s2 = var2['hjarn_struktur']

            struktur_aktivering[s1] += forstarkn
            struktur_aktivering[s2] += forstarkn * 0.5

            if korr['vikt'] >= 5.0:
                forstarkta_par_raw.append({
                    'var1': var1['namn'], 'var2': var2['namn'],
                    'var1_kod': kod1, 'var2_kod': kod2,
                    'vikt': korr['vikt'],
                    'avv1': round(avv1, 2), 'avv2': round(avv2, 2),
                    'mekanism': korr['mekanism'],
                    'referens': korr['referens'],
                    'forstarkningsfaktor': round(forstarkn, 2),
                })

    # Deduplicera par
    seen_par = set()
    forstarkta_par = []
    for par in sorted(forstarkta_par_raw, key=lambda x: x['forstarkningsfaktor'], reverse=True):
        key = tuple(sorted([par['var1'], par['var2']]))
        if key not in seen_par:
            seen_par.add(key)
            forstarkta_par.append(par)

    # ─── Steg 3: normalisera strukturaktivering ───────────────────────────────
    max_akt = max(struktur_aktivering.values()) if struktur_aktivering else 1
    normaliserad = {
        s: round((v / max_akt) * 100, 1)
        for s, v in sorted(struktur_aktivering.items(), key=lambda x: x[1], reverse=True)
    }

    # ─── Steg 4: matrisförstärkt T-poäng (för spindel lager 3) ──────────────
    patologiska = {k: v for k, v in avvikelser.items() if v > 0.0}
    matris_t = {}
    for kod, avv in patologiska.items():
        tscore_key = KOD_TILL_TSCORE.get(kod)
        if not tscore_key or tscore_key == 'tmt_ba_kvot':
            continue
        t_orig = tscorer.get(tscore_key)
        if t_orig is None:
            continue
        var = variabler[kod]
        forstarkn_sum = 0.0
        for kod2, avv2 in patologiska.items():
            if kod2 == kod:
                continue
            korr = korr_lookup.get((var['id'], variabler[kod2]['id']))
            if korr:
                forstarkn_sum += avv2 * korr['vikt'] / 10.0
        delta = min(15, forstarkn_sum * 8)
        matris_t[tscore_key] = round(max(20, t_orig - delta), 1)

    # ─── Steg 5: diagnospoäng ─────────────────────────────────────────────────
    diagnos_score = defaultdict(float)
    diagnos_max = defaultdict(float)
    id_till_kod = {v['id']: k for k, v in variabler.items()}

    for (diagnos, var_id, forv, diag_vikt, sens, spec_val) in diag_rows:
        kod = id_till_kod.get(var_id)
        if kod not in gematta:
            continue
        diagnos_max[diagnos] += diag_vikt
        avv = avvikelser.get(kod, 0.0)
        if avv == 0.0:
            continue
        var = variabler[kod]
        if var['patologi_riktning'] == forv or (forv == 'lågt' and var['patologi_riktning'] == 'lågt'):
            diagnos_score[diagnos] += diag_vikt * avv * sens

    diagnos_pct = {
        d: round((diagnos_score[d] / diagnos_max[d]) * 100, 1)
        for d in diagnos_max if diagnos_max[d] > 0
    }
    diagnos_rank = sorted(diagnos_pct.items(), key=lambda x: x[1], reverse=True)

    # ─── Steg 6: textsammanfattning ───────────────────────────────────────────
    sammanfattning = _bygg_sammanfattning(
        patologiska, forstarkta_par[:5], normaliserad, diagnos_rank, variabler
    )

    return {
        'struktur_aktivering': normaliserad,
        'forstarkta_par': forstarkta_par[:10],
        'patologiska_variabler': {k: round(v, 3) for k, v in patologiska.items()},
        'avvikelser': {k: round(v, 3) for k, v in avvikelser.items()},
        'diagnos_score': diagnos_pct,
        'diagnos_rank': diagnos_rank[:4],
        'matris_t': matris_t,
        'sammanfattning': sammanfattning,
        'n_patologiska': len(patologiska),
        'n_forstarkta_par': len(forstarkta_par),
    }


def _bygg_sammanfattning(patologiska, forstarkta_par, normaliserad, diagnos_rank, variabler):
    rader = ["MATRISANALYS – Multidimensionell profil", "─" * 42]

    if not patologiska:
        rader.append("\nSamtliga testresultat inom normalgränser.")
        rader.append("Inga strukturella aktiveringssignaler.")
        return "\n".join(rader)

    if not forstarkta_par:
        patvar_namn = [variabler[k]['namn'] for k in list(patologiska.keys())[:3]]
        rader.append(f"\nEnstaka avvikelse i {', '.join(patvar_namn)}.")
        rader.append("Ingen konvergent signal från flera oberoende mått.")
    else:
        starkaste = forstarkta_par[0]
        top_struct = list(normaliserad.keys())[0] if normaliserad else "okänd"
        rader.append(f"\nKonvergent signal: {len(forstarkta_par)} oberoende mått pekar på")
        rader.append(f"samma hjärnstruktur ({top_struct}).")
        rader.append(f"Starkaste förstärkningspar: {starkaste['var1']} + {starkaste['var2']}")
        rader.append(f"(förstärkning {starkaste['forstarkningsfaktor']:.1f}/10)")

    if diagnos_rank:
        rader.append("\nDiagnos-indikation (matrisbaserad):")
        for d, pct in diagnos_rank[:3]:
            rader.append(f"  {d}: {pct}%")

    return "\n".join(rader)


# ─── VALIDERINGSSCENARIER ────────────────────────────────────────────────────

def _validera():
    scenarion = [
        {
            'namn': 'A – Alla normala',
            'tscorer': {
                'ravlt_dr_t': 52, 'bvmt_dr_t': 48, 'tmt_b_t': 50, 'block_t': 47
            },
            'bilddiagnostik': {'mta_h': 0, 'mta_v': 0, 'fazekas': 0},
            'forvantad_patol': 0,
            'forvantad_par': 0,
        },
        {
            'namn': 'B – Isolerad patologi (RAVLT_DR=28)',
            'tscorer': {'ravlt_dr_t': 28, 'bvmt_dr_t': 48},
            'bilddiagnostik': {},
            'forvantad_ravlt_dr_avv': 0.60,
            'forvantad_bvmt_dr_avv': 0.0,
            'forvantad_forstarkn_ravlt_bvmt': 0.0,
        },
        {
            'namn': 'C – Konvergent patologi (AD-mönster)',
            'tscorer': {'ravlt_dr_t': 25, 'bvmt_dr_t': 30, 'tmt_b_t': 38, 'block_t': 42},
            'bilddiagnostik': {'mta_h': 3, 'mta_v': 3},
            'forvantad_ravlt_dr_avv': 0.85,
            'forvantad_bvmt_dr_avv': 0.60,
            'forvantad_mta_avv': 0.85,
            'forvantad_block_avv': 0.0,
        },
        {
            'namn': 'D – Subkortikal/vaskulär',
            'tscorer': {'tmt_b_t': 32, 'kod_t': 34, 'ravlt_dr_t': 42, 'bvmt_dr_t': 44},
            'bilddiagnostik': {'fazekas': 2},
            'forvantad_fazekas_avv': 0.55,
            'forvantad_ravlt_avv': 0.0,
            'forvantad_bvmt_avv': 0.0,
        },
    ]

    print("\n" + "═" * 55)
    print("GRANSKNING AV MATRISBERÄKNING:")
    print("  - Avvikelse beräknas via berakna_avvikelse() steg-funktion")
    print("  - T≥40 ger alltid avvikelse 0.0 (normalt = noll bidrag)")
    print("  - Förstärkning = avv1 × avv2 × vikt (0–10 skala)")
    print("  - Normala variabler utesluts från direktbidrag OCH förstärkning")
    print("═" * 55 + "\n")

    for sc in scenarion:
        res = berakna_matrisaktivering(sc['tscorer'], sc.get('bilddiagnostik', {}), 70)
        avv = res['avvikelser']
        par = res['forstarkta_par']
        patol = res['patologiska_variabler']
        dom = list(res['struktur_aktivering'].keys())[0] if res['struktur_aktivering'] else 'ingen'
        dom_pct = list(res['struktur_aktivering'].values())[0] if res['struktur_aktivering'] else 0

        ok = True
        felmeddelanden = []

        if sc['namn'].startswith('A'):
            if len(patol) > 0:
                ok = False; felmeddelanden.append(f"  FEL: {len(patol)} patologiska variabler, förväntat 0")
            if len(par) > 0:
                ok = False; felmeddelanden.append(f"  FEL: {len(par)} förstärkningspar, förväntat 0")

        if sc['namn'].startswith('B'):
            rd = avv.get('ravlt_dr', 0)
            bd = avv.get('bvmt_dr', 0)
            fp_ravlt_bvmt = next((p for p in par if 'RAVLT' in p['var1'] and 'BVMT' in p['var2'] or
                                  'BVMT' in p['var1'] and 'RAVLT' in p['var2']), None)
            if abs(rd - 0.75) > 0.05:
                ok = False; felmeddelanden.append(f"  FEL: ravlt_dr avvikelse={rd}, förväntat ≈0.75 (T=28 → [27,30) → 0.75)")
            if bd != 0.0:
                ok = False; felmeddelanden.append(f"  FEL: bvmt_dr avvikelse={bd}, förväntat 0.0")
            if fp_ravlt_bvmt is not None:
                ok = False; felmeddelanden.append(f"  FEL: RAVLT↔BVMT förstärkt, förväntat 0.0 (en är normal)")

        if sc['namn'].startswith('C'):
            rd = avv.get('ravlt_dr', 0)
            bd = avv.get('bvmt_dr', 0)
            mh = avv.get('mta_hoger', 0)
            mv = avv.get('mta_vanster', 0)
            bl = avv.get('block_design', 0)
            if abs(rd - 0.85) > 0.05:
                ok = False; felmeddelanden.append(f"  FEL: ravlt_dr avvikelse={rd}, förväntat 0.85")
            if abs(bd - 0.60) > 0.05:
                ok = False; felmeddelanden.append(f"  FEL: bvmt_dr avvikelse={bd}, förväntat 0.60")
            if abs(mh - 0.85) > 0.05:
                ok = False; felmeddelanden.append(f"  FEL: mta_hoger avvikelse={mh}, förväntat 0.85")
            if bl != 0.0:
                ok = False; felmeddelanden.append(f"  FEL: block_design avvikelse={bl}, förväntat 0.0")
            # Förväntat starkaste par: RAVLT_DR↔MTA_v = 0.85×0.85×9.0 = 6.50
            forvantad_forstarkn = round(0.85 * 0.85 * 9.0, 2)
            topp_par = par[0] if par else None
            if topp_par is None:
                ok = False; felmeddelanden.append("  FEL: Inga förstärkningspar")
            else:
                if abs(topp_par['forstarkningsfaktor'] - forvantad_forstarkn) > 0.5:
                    ok = False; felmeddelanden.append(
                        f"  FEL: Topp-förstärkning={topp_par['forstarkningsfaktor']}, förväntat ≈{forvantad_forstarkn}")

        if sc['namn'].startswith('D'):
            fz = avv.get('fazekas', 0)
            rd = avv.get('ravlt_dr', 0)
            bd = avv.get('bvmt_dr', 0)
            if abs(fz - 0.55) > 0.05:
                ok = False; felmeddelanden.append(f"  FEL: fazekas avvikelse={fz}, förväntat 0.55")
            if rd != 0.0:
                ok = False; felmeddelanden.append(f"  FEL: ravlt_dr avvikelse={rd}, förväntat 0.0 (normalt)")
            if bd != 0.0:
                ok = False; felmeddelanden.append(f"  FEL: bvmt_dr avvikelse={bd}, förväntat 0.0 (normalt)")

        status = "GODKÄND" if ok else "FEL"
        print(f"SCENARIO {sc['namn']}: {status}")
        patol_lista = ', '.join(f"{k}={v}" for k, v in sorted(patol.items())) or 'inga'
        print(f"  Patologiska variabler: {patol_lista}")
        par_lista = ', '.join(f"{p['var1'].split()[0]}↔{p['var2'].split()[0]}={p['forstarkningsfaktor']}"
                              for p in par[:4]) or 'inga'
        print(f"  Aktiva förstärkningspar: {par_lista}")
        print(f"  Dominerande struktur: {dom} ({dom_pct}%)")
        for fel in felmeddelanden:
            print(fel)
        print()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    skapa_databas()
    print("Klar. matris.db är skapad.")
    _validera()
