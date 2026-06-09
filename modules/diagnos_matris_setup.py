"""
diagnos_matris_setup.py
Korrelationsmatris: Demenssjukdomar × Neuropsykologiska test
Vikterna beräknas via sjukdomars hjärnregionsprofil × testens regionspecificitet.
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'diagnos_matris.db')

# ─── DEMENSSJUKDOMAR ──────────────────────────────────────────────────────────
# (id, namn, kategori, patologi, kortbeskrivning)
DEMENSSJUKDOMAR = [
    ('AD',       'Alzheimers sjukdom (typisk)',         'AD-spektrum',     'Amyloid β, tau (NFT)',
     'Amnestisk debut, episodisk minnesförlust, hippocampal atrofi bilateral. '
     'Gradvis progression. Vanligast 65+. CSF/PET-biomarkörer specifika.'),
    ('AD_post',  'Bakre kortikal atrofi (AD)',          'AD-spektrum',     'Amyloid β, tau (posterior)',
     'AD-variant med visuospatial debut. Bevarad episodisk minnesförmåga tidigt. '
     'Parieto-occipital atrofi. Ofta yngre debut (<65 år).'),
    ('DLB',      'Lewykroppsdemens',                    'Lewykroppar',     'α-synuklein (kortikal)',
     'Fluktuerande kognition, synhallucinationer, parkinsonism, RBD. '
     'Disproportionell visuospatial svikt. DaTscan patologisk. Lewy-kortikal distribution.'),
    ('PDD',      'Parkinsons sjukdom med demens',       'Lewykroppar',     'α-synuklein (subkortikal→kortikal)',
     'PD-diagnos >1 år före demens. Exekutiv och visuospatial svikt dominerar. '
     'Subkortikal-frontal profil. RBD vanlig. Lewy-bodies diffust.'),
    ('bvFTD',    'FTD – beteendevariant',               'FTD-spektrum',    'TDP-43, tau, FUS',
     'Beteendeförändringar tidigt: disinhibition, apati, kompulsivitet, hyperoralitet. '
     'Bevarad spatial förmåga och episodiskt minne tidigt. Frontal-insulär atrofi.'),
    ('svPPA',    'Semantisk demens (svPPA)',             'FTD-spektrum',    'TDP-43 typ C',
     'Semantisk minnesförlust: anomia, ordkomprehension. Flytande men tomt tal. '
     'Anterior temporal bilateral atrofi, vänsterdominant. Episodiskt minne relativt bevarat.'),
    ('nfvPPA',   'PPA – icke-flytande variant',         'FTD-spektrum',    'Tau (CBD/PSP-patologi)',
     'Agrammatism och talapraxia. Mödosamt, tveksamt tal. Broca-region och '
     'premotorisk cortex vänster. Episodiskt minne bevarat.'),
    ('lvPPA',    'PPA – logopenisk variant',            'AD-spektrum',     'Amyloid β, tau (posterior temporal)',
     'Ordfyndsstörning och nedsatt meningsrepetition. Relativt bevarat '
     'semantisk kunskap. Posterior temporal-parietal vänster. AD-biomarkörer positiva ~80%.'),
    ('VaD_sub',  'Vaskulär demens – subkortikal',       'Vaskulär',        'Cerebral småkärlssjukdom',
     'Exekutiv svikt och processhastighet nedsatt. Gångstörning. '
     'Fazekas ≥2. Stegvis eller gradvis förlopp. Subkortikal vit substans-patologi.'),
    ('VaD_multi','Vaskulär demens – kortikal/multiinfarkt','Vaskulär',      'Makroangiopati, multiinfarkter',
     'Varierande beroende på infarkters lokalisation. Ofta abrupt debut. '
     'Stegvis förlopp. Multipla kortikala infarkter.'),
    ('PSP_R',    'Progressiv supranukleär pares',       'Parkinsonistisk', 'Tau (4R)',
     'Vertikal blickpares, tidiga fall bakåt, axial rigiditet. Exekutiv frontal '
     'svikt. Hjärnstam/midbrain-atrofi. Hummingbird-tecken MR.'),
    ('CBS',      'Kortikobasal degeneration',           'Parkinsonistisk', 'Tau (CBD, 4R)',
     'Asymmetrisk limbapraxia, alien hand, kortikal sensibilitetsnedsättning. '
     'Parietal-frontal atrofi asymmetrisk. Snabb progression.'),
    ('MSA_P',    'Multipel systematrofi – P-typ',       'Parkinsonistisk', 'α-synuklein (subkortikal)',
     'Svår parkinsonism med autonom svikt. Begränsad L-dopa-respons. '
     'Putamen-atrofi. Kognitiv påverkan relativt lindrig/sen.'),
    ('FTD_MND',  'FTD med motorneurosjukdom (ALS)',     'FTD-spektrum',    'TDP-43 typ B',
     'FTD-beteendeprofil kombinerat med MND-tecken: fasciculationer, muskelatrofi. '
     'C9orf72-mutation vanlig. Frontal-temporal + motorisk cortex.'),
    ('NPH',      'Normaltrykkshydrocefalus',            'Övrigt',          'CSF-cirkulationsstörning',
     'Klassisk triad: demens + gångstörning + urininkontinens. Subkortikal-frontal '
     'svikt. Karaktäristisk gång (magnetfotsgång). Potentiellt reversibel.'),
    ('CJD',      'Creutzfeldt-Jakobs sjukdom',          'Prionsjukdom',    'Prionprotein (PrPSc)',
     'Snabbt progredierande demens (veckor-månader). Myoklonus, ataxia, '
     'synstörningar. 14-3-3 i CSF. DWI-MR karakteristisk. Alltid fatal.'),
    ('Mixed',    'Blandad demens (AD + VaD)',           'Blandad',         'Amyloid β + vaskulär',
     'AD-hippocampal profil kombinerat med subkortikal vitsubstanspåverkan. '
     'Mycket vanlig i klinisk praxis (>50% av äldre demensfall).'),
]

# ─── SJUKDOMARS HJÄRNREGIONSPROFIL ────────────────────────────────────────────
# Evidensbaserade vikter 0–10 per region.
# Regioner matchar nyckelord i REGION_TO_STRUKT nedan.
DIAGNOS_HJARN = {
    'AD': {
        'hippocampus': 9.5, 'entorhinal': 9.5, 'perirhinal': 8.5,
        'temporal_anterior': 6.0, 'temporal_lateral': 5.0, 'parietal': 6.0,
        'occipital': 2.0, 'frontal_dlpfc': 4.0, 'frontal_inferior_L': 3.0,
        'anterior_cingulate': 5.0, 'striatum': 2.0, 'thalamus': 2.0,
        'white_matter': 3.0, 'diffuse_cortex': 3.0,
    },
    'AD_post': {
        'hippocampus': 4.0, 'entorhinal': 3.0, 'perirhinal': 3.0,
        'temporal_anterior': 3.0, 'temporal_lateral': 4.0, 'parietal': 9.0,
        'occipital': 9.0, 'frontal_dlpfc': 2.0, 'frontal_inferior_L': 1.0,
        'anterior_cingulate': 2.0, 'striatum': 1.0, 'thalamus': 1.0,
        'white_matter': 4.0, 'diffuse_cortex': 5.0,
    },
    'DLB': {
        'hippocampus': 4.0, 'entorhinal': 3.0, 'perirhinal': 3.0,
        'temporal_anterior': 3.0, 'temporal_lateral': 5.0, 'parietal': 8.5,
        'occipital': 9.0, 'frontal_dlpfc': 4.0, 'frontal_inferior_L': 2.0,
        'anterior_cingulate': 4.0, 'striatum': 6.0, 'thalamus': 4.0,
        'white_matter': 5.0, 'diffuse_cortex': 6.0,
    },
    'PDD': {
        'hippocampus': 3.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 2.0, 'temporal_lateral': 3.0, 'parietal': 3.0,
        'occipital': 2.0, 'frontal_dlpfc': 5.0, 'frontal_inferior_L': 3.0,
        'anterior_cingulate': 3.0, 'striatum': 8.0, 'thalamus': 6.0,
        'white_matter': 4.0, 'diffuse_cortex': 3.0,
    },
    'bvFTD': {
        'hippocampus': 2.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 8.0, 'temporal_lateral': 7.0, 'parietal': 3.0,
        'occipital': 1.0, 'frontal_dlpfc': 9.0, 'frontal_inferior_L': 8.0,
        'anterior_cingulate': 9.0, 'striatum': 3.0, 'thalamus': 2.0,
        'white_matter': 4.0, 'diffuse_cortex': 5.0,
    },
    'svPPA': {
        'hippocampus': 0.5, 'entorhinal': 2.0, 'perirhinal': 4.5,
        'temporal_anterior': 9.0, 'temporal_lateral': 8.0, 'parietal': 3.0,
        'occipital': 1.0, 'frontal_dlpfc': 2.0, 'frontal_inferior_L': 3.0,
        'anterior_cingulate': 2.0, 'striatum': 1.0, 'thalamus': 1.0,
        'white_matter': 3.0, 'diffuse_cortex': 4.0,
    },
    'nfvPPA': {
        'hippocampus': 2.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 3.0, 'temporal_lateral': 3.0, 'parietal': 3.0,
        'occipital': 1.0, 'frontal_dlpfc': 8.0, 'frontal_inferior_L': 9.5,
        'anterior_cingulate': 5.0, 'striatum': 2.0, 'thalamus': 1.0,
        'white_matter': 4.0, 'diffuse_cortex': 3.0,
    },
    'lvPPA': {
        'hippocampus': 3.0, 'entorhinal': 3.0, 'perirhinal': 3.0,
        'temporal_anterior': 3.0, 'temporal_lateral': 7.0, 'parietal': 8.0,
        'occipital': 2.0, 'frontal_dlpfc': 5.0, 'frontal_inferior_L': 4.0,
        'anterior_cingulate': 2.0, 'striatum': 1.0, 'thalamus': 1.0,
        'white_matter': 3.0, 'diffuse_cortex': 4.0,
    },
    'VaD_sub': {
        'hippocampus': 3.0, 'entorhinal': 3.0, 'perirhinal': 2.0,
        'temporal_anterior': 2.0, 'temporal_lateral': 3.0, 'parietal': 3.0,
        'occipital': 2.0, 'frontal_dlpfc': 6.0, 'frontal_inferior_L': 5.0,
        'anterior_cingulate': 6.0, 'striatum': 7.5, 'thalamus': 6.0,
        'white_matter': 9.5, 'diffuse_cortex': 2.0,
    },
    'VaD_multi': {
        'hippocampus': 4.0, 'entorhinal': 3.0, 'perirhinal': 3.0,
        'temporal_anterior': 4.0, 'temporal_lateral': 5.0, 'parietal': 6.0,
        'occipital': 4.0, 'frontal_dlpfc': 7.0, 'frontal_inferior_L': 6.0,
        'anterior_cingulate': 5.0, 'striatum': 4.0, 'thalamus': 4.0,
        'white_matter': 8.0, 'diffuse_cortex': 6.0,
    },
    'PSP_R': {
        'hippocampus': 2.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 2.0, 'temporal_lateral': 2.0, 'parietal': 3.0,
        'occipital': 2.0, 'frontal_dlpfc': 7.5, 'frontal_inferior_L': 4.0,
        'anterior_cingulate': 7.0, 'striatum': 6.0, 'thalamus': 9.0,
        'white_matter': 4.0, 'diffuse_cortex': 2.0,
    },
    'CBS': {
        'hippocampus': 2.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 3.0, 'temporal_lateral': 3.0, 'parietal': 9.5,
        'occipital': 2.0, 'frontal_dlpfc': 8.0, 'frontal_inferior_L': 5.0,
        'anterior_cingulate': 4.0, 'striatum': 6.0, 'thalamus': 4.0,
        'white_matter': 4.0, 'diffuse_cortex': 3.0,
    },
    'MSA_P': {
        'hippocampus': 2.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 2.0, 'temporal_lateral': 2.0, 'parietal': 4.0,
        'occipital': 1.0, 'frontal_dlpfc': 5.0, 'frontal_inferior_L': 3.0,
        'anterior_cingulate': 3.0, 'striatum': 9.0, 'thalamus': 5.0,
        'white_matter': 4.0, 'diffuse_cortex': 2.0,
    },
    'FTD_MND': {
        'hippocampus': 3.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 7.0, 'temporal_lateral': 6.0, 'parietal': 4.0,
        'occipital': 1.0, 'frontal_dlpfc': 8.0, 'frontal_inferior_L': 7.0,
        'anterior_cingulate': 6.0, 'striatum': 2.0, 'thalamus': 1.0,
        'white_matter': 5.0, 'diffuse_cortex': 4.0,
    },
    'NPH': {
        'hippocampus': 3.0, 'entorhinal': 2.0, 'perirhinal': 2.0,
        'temporal_anterior': 2.0, 'temporal_lateral': 2.0, 'parietal': 3.0,
        'occipital': 1.0, 'frontal_dlpfc': 7.0, 'frontal_inferior_L': 5.0,
        'anterior_cingulate': 5.0, 'striatum': 3.0, 'thalamus': 3.0,
        'white_matter': 7.0, 'diffuse_cortex': 2.0,
    },
    'CJD': {
        'hippocampus': 7.0, 'entorhinal': 6.0, 'perirhinal': 6.0,
        'temporal_anterior': 5.0, 'temporal_lateral': 6.0, 'parietal': 7.0,
        'occipital': 6.0, 'frontal_dlpfc': 6.0, 'frontal_inferior_L': 5.0,
        'anterior_cingulate': 6.0, 'striatum': 7.0, 'thalamus': 7.0,
        'white_matter': 8.0, 'diffuse_cortex': 8.0,
    },
    'Mixed': {
        'hippocampus': 8.0, 'entorhinal': 8.0, 'perirhinal': 7.0,
        'temporal_anterior': 5.0, 'temporal_lateral': 5.0, 'parietal': 7.0,
        'occipital': 3.0, 'frontal_dlpfc': 5.0, 'frontal_inferior_L': 3.0,
        'anterior_cingulate': 4.0, 'striatum': 3.0, 'thalamus': 3.0,
        'white_matter': 7.0, 'diffuse_cortex': 5.0,
    },
}

# ─── REGION → TEST-STRUKTUR-STRÄNGAR ─────────────────────────────────────────
# Mappar regionnyckelord mot hjarn_struktur-strängar i variabler-tabellen.
# Varje träff aktiverar korrelationen med det variabelns lokalisation_vikt.
REGION_TO_STRUKT = {
    'hippocampus':        ['hippocampus CA1, subiculum',
                           'hippocampus, entorhinalcortex',
                           'hippocampus höger, parietallob',
                           'hippocampus höger, parahippocampal',
                           'hippocampus höger, frontal-parietal',
                           'hippocampus höger, entorhinalcortex',
                           'hippocampus vänster, entorhinalcortex',
                           'perirhinal cortex, hippocampus'],
    'entorhinal':         ['hippocampus, entorhinalcortex',
                           'hippocampus höger, entorhinalcortex',
                           'hippocampus vänster, entorhinalcortex'],
    'perirhinal':         ['perirhinal cortex, hippocampus'],
    'temporal_anterior':  ['anteriora temporalloben vänster'],
    'temporal_lateral':   ['temporallob vänster, frontal',
                           'temporallob vänster, neocortex'],
    'parietal':           ['parietallob höger, occipital',
                           'parietallob höger, occipital-parietal',
                           'parietallob, precuneus, occipital',
                           'hippocampus höger, parietallob',
                           'DLPFC bilateral, inferior parietal',
                           'DLPFC bilateral, parietallob'],
    'occipital':          ['parietallob höger, occipital',
                           'parietallob höger, occipital-parietal',
                           'parietallob, precuneus, occipital'],
    'frontal_dlpfc':      ['DLPFC bilateral, anteriora cingulate',
                           'DLPFC, anterior cingulate',
                           'inferior frontal vänster (Broca), DLPFC',
                           'DLPFC bilateral, inferior parietal',
                           'DLPFC bilateral, parietallob',
                           'striatum, thalamus, prefrontal',
                           'temporallob vänster, frontal'],
    'frontal_inferior_L': ['inferior frontal vänster (Broca), DLPFC'],
    'anterior_cingulate': ['anteriora cingulate, thalamus, striatum',
                           'DLPFC bilateral, anteriora cingulate',
                           'DLPFC, anterior cingulate'],
    'striatum':           ['anteriora cingulate, thalamus, striatum',
                           'striatum, thalamus, prefrontal'],
    'thalamus':           ['anteriora cingulate, thalamus, striatum',
                           'striatum, thalamus, prefrontal'],
    'white_matter':       ['vit substans, periventrikulärt'],
    'diffuse_cortex':     ['cortex diffust'],
}

# ─── T-POÄNG-NYCKEL TILL VARIABELKOD ─────────────────────────────────────────
KOD_TILL_TSCORE = {
    'ravlt_total': 'ravlt_total_t', 'ravlt_dr': 'ravlt_dr_t',
    'bvmt_total': 'bvmt_total_t',  'bvmt_dr': 'bvmt_dr_t',
    'rcft_dr': 'rcft_30min_t',     'rcft_kopia': 'rcft_kop_t',
    'tmt_a': 'tmt_a_t',           'tmt_b': 'tmt_b_t',
    'fas_total': 'fas_t',          'djurnamn': 'djur_t',
    'block_design': 'block_t',     'kodning': 'kod_t',
    'sifferrep_bak': 'siff_t',     'likheter': 'lik_t',
    'information': 'info_t',
}
BILD_TILL_KOD = {
    'mta_h': ('mta_hoger', 4.0), 'mta_v': ('mta_vanster', 4.0),
    'gca': ('gca', 3.0), 'koedam': ('koedam', 3.0), 'fazekas': ('fazekas', 3.0),
}

# ─── DATABAS ─────────────────────────────────────────────────────────────────

def skapa_databas():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
    DROP TABLE IF EXISTS demenssjukdomar;
    DROP TABLE IF EXISTS diagnos_test_matris;

    CREATE TABLE demenssjukdomar (
        id          TEXT PRIMARY KEY,
        namn        TEXT,
        kategori    TEXT,
        patologi    TEXT,
        beskrivning TEXT
    );

    CREATE TABLE diagnos_test_matris (
        diagnos_id  TEXT,
        var_kod     TEXT,
        vikt        REAL,
        PRIMARY KEY (diagnos_id, var_kod)
    );
    """)

    for row in DEMENSSJUKDOMAR:
        c.execute("INSERT INTO demenssjukdomar VALUES (?,?,?,?,?)", row)

    conn.commit()
    conn.close()
    print(f"diagnos_matris.db: {len(DEMENSSJUKDOMAR)} sjukdomar")


