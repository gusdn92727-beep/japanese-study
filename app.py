import streamlit as st
from google import genai
from PIL import Image
from gtts import gTTS
import io
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="효주와 현우의 일본어 공부 도우미",
    page_icon="🇯🇵",
    layout="centered"
)

# 2. 파일 기반 영구 데이터 저장/불러오기 함수
DATA_FILE = "study_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"vocab_list": [], "wrong_notes": []}
    return {"vocab_list": [], "wrong_notes": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 영구 데이터 로드 및 세션 상태 초기화
saved_data = load_data()

if "vocab_list" not in st.session_state:
    st.session_state.vocab_list = saved_data.get("vocab_list", [])
if "wrong_notes" not in st.session_state:
    st.session_state.wrong_notes = saved_data.get("wrong_notes", [])
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "last_text" not in st.session_state:
    st.session_state.last_text = ""

# 3. 비밀번호 보안 기능
ACCESS_PASSWORD = "0487"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 효주와 현우의 일본어 공부 도우미")
    pwd_input = st.text_input("접속 비밀번호를 입력하세요", type="password")
    if st.button("접속하기", use_container_width=True):
        if pwd_input == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# Gemini API 설정
MY_API_KEY = "AQ.Ab8RN6KvkSApFltbjfoBGzd1S5KAd4dWJiR0PwWAbe7Zarz7iA"

# 사이드바: 학습자 모드 및 레벨 설정
st.sidebar.title("⚙️ 학습 및 사용자 설정")

current_user = st.sidebar.radio(
    "👤 현재 누구의 공부 모드인가요?",
    ["👦 현우 공부 모드 (효주가 가르쳐주기)", "👩 효주 자체 공부 모드 (심화 학습)"]
)

st.sidebar.markdown("---")

hw_level = st.sidebar.selectbox(
    "👦 현우 님 레벨",
    ["입문/초급 (N5~N4)", "중급 (N3)", "상급 (N2~N1)"],
    index=0
)

hj_level = st.sidebar.selectbox(
    "👩 효주 님 레벨",
    ["중급 (N3)", "상급 (N2~N1)", "비즈니스/원어민 수준"],
    index=1
)

st.title("🇯🇵 효주와 현우의 맞춤형 일본어 교실")

if "현우" in current_user:
    st.caption(f" 현재 모드: **현우 학습 모드** | 현우 레벨: **{hw_level}** (효주의 가르치기 팁 포함)")
else:
    st.caption(f" 현재 모드: **효주 심화 학습 모드** | 효주 레벨: **{hj_level}** (고난도 문법 및 뉘앙스)")

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 문장/이미지 분석", 
    "👩‍🏫 현우 맞춤 퀴즈 생성", 
    "💬 AI 대화 연습", 
    "⭐ 구분된 단어장", 
    "❌ 오답노트"
])

