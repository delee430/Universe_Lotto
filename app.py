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

# [1] 시스템 설정 및 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(current_dir, 'sweph')
if not os.path.exists(ephe_path): os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.5.6")
st.markdown("<style>.small-font { font-size:13px !important; }</style>", unsafe_allow_html=True)

# --- [함수 정의 영역] ---
def get_user_id(name, birthday):
    return hashlib.md5(f"{name}_{birthday.strftime('%Y%m%d')}".encode()).hexdigest()[:8]

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
    return pd.DataFrame(results), seeds

def draw_astrology_card(u_id, target_date, planet_data, res_sets, final_res):
    planet_markers = ""
    center, radius = 100, 80
    symbols = {"태양": "☀️", "달": "🌙", "수성": "💧", "금성": "✨", "화성": "🔥", "목성": "⚡", "토성": "🪐", "천왕성": "🌀", "해왕성": "🔱", "명왕성": "💀"}
    for p_name, p_info in planet_data.items():
        angle_rad = math.radians(p_info['angle'] - 90)
        px, py = center + radius * math.cos(angle_rad), center + radius * math.sin(angle_rad)
        sym = symbols.get(p_name, "●")
        planet_markers += f'<div style="position:absolute; left:{px}px; top:{py}px; font-size:14px; transform:translate(-50%, -50%);">{sym}</div>'

    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 10px;">
        <div style="width: 340px; background: #1a1c23; border: 1px solid #444; border-radius: 15px; padding: 25px; text-align: center; color: white; box-shadow: 0 10px 40px rgba(0,0,0,0.7);">
            <div style="font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 15px;">ID: {u_id}</div>
            <div style="position: relative; width: 200px; height: 200px; margin: 0 auto; border: 1px solid #333; border-radius: 50%; background: url('https://img.icons8.com/ios/200/ffffff/zodiac-wheel.png') no-repeat center; background-size: 90%;">
                {planet_markers}
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 50px; height: 50px; background: white; padding: 2px; border-radius: 4px;">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=50x50&data={u_id}" style="width:100%;"/>
                </div>
            </div>
            <div style="font-size: 15px; color: #FFFFFF; font-weight: bold; margin: 20px 0;">{target_date} ANALYSIS</div>
            <div style="font-size: 15px; color: #FFFFFF; line-height: 1.8; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px;">
                {'<br>'.join([str(s) for s in res_sets])}
            </div>
            <div style="background: rgba(0,255,204,0.2); border-radius: 8px; padding: 12px; color: #00ffcc; font-weight: bold; font-size: 24px; border: 2px solid #00ffcc;">{final_res}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- [사이드바 설정 및 데이터 생성] ---
with st.sidebar:
    st.header("👤 연구원 프로필")
    user_name = st.text_input("성함", "설계자")
    birthday = st.date_input("생년월일", value=date(1990, 1, 1), min_value=date(1800, 1, 1), max_value=date(2100, 12, 31))
    analysis_date = st.date_input("분석 기준일", value=date.today())
    u_id = get_user_id(user_name, birthday)

target_sat = analysis_date + timedelta(days=(5 - analysis_date.weekday()) % 7)
astro_df, p_seeds = get_advanced_astro(target_sat, birthday)

st.title(f"🌌 {user_name}의 우주 공명 아카이브 V4.5.6")

# --- [천지인 숫자 매트릭스 복구] ---
ace_list, sky_list, human_list = [], [], []
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("📊 [地] 에이스라인")
    # 마스터리스트(지상 데이터) 기반 계산
    ace_seed = sum(p_seeds[:3]) # 대체 시드
    for i in range(5):
        random.seed(ace_seed + i)
        n = sorted(random.sample(range(1, 46), 6))
        ace_list.append(n); st.markdown(f"<p class='small-font'>E-{i+1}: {n}</p>", unsafe_allow_html=True)

with c2:
    st.subheader("🪐 [天] 우주기운")
    for i in range(5):
        random.seed(p_seeds[5] + p_seeds[9] + i)
        n = sorted(random.sample(range(1, 46), 6))
        sky_list.append(n); st.markdown(f"<p class='small-font'>S-{i+1}: {n}</p>", unsafe_allow_html=True)

with c3:
    st.subheader("🧬 [人] 나의공명")
    for i in range(5):
        random.seed(p_seeds[1] + p_seeds[2] + int(u_id, 16) % 1000 + i)
        n = sorted(random.sample(range(1, 46), 6))
        human_list.append(n); st.markdown(f"<p class='small-font'>M-{i+1}: {n}</p>", unsafe_allow_html=True)

# 최종 결과 계산
all_comb = ace_list + sky_list + human_list
counts = collections.Counter([n for combo in all_comb for n in combo])
top_nums = sorted([n for n, c in counts.items() if c > 1], key=lambda x: counts[x], reverse=True)
random.seed(int(u_id, 16))
final_set = sorted((top_nums[:6] + random.sample(range(1, 46), 6))[:6])

st.divider()
st.success(f"## 🍀 최종 공명 조합: {final_set}")

# --- [공명 카드 발행 섹션] ---
with st.expander("🪐 정밀 분석 및 공명 카드 발행", expanded=True):
    z_list = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    planet_dict_for_card = {}
    for _, row in astro_df.iterrows():
        if row['별자리'] in z_list:
            full_angle = (z_list.index(row['별자리']) * 30) + row['좌표']
            planet_dict_for_card[row['행성']] = {'angle': full_angle}

    draw_astrology_card(u_id.upper(), target_sat.strftime('%Y-%m-%d'), planet_dict_for_card, human_list, final_set)
    
    # 해설 테이블
    st.markdown(f"""
    <div style="width: 340px; margin: 10px auto; padding: 15px; background: #FFFFFF; border-radius: 10px; border: 1px solid #ddd; color: #000000;">
        <div style="font-size: 13px; color: #008080; margin-bottom: 10px; font-weight: bold; text-align: center;">[ 행성 기호 가이드 ]</div>
        <table style="width: 100%; font-size: 12px; color: #000000; border-collapse: collapse; line-height: 1.7;">
            <tr><td>☀️ 태양: 자아/생명력</td><td>🌙 달: 감정/내면</td></tr>
            <tr><td>💧 수성: 소통/지성</td><td>✨ 금성: 사랑/가치</td></tr>
            <tr><td>🔥 화성: 열정/행동</td><td>⚡ 목성: 확장/행운</td></tr>
            <tr><td>🪐 토성: 인내/질서</td><td>🌀 천왕성: 변화/혁신</td></tr>
            <tr><td>🔱 해왕성: 영감/꿈</td><td>💀 명왕성: 변형/재생</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.table(astro_df)
