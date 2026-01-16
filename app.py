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
# --- [함수: 텍스트 가시성 대폭 개선 버전] ---
def draw_astrology_card(u_id, target_date, planet_data, res_sets, final_res):
    planet_markers = ""
    center, radius = 100, 80
    symbols = {"태양": "☀️", "달": "🌙", "수성": "💧", "금성": "✨", "화성": "🔥", "목성": "⚡", "토성": "🪐", "천왕성": "🌀", "해왕성": "🔱", "명왕성": "💀"}
    
    for p_name, p_info in planet_data.items():
        angle_rad = math.radians(p_info['angle'] - 90)
        px, py = center + radius * math.cos(angle_rad), center + radius * math.sin(angle_rad)
        sym = symbols.get(p_name, "●")
        planet_markers += f'<div style="position:absolute; left:{px}px; top:{py}px; font-size:14px; transform:translate(-50%, -50%);">{sym}</div>'

    # 핵심: 모든 텍스트를 흰색(#FFFFFF)으로 강제 지정하고 크기를 키움
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; flex-direction: column; padding: 10px;">
        <div style="width: 340px; background: #1a1c23; 
                    border: 1px solid #444; border-radius: 15px; padding: 25px; text-align: center; color: white;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.7);">
            
            <div style="font-size: 16px; font-weight: bold; letter-spacing: 1px; color: #FFFFFF !important; margin-bottom: 15px;">
                ID: {u_id}
            </div>
            
            <div style="position: relative; width: 200px; height: 200px; margin: 0 auto; 
                        border: 1px solid #333; border-radius: 50%; background: url('https://img.icons8.com/ios/200/ffffff/zodiac-wheel.png') no-repeat center; background-size: 90%;">
                {planet_markers}
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                            width: 50px; height: 50px; background: white; padding: 2px; border-radius: 4px;">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=50x50&data=https://universelotto-tzqbe6sppmmbesq9rndwah.streamlit.app/?id={u_id}" style="width:100%;"/>
                </div>
            </div>
            
            <div style="font-size: 15px; color: #FFFFFF !important; font-weight: bold; margin: 20px 0;">
                {target_date} ANALYSIS
            </div>
            
            <div style="font-size: 15px; color: #FFFFFF !important; line-height: 1.8; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px;">
                {'<br>'.join([str(s) for s in res_sets])}
            </div>
            
            <div style="background: rgba(0,255,204,0.2); border-radius: 8px; padding: 12px; 
                        color: #00ffcc; font-weight: bold; font-size: 24px; border: 2px solid #00ffcc;">
                {final_res}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- [실행부: 테이블 글자색 검은색 유지] ---
st.divider()
with st.expander("🪐 정밀 분석 및 공명 카드 발행", expanded=True):
    z_list = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    planet_dict_for_card = {}
    for _, row in astro_df.iterrows():
        if row['별자리'] in z_list:
            full_angle = (z_list.index(row['별자리']) * 30) + row['좌표']
            planet_dict_for_card[row['행성']] = {'angle': full_angle}

    draw_astrology_card(u_id.upper(), target_sat.strftime('%Y-%m-%d'), planet_dict_for_card, human_list, final_set)
    
    # 해설 테이블: 배경은 밝게, 글자는 검은색(#000000)
    st.markdown(f"""
    <div style="width: 340px; margin: 10px auto; padding: 15px; background: #FFFFFF; border-radius: 10px; border: 1px solid #ddd; color: #000000; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 13px; color: #008080; margin-bottom: 10px; font-weight: bold; text-align: center;">[ 행성 기호 가이드 ]</div>
        <table style="width: 100%; font-size: 12px; color: #000000 !important; border-collapse: collapse; line-height: 1.7;">
            <tr><td>☀️ 태양: 자아/생명력</td><td>🌙 달: 감정/내면</td></tr>
            <tr><td>💧 수성: 소통/지성</td><td>✨ 금성: 사랑/가치</td></tr>
            <tr><td>🔥 화성: 열정/행동</td><td>⚡ 목성: 확장/행운</td></tr>
            <tr><td>🪐 토성: 인내/질서</td><td>🌀 천왕성: 변화/혁신</td></tr>
            <tr><td>🔱 해왕성: 영감/꿈</td><td>💀 명왕성: 변형/재생</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("👤 연구원 프로필")
    user_name = st.text_input("성함", "설계자")
    birthday = st.date_input("생년월일", value=date(1990, 1, 1), min_value=date(1800, 1, 1), max_value=date(2100, 12, 31))
    analysis_date = st.date_input("분석 기준일", value=date.today())
    u_id = get_user_id(user_name, birthday)
    st.info(f"🆔 연구원 ID: {u_id.upper()}")

target_sat = analysis_date + timedelta(days=(5 - analysis_date.weekday()) % 7)
astro_df, p_seeds, aspects_txt = get_advanced_astro(target_sat, birthday)

st.title(f"🌌 {user_name}의 우주 공명 아카이브 V4.5.4")

# [1] 숫자 매트릭스 계산 영역
ace_list, sky_list, human_list = [], [], []
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("📊 [地] 에이스라인")
    if os.path.exists('master_list.xlsm'):
        df_xl = pd.read_excel('master_list.xlsm', engine='openpyxl')
        last_idx = df_xl.iloc[:, 2].last_valid_index()
        stable_df = df_xl.iloc[max(0, last_idx-54):last_idx+1, 2:9]
        ace_seed = int(np.nansum(pd.to_numeric(stable_df.values.flatten(), errors='coerce')))
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

# [2] 최종 결과 및 QR/저장
st.divider()
all_comb = ace_list + sky_list + human_list
if all_comb:
    counts = collections.Counter([n for combo in all_comb for n in combo])
    top_nums = sorted([n for n, c in counts.items() if c > 1], key=lambda x: counts[x], reverse=True)
    random.seed(int(u_id, 16))
    final_set = sorted((top_nums[:6] + random.sample(range(1, 46), 6))[:6])
    
    res_l, res_r = st.columns([2, 1])
    with res_l:
        st.success(f"## 🍀 최종 공명 조합: {final_set}")
        if st.button("📊 이 주의 분석 저장"):
            log_f = 'resonance_log.csv'
            rows = []
            for cat, data in zip(['지', '천', '인'], [ace_list, sky_list, human_list]):
                for i, nums in enumerate(data):
                    rows.append({'추첨일': target_sat, 'ID': u_id, '이름': user_name, '구분': f"{cat}_{i+1}", '데이터': str(nums), '각도정보': ''})
            rows.append({'추첨일': target_sat, 'ID': u_id, '이름': user_name, '구분': '최종', '데이터': str(final_set), '각도정보': ''})
            rows.append({'추첨일': target_sat, 'ID': u_id, '이름': user_name, '구분': '🪐각도', '데이터': 'Aspects', '각도정보': aspects_txt})
            pd.DataFrame(rows).to_csv(log_f, mode='a', index=False, header=not os.path.exists(log_f), encoding='utf-8-sig')
            st.toast("저장 완료!")

    with res_r:
        qr = qrcode.make(f"ID:{u_id}\nNum:{final_set}")
        buf = io.BytesIO(); qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"Researcher: {u_id.upper()}", width=110)

# [3] 행성 분석 및 공명 카드 발행
st.divider()

# astro_df가 위에서 정상적으로 생성되었는지 체크
if 'astro_df' in locals() and not astro_df.empty:
    with st.expander("🪐 정밀 분석 및 공명 카드 발행", expanded=True):
        # 1. 행성 데이터 변환 로직
        z_list = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
        planet_dict_for_card = {}
        
        for _, row in astro_df.iterrows():
            if row['별자리'] in z_list:
                full_angle = (z_list.index(row['별자리']) * 30) + row['좌표']
                planet_dict_for_card[row['행성']] = {'angle': full_angle}

        # 2. 카드 드로잉 함수 호출
        # (함수 이름이 draw_astrology_card로 상단에 정의되어 있어야 합니다)
        try:
            draw_astrology_card(u_id.upper(), target_sat.strftime('%Y-%m-%d'), planet_dict_for_card, human_list, final_set)
            
            # 3. 해설 테이블 (흰 배경에 검은 글씨)
            st.markdown(f"""
            <div style="width: 340px; margin: 10px auto; padding: 15px; background: #FFFFFF; border-radius: 10px; border: 1px solid #ddd; color: #000000; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; color: #008080; margin-bottom: 10px; font-weight: bold; text-align: center;">[ 행성 기호 가이드 ]</div>
                <table style="width: 100%; font-size: 12px; color: #000000 !important; border-collapse: collapse; line-height: 1.7;">
                    <tr><td>☀️ 태양: 자아/생명력</td><td>🌙 달: 감정/내면</td></tr>
                    <tr><td>💧 수성: 소통/지성</td><td>✨ 금성: 사랑/가치</td></tr>
                    <tr><td>🔥 화성: 열정/행동</td><td>⚡ 목성: 확장/행운</td></tr>
                    <tr><td>🪐 토성: 인내/질서</td><td>🌀 천왕성: 변화/혁신</td></tr>
                    <tr><td>🔱 해왕성: 영감/꿈</td><td>💀 명왕성: 변형/재생</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**현재 주요 각도(Aspects):** {aspects_txt}")
            st.table(astro_df)
            
        except NameError:
            st.error("카드 그리기 함수(draw_astrology_card)가 정의되지 않았습니다. 코드 상단을 확인해주세요.")
else:
    st.warning("천체 데이터(astro_df)를 불러오지 못했습니다. 생년월일을 다시 확인해주세요.")