# ----- TAB 1: 문장 및 이미지 분석 -----
with tab1:
    sub_tab1, sub_tab2 = st.tabs(["📝 텍스트 입력", "📷 사진 업로드/촬영"])
    
    selected_text = ""
    uploaded_image = None

    with sub_tab1:
        selected_text = st.text_area("분석할 일본어 또는 한국어 문장/단어를 입력하세요", height=120)

    with sub_tab2:
        uploaded_image = st.file_uploader(
            "이미지를 업로드하거나 카메라로 찍으세요", 
            type=["jpg", "jpeg", "png", "webp", "bmp", "heic"]
        )
        if uploaded_image is not None:
            st.image(uploaded_image, caption="업로드된 이미지", use_container_width=True)

    if "현우" in current_user:
        prompt_instruction = f"""
        당신은 일본어를 배우는 남자친구(현우)와 가르쳐주는 여자친구(효주)를 돕는 AI 조교입니다.
        현재 분석 대상: 현우 (목표 레벨: {hw_level})

        [중요 표기 규칙]
        - HTML 태그(<ruby> 등) 절대 사용 금지.
        - 한자의 읽는 법(후리가나)은 반드시 '한자(히라가나)' 형태로 표기하세요.

        1. **원문 분석 & 번역**: 쉬운 발음[한글 발음] 및 {hw_level} 수준에 맞춘 설명.
        2. **단어 및 주요 문법**: JLPT 급수와 기초 개념 친절하게 설명.
        3. **[👩‍🏫 효주 님을 위한 가르치기 팁]**: 현우에게 이 문장을 쉽게 설명할 수 있는 포인트(발음 주의점, 쉽게 외우는 팁)를 2~3줄로 다정하게 적어주세요.
        """
    else:
        prompt_instruction = f"""
        당신은 상급 일본어를 공부하는 효주 님을 위한 전문 AI 튜터입니다.
        현재 분석 대상: 효주 (목표 레벨: {hj_level})

        [중요 표기 규칙]
        - HTML 태그(<ruby> 등) 절대 사용 금지.
        - 한자의 읽는 법은 '한자(히라가나)' 형태로 표기하세요.

        1. **심화 문맥 & 뉘앙스 분석**: 단순 번역을 넘어 해당 표현의 실생활 뉘앙스, 유의어와의 차이점을 깊이 있게 설명하세요.
        2. **고급 문법 & 비즈니스/회화 활용법**: {hj_level} 레벨에 어울리는 정중어/경어 표현 및 관련 고급 어휘 추천.
        3. **[💡 효주 님을 위한 심화 포인트]**: 고급 학습자를 위한 격식체 표현이나 자주 실수하는 미묘한 뉘앙스 구별법을 적어주세요.
        """

    if st.button("✨ 상세 분석하기", type="primary", use_container_width=True):
        if not MY_API_KEY:
            st.error("API 키를 확인해 주세요!")
        else:
            with st.spinner("AI가 분석 중입니다..."):
                try:
                    client = genai.Client(api_key=MY_API_KEY)
                    
                    if uploaded_image is not None:
                        img = Image.open(uploaded_image)
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[prompt_instruction, img]
                        )
                    elif selected_text.strip():
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=f"{prompt_instruction}\n\n[분석할 텍스트]:\n{selected_text}"
                        )
                    else:
                        st.warning("분석할 텍스트를 입력하거나 이미지를 올려주세요.")
                        st.stop()

                    st.session_state.last_analysis = response.text
                    st.session_state.last_text = selected_text

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

    # 분석 결과 출력 및 바로 단어장 저장 기능
    if st.session_state.last_analysis:
        st.markdown("---")
        st.markdown(st.session_state.last_analysis, unsafe_allow_html=True)

        if st.session_state.last_text.strip():
            st.markdown("### 🔊 음성 듣기")
            try:
                tts = gTTS(text=st.session_state.last_text, lang='ja')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp, format='audio/mp3')
            except Exception:
                pass

        # 🌟 단어 바로 추가하기 섹션
        st.markdown("---")
        st.subheader("⭐ 분석한 단어/문장 바로 단어장에 저장하기")
        
        default_word = st.session_state.last_text if st.session_state.last_text else ""
        default_owner_idx = 0 if "현우" in current_user else 1

        with st.form("quick_add_vocab_form"):
            quick_owner = st.radio("저장할 단어장", ["👦 현우 단어장", "👩 효주 단어장", "👫 공동 단어장"], 
                                   index=default_owner_idx, horizontal=True)
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                q_word = st.text_input("단어 (일본어)", value=default_word)
                q_meaning = st.text_input("뜻 (한국어)")
            with col_q2:
                q_reading = st.text_input("발음/읽는법 (히라가나)")
                q_memo = st.text_input("메모/뉘앙스 팁")
            
            if st.form_submit_button("📥 단어장에 바로 추가하기", use_container_width=True):
                if q_word and q_meaning:
                    st.session_state.vocab_list.append({
                        "owner": quick_owner,
                        "word": q_word,
                        "reading": q_reading,
                        "meaning": q_meaning,
                        "memo": q_memo
                    })
                    # 파일에 즉시 저장
                    save_data({"vocab_list": st.session_state.vocab_list, "wrong_notes": st.session_state.wrong_notes})
                    st.success(f"[{quick_owner}]에 '{q_word}' 단어가 영구 저장되었습니다!")
                else:
                    st.warning("단어와 뜻을 입력해 주세요.")

# ----- TAB 2: 👩‍🏫 현우 맞춤 퀴즈 생성기 -----
with tab2:
    st.subheader("🎲 맞춤형 퀴즈 출제기")
    st.caption("효주 님이 현우 님에게 낼 퀴즈나, 서로 풀어볼 수 있는 일본어 문제를 만들어 드립니다.")

    quiz_input = st.text_input("퀴즈로 만들 단어나 문장 입력 (예: 勉強, 友達とご飯を食べます)")
    if st.button("🎲 퀴즈 생성하기", use_container_width=True):
        if quiz_input.strip():
            with st.spinner("퀴즈 생성 중..."):
                try:
                    client = genai.Client(api_key=MY_API_KEY)
                    quiz_prompt = f"""
                    사용자를 위한 일본어 퀴즈를 만들어줘. 
                    대상 레벨: {hw_level if '현우' in current_user else hj_level}
                    입력 단어/문장: '{quiz_input}'
                    
                    1. [문제]: 객관식(4지선다) 또는 빈칸 채우기 문제 1개
                    2. [정답 및 해설]: 구분선 밑에 정답과 핵심 풀이 표시
                    """
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=quiz_prompt
                    )
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
        else:
            st.warning("단어나 문장을 입력해 주세요.")

