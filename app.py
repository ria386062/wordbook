import streamlit as st
import pandas as pd
from gtts import gTTS
import os
from io import BytesIO
import random

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 関数定義
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE): 
        return [{"word": "example", "meaning": "例", "miss_count": 0}]
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

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Wordbook", layout="centered")

# スマホで見やすくするためのCSS
st.markdown("""
<style>
    .stButton>button {
        height: 3em;
        font-weight: bold;
    }
    .big-word {
        font-size: 40px !important;
        text-align: center;
        color: #2c3e50;
        margin: 0;
        padding: 20px 0;
    }
    .big-meaning {
        font-size: 24px !important;
        text-align: center;
        color: #27ae60;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# セッション初期化
if 'vocab_list' not in st.session_state: st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state: st.session_state.study_queue = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'study_mode' not in st.session_state: st.session_state.study_mode = False

st.title("📱 My Wordbook")

# タブ切り替え
tab1, tab2 = st.tabs(["📚 学習 (Study)", "✏️ 登録 (Add)"])

# ---------------------------------------------------------
# タブ1: 学習モード
# ---------------------------------------------------------
with tab1:
    if not st.session_state.study_mode:
        # --- メニュー ---
        st.write("設定を選んでスタート")
        
        filter_mode = st.radio("対象", ["すべて", "苦手のみ (Miss≧1)"], horizontal=True)
        order_mode = st.radio("順番", ["番号順", "ランダム"], horizontal=True)
        
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
                st.rerun()

    else:
        # --- 学習画面 ---
        queue = st.session_state.study_queue
        idx = st.session_state.current_index
        total = len(queue)
        
        if idx < total:
            data = queue[idx]
            
            # 進捗バー
            st.progress((idx + 1) / total)
            
            # === 単語表示 (大きく見やすく) ===
            st.markdown(f"<div class='big-word'>{data['word']}</div>", unsafe_allow_html=True)

            # === 音声再生 (スマホ対応) ===
            # 自動再生はできないので、押しやすい位置にプレイヤーを置く
            audio_bytes = get_audio_bytes(data['word'])
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')

            # ミス表示
            if data['miss_count'] > 0:
                st.caption(f"⚠️ 過去のミス: {data['miss_count']}回")

            st.divider()

            # === 答え合わせ (アコーディオン) ===
            # スマホで押しやすい「答えを見る」エリア
            with st.expander("👁️ 答えを表示 (タップ)", expanded=False):
                st.markdown(f"<div class='big-meaning'>{data['meaning']}</div>", unsafe_allow_html=True)
                
                st.write("") # スペース
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🙆 次へ", type="primary", use_container_width=True):
                        st.session_state.current_index += 1
                        st.rerun()
                with col2:
                    if st.button("🙅 ミス", use_container_width=True):
                        # ミス回数更新
                        word_to_update = data['word']
                        for item in st.session_state.vocab_list:
                            if item['word'] == word_to_update:
                                item['miss_count'] += 1
                        save_data(st.session_state.vocab_list)
                        st.session_state.current_index += 1
                        st.rerun()
                
                st.caption("辞書リンク:")
                st.markdown(f"[Cambridge Dictionary](https://dictionary.cambridge.org/ja/dictionary/english/{data['word']})")

            # 中断ボタン
            st.write("")
            if st.button("メニューに戻る"):
                st.session_state.study_mode = False
                st.rerun()
                
        else:
            st.success("学習完了！")
            if st.button("トップへ戻る", type="primary"):
                st.session_state.study_mode = False
                st.rerun()

# ---------------------------------------------------------
# タブ2: 単語登録 (スマホで見やすいシンプル版)
# ---------------------------------------------------------
with tab2:
    st.header("単語の追加")
    
    # シンプルな入力フォーム
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

    st.divider()
    
    # 編集モードへのリンク（必要な時だけ開く）
    with st.expander("📋 リスト一覧・編集・削除"):
        st.info("修正する場合はここをタップして編集してください")
        df = pd.DataFrame(st.session_state.vocab_list)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="editor"
        )
        if st.button("変更を保存"):
            new_list = edited_df.to_dict('records')
            new_list = [d for d in new_list if d['word'] and d['meaning']]
            st.session_state.vocab_list = new_list
            save_data(new_list)
            st.success("保存しました")
