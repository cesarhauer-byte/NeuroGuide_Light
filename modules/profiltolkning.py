# ══════════════════════════════════════════════════════════════════════
# ROBARET v3 – Profiltolkningsmodul
# Mönsterigenkänning + fritekstsammanfattning
# ══════════════════════════════════════════════════════════════════════

# ── MÖNSTERDEFINITIONER ───────────────────────────────────────────────
# Varje mönster har:
#   - namn
#   - beskrivning
#   - villkor: lista av (test, operator, tröskel)
#   - associerade diagnoser
#   - klinisk kommentar

MONSTER = [
    {
        "id": "hippocampalt",
        "namn": "Hippocampalt minnesmönster",
        "beskrivning": "Svår episodisk minnesnedsättning med normal inkodningskurva men kraftigt nedsatt fördröjd återgivning.",
        "villkor": [
            ("ravlt_dr_t",   "<=", 35),
            ("bvmt_dr_t",    "<=", 35),
        ],
        "bonus": [
            ("ravlt_total_t", ">=", 35),  # relativt bevarat inlärning
        ],
        "diagnoser": ["AD", "Hippocampal skleros"],
        "kommentar": "Profilen är förenlig med hippocampal dysfunktion. Överväg AD-biomarkörer om ej gjort."
    },
    {
        "id": "dlb_visuospatial",
        "namn": "DLB-mönster – visuospatial svikt",
        "beskrivning": "Disproportionell visuospatial nedsättning med relativt bevarat verbalt episodiskt minne.",
        "villkor": [
            ("block_t",      "<=", 35),
        ],
        "bonus": [
            ("ravlt_dr_t",   ">=", 40),
            ("bvmt_dr_t",    "<=", 40),
        ],
        "diagnoser": ["DLB", "PDD"],
        "kommentar": "Disproportionell visuospatial svikt relativt verbalt minne. Förenligt med DLB/PDD-profil."
    },
    {
        "id": "exekutivt",
        "namn": "Exekutivt/frontalt mönster",
        "beskrivning": "Nedsatt exekutiv funktion med relativt bevarat episodiskt minne.",
        "villkor": [
            ("tmt_b_t",      "<=", 35),
        ],
        "bonus": [
            ("fas_t",        "<=", 40),
            ("ravlt_dr_t",   ">=", 40),
        ],
        "diagnoser": ["bvFTD", "PSP", "VaD"],
        "kommentar": "Exekutiv svikt med relativt bevarat episodiskt minne. Överväg frontalt/subkortikalt mönster."
    },
    {
        "id": "subkortikalt",
        "namn": "Subkortikalt mönster",
        "beskrivning": "Psykomotorisk långsamhet och uppmärksamhetsnedsättning.",
        "villkor": [
            ("tmt_a_t",      "<=", 35),
            ("kod_t",        "<=", 35),
        ],
        "bonus": [
            ("tmt_b_t",      "<=", 40),
        ],
        "diagnoser": ["VaD", "PSP", "MSA", "PDD"],
        "kommentar": "Psykomotorisk nedsättning och uppmärksamhetssvikt. Förenligt med subkortikal patologi."
    },
    {
        "id": "semantiskt",
        "namn": "Semantiskt mönster",
        "beskrivning": "Nedsatt semantisk kunskap och ordflöde med relativt bevarat episodiskt minne.",
        "villkor": [
            ("djur_t",       "<=", 35),
        ],
        "bonus": [
            ("fas_t",        ">=", 40),
            ("ravlt_dr_t",   ">=", 40),
        ],
        "diagnoser": ["svPPA", "AD"],
        "kommentar": "Selektiv semantisk nedsättning. Överväg svPPA eller AD med temporaldominans."
    },
    {
        "id": "amnestiskt_multidomän",
        "namn": "Amnestiskt multidomänmönster",
        "beskrivning": "Nedsättning i flera kognitiva domäner inklusive minne.",
        "villkor": [
            ("ravlt_dr_t",   "<=", 35),
            ("tmt_b_t",      "<=", 40),
            ("block_t",      "<=", 40),
        ],
        "bonus": [],
        "diagnoser": ["AD", "VaD", "DLB"],
        "kommentar": "Multidomän kognitiv nedsättning. Bred differentialdiagnostik rekommenderas."
    },
    {
        "id": "isolerad_exekutiv",
        "namn": "Isolerad exekutiv nedsättning",
        "beskrivning": "Exekutiv svikt utan tydlig minnespåverkan.",
        "villkor": [
            ("tmt_b_t",      "<=", 35),
            ("ravlt_dr_t",   ">=", 40),
            ("bvmt_dr_t",    ">=", 40),
        ],
        "bonus": [],
        "diagnoser": ["bvFTD", "PSP-F", "VaD"],
        "kommentar": "Isolerad exekutiv nedsättning utan amnesi. Överväg frontal etiologi."
    },
    {
        "id": "normalt",
        "namn": "Inom normalgränser",
        "beskrivning": "Inga signifikanta nedsättningar påvisade.",
        "villkor": [],
        "bonus": [],
        "diagnoser": [],
        "kommentar": "Testprofilen visar inga signifikanta nedsättningar i de normerade deltesten."
    },
]

