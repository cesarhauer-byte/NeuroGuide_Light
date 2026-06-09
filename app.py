from flask import Flask, render_template, request, jsonify
import json, sqlite3, os, datetime, random, sys

app = Flask(__name__)

# FIX [KR-2]: Kända icke-monotona värden (döda SS-zoner) identifierade vid granskning:
# TMT_A: ålder 66 SS=11, ålder 81 SS=4, ålder 84 SS=3, ålder 87 SS=6
# TMT_B: ålder 63 SS=15, ålder 66 SS=14, ålder 81 SS=4/14/16, ålder 84/87 SS=12/16
# Tabelldata härstammar från publicerade normer – korrigering kräver källgranskning.
# Källa: TMT 15b Tabell 4.19 A-MSS (Age-Corrected Norms).
TMT_15B_NORM = {
    56: {  # 56–62 år, N=160
        "A": {18:15, 17:16, 16:17, 15:19, 14:21, 13:24, 12:26, 11:29, 10:33,
              9:36,  8:40,  7:48,  6:54,  5:58,  4:61,  3:74,  2:9999},
        "B": {18:33, 17:35, 16:38, 15:41, 14:48, 13:54, 12:59, 11:63, 10:77,
              9:87,  8:96,  7:116, 6:140, 5:155, 4:187, 3:225, 2:9999},
    },
    63: {  # 63–65 år, N=206
        "A": {18:15, 17:16, 16:18, 15:21, 14:22, 13:25, 12:28, 11:30, 10:35,
              9:38,  8:44,  7:49,  6:55,  5:60,  4:64,  3:74,  2:9999},
        "B": {18:33, 17:37, 16:41, 15:44, 14:50, 13:57, 12:62, 11:72, 10:82,
              9:91,  8:103, 7:131, 6:154, 5:188, 4:199, 3:228, 2:9999},
    },
    66: {  # 66–68 år, N=152
        "A": {18:17, 17:19, 16:20, 15:21, 14:24, 13:26, 12:28, 11:31, 10:36,
              9:39,  8:45,  7:49,  6:57,  5:63,  4:73,  3:106, 2:9999},
        "B": {18:33, 17:40, 16:42, 15:46, 14:53, 13:60, 12:68, 11:74, 10:84,
              9:96,  8:106, 7:131, 6:154, 5:189, 4:209, 3:240, 2:9999},
    },
    69: {  # 69–71 år, N=134
        "A": {18:17, 17:19, 16:20, 15:22, 14:25, 13:28, 12:30, 11:33, 10:37,
              9:41,  8:46,  7:55,  6:62,  5:75,  4:92,  3:110, 2:9999},
        "B": {18:33, 17:40, 16:42, 15:49, 14:54, 13:62, 12:71, 11:79, 10:90,
              9:103, 8:136, 7:159, 6:211, 5:219, 4:229, 3:240, 2:9999},
    },
    72: {  # 72–74 år, N=125
        "A": {18:17, 17:19, 16:21, 15:24, 14:26, 13:28, 12:31, 11:35, 10:40,
              9:45,  8:54,  7:63,  6:80,  5:89,  4:107, 3:110, 2:9999},
        "B": {18:33, 17:40, 16:44, 15:52, 14:63, 13:68, 12:77, 11:83, 10:104,
              9:137, 8:156, 7:211, 6:224, 5:234, 4:239, 3:250, 2:9999},
    },
    75: {  # 75–77 år, N=111
        "A": {18:18, 17:19, 16:22, 15:24, 14:26, 13:29, 12:32, 11:35, 10:41,
              9:45,  8:56,  7:70,  6:80,  5:93,  4:107, 3:110, 2:9999},
        "B": {18:33, 17:40, 16:44, 15:52, 14:66, 13:72, 12:80, 11:91, 10:123,
              9:144, 8:167, 7:233, 6:236, 5:239, 4:249, 3:263, 2:9999},
    },
    78: {  # 78–80 år, N=89
        "A": {18:18, 17:20, 16:22, 15:25, 14:28, 13:31, 12:35, 11:39, 10:42,
              9:52,  8:58,  7:72,  6:82,  5:93,  4:107, 3:110, 2:9999},
        "B": {18:33, 17:40, 16:44, 15:65, 14:69, 13:81, 12:91, 11:100, 10:134,
              9:144, 8:159, 7:233, 6:236, 5:239, 4:249, 3:263, 2:9999},
    },
    81: {  # 81–83 år, N=81
        "A": {18:20, 17:21, 16:22, 15:27, 14:30, 13:35, 12:39, 11:42, 10:52,
              9:57,  8:63,  7:74,  6:83,  5:93,  4:111, 3:115, 2:9999},
        "B": {18:40, 17:44, 16:65, 15:69, 14:81, 13:93, 12:103, 11:114, 10:141,
              9:157, 8:182, 7:233, 6:239, 5:249, 4:262, 3:315, 2:9999},
    },
    84: {  # 84–86 år — identisk med 81–83 per tabell 4.19
        "A": {18:20, 17:21, 16:22, 15:27, 14:30, 13:35, 12:39, 11:42, 10:52,
              9:57,  8:63,  7:74,  6:83,  5:93,  4:111, 3:115, 2:9999},
        "B": {18:40, 17:44, 16:65, 15:69, 14:81, 13:93, 12:103, 11:114, 10:141,
              9:157, 8:182, 7:233, 6:239, 5:249, 4:262, 3:315, 2:9999},
    },
    87: {  # 87–89 år — identisk med 81–83 per tabell 4.19
        "A": {18:20, 17:21, 16:22, 15:27, 14:30, 13:35, 12:39, 11:42, 10:52,
              9:57,  8:63,  7:74,  6:83,  5:93,  4:111, 3:115, 2:9999},
        "B": {18:40, 17:44, 16:65, 15:69, 14:81, 13:93, 12:103, 11:114, 10:141,
              9:157, 8:182, 7:233, 6:239, 5:249, 4:262, 3:315, 2:9999},
    },
    90: {  # 90–97 år — identisk med 81–83 per tabell 4.19
        "A": {18:20, 17:21, 16:22, 15:27, 14:30, 13:35, 12:39, 11:42, 10:52,
              9:57,  8:63,  7:74,  6:83,  5:93,  4:111, 3:115, 2:9999},
        "B": {18:40, 17:44, 16:65, 15:69, 14:81, 13:93, 12:103, 11:114, 10:141,
              9:157, 8:182, 7:233, 6:239, 5:249, 4:262, 3:315, 2:9999},
    },
}

# Espenes et al. 2023 – Regressionsnormer RAVLT, norsk/svenska vuxna 49–79 år.
# Källa: The Clinical Neuropsychologist 37(6):1276-1301.
_RAVLT_C = dict(
    intercept=5.052935, age=-0.041005, edu=0.127599, sex=0.761477,
    mean_age=64.34426, mean_edu=12.66189,
    total=dict(intercept=42.295694, age=-0.269194, edu=1.095370, sex=5.853990, sd=7.981813),
    t1=dict(b=0,        edu=0,        sex=0,         sd=1.589299),
    t2=dict(b=2.456629, edu=0.096803, sex=0.540453,  sd=1.812938),
    t3=dict(b=3.825560, edu=0.122444, sex=0.620025,  sd=2.068447),
    t4=dict(b=5.099066, edu=0.120430, sex=0.317594,  sd=2.167247),
    t5=dict(b=5.591102, edu=0.157893, sex=0.570805,  sd=2.118599),
    t6=dict(b=3.281919, edu=0.212357, sex=0.900086,  sd=2.676763),
    t7=dict(b=3.150541, edu=0.230134, sex=0.712087,  sd=2.695187),
    tB=dict(b=0.181328, edu=0.053071, sex=-0.414812, sd=1.673211),
)

# FIX [VA-3]: Max-ålder i normer är 72. Patienter 73+ normeras mot 72-åringars data.
BVMT_NORMS = {
    'total': {
        18:(25.0,6.5),
        36:(26.00,4.80), 38:(25.70,4.86), 40:(25.40,4.91),
        42:(25.09,4.96), 44:(24.79,5.02), 46:(24.48,5.07),
        48:(24.18,5.12), 50:(23.87,5.18), 52:(23.57,5.23),
        54:(23.27,5.28), 56:(22.96,5.34), 58:(22.66,5.39),
        60:(22.35,5.44), 62:(22.05,5.50), 64:(21.74,5.55),
        66:(21.44,5.60), 68:(21.14,5.66), 70:(20.83,5.71),
        72:(20.22,5.82)
    },
    'dr': {
        18:(9.5,2.5),
        36:(9.80,1.71), 38:(9.69,1.75), 40:(9.58,1.79),
        42:(9.47,1.83), 44:(9.36,1.86), 46:(9.25,1.90),
        48:(9.14,1.94), 50:(9.03,1.98), 52:(8.92,2.01),
        54:(8.81,2.05), 56:(8.70,2.09), 58:(8.59,2.13),
        60:(8.48,2.17), 62:(8.37,2.20), 64:(8.26,2.24),
        66:(8.15,2.28), 68:(8.04,2.32), 70:(7.93,2.36),
        72:(7.71,2.43)
    },
}

# Källa: Geriatriskt Centrums Rättningsprogram (WAIS-IV svenska normer).
BLOCK_NORM = {
    16: [0,  9, 15, 16, 21, 28, 34, 40, 45, 49, 53, 56, 59, 61, 63, 64, 65, None, 66],
    18: [0,  9, 15, 16, 21, 28, 34, 40, 45, 49, 53, 56, 59, 61, 63, 64, 65, None, 66],
    20: [0,  8, 11, 15, 20, 27, 33, 39, 45, 49, 53, 56, 59, 61, 63, 64, 65, None, 66],
    25: [0,  8, 11, 15, 20, 27, 33, 39, 45, 49, 53, 56, 59, 61, 63, 64, None, 65, 66],
    30: [0,  7, 10, 14, 19, 26, 32, 38, 44, 48, 52, 55, 58, 61, 63, None, 64, 65, 66],
    35: [0,  6,  9, 13, 18, 23, 28, 33, 38, 43, 48, 52, 55, 58, 61, 63, 64, 65, 66],
    45: [0,  5,  8, 12, 17, 22, 27, 31, 36, 41, 46, 50, 54, 57, 60, 62, 64, 65, 66],
    55: [0,  5,  7, 11, 16, 20, 25, 29, 34, 38, 42, 47, 51, 55, 58, 61, 63, 65, 66],
    65: [0,  4,  7, 11, 15, 19, 23, 26, 31, 34, 38, 43, 47, 51, 55, 58, 61, 64, 66],
    70: [0,  4,  7, 10, 14, 17, 21, 24, 28, 31, 35, 39, 43, 47, 51, 55, 58, 62, 66],
    75: [0,  3,  6,  9, 12, 14, 17, 20, 23, 27, 30, 34, 37, 41, 45, 49, 53, 57, 61],
    80: [0,  3,  6,  8, 11, 13, 15, 18, 21, 24, 27, 31, 34, 38, 41, 45, 49, 53, 57],
    85: [0,  3,  5,  7,  9, 11, 13, 15, 18, 21, 24, 27, 31, 34, 37, 41, 45, 49, 53],
}
LIK_NORM = {
    16: [0,  6,  8, 10, 12, 14, 16, 17, 19, 21, 22, 24, 26, 27, 28, 29, 30, 31, 33],
    18: [0,  7,  9, 11, 13, 15, 16, 17, 19, 21, 23, 25, 26, 27, 28, 29, 30, 31, 33],
    20: [0,  7, 10, 12, 14, 16, 17, 18, 20, 22, 23, 26, 27, 28, 29, 30, 31, 32, 34],
    25: [0,  8, 10, 12, 14, 16, 17, 18, 20, 22, 23, 26, 27, 28, 29, 30, 32, 34, 35],
    30: [0,  8, 10, 12, 14, 16, 17, 18, 20, 22, 23, 26, 27, 28, 29, 30, 32, 34, 36],
    35: [0,  8, 10, 12, 14, 16, 17, 18, 20, 22, 23, 26, 27, 28, 29, 30, 32, 34, 36],
    45: [0,  7,  9, 12, 14, 16, 17, 18, 20, 22, 23, 26, 27, 28, 29, 30, 32, 34, 36],
    55: [0,  6,  8, 11, 13, 15, 16, 17, 19, 21, 23, 25, 27, 28, 29, 30, 32, 33, 35],
    65: [0,  5,  7, 10, 12, 15, 16, 17, 18, 21, 22, 24, 26, 27, 28, 30, 31, 34, 35],
    70: [0,  4,  6,  9, 11, 14, 15, 16, 18, 21, 22, 23, 25, 27, 28, 30, 31, 34, 35],
    75: [0,  4,  6,  8, 10, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 32, 33, 34, 35],
    80: [0,  3,  5,  7,  9, 12, 14, 16, 19, 21, 23, 25, 27, 28, 30, 31, 32, 33, 34],
    85: [0,  2,  4,  6,  8, 11, 13, 15, 17, 20, 22, 24, 26, 27, 29, 30, 31, 32, 34],
}
INFO_NORM = {
    16: [0,  2,  3,  4,  6,  8,  9, 11, 13, 14, 16, 17, 19, 21, 22, 23, 24, 25, 26],
    18: [0,  2,  3,  4,  6,  8,  9, 11, 13, 14, 16, 17, 19, 21, 22, 23, 24, 25, 26],
    20: [0,  2,  3,  4,  6,  8,  9, 11, 13, 14, 16, 17, 19, 21, 22, 23, 24, 25, 26],
    25: [0,  2,  3,  4,  6,  8,  9, 11, 13, 14, 16, 17, 19, 21, 22, 23, 24, 25, 26],
    30: [0,  2,  3,  4,  6,  8,  9, 11, 13, 14, 16, 17, 19, 21, 22, 23, 24, 25, 26],
    35: [0,  3,  4,  6,  8,  9, 11, 13, 14, 15, 17, 18, 20, 22, 23, 24, None, 25, 26],
    45: [0,  3,  4,  6,  8,  9, 11, 13, 14, 15, 17, 18, 20, 22, 23, 24, None, 25, 26],
    55: [0,  3,  4,  6,  8,  9, 11, 13, 14, 15, 17, 18, 20, 22, 23, 24, None, 25, 26],
    65: [0,  3,  4,  6,  8,  9, 11, 13, 14, 15, 17, 18, 20, 22, 23, 24, 25, None, 26],
    70: [0,  3,  4,  6,  8,  9, 11, 13, 14, 15, 17, 18, 20, 22, 23, 24, 25, None, 26],
    75: [0,  1,  2,  3,  4,  6,  8,  9, 11, 13, 15, 17, 19, 21, 23, 24, 25, None, 26],
    80: [0,  1,  2,  3,  4,  5,  7,  8, 10, 12, 14, 16, 18, 20, 22, 23, 24, 25, 26],
    85: [0, None, 1,  2,  3,  4,  6,  7,  9, 11, 13, 15, 17, 19, 21, 23, 24, 25, 26],
}
KOD_NORM = {
    16: [0, 20, 23, 28, 34, 40, 47, 53, 59, 65, 71, 77, 81, 85, 91, 97, 102, 106, 109],
    18: [0, 20, 23, 28, 34, 40, 47, 53, 59, 65, 71, 77, 81, 85, 91, 97, 102, 106, 109],
    20: [0, 20, 23, 28, 34, 40, 47, 53, 59, 65, 71, 77, 81, 85, 91, 97, 102, 106, 109],
    25: [0, 20, 23, 28, 34, 40, 47, 53, 59, 65, 71, 77, 81, 85, 91, 97, 102, 106, 109],
    30: [0, 19, 22, 27, 33, 39, 46, 52, 58, 64, 70, 76, 80, 84, 90, 96, 101, 105, 107],
    35: [0, 19, 22, 27, 33, 39, 46, 52, 58, 64, 70, 76, 80, 84, 90, 96, 101, 105, 107],
    45: [0, 18, 21, 26, 32, 38, 44, 50, 56, 62, 67, 72, 76, 80, 84, 90,  96,  99, 102],
    55: [0, 16, 18, 20, 25, 31, 37, 42, 51, 55, 61, 66, 69, 72, 77, 82,  88,  94,  99],
    65: [0, 14, 16, 18, 23, 29, 35, 40, 49, 53, 59, 64, 66, 70, 72, 76,  81,  86,  93],
    70: [0, 11, 14, 16, 20, 26, 30, 35, 44, 50, 56, 61, 64, 69, 71, 75,  80,  85,  91],
    75: [0,  6,  9, 13, 18, 23, 28, 33, 38, 43, 47, 53, 58, 63, 68, 73,  78,  83,  88],
    80: [0,  4,  7, 10, 14, 18, 22, 28, 33, 38, 43, 47, 53, 58, 63, 68,  72,  78,  83],
    85: [0,  3,  5,  7, 10, 14, 17, 22, 27, 32, 37, 42, 47, 52, 57, 62,  67,  72,  77],
}
# WAIS-III normer (intentionellt, ej WAIS-IV). 19 element per åldersgrupp.
SIFF_NORM_III = {
    16: [0,  3,  5,  7,  9, 11, 13, 14, 16, 17, 19, 20, 21, 23, 24, 25, 26, 27, 28],
    18: [0,  4,  6,  8, 10, 11, 13, 14, 16, 17, 19, 20, 21, 23, 24, 26, 27, 28, 29],
    20: [0,  4,  6,  8, 10, 11, 13, 14, 16, 17, 19, 20, 22, 23, 24, 26, 27, 28, 29],
    25: [0,  4,  6,  8, 10, 11, 13, 14, 16, 17, 19, 20, 22, 23, 24, 26, 27, 28, 29],
    30: [0,  3,  5,  7,  9, 11, 12, 14, 15, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29],
    35: [0,  3,  5,  7,  9, 11, 12, 14, 15, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29],
    45: [0,  3,  5,  7,  9, 11, 12, 14, 15, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29],
    55: [0,  2,  4,  6,  8,  9, 11, 13, 14, 16, 17, 19, 20, 22, 23, 25, 26, 27, 28],
    65: [0,  2,  4,  6,  8,  9, 11, 13, 14, 16, 17, 18, 20, 21, 23, 24, 25, 26, 27],
    70: [0,  2,  4,  6,  8,  9, 11, 12, 14, 15, 16, 18, 19, 20, 22, 23, 24, 25, 26],
    75: [0,  2,  4,  6,  8,  9, 11, 12, 13, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25],
    80: [0,  1,  3,  5,  7,  9, 10, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24],
    85: [0,  1,  3,  5,  7,  9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
}
# FIX [VA-1]: Normer täcker 16,30,65 år. Patienter 66+ normeras mot 65-åringars data.
FLODE_NORMS = {
    'A': {
        16: (37.5,11.4, 23.0,4.0, 17.0,3.7),
        30: (42.3,10.0, 24.9,6.4, 17.1,4.7),
        65: (36.6,15.1, 17.8,5.7, 14.9,6.4),
    },
    'B': {
        16: (42.4,10.0, 26.4,5.1, 23.0,6.3),
        30: (49.0,13.3, 27.1,5.4, 22.3,6.4),
        65: (45.2,10.1, 20.6,5.7, 19.4,5.6),
    },
}

# RCFT-normer (Meyers & Meyers 1995, Professional Manual PAR Inc.)
# Källa: Standardiserade normer för vuxna, ålderskorrigerade. Max = 36 poäng.
RCFT_NORMS = {
    'kopia': {
        18: (33.9, 2.9),
        40: (33.0, 3.2),
        50: (32.0, 4.0),
        60: (29.7, 5.0),
        70: (26.7, 5.9),
        80: (22.9, 6.5),
    },
    'omedelbar': {
        18: (20.7, 6.9),
        40: (18.2, 7.1),
        50: (16.8, 7.5),
        60: (14.5, 7.6),
        70: (11.4, 7.2),
        80: (8.0,  5.9),
    },
    'fordrojd': {
        18: (20.5, 7.0),
        40: (18.4, 7.0),
        50: (16.9, 7.3),
        60: (14.4, 7.5),
        70: (11.5, 7.3),
        80: (8.2,  5.7),
    },
}

# Klocktest-normer (Shulman 2000, Rouleau 1992)
# Shulman-skala: 0–5 poäng. Cutoff: ≥4 = normalt, 3 = minimal, ≤2 = patologiskt
KLOCKTEST_NORMS = {
    'shulman': {'cutoff_normal': 4, 'cutoff_patol': 2},
    'rouleau': {'max': 10, 'cutoff_normal': 8, 'cutoff_patol': 6},
}


# ─── KONVERTERINGSFUNKTIONER ──────────────────────────────────────────────────

def get_age_key(norm_dict, age):
    keys = sorted(norm_dict.keys())
    selected = keys[0]
    for k in keys:
        if age >= k: selected = k
    return selected

def raw_to_scaled_wais(raw, norm_dict, age):
    if raw is None: return None
    key = get_age_key(norm_dict, age)
    thresholds = norm_dict[key]
    for i in range(len(thresholds) - 1, -1, -1):
        if thresholds[i] is not None and raw >= thresholds[i]:
            return i + 1
    return 1

def tmt_to_ss(seconds, test, age):
    """TMT tid → skalpoäng. Kortare tid = bättre = HÖGRE SS. Källa: TMT 15b Tabell 4.19 A-MSS."""
    if seconds is None:
        return None
    key = get_age_key(TMT_15B_NORM, age)
    if key is None:
        return None
    table = TMT_15B_NORM[key][test]
    for ss in range(18, 1, -1):
        if seconds <= table[ss]:
            return ss
    return 2

def ss_to_t(ss, max_ss=18):
    if ss is None: return None
    # FIX [VA-5]: TMT SS->T: M=10,SD=3 (WAIS-IV standard)
    return round(50 + (ss - 10) * (10.0 / 3.0), 1)

def scaled_to_t(scaled):
    if scaled is None: return None
    # FIX [KR-1]: WAIS-IV SS->T: M=10,SD=3 → T=50+(SS-10)*(10/3)
    return round(50 + (scaled - 10) * (10.0 / 3.0), 1)

def mean_sd_to_t(raw, mean, sd):
    if raw is None or sd == 0: return None
    z = (raw - mean) / sd
    return round(max(20, min(80, 50 + 10 * z)), 1)

def t_color_label(t):
    if t is None: return "gray", "—"
    if t <= 29:   return "red",    "Patologiskt"
    elif t <= 34: return "orange", "Tydligt nedsatt"
    elif t <= 39: return "yellow", "Nedsatt"
    elif t <= 59: return "green",  "Normalt"
    else:         return "blue",   "Över genomsnittet"

def ravlt_t(raw, domain, age, sex=None, edu=None):
    """RAVLT T-poäng via Espenes et al. 2023 (norsk/svenska, 49–79 år)."""
    if raw is None:
        return None
    sex_f = 1 if sex and sex.lower() in ('kvinna', 'k', 'f') else 0
    edu_y = float(edu) if edu else _RAVLT_C['mean_edu']
    ac = age - _RAVLT_C['mean_age']
    ec = edu_y - _RAVLT_C['mean_edu']
    c = _RAVLT_C
    if domain == 'total':
        tc = c['total']
        pred = tc['intercept'] + ac * tc['age'] + ec * tc['edu'] + sex_f * tc['sex']
        sd = tc['sd']
    else:
        key_map = {'dr': 't7', 'dist': 'tB', 'f5': 't6'}
        tr = c.get(key_map.get(domain, domain))
        if tr is None:
            return None
        pred = (c['intercept'] + sex_f * c['sex'] + ac * c['age'] + ec * c['edu']
                + tr['b'] + ec * tr['edu'] + sex_f * tr['sex'])
        sd = tr['sd']
    z = (raw - pred) / sd
    return round(max(20, min(80, 50 + 10 * z)), 1)

def bvmt_t(raw, domain, age):
    norms = BVMT_NORMS.get(domain, {})
    key = get_age_key(norms, age)
    mean, sd = norms[key]
    return mean_sd_to_t(raw, mean, sd)

def flode_t(raw, test, age, utb='A'):
    norm = FLODE_NORMS.get(utb, FLODE_NORMS['A'])
    key = get_age_key(norm, age)
    vals = norm[key]
    if test == 'fas':    mean, sd = vals[0], vals[1]
    elif test == 'djur': mean, sd = vals[2], vals[3]
    else:                mean, sd = vals[4], vals[5]
    return mean_sd_to_t(raw, mean, sd)

def rcft_t(raw, domain, age):
    """RCFT råpoäng → T-poäng. Källa: Meyers & Meyers 1995."""
    norms = RCFT_NORMS.get(domain, {})
    if not norms:
        return None
    key = get_age_key(norms, age)
    mean, sd = norms[key]
    return mean_sd_to_t(raw, mean, sd)


# ─── PATIENTLAGRING ───────────────────────────────────────────────────────────

def _patient_db():
    path = os.path.join(os.path.dirname(__file__), 'patients_light.db')
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS patienter (
        patient_id TEXT PRIMARY KEY,
        data_json TEXT,
        sparad_datum TEXT,
        andrad_datum TEXT,
        version TEXT DEFAULT 'NGLv1'
    )""")
    conn.commit()
    return conn


# ─── DATABASINITIERING ────────────────────────────────────────────────────────
# OBS: Render ephemeral filesystem – databaser återskapas vid varje omstart

def initialisera_databaser():
    """Skapar matris.db och diagnos_matris.db om de inte finns."""
    import importlib.util
    modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")

    setup_skript = [
        ("matris_setup",        "matris.db"),
        ("diagnos_matris_setup","diagnos_matris.db"),
    ]

    for skript, db_namn in setup_skript:
        db_path = os.path.join(modules_dir, db_namn)
        if not os.path.exists(db_path):
            skript_path = os.path.join(modules_dir, skript + ".py")
            try:
                spec  = importlib.util.spec_from_file_location(skript, skript_path)
                modul = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modul)
                if hasattr(modul, "skapa_databas"):
                    modul.skapa_databas()
                if hasattr(modul, "spara_vikter"):
                    modul.spara_vikter()
                print(f"✅ {db_namn} skapad")
            except Exception as e:
                print(f"⚠️  Kunde inte skapa {db_namn}: {e}")
        else:
            print(f"✓  {db_namn} finns redan")

initialisera_databaser()

# ─── ROUTES ───────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
from profiltolkning import tolka_profil, generera_sammanfattning

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/berakna", methods=["POST"])
def berakna():
    d = request.json
    res = {}
    age = int(d.get("alder", 70))
    kon = d.get("kon") or None
    utb = d.get("utb") or None

    # RAVLT
    forsok = [int(d.get(f"ravlt_{i}")) for i in range(1,6) if d.get(f"ravlt_{i}") not in (None,"")]
    if forsok:
        tot = sum(forsok)
        t = ravlt_t(tot, 'total', age, sex=kon, edu=utb)
        c, l = t_color_label(t)
        res.update({"ravlt_total":tot,"ravlt_total_t":t,"ravlt_total_color":c,"ravlt_total_label":l})
    for key, domain in [("ravlt_dr","dr"),("ravlt_dist","dist")]:
        v = d.get(key)
        if v not in (None,""):
            raw=int(v); t=ravlt_t(raw,domain,age,sex=kon,edu=utb); c,l=t_color_label(t)
            res.update({key:raw,key+"_t":t,key+"_color":c,key+"_label":l})
    for key in ["ravlt_rek_sp","ravlt_rek_fp"]:
        v=d.get(key)
        if v not in (None,""): res[key]=int(v)
    # RAVLT Retention % = (Fördröjd ÅG / Trial 5) × 100, referens ≥80 %
    ravlt_5v = d.get("ravlt_5")
    if ravlt_5v not in (None,"") and res.get("ravlt_dr") is not None:
        t5 = int(ravlt_5v)
        if t5 > 0:
            ret = round((res["ravlt_dr"] / t5) * 100, 1)
            res["ravlt_retention_pct"] = ret
            res["ravlt_retention_ok"] = ret >= 80

    # BVMT-R
    bvals=[int(d.get(f"bvmt_{i}")) for i in range(1,4) if d.get(f"bvmt_{i}") not in (None,"")]
    if bvals:
        tot=sum(bvals); t=bvmt_t(tot,'total',age); c,l=t_color_label(t)
        res.update({"bvmt_total":tot,"bvmt_total_t":t,"bvmt_total_color":c,"bvmt_total_label":l})
    v=d.get("bvmt_dr")
    if v not in (None,""):
        raw=int(v); t=bvmt_t(raw,'dr',age); c,l=t_color_label(t)
        res.update({"bvmt_dr":raw,"bvmt_dr_t":t,"bvmt_dr_color":c,"bvmt_dr_label":l})
    for key in ["bvmt_rek_sp","bvmt_rek_fp"]:
        v=d.get(key)
        if v not in (None,""): res[key]=int(v)
    # BVMT Learning Index = Trial3 − Trial1, referens ≥3
    bvmt_1v = d.get("bvmt_1"); bvmt_3v = d.get("bvmt_3")
    if bvmt_1v not in (None,"") and bvmt_3v not in (None,""):
        li = int(bvmt_3v) - int(bvmt_1v)
        res["bvmt_learning_index"] = li
        res["bvmt_learning_ok"] = li >= 3
    # BVMT Retention % = (Fördröjd ÅG / Trial3) × 100, referens ≥70 %
    if bvmt_3v not in (None,"") and res.get("bvmt_dr") is not None:
        t3 = int(bvmt_3v)
        if t3 > 0:
            ret = round((res["bvmt_dr"] / t3) * 100, 1)
            res["bvmt_retention_pct"] = ret
            res["bvmt_retention_ok"] = ret >= 70
    # BVMT Igenkänning Index = Hits − Falsklarm, referens ≥9
    bsp = d.get("bvmt_rek_sp"); bfp = d.get("bvmt_rek_fp")
    if bsp not in (None,"") and bfp not in (None,""):
        res["bvmt_rek_index"] = int(bsp) - int(bfp)
        res["bvmt_rek_index_ok"] = res["bvmt_rek_index"] >= 9

    # RCFT
    for key, domain in [("rcft_kop","kopia"),("rcft_3min","omedelbar"),("rcft_30min","fordrojd")]:
        v=d.get(key)
        if v not in (None,""):
            raw=float(v); t=rcft_t(raw,domain,age); c,l=t_color_label(t)
            res.update({key:raw,key+"_t":t,key+"_color":c,key+"_label":l})
    for key in ["rcft_rek_sp","rcft_rek_fp"]:
        v=d.get(key)
        if v not in (None,""): res[key]=int(v)

    # Sifferrepetition
    sf=d.get("siff_fram"); sb=d.get("siff_bak"); so=d.get("siff_ordning")
    if sf not in (None,"") and sb not in (None,""):
        tot=int(sf)+int(sb)+(int(so) if so not in (None,"") else 0)
        sk=raw_to_scaled_wais(tot,SIFF_NORM_III,age); t=scaled_to_t(sk); c,l=t_color_label(t)
        res.update({"siff_raw_total":tot,"siff_skalp":sk,"siff_t":t,"siff_color":c,"siff_label":l})

    # WAIS-IV deltester
    for key,norm,lbl in [("info_raw",INFO_NORM,"info"),("lik_raw",LIK_NORM,"lik"),
                          ("block_raw",BLOCK_NORM,"block"),("kod_raw",KOD_NORM,"kod")]:
        v=d.get(key)
        if v not in (None,""):
            raw=int(v); sk=raw_to_scaled_wais(raw,norm,age); t=scaled_to_t(sk); c,l=t_color_label(t)
            res.update({key:raw,lbl+"_skalp":sk,lbl+"_t":t,lbl+"_color":c,lbl+"_label":l})

    # TMT
    for test,key in [("A","tmt_a"),("B","tmt_b")]:
        v=d.get(key)
        if v not in (None,""):
            sek=int(v); ss=tmt_to_ss(sek,test,age); t=ss_to_t(ss); c,l=t_color_label(t)
            res.update({key:sek,key+"_ss":ss,key+"_t":t,key+"_color":c,key+"_label":l})
    # TMT B/A-kvot
    if res.get("tmt_a") and res.get("tmt_b") and res["tmt_a"] > 0:
        res["tmt_ba_kvot"] = round(res["tmt_b"] / res["tmt_a"], 2)

    # Verbalt flöde
    utb_flode = d.get("utb_flode", "A")
    for test in ["fas","djur"]:
        v=d.get(test)
        if v not in (None,""):
            raw=int(v); t=flode_t(raw,test,age,utb_flode); c,l=t_color_label(t)
            res.update({test:raw,test+"_t":t,test+"_color":c,test+"_label":l})
    # FAS total (F+A+S)
    fas_f=d.get("fas_f"); fas_a=d.get("fas_a"); fas_s=d.get("fas_s")
    if fas_f not in (None,"") and fas_a not in (None,"") and fas_s not in (None,""):
        fas_tot=int(fas_f)+int(fas_a)+int(fas_s)
        t=flode_t(fas_tot,'fas',age,utb_flode); c,l=t_color_label(t)
        res.update({"fas":fas_tot,"fas_t":t,"fas_color":c,"fas_label":l})
    elif d.get("fas") not in (None,""):
        v=d.get("fas"); raw=int(v); t=flode_t(raw,'fas',age,utb_flode); c,l=t_color_label(t)
        res.update({"fas":raw,"fas_t":t,"fas_color":c,"fas_label":l})

    # Klocktest
    for key in ["klocka_rita","klocka_avlasa"]:
        v=d.get(key)
        if v not in (None,""): res[key]=float(v)

    # Bilddiagnostik (lagras råvärden för spindeldiagram)
    for key in ["mta_h","mta_v","gca","koedam","fazekas","fazekas_pv","fazekas_dvs"]:
        v=d.get(key)
        if v not in (None,""): res[key]=float(v)

    return jsonify(res)

@app.route("/profiltolkning", methods=["POST"])
def profiltolkning_route():
    d = request.json
    matchade = tolka_profil(d)
    sammanfattning = generera_sammanfattning(d, matchade)
    return jsonify({
        "sammanfattning": sammanfattning,
        "monster": [
            {
                "namn": m["monster"]["namn"],
                "kommentar": m["monster"]["kommentar"] + (" (lätt nedsättning)" if m.get("mjuk_matchning") else ""),
                "diagnoser": m["monster"]["diagnoser"],
                "styrka": m["styrka"]
            }
            for m in matchade
        ]
    })

@app.route('/patient_spara', methods=['POST'])
def patient_spara():
    d = request.json or {}
    pid = str(d.get('patient_id') or '').strip()
    if not pid:
        return jsonify({'ok': False, 'error': 'Patient-ID saknas'}), 400
    data = d.get('data', {})
    nu = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    conn = _patient_db()
    befintlig = conn.execute('SELECT sparad_datum FROM patienter WHERE patient_id=?', (pid,)).fetchone()
    sparad = befintlig[0] if befintlig else nu
    conn.execute("""INSERT OR REPLACE INTO patienter (patient_id, data_json, sparad_datum, andrad_datum, version)
        VALUES (?,?,?,?,'NGLv1')""", (pid, json.dumps(data, ensure_ascii=False), sparad, nu))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'patient_id': pid, 'datum': nu})

@app.route('/patient_lista')
def patient_lista():
    conn = _patient_db()
    rader = conn.execute(
        'SELECT patient_id, sparad_datum, andrad_datum FROM patienter ORDER BY andrad_datum DESC'
    ).fetchall()
    conn.close()
    return jsonify([{'patient_id': r[0], 'sparad_datum': r[1], 'andrad_datum': r[2]} for r in rader])

@app.route('/patient_hamta', methods=['POST'])
def patient_hamta():
    d = request.json or {}
    pid = str(d.get('patient_id') or '').strip()
    if not pid:
        return jsonify({'ok': False, 'error': 'Patient-ID saknas'}), 400
    conn = _patient_db()
    row = conn.execute(
        'SELECT data_json, sparad_datum, andrad_datum FROM patienter WHERE patient_id=?', (pid,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'ok': False, 'error': 'Patienten hittades inte'}), 404
    try:
        data = json.loads(row[0])
    except Exception:
        data = {}
    return jsonify({'ok': True, 'patient_id': pid, 'data': data,
                    'sparad_datum': row[1], 'andrad_datum': row[2]})

@app.route('/patient_ny', methods=['POST'])
def patient_ny():
    nu = datetime.datetime.now()
    pid = f"NUS-{nu.year}{str(nu.month).zfill(2)}-{random.randint(1000,9999)}"
    return jsonify({'ok': True, 'patient_id': pid})


@app.route('/diagnos_matris_data')
def diagnos_matris_data():
    from modules.diagnos_matris_setup import hamta_matrisdata
    return jsonify(hamta_matrisdata())

@app.route('/diagnos_matris_analys', methods=['POST'])
def diagnos_matris_analys():
    from modules.diagnos_matris_setup import matcha_patient
    d = request.json or {}
    scores = matcha_patient(
        tscorer=d.get('tscorer', {}),
        bilddiagnostik=d.get('bilddiagnostik', {})
    )
    return jsonify({'scores': scores})

@app.route('/matris_analys', methods=['POST'])
def matris_analys():
    from modules.matris_setup import berakna_matrisaktivering
    d = request.json or {}
    resultat = berakna_matrisaktivering(
        tscorer=d.get('tscorer', {}),
        bilddiagnostik=d.get('bilddiagnostik', {}),
        alder=int(d.get('alder', 70))
    )
    return jsonify(resultat)

@app.route('/matris_data')
def matris_data():
    from modules.matris_setup import hamta_matrisdata
    return jsonify(hamta_matrisdata())

@app.route('/matris_uppdatera', methods=['POST'])
def matris_uppdatera():
    from modules.matris_setup import uppdatera_vikt
    d = request.json or {}
    var1_id = d.get('var1_id')
    var2_id = d.get('var2_id')
    ny_vikt = d.get('vikt')
    if var1_id is None or var2_id is None or ny_vikt is None:
        return jsonify({'ok': False, 'error': 'Saknar parametrar'}), 400
    return jsonify({'ok': uppdatera_vikt(int(var1_id), int(var2_id), float(ny_vikt))})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5010))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    host = "0.0.0.0"
    print(f"NeuroGuide Light startar på http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)