# ─── BERÄKNA TEST-DIAGNOS-VIKTER ─────────────────────────────────────────────

def berakna_alla_vikter():
    """
    Beräknar diagnos × test-vikter via regionöverlapp.
    Returnerar: {diagnos_id: {var_kod: normaliserad_vikt (0-10)}}
    """
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from modules.matris_setup import VARIABLER as _VARIABLER

    # Bygg struktur-lookup: hjarn_struktur → (var_kod, lokalisation_vikt)
    strukt_lookup = {}
    for v in _VARIABLER:
        vkod, vstrukt, vlok = v[1], v[5], v[7]
        if vstrukt not in strukt_lookup:
            strukt_lookup[vstrukt] = []
        strukt_lookup[vstrukt].append((vkod, vlok))

    resultat = {}
    for diagnos_id, regioner in DIAGNOS_HJARN.items():
        test_vikter = {}

        for region, severity in regioner.items():
            strukt_list = REGION_TO_STRUKT.get(region, [])
            for strukt in strukt_list:
                for vkod, vlok in strukt_lookup.get(strukt, []):
                    bidrag = (severity / 10.0) * vlok
                    test_vikter[vkod] = test_vikter.get(vkod, 0.0) + bidrag

        # Normalisera 0–10
        max_v = max(test_vikter.values()) if test_vikter else 1.0
        resultat[diagnos_id] = {k: round(v / max_v * 10, 2) for k, v in test_vikter.items()}

    return resultat


def spara_vikter():
    """Beräknar och sparar alla diagnos-test-vikter till DB."""
    skapa_databas()
    vikter = berakna_alla_vikter()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for diagnos_id, tvikter in vikter.items():
        for vkod, vikt in tvikter.items():
            c.execute("INSERT OR REPLACE INTO diagnos_test_matris VALUES (?,?,?)",
                      (diagnos_id, vkod, vikt))
    conn.commit()
    conn.close()
    total = sum(len(v) for v in vikter.values())
    print(f"Sparade {total} diagnos-test-vikter ({len(vikter)} sjukdomar)")
    return vikter


def hamta_matrisdata():
    """
    Returnerar hela matrisen för frontend-visualisering.
    {diagnos_lista, var_lista, matris (N_diag × N_var)}
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    diagnoser = c.execute(
        "SELECT id, namn, kategori, patologi, beskrivning FROM demenssjukdomar ORDER BY rowid"
    ).fetchall()
    vikter_rows = c.execute("SELECT diagnos_id, var_kod, vikt FROM diagnos_test_matris").fetchall()
    conn.close()

    # Hämta variabler från matris.db
    import sqlite3 as _sq3, os as _os
    matris_db = _os.path.join(_os.path.dirname(__file__), 'matris.db')
    conn2 = _sq3.connect(matris_db)
    variabler = conn2.execute(
        "SELECT id, kod, namn, hjarn_struktur FROM variabler ORDER BY id"
    ).fetchall()
    conn2.close()

    diag_idx = {d[0]: i for i, d in enumerate(diagnoser)}
    var_idx  = {v[1]: i for i, v in enumerate(variabler)}

    n_d, n_v = len(diagnoser), len(variabler)
    matris = [[0.0] * n_v for _ in range(n_d)]

    for (did, vkod, vikt) in vikter_rows:
        di = diag_idx.get(did)
        vi = var_idx.get(vkod)
        if di is not None and vi is not None:
            matris[di][vi] = vikt

    return {
        'diagnoser': [{'id':d[0],'namn':d[1],'kategori':d[2],'patologi':d[3],'beskrivning':d[4]}
                      for d in diagnoser],
        'variabler': [{'id':v[0],'kod':v[1],'namn':v[2],'hjarn_struktur':v[3]}
                      for v in variabler],
        'matris': matris,
        'n_diag': n_d, 'n_var': n_v,
    }


def _hamta_deviation(vkod, tscorer, bilddiagnostik):
    """Returnerar (deviation 0-1, measured bool) för en variabel."""
    tscore_key = KOD_TILL_TSCORE.get(vkod)
    if tscore_key:
        t = tscorer.get(tscore_key)
        if t is not None:
            return max(0.0, (40 - float(t)) / 40), True

    if vkod == 'tmt_ba_kvot':
        kvot = tscorer.get('tmt_ba_kvot')
        if kvot is not None:
            fv = float(kvot)
            return (min(1.0, (fv - 3.0) / 3.0) if fv > 3.0 else 0.0), True

    if vkod in ('mta_hoger', 'mta_vanster', 'gca', 'koedam', 'fazekas'):
        for fk, (vc, mx) in BILD_TILL_KOD.items():
            if vc == vkod:
                v = bilddiagnostik.get(fk)
                if v is not None:
                    fv = float(v)
                    return (min(1.0, fv / mx) if fv >= mx * 0.5 else 0.0), True

    return 0.0, False


def matcha_patient(tscorer: dict, bilddiagnostik: dict) -> dict:
    """
    Beräknar hur väl patientens profil matchar varje demenssjukdom.

    Kontrastformel: bidrag = (2*vn - 1) * dev
      vn = normaliserad vikt (0-1), dev = patientens deviation (0-1)
      Om vn=0.9 och dev=0.8 → bidrag +0.64  (förväntat + faktiskt patologiskt)
      Om vn=0.2 och dev=0.8 → bidrag −0.48  (oförväntat patologiskt → straff)
      Om dev=0  → bidrag=0 (normalt test bidrar inte alls)

    Returnerar: {diagnos_id: match_procent (0-100), ...} sorterat fallande.
    Poängen är absoluta (ej normaliserade mot max i batchen) för att
    spindeln ska kunna jämföras rättvist mellan olika testbatterier.
    """
    vikter = berakna_alla_vikter()

    # Samla alla uppmätta deviationer en gång
    measured_devs = {}
    for vkod in set(k for tv in vikter.values() for k in tv):
        dev, ok = _hamta_deviation(vkod, tscorer, bilddiagnostik)
        if ok:
            measured_devs[vkod] = dev

    if not measured_devs:
        return {d: 0.0 for d in vikter}

    result = {}
    for diagnos_id, tvikter in vikter.items():
        score      = 0.0
        ideal_max  = 0.0  # max möjlig score om alla högt-viktade test vore 100% patologiska
        denom      = 0.0  # sum(vn) för alla mätta variabler

        for vkod, vikt in tvikter.items():
            if vikt < 1.0 or vkod not in measured_devs:
                continue
            vn  = vikt / 10.0
            dev = measured_devs[vkod]
            score += (2.0 * vn - 1.0) * dev
            denom += vn
            if vn > 0.5:
                ideal_max += (2.0 * vn - 1.0)  # max bidrag om dev=1 för detta test

        if denom <= 0 or ideal_max <= 0:
            result[diagnos_id] = 0.0
        else:
            # Normalisera mot ideal_max/denom (vad en "perfekt" patient skulle ge)
            ideal_pct = ideal_max / denom
            raw_pct   = max(0.0, score / denom)
            result[diagnos_id] = round(min(100.0, raw_pct / ideal_pct * 100), 1)

    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))


if __name__ == '__main__':
    spara_vikter()
    print("Klar.")
