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

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.6.2")

# --- [핵심 함수] ---
def get_user_id(name, birthday):
    return hashlib.md5(f"{name}_{birthday.strftime('%Y%m%d')}".encode()).hexdigest()[:8]

def get_advanced_astro(target_date, birthday):
    jd_t = swe.julday(target_date.year, target_date.month, target_date.day, 11)
    jd_b = swe.julday(birthday.year, birthday.month, birthday.day, 12)
    results, seeds, pos_dict = [], [], {}
    planets = {"태양": swe.SUN, "달": swe.MOON, "수성": swe.MERCURY, "금성": swe.VENUS, "화성": swe.MARS, 
               "목성": swe.JUPITER, "토성": swe.SATURN, "천왕성": swe.URANUS, "해왕성": swe.NEPTUNE, "명왕성": swe.PLUTO}
    for name, code in planets.items():
        res_t, _ = swe.calc_ut(jd_t, code)
        res_b, _ = swe.calc_ut(jd_b, code)
        seeds.append(int(res_t[0] * 1000 + res_b[0] * 10 + birthday.day))
    return seeds

# --- [사이드바 설정] ---
with st.sidebar:
    st.header("👤 연구원 프로필")
    user_name = st.text_input("성함", "설계자")
    min_d, max_d = date(1900, 1, 1), date(2100, 12, 31)
    birthday = st.date_input("생년월일", value=date(1990, 1, 1), min_value=min_d, max_value=max_d)
    analysis_date = st.date_input("분석 기준일", value=date.today(), min_value=min_d, max_value=max_d)
    u_id = get_user_id(user_name, birthday)
    st.info(f"현재 접속 ID: {u_id}")

p_seeds = get_advanced_astro(analysis_date, birthday)

# --- [번호 계산 로직 - 간소화 버전] ---
def generate_nums(seed_val, count=5):
    res = []
    for i in range(count):
        random.seed(seed_val + i)
        res.append(sorted(random.sample(range(1, 46), 6)))
    return res

human_list = generate_nums(p_seeds[1] + p_seeds[2] + int(u_id, 16) % 1000)
final_set = human_list[0] # 예시

# --- [메인 화면] ---
st.title(f"🌌 {user_name}의 통합 공명 아카이브 V4.6.2")

# --- [로그 저장 및 통합 관리 섹션] ---
st.divider()
log_col1, log_col2 = st.columns([1, 1])

log_f = 'integrated_resonance_log.csv'

with log_col1:
    st.subheader("💾 현재 데이터 기록")
    if st.button("📊 이 시점의 로그 서버에 기록"):
        new_data = pd.DataFrame([{
            '이름': user_name,
            '생일': birthday.strftime('%Y-%m-%d'),
            'ID': u_id,
            '분석일': analysis_date.strftime('%Y-%m-%d'),
            '최종번호': str(final_set),
            '기록시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }])
        new_data.to_csv(log_f, mode='a', index=False, header=not os.path.exists(log_f), encoding='utf-8-sig')
        st.success(f"[{user_name}]님의 데이터가 통합 서버에 기록되었습니다.")

with log_col2:
    st.subheader("📥 전체 로그 내려받기")
    if os.path.exists(log_f):
        with open(log_f, "rb") as file:
            st.download_button(
                label="📁 통합 마스터 로그(.csv) 다운로드",
                data=file,
                file_name="master_resonance_log.csv",
                mime="text/csv"
            )
    else:
        st.write("아직 기록된 로그가 없습니다.")

# --- [ID별/개인별 로그 출력 섹션] ---
st.divider()
st.subheader("🔍 아카이브 히스토리 분석")

if os.path.exists(log_f):
    master_df = pd.read_csv(log_f)
    
    # 필터링 옵션
    filter_opt = st.radio("조회 모드", ["전체 보기", "현재 접속자(ID) 기록만 보기"], horizontal=True)
    
    if filter_opt == "현재 접속자(ID) 기록만 보기":
        # 이름과 생일이 같은(즉, ID가 같은) 데이터만 필터링
        display_df = master_df[master_df['ID'] == u_id]
    else:
        display_df = master_df

    st.dataframe(display_df, use_container_width=True)
    st.caption("※ 이름과 생일이 동일한 기록은 같은 ID로 묶여 관리됩니다.")
else:
    st.info("데이터를 먼저 기록해주세요.")
