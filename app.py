import streamlit as st
import swisseph as swe
import pandas as pd
import collections
import random
import os
import hashlib
import math
from datetime import datetime, date, timedelta

# [1] 시스템 및 드라이브 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
ephe_path = os.path.join(current_dir, 'sweph')
if not os.path.exists(ephe_path): os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

# [1] 드라이브 저장 경로 설정 (어제의 파일과 충돌 방지)
# 새롭게 관리할 폴더명을 지정합니다.
LOG_DIR = 'universe_lotto'
LOG_FILE = os.path.join(LOG_DIR, 'resonance_log.csv')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

st.set_page_config(layout="wide", page_title="우주 공명 아카이브 V4.7.1")

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
            <div style="background: rgba(0,255,204,0.2); border-radius: 8px; padding: 12px; color: #00ffcc; font-weight: bold; font-size: 24px; border: 2px solid #00ffcc;">{final_res}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- [데이터 생성 로직] ---
with st.sidebar:
    st.header("👤 연구원 프로필")
    user_name = st.text_input("성함", "설계자")
    min_d, max_d = date(1900, 1, 1), date(2100, 12, 31)
    birthday = st.date_input("생년월일", value=date(1990, 1, 1), min_value=min_d, max_value=max_d)
    analysis_date = st.date_input("분석 기준일", value=date.today(), min_value=min_d, max_value=max_d)
    u_id = get_user_id(user_name, birthday)

astro_df, p_seeds, aspects_txt = get_advanced_astro(analysis_date, birthday)

ace_list, sky_list, human_list = [], [], []
for i in range(5):
    random.seed(sum(p_seeds[:3]) + i); ace_list.append(sorted(random.sample(range(1, 46), 6)))
    random.seed(p_seeds[5] + p_seeds[9] + i); sky_list.append(sorted(random.sample(range(1, 46), 6)))
    random.seed(p_seeds[1] + p_seeds[2] + int(u_id, 16) % 1000 + i); human_list.append(sorted(random.sample(range(1, 46), 6)))

all_comb = ace_list + sky_list + human_list
counts = collections.Counter([n for combo in all_comb for n in combo])
top_nums = sorted([n for n, c in counts.items() if c > 1], key=lambda x: counts[x], reverse=True)
random.seed(int(u_id, 16)); final_set = sorted((top_nums[:6] + random.sample(range(1, 46), 6))[:6])

# --- [상단 출력 섹션] ---
st.title(f"🌌 {user_name}의 통합 공명 아카이브 V4.7.1")

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("📊 [地] 에이스")
    for i, nums in enumerate(ace_list): display_lotto_box(nums, f"E{i+1}")
with c2:
    st.subheader("🪐 [天] 우주기운")
    for i, nums in enumerate(sky_list): display_lotto_box(nums, f"S{i+1}")
with c3:
    st.subheader("🧬 [人] 나의공명")
    for i, nums in enumerate(human_list): display_lotto_box(nums, f"M{i+1}")

st.divider()

# --- [최종 조합 및 로그/다운로드 섹션] ---
# --- [로그 저장 및 개인별 다운로드 섹션] ---
st.divider()
res_l, res_r = st.columns([3, 1])

with res_l:
    # 최종 번호 시각화 (기존 동일)
    st.markdown(f"### 🍀 최종 공명 조합 ({analysis_date.strftime('%Y-%m-%d')})")
    # ... (번호 박스 출력) ...

with res_r:
    # [중요] 기존 파일을 건드리지 않고 오직 지정된 새 로그 파일에만 기록
    if st.button("💾 새 마스터 로그에 저장"):
        new_row = pd.DataFrame([{
            'ID': u_id, 
            '이름': user_name, 
            '분석일': analysis_date, 
            '번호': str(final_set), 
            '각도': aspects_txt,
            '기록시점': datetime.now().strftime('%Y-%m-%d %H:%M')
        }])
        # 새 로그 파일에 덧붙이기 (기존 파일은 건드리지 않음)
        new_row.to_csv(LOG_FILE, mode='a', index=False, header=not os.path.exists(LOG_FILE), encoding='utf-8-sig')
        st.toast(f"{analysis_date} 데이터가 통합 로그에 추가되었습니다.")
    
    # 내 기록만 내려받기 (전체 로그는 비공개)
    if os.path.exists(LOG_FILE):
        m_df = pd.read_csv(LOG_FILE)
        user_only_df = m_df[m_df['ID'] == u_id]
        if not user_only_df.empty:
            csv_user = user_only_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 {user_name}님 기록만 받기", csv_user, file_name=f"my_log_{u_id}.csv", mime="text/csv")
            
# ... (상단 핵심 연산 및 로그 저장 로직은 V4.7.1과 동일) ...

# --- [공명 카드 및 기운 해석 섹션] ---
st.divider()
with st.expander("🪐 정밀 분석 및 공명 카드 발행", expanded=True):
    z_list = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    p_dict = {row['행성']: {'angle': (z_list.index(row['별자리']) * 30) + row['좌표']} for _, row in astro_df.iterrows()}
    
    # [1] 공명 카드 출력
    draw_astrology_card(u_id.upper(), analysis_date.strftime('%Y-%m-%d'), p_dict, human_list, final_set)
    
    # [2] 🌟 이모지 공명 해석 테이블 추가
    st.write("### 🔮 우주 기운 이모지 해석")
    emoji_data = [
        {"기호": "☀️", "행성": "태양", "의미": "핵심 에너지, 자아, 생명력의 중심"},
        {"기호": "🌙", "행성": "달", "의미": "무의식, 감정, 매일의 변화와 리듬"},
        {"기호": "💧", "행성": "수성", "의미": "지성, 소통, 데이터의 흐름과 계산"},
        {"기호": "✨", "행성": "금성", "의미": "아름다움, 조화, 금전적 가치와 매력"},
        {"기호": "🔥", "행성": "화성", "의미": "열정, 행동력, 돌파하는 힘과 추진력"},
        {"기호": "⚡", "행성": "목성", "의미": "확장, 행운, 기회의 확대와 낙관주의"},
        {"기호": "🪐", "행성": "토성", "의미": "인내, 구조, 질서와 장기적인 결실"},
        {"기호": "🌀", "행성": "천왕성", "의미": "혁신, 변화, 예상치 못한 반전과 직관"},
        {"기호": "🔱", "행성": "해왕성", "의미": "영감, 꿈, 초월적인 상상력과 공명"},
        {"기호": "💀", "행성": "명왕성", "의미": "재탄생, 변형, 근본적인 변화의 잠재력"}
    ]
    st.table(pd.DataFrame(emoji_data))

    # [3] 행성 정밀 분석표 및 아스펙트
    st.write("### 🌌 행성 위치 정밀 데이터")
    st.table(astro_df)
    st.info(f"**현재 공명 각도:** {aspects_txt}")

