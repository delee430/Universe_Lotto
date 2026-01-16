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
from datetime import datetime, date, timedelta

# [1] 경로 및 시스템 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(current_dir, 'sweph')
if not os.path.exists(ephe_path): os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.5.3")
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

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("👤 연구원 프로필")
    user_name = st.text_input("성함", "설계자")
    birthday = st.date_input("생년월일", value=date(1990, 1, 1))
    analysis_date = st.date_input("분석 기준일", value=date.today())
    u_id = get_user_id(user_name, birthday)
    st.info(f"🆔 연구원 ID: {u_id.upper()}")

target_sat = analysis_date + timedelta(days=(5 - analysis_date.weekday()) % 7)
astro_df, p_seeds, aspects_txt = get_advanced_astro(target_sat, birthday)

st.title(f"🌌 {user_name}의 우주 공명 아카이브 V4.3.5")

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
        if st.button("📊 이 주의 분석 16줄 + 천체각도 저장"):
            log_f = 'resonance_log.csv'
            rows = []
            for cat, data in zip(['지', '천', '인'], [ace_list, sky_list, human_list]):
                for i, nums in enumerate(data):
                    rows.append({'추첨일': target_sat, 'ID': u_id, '이름': user_name, '구분': f"{cat}_{i+1}", '데이터': str(nums), '각도정보': ''})
            rows.append({'추첨일': target_sat, 'ID': u_id, '이름': user_name, '구분': '최종', '데이터': str(final_set), '각도정보': ''})
            rows.append({'추첨일': target_sat, 'ID': u_id, '이름': user_name, '구분': '🪐각도', '데이터': 'Aspects', '각도정보': aspects_txt})
            pd.DataFrame(rows).to_csv(log_f, mode='a', index=False, header=not os.path.exists(log_f), encoding='utf-8-sig')
            st.toast("성공적으로 저장되었습니다!")

    with res_r:
        qr = qrcode.make(f"ID:{u_id}\nNum:{final_set}")
        buf = io.BytesIO(); qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"Researcher: {u_id.upper()}", width=110)

# [3] 행성 분석 데이터 (맨 아래 배치)
st.divider()
with st.expander("🪐 정밀 분석 데이터 및 개인 아카이브", expanded=False):
    st.write(f"**현재 주요 각도(Aspects):** {aspects_txt}")
    st.table(astro_df)
    if os.path.exists('resonance_log.csv'):
        try:
            logs = pd.read_csv('resonance_log.csv', on_bad_lines='skip')
            my_data = logs[logs['ID'].astype(str) == str(u_id)]
            if not my_data.empty:
                csv = my_data.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📂 내 기록 CSV 다운로드", csv, f"archive_{u_id}.csv", "text/csv")
        except: st.error("로그 파일 구조를 갱신해야 합니다. 데이터를 한 번 저장해 보세요.")