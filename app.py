import streamlit as st
import pandas as pd
from gtts import gTTS
import os
from io import BytesIO
import random
import base64
import time

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 関数定義
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE): 
        return [{"word": "Start", "meaning": "開始", "miss_count": 0}]
    try:
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        return df.to_dict('records')
    except:
        return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

@st.cache_data(show_spinner=False)
def get_audio_bytes(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.getvalue()
    except:
        return None

# ★重要修正: 毎回異なるHTMLを生成して、ブラウザに再読み込みを強制させる
def get_autoplay_html(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    # time.time()を使って、毎回IDを変えることでブラウザのキャッシュを回避
    unique_id = int(time.time() * 1000) 
    return f"""
        <audio autoplay style="display:none;" id="audio_{unique_id}">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById("audio_{unique_id}");
            audio.play();
        </script>
    """

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Wordbook", layout="centered")

# CSS: スマホで見やすくする
st.markdown("""
<style>
    .stButton>button {
        height: 3.5em;
        font-weight: bold;
        border-radius: 10px;
        font-size: 18px !important;
    }
    .big-word {
        font-size: 42px !important;
        text-align: center;
        color: #2c3e50;
        margin: 20px 0;
        font-weight: 800;
    }
    .big-meaning {
        font-size: 28px !important;
        text-align: center;
        color: #e74c3c;
        font-weight: bold;
        padding: 20px;
        background-color: #fdf2f0;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# セッション初期化
if 'vocab_list' not in st.session_state: st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state: st.session_state.study_queue = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'study_mode' not in st.session_state: st.session_state.study_mode = False
# ★新機能: 答えを表示しているかどうかのフラグ
if 'is_answer_visible' not in st.session_state: st.session_state.is_answer_visible = False

st.title("📱 My Wordbook v13")

# タブ切り替え
tab1, tab2 = st.tabs(["📚 学習 (Study)", "✏️ 登録 (Add)"])

# ---------------------------------------------------------
# タブ1: 学習モード
# ---------------------------------------------------------
with tab1:
    if not st.session_state.study_mode:
        # === メニュー画面 ===
        st.write("設定を選んでスタート")
        col1, col2 = st.columns(2)
        with col1:
            filter_mode = st.radio("対象", ["すべて", "苦手のみ (Miss≧1)"])
        with col2:
            order_mode = st.radio("順番", ["番号順", "ランダム"])
        
        if st.button("▶ 学習スタート", type="primary", use_container_width=True):
            target_list = st.session_state.vocab_list.copy()
            if filter_mode == "苦手のみ (Miss≧1)":
                target_list = [w for w in target_list if w["miss_count"] >= 1]
            
            if not target_list:
                st.error("単語がありません")
            else:
                if order_mode == "ランダム": random.shuffle(target_list)
                st.session_state.study_queue = target_list
                st.session_state.current_index = 0
                st.session_state.study_mode = True
                st.session_state.is_answer_visible = False # 最初は答えを隠す
                st.rerun()

    else:
        # === 学習中画面 ===
        queue = st.session_state.study_queue
        idx = st.session_state.current_index
        total = len(queue)
        
        if idx < total:
            data = queue[idx]
            
            # ヘッダー
            st.progress((idx + 1) / total)
            st.caption(f"Question {idx + 1} / {total}")
            
            # 1. 単語表示（常に表示）
            st.markdown(f"<div class='big-word'>{data['word']}</div>", unsafe_allow_html=True)
            
            # 音声再生処理
            audio_bytes = get_audio_bytes(data['word'])
            
            # ★フェーズ分岐: 答えを見る前 or 見た後
            if not st.session_state.is_answer_visible:
                # ==========================
                # PHASE A: 問題出題中
                # ==========================
                
                # 自動再生（答えを見る前だけ再生する）
                # keyにidxを含めることで、単語が変わるたびに強制的に再描画させる
                if audio_bytes:
                    autoplay_html = get_autoplay_html(audio_bytes)
                    st.components.v1.html(autoplay_html, height=0)

                # 手動再生ボタン（予備）
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/mp3')

                st.write("") # スペース調整
                st.info("答えを思い浮かべてください...")
                
                # 「答えを見る」ボタン
                if st.button("答えを表示 (Show Answer)", type="primary", use_container_width=True):
                    st.session_state.is_answer_visible = True
                    st.rerun()

            else:
                # ==========================
                # PHASE B: 答え合わせ中
                # ==========================
                
                # 意味をドカンと表示
                st.markdown(f"<div class='big-meaning'>{data['meaning']}</div>", unsafe_allow_html=True)

                # ミス回数表示
                if data['miss_count'] > 0:
                    st.markdown(f"<p style='text-align:center; color:red;'>⚠️ 過去のミス: {data['miss_count']}回</p>", unsafe_allow_html=True)

                st.write("") # スペース

                # 判定ボタンエリア
                col1, col2 = st.columns(2)
                with col1:
                    # 分かったボタン
                    if st.button("🙆 次へ (Next)", type="primary", use_container_width=True):
                        st.session_state.current_index += 1
                        st.session_state.is_answer_visible = False # 次の単語のために隠す
                        st.rerun()
                with col2:
                    # 分からないボタン
                    if st.button("🙅 ミス (Miss)", use_container_width=True):
                        word_to_update = data['word']
                        for item in st.session_state.vocab_list:
                            if item['word'] == word_to_update:
                                item['miss_count'] += 1
                        save_data(st.session_state.vocab_list)
                        
                        st.session_state.current_index += 1
                        st.session_state.is_answer_visible = False # 次の単語のために隠す
                        st.rerun()
                
                st.markdown("---")
                st.markdown(f"[📖 辞書で確認する](https://dictionary.cambridge.org/ja/dictionary/english/{data['word']})")

            # 中断ボタン（常に下部に表示）
            st.divider()
            if st.button("メニューに戻る", key="menu_back"):
                st.session_state.study_mode = False
                st.rerun()
                
        else:
            # 終了画面
            st.success("🎉 学習完了！ Great Job!")
            st.balloons()
            if st.button("トップへ戻る", type="primary"):
                st.session_state.study_mode = False
                st.rerun()

# ---------------------------------------------------------
# タブ2: 単語登録
# ---------------------------------------------------------
with tab2:
    st.header("単語の追加")
    with st.form("add_form", clear_on_submit=True):
        new_word = st.text_input("英単語")
        new_meaning = st.text_input("意味")
        submitted = st.form_submit_button("追加する", type="primary", use_container_width=True)
        
        if submitted:
            if new_word and new_meaning:
                st.session_state.vocab_list.append({"word": new_word, "meaning": new_meaning, "miss_count": 0})
                save_data(st.session_state.vocab_list)
                st.success(f"「{new_word}」を追加しました！")
            else:
                st.warning("文字を入力してください")
    
    with st.expander("📋 リスト一覧・編集・削除"):
        df = pd.DataFrame(st.session_state.vocab_list)
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
        if st.button("変更を保存"):
            new_list = edited_df.to_dict('records')
            new_list = [d for d in new_list if d['word'] and d['meaning']]
            st.session_state.vocab_list = new_list
            save_data(new_list)
            st.success("保存しました")
