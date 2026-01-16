import streamlit as st
import swisseph as swe
import pandas as pd
import numpy as np
import collections
import random
import os
import qrcode
import io
import hashlib
import math
from datetime import datetime, date, timedelta

# [1] 경로 및 시스템 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(current_dir, 'sweph')
if not os.path.exists(ephe_path): os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.5.4")
st.markdown("<style>.small-font { font-size:13px !important; } .stTable { font-size: 11px !important; }</style>", unsafe_allow_html=True)

# --- 핵심 로직 함수 ---
def get_user_id(name, birthday):
    return hashlib.md5(f"{name}_{birthday.strftime('%Y%m%d')}".encode()).hexdigest()[:8]

def get_aspects(pos_dict):
    aspects = []
    p_names = list(pos_dict.keys())
    for i in range(len(p_names)):
        for j in range(i + 1, len(p_names)):
            p1, p2 = p_names[i], p_names[j]
            diff = abs(pos_dict[p1] - pos_dict[p2])
            diff = diff if diff <= 180 else 360 - diff
            if diff < 5: aspects.append(f"{p1}-{p2}:0°")
            elif 85 < diff < 95: aspects.append(f"{p1}-{p2}:90°")
            elif 115 < diff < 125: aspects.append(f"{p1}-{p2}:120°")
            elif 175 < diff <= 180: aspects.append(f"{p1}-{p2}:180°")
    return ", ".join(aspects) if aspects else "특이 각도 없음"

def get_advanced_astro(target_date, birthday):
    jd_t = swe.julday(target_date.year, target_date.month, target_date.day, 11)
    jd_b = swe.julday(birthday.year, birthday.month, birthday.day, 12)
    results, seeds, pos_dict = [], [], {}
    planets = {"태양": swe.SUN, "달": swe.MOON, "수성": swe.MERCURY, "금성": swe.VENUS, "화성": swe.MARS, 
               "목성": swe.JUPITER, "토성": swe.SATURN, "천왕성": swe.URANUS, "해왕성": swe.NEPTUNE, "명왕성": swe.PLUTO}
    zodiacs = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    for name, code in planets.items():
        try:
            res_t, _ = swe.calc_ut(jd_t, code)
            res_b, _ = swe.calc_ut(jd_b, code)
            results.append({"행성": name, "별자리": zodiacs[int(res_t[0] // 30)], "좌표": round(res_t[0] % 30, 2), "공명": round(abs(res_t[0] - res_b[0]), 2)})
            seeds.append(int(res_t[0] * 1000 + res_b[0] * 10 + birthday.day))
            pos_dict[name] = res_t[0]
        except: seeds.append(random.randint(1, 1000000))
    return pd.DataFrame(results), seeds, get_aspects(pos_dict)

# --- 공명 카드 드로잉 함수 (HTML/CSS) ---
def draw_astrology_card(u_id, target_date, planet_data, res_sets, final_res):
    planet_markers = ""
    center, radius = 1