# ── MATCHNINGSFUNKTION ────────────────────────────────────────────────

def tolka_profil(testres: dict) -> list:
    """
    Tar emot en dict med T-poäng (t.ex. {"ravlt_dr_t": 32, "block_t": 28 ...})
    Returnerar lista av matchade mönster, sorterade efter träffsäkerhet.
    """
    matchade = []

    for m in MONSTER:
        if m["id"] == "normalt":
            continue

        # Kolla obligatoriska villkor
        obligatoriska_ok = True
        for (test, op, trösk) in m["villkor"]:
            val = testres.get(test)
            if val is None:
                obligatoriska_ok = False
                break
            if op == "<=" and not (val <= trösk):
                obligatoriska_ok = False
                break
            if op == ">=" and not (val >= trösk):
                obligatoriska_ok = False
                break

        if not obligatoriska_ok:
            continue

        # Räkna bonuspoäng
        bonus = 0
        for (test, op, trösk) in m["bonus"]:
            val = testres.get(test)
            if val is None:
                continue
            if op == "<=" and val <= trösk:
                bonus += 1
            if op == ">=" and val >= trösk:
                bonus += 1

        matchade.append({
            "monster": m,
            "bonus": bonus,
            "styrka": len(m["villkor"]) + bonus
        })

    # Sortera efter styrka
    matchade.sort(key=lambda x: x["styrka"], reverse=True)

    # FIX [VA-7/VA-8]: Mjukare matchning för T 36-39 ("Nedsatt"-zonen)
    if not matchade:
        for m in MONSTER:
            if m["id"] == "normalt":
                continue
            obligatoriska_ok = True
            for (test, op, trösk) in m["villkor"]:
                val = testres.get(test)
                if val is None:
                    obligatoriska_ok = False
                    break
                mjuk_trösk = trösk + 4  # utöka med 4 T-poäng
                if op == "<=" and not (val <= mjuk_trösk):
                    obligatoriska_ok = False
                    break
                if op == ">=" and not (val >= trösk - 4):
                    obligatoriska_ok = False
                    break
            if not obligatoriska_ok:
                continue
            bonus = 0
            for (test, op, trösk) in m["bonus"]:
                val = testres.get(test)
                if val is None:
                    continue
                if op == "<=" and val <= trösk + 4:
                    bonus += 1
                if op == ">=" and val >= trösk - 4:
                    bonus += 1
            matchade.append({
                "monster": m,
                "bonus": bonus,
                "styrka": len(m["villkor"]) + bonus,
                "mjuk_matchning": True
            })
        matchade.sort(key=lambda x: x["styrka"], reverse=True)

    # Om inga mönster matchade ens med mjuk matchning, returnera "normalt"
    if not matchade:
        normalt = next(m for m in MONSTER if m["id"] == "normalt")
        matchade.append({"monster": normalt, "bonus": 0, "styrka": 0})

    return matchade


# ── FRITEKSTSAMMANFATTNING ────────────────────────────────────────────

