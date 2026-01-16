# [3] 행성 분석 및 공명 카드 발행
st.divider()
with st.expander("🪐 정밀 분석 및 공명 카드 발행", expanded=True):
    # 행성 데이터 변환
    z_list = ["양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리", "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리"]
    planet_dict_for_card = {}
    for _, row in astro_df.iterrows():
        if row['별자리'] in z_list:
            full_angle = (z_list.index(row['별자리']) * 30) + row['좌표']
            planet_dict_for_card[row['행성']] = {'angle': full_angle}

    if st.button("🧧 나의 우주 공명 카드 발행하기"):
        # 카드 드로잉 호출
        draw_astrology_card(u_id.upper(), target_sat.strftime('%Y-%m-%d'), planet_dict_for_card, human_list, final_set)
        
        # 해설 테이블 출력 (카드 바로 아래)
        st.markdown(f"""
        <div style="width: 340px; margin: 0 auto; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; border: 1px dashed #555; color: white;">
            <div style="font-size: 12px; color: #00ffcc; margin-bottom: 10px; font-weight: bold; text-align: center;">[ 행성 기호 가이드 ]</div>
            <table style="width: 100%; font-size: 11px; color: #FFFFFF; border-collapse: collapse; line-height: 1.6;">
                <tr><td>☀️ 태양: 자아/생명력</td><td>🌙 달: 감정/내면</td></tr>
                <tr><td>💧 수성: 소통/지성</td><td>✨ 금성: 사랑/가치</td></tr>
                <tr><td>🔥 화성: 열정/행동</td><td>⚡ 목성: 확장/행운</td></tr>
                <tr><td>🪐 토성: 인내/질서</td><td>🌀 천왕성: 변화/혁신</td></tr>
                <tr><td>🔱 해왕성: 영감/꿈</td><td>💀 명왕성: 변형/재생</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
    
    # 💥 이 부분의 들여쓰기가 중요합니다! (위에 있는 if 버튼과 시작 세로줄을 맞춰주세요)
    st.write(f"**현재 주요 각도(Aspects):** {aspects_txt}")
    st.table(astro_df)
