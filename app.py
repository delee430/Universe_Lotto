import streamlit as st
import swisseph as swe
import pandas as pd
import collections
import random
import os
import hashlib
import math
from datetime import datetime, date, timedelta

# [1] 시스템 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(current_dir, 'sweph')
if not os.path.exists(ephe_path): os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.6.3")

# --- [UI 헬퍼 함수] ---
def display_lotto_box(numbers, prefix=""):
    num_html = "".join([f'<span style="display:inline-block; width:30px; height:30px; line-height:30px; margin:2px; background:#2e313d; color:#00ffcc; border-radius:5px; text-align:center; font-weight:bold; font-size:14px; border:1px solid #444;">{n}</span>' for n in numbers])
    st.markdown(f"**{prefix}** {num_html}", unsafe_allow_html=True)

# --- [핵심 연산 함수] ---
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
            elif 115 < diff < 125: aspects.append(f"{p1}-{p2}:120°")
    return ", ".join(aspects) if aspects else "특이 각도 없음"

def get_advanced_astro(target_date, birthday):
    jd_t = swe.julday(target_date.year, target_date.month, target_date.day, 11)
    jd_b = swe.julday(birthday.year, birthday.month, birthday.day, 12)
    results, seeds, pos_dict = [], [], {}
    planets = {"태양": swe.SUN, "달": swe.MOON, "수성": swe.MERCURY, "금성": swe.VENUS, "화성": swe.MARS, 
               "목성": swe.JUPITER, "토성": swe.SATURN, "천왕성": swe.URANUS, "해왕성": swe.NEPTUNE, "명왕성": swe.PLUTO}
    zodiacs = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    for name, code in planets.items():
        res_t, _ = swe.calc_ut(jd_t, code)
        res_b, _ = swe.calc_ut(jd_b, code)
        results.append({"행성": name, "별자리": zodiacs[int(res_t[0] // 30)], "좌표": round(res_t[0] % 30, 2), "공명": round(abs(res_t[0] - res_b[0]), 2)})
        seeds.append(int(res_t[0] * 1000 + res_b[0] * 10 + birthday.day))
        pos_dict[name] = res_t[0]
    return pd.DataFrame(results), seeds, get_aspects(pos_dict)

def draw_astrology_card(u_id, target_date, planet_data, res_sets, final_res):
    planet_markers = ""
    symbols = {"태양": "☀️", "달": "🌙", "수성": "💧", "금성": "✨", "화성": "🔥", "목성": "⚡", "토성": "🪐", "천왕성": "🌀", "해왕성": "🔱", "명왕성": "💀"}
    for p_name, p_info in planet_data.items():
        angle_rad = math.radians(p_info['angle'] - 90)
        px, py = 100 + 80 * math.cos(angle_rad), 100 + 80 * math.sin(angle_rad)
        planet_markers += f'<div style="position:absolute; left:{px}px; top:{py}px; font-size:14px; transform:translate(-50%, -50%);">{symbols.get(p_name, "●")}</div>'
    st.markdown(f"""
    <div style="display: flex; justify-content: center; padding: 10px;">
        <div style="width: 340px; background: #1a1c23; border: 1px solid #444; border-radius: 15px; padding: 25px; text-align: center; color: white;">
            <div style="font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 15px;">ID: {u_id}</div>
            <div style="position: relative; width: 200px; height: 200px; margin: 0 auto; border: 1px solid #333; border-radius: 50%; background: url('https://img.icons8.com/ios/200/ffffff/zodiac-wheel.png') no-repeat center; background-size: 90%;">{planet_markers}</div>
            <div style="font-size: 15px; color: #FFFFFF; font-weight: bold; margin: 20px 0;">{target_date} ANALYSIS</div>
            <div style="font-size: 15px; color: #FFFFFF; line-height: 1.8; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px;">{'<br>'.join([str(s) for s in res_sets])}</div>
            <div style="background: rgba(0,255,204,0.2); border-radius: 8px; padding: 12px