def generera_sammanfattning(testres: dict, matchade: list) -> str:
    """
    Genererar en klinisk fritekstsammanfattning baserat på T-poäng och matchade mönster.
    Returnerar en sträng som kan visas i gränssnittet eller skickas till Claude AI.
    """
    rader = []

    # Domänöversikt
    domaner = {
        "Verbalt episodiskt minne": [
            ("RAVLT total", testres.get("ravlt_total_t")),
            ("RAVLT fördröjd ÅG", testres.get("ravlt_dr_t")),
        ],
        "Visuospatialt minne": [
            ("BVMT-R total", testres.get("bvmt_total_t")),
            ("BVMT-R fördröjd ÅG", testres.get("bvmt_dr_t")),
        ],
        "Exekutiv funktion": [
            ("TMT-B", testres.get("tmt_b_t")),
            ("FAS", testres.get("fas_t")),
            ("Djur", testres.get("djur_t")),
        ],
        "Psykomotorisk hastighet": [
            ("TMT-A", testres.get("tmt_a_t")),
            ("Kodning", testres.get("kod_t")),
        ],
        "Visuospatial konstruktion": [
            ("Blockmönster", testres.get("block_t")),
        ],
        "Arbetsminne": [
            ("Sifferrepetition", testres.get("siff_t")),
        ],
    }

    def t_till_ord(t):
        if t is None: return None
        if t <= 29:   return "patologisk nedsättning"
        if t <= 34:   return "tydlig nedsättning"
        if t <= 39:   return "lätt nedsättning"
        if t <= 59:   return "normalprestation"
        return "över genomsnittet"

    for doman, tester in domaner.items():
        tillgangliga = [(namn, t) for namn, t in tester if t is not None]
        if not tillgangliga:
            continue
        t_vals = [t for _, t in tillgangliga]
        medel_t = sum(t_vals) / len(t_vals)
        nivå = t_till_ord(medel_t)
        testnamn = ", ".join([f"{n} T:{int(t)}" for n, t in tillgangliga])
        rader.append(f"{doman}: {nivå} ({testnamn})")

    sammanfattning = "NEUROPSYKOLOGISK PROFIL\n"
    sammanfattning += "─" * 40 + "\n"
    sammanfattning += "\n".join(rader)
    sammanfattning += "\n\n"

    if matchade and matchade[0]["monster"]["id"] != "normalt":
        sammanfattning += "MÖNSTERANALYS\n"
        sammanfattning += "─" * 40 + "\n"
        for m in matchade[:2]:  # Visa max 2 mönster
            sammanfattning += f"▶ {m['monster']['namn']}\n"
            sammanfattning += f"  {m['monster']['kommentar']}\n"
            if m['monster']['diagnoser']:
                sammanfattning += f"  Differentialdiagnoser: {', '.join(m['monster']['diagnoser'])}\n"
            sammanfattning += "\n"
    else:
        sammanfattning += "Testprofilen visar inga signifikanta nedsättningar.\n"

    return sammanfattning


# ── TESTKÖRNING ───────────────────────────────────────────────────────

if __name__ == "__main__":
    # Testfall – typisk AD-profil
    testfall_AD = {
        "ravlt_total_t": 32,
        "ravlt_dr_t": 22,
        "bvmt_total_t": 38,
        "bvmt_dr_t": 28,
        "tmt_a_t": 45,
        "tmt_b_t": 42,
        "block_t": 44,
        "kod_t": 46,
        "fas_t": 48,
        "djur_t": 40,
        "siff_t": 50,
    }

    print("=== TESTFALL: AD-profil ===\n")
    matchade = tolka_profil(testfall_AD)
    print(generera_sammanfattning(testfall_AD, matchade))

    print("\n=== TESTFALL: DLB-profil ===\n")
    testfall_DLB = {
        "ravlt_total_t": 45,
        "ravlt_dr_t": 42,
        "bvmt_total_t": 28,
        "bvmt_dr_t": 25,
        "tmt_a_t": 40,
        "tmt_b_t": 38,
        "block_t": 22,
        "kod_t": 38,
        "fas_t": 44,
        "djur_t": 42,
        "siff_t": 48,
    }
    matchade2 = tolka_profil(testfall_DLB)
    print(generera_sammanfattning(testfall_DLB, matchade2))