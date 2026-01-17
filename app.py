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

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.5.9")

# --- [핵심 함수] ---
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
            <div style="background: rgba(0,255,204,0.2); border-radius: 8px; padding: 12px; color: #00ffcc; font-weight: bold; font-size: 24px; border: 2px solid #00ffcc;">{final_res}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- [사이드바 설정: 날짜 범위 대폭 확장] ---
with st.sidebar:
    st.header("👤 연구원 프로필")
    user_name = st.text_input("성함", "설계자")
    # 생년월일과 분석 기준일의 범위를 1900년부터 2100년까지로 설정
    min_d = date(1900, 1, 1)
    max_d = date(2100, 12, 31)
    birthday = st.date_input("생년월일", value=date(1990, 1, 1), min_value=min_d, max_value=max_d)
    analysis_date = st.date_input("분석 기준일", value=date.today(), min_value=min_d, max_value=max_d)
    u_id = get_user_id(user_name, birthday)

# 로또 추첨일(토요일)로 자동 보정하지 않고, 선택한 '분석 기준일' 그 자체를 분석 시점으로 사용
target_sat = analysis_date 
astro_df, p_seeds, aspects_txt = get_advanced_astro(target_sat, birthday)

# --- [천지인 매트릭스 계산] ---
ace_list, sky_list, human_list = [], [], []
for i in range(5):
    random.seed(sum(p_seeds[:3]) + i); ace_list.append(sorted(random.sample(range(1, 46), 6)))
    random.seed(p_seeds[5] + p_seeds[9] + i); sky_list.append(sorted(random.sample(range(1, 46), 6)))
    random.seed(p_seeds[1] + p_seeds[2] + int(u_id, 16) % 1000 + i); human_list.append(sorted(random.sample(range(1, 46), 6)))

all_comb = ace_list + sky_list + human_list
counts = collections.Counter([n for combo in all_comb for n in combo])
top_nums = sorted([n for n, c in counts.items() if c > 1], key=lambda x: counts[x], reverse=True)
random.seed(int(u_id, 16))
final_set = sorted((top_nums[:6] + random.sample(range(1, 46), 6))[:6])

# --- [화면 출력] ---
st.title(f"🌌 {user_name}의 우주 공명 아카이브 V4.5.9")
c1, c2, c3 = st.columns(3)
with c1: st.subheader("📊 [地] 에이스"); st.write(ace_list)
with c2: st.subheader("🪐 [天] 우주기운"); st.write(sky_list)
with c3: st.subheader("🧬 [人] 나의공명"); st.write(human_list)

st.divider()
res_l, res_r = st.columns([3, 1])
with res_l: st.success(f"## 🍀 최종 공명 조합 ({target_sat.strftime('%Y-%m-%d')}): {final_set}")
with res_r:
    if st.button("📊 이 시점의 데이터 저장"):
        log_f = 'resonance_log.csv'
        log_df = pd.DataFrame([{'분석일': target_sat, 'ID': u_id, '결과': str(final_set), '각도': aspects_txt}])
        log_df.to_csv(log_f, mode='a', index=False, header=not os.path.exists(log_f), encoding='utf-8-sig')
        st.toast(f"{target_sat} 데이터 저장 완료!")

with st.expander("🪐 정밀 분석 및 공명 카드 발행", expanded=True):
    z_list = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    planet_dict = {row['행성']: {'angle': (z_list.index(row['별자리']) * 30) + row['좌표']} for _, row in astro_df.iterrows()}
    draw_astrology_card(u_id.upper(), target_sat.strftime('%Y-%m-%d'), planet_dict, human_list, final_set)
    st.table(astro_df)