# ----- TAB 3: AI 대화 연습 -----
with tab3:
    st.subheader("💬 AI 일본어 회화 챗봇")
    active_level = hw_level if "현우" in current_user else hj_level
    st.caption(f"현재 **{current_user.split()[0]}** 상태로 대화 중입니다. (수준: {active_level})")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if chat_input := st.chat_input("일본어로 메시지를 입력하세요..."):
        st.session_state.chat_history.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)

        with st.chat_message("assistant"):
            with st.spinner("답변 작성 중..."):
                try:
                    client = genai.Client(api_key=MY_API_KEY)
                    chat_prompt = f"""
                    너는 친절한 일본어 선생님이야. 상대방의 수준은 [{active_level}]이야.
                    어색하거나 틀린 표현이 있다면 친절히 교정해주고, 수준에 맞춰 일본어로 대화를 이어가며 한국어 번역도 함께 적어줘.
                    """
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=f"{chat_prompt}\n\n[사용자 메시지]: {chat_input}"
                    )
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# ----- TAB 4: ⭐ 영구 보존 단어장 -----
with tab4:
    st.subheader("⭐ 단어장")
    
    owner = st.radio("단어장 선택", ["👦 현우 단어장", "👩 효주 단어장", "👫 공동 단어장"], horizontal=True)

    with st.form("add_vocab_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_word = st.text_input("단어 (일본어)")
            new_meaning = st.text_input("뜻 (한국어)")
        with col2:
            new_reading = st.text_input("발음/읽는법 (히라가나)")
            new_memo = st.text_input("메모/뉘앙스 팁")
        
        if st.form_submit_button(f"'{owner}'에 단어 저장"):
            if new_word and new_meaning:
                st.session_state.vocab_list.append({
                    "owner": owner, "word": new_word, "reading": new_reading, 
                    "meaning": new_meaning, "memo": new_memo
                })
                # 파일에 영구 저장
                save_data({"vocab_list": st.session_state.vocab_list, "wrong_notes": st.session_state.wrong_notes})
                st.success(f"[{owner}]에 '{new_word}' 단어가 안전하게 영구 저장되었습니다!")
                st.rerun()

    st.markdown("---")
    
    filtered_list = [item for item in st.session_state.vocab_list if item.get("owner") == owner]
    
    if not filtered_list:
        st.info(f"[{owner}]에 저장된 단어가 없습니다.")
    else:
        for idx, item in enumerate(st.session_state.vocab_list):
            if item.get("owner") == owner:
                col_a, col_b, col_c = st.columns([3, 4, 1])
                with col_a:
                    st.write(f"**{item['word']}** ({item['reading']})")
                with col_b:
                    st.write(f"{item['meaning']} | *{item['memo']}*")
                with col_c:
                    if st.button("삭제", key=f"del_v_{idx}"):
                        st.session_state.vocab_list.pop(idx)
                        save_data({"vocab_list": st.session_state.vocab_list, "wrong_notes": st.session_state.wrong_notes})
                        st.rerun()

# ----- TAB 5: ❌ 영구 보존 오답노트 -----
with tab5:
    st.subheader("❌ 오답노트")
    st.caption("헷갈리는 문법이나 자주 틀리는 표현을 모아두고 복습하세요.")
    
    with st.form("add_wrong_form"):
        w_item = st.text_input("틀린 문장/단어")
        w_correct = st.text_input("올바른 표현/해설")
        w_reason = st.text_area("메모/주의할 뉘앙스")
        
        if st.form_submit_button("오답 노트 추가"):
            if w_item and w_correct:
                st.session_state.wrong_notes.append({
                    "item": w_item, "correct": w_correct, "reason": w_reason
                })
                # 파일에 영구 저장
                save_data({"vocab_list": st.session_state.vocab_list, "wrong_notes": st.session_state.wrong_notes})
                st.success("오답 노트가 안전하게 영구 저장되었습니다!")
                st.rerun()

    st.markdown("---")
    if not st.session_state.wrong_notes:
        st.info("기록된 오답이 없습니다.")
    else:
        for idx, item in enumerate(st.session_state.wrong_notes):
            with st.expander(f"📌 {item['item']}"):
                st.write(f"**정답/해설:** {item['correct']}")
                st.write(f"**메모:** {item['reason']}")
                if st.button("복습 완료 (삭제)", key=f"del_w_{idx}"):
                    st.session_state.wrong_notes.pop(idx)
                    save_data({"vocab_list": st.session_state.vocab_list, "wrong_notes": st.session_state.wrong_notes})
                    st.rerun()

### ✨ 추가된 기능 핵심 요약
1. **검색 후 바로 저장**: 단어를 검색하고 분석 결과를 확인한 뒤, 스크롤을 살짝만 내리면 방금 검색한 단어가 자동으로 채워진 저장 양식이 나옵니다.
2. **단어장 자동 선택**: 현재 선택된 공부 모드(현우/효주)에 맞춰 기본 단어장이 알아서 지정됩니다.
3. **영구 저장 연동**: 여기서 추가한 단어도 즉시 `study_data.json` 파일에 저장되어 앱을 새로고침하거나 나중에 다시 들어와도 안 지워집니다!
