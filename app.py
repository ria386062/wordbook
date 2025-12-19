import streamlit as st
import pandas as pd
from gtts import gTTS
import os
import tempfile
import random

DATA_FILE = "my_wordbook.csv"

# --- データ読み込み・保存 ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        # CSVを読み込む（ヘッダーなしと仮定）
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        return df.to_dict('records')
    except:
        return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# --- 音声生成 ---
def get_audio_bytes(text):
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as audio_file:
                audio_bytes = audio_file.read()
        return audio_bytes
    except:
        return None

# ==========================================
# アプリ本体
# ==========================================
st.title("📱 My Smart Wordbook")

# セッション状態の初期化（画面が変わっても変数を保持するため）
if 'vocab_list' not in st.session_state:
    st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state:
    st.session_state.study_queue = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'study_mode' not in st.session_state:
    st.session_state.study_mode = False

# --- サイドバー：単語登録 & 設定 ---
with st.sidebar:
    st.header("⚙️ 設定 & 登録")
    
    # 新規登録
    with st.expander("📝 単語を追加"):
        new_word = st.text_input("単語")
        new_meaning = st.text_input("意味")
        if st.button("追加"):
            if new_word and new_meaning:
                st.session_state.vocab_list.append({"word": new_word, "meaning": new_meaning, "miss_count": 0})
                save_data(st.session_state.vocab_list)
                st.success(f"「{new_word}」を追加しました")
            else:
                st.warning("単語と意味を入力してください")

    st.divider()

    # 学習設定
    st.subheader("学習モード設定")
    filter_mode = st.radio("出題対象", ["すべて", "苦手のみ (Miss≧1)"])
    order_mode = st.radio("順番", ["番号順", "ランダム"])
    
    # 開始・リセットボタン
    if st.button("▶ 学習スタート / リセット", type="primary"):
        target_list = st.session_state.vocab_list.copy()
        
        # フィルター
        if filter_mode == "苦手のみ (Miss≧1)":
            target_list = [w for w in target_list if w["miss_count"] >= 1]
        
        if not target_list:
            st.error("対象の単語がありません！")
        else:
            # シャッフル
            if order_mode == "ランダム":
                random.shuffle(target_list)
            
            st.session_state.study_queue = target_list
            st.session_state.current_index = 0
            st.session_state.show_answer = False
            st.session_state.study_mode = True
            st.rerun()

# --- メインエリア：学習画面 ---
if st.session_state.study_mode and st.session_state.study_queue:
    # 現在のデータ取得
    idx = st.session_state.current_index
    total = len(st.session_state.study_queue)
    
    if idx < total:
        data = st.session_state.study_queue[idx]
        
        # 進捗バー
        st.progress((idx + 1) / total)
        st.caption(f"Question {idx + 1} / {total}")

        # 単語カード表示
        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; text-align:center;">
            <h1 style="color:#2c3e50;">{data['word']}</h1>
        </div>
        """, unsafe_allow_html=True)

        # 音声再生（ブラウザのプレイヤーを表示）
        audio_bytes = get_audio_bytes(data['word'])
        if audio_bytes:
            st.audio(audio_bytes, format='audio/mp3')

        # ミス回数表示
        if data['miss_count'] > 0:
            st.error(f"⚠️ Miss Count: {data['miss_count']}")

        # --- 答え合わせエリア ---
        if not st.session_state.show_answer:
            if st.button("答えを見る", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        else:
            # 答え表示
            st.markdown(f"""
            <div style="text-align:center; margin-top:10px;">
                <h2 style="color:#555;">{data['meaning']}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🙆 分かる", use_container_width=True):
                    # 次へ
                    st.session_state.current_index += 1
                    st.session_state.show_answer = False
                    st.rerun()
            with col2:
                if st.button("🙅 分からない", use_container_width=True):
                    # ミス回数更新
                    # study_queueの中身だけでなく、大元のvocab_listも更新して保存が必要
                    word_to_update = data['word']
                    for item in st.session_state.vocab_list:
                        if item['word'] == word_to_update:
                            item['miss_count'] += 1
                    save_data(st.session_state.vocab_list)
                    
                    # 次へ
                    st.session_state.current_index += 1
                    st.session_state.show_answer = False
                    st.rerun()

    else:
        st.success("🎉 学習完了！お疲れ様でした！")
        if st.button("トップに戻る"):
            st.session_state.study_mode = False
            st.rerun()

else:
    if not st.session_state.vocab_list:
        st.info("👈 左のサイドバーから単語を追加してください")
    else:
        st.info("👈 左のサイドバーで設定をして「学習スタート」を押してください")
        # データ一覧表示
        with st.expander("登録済み単語リストを見る"):
            st.dataframe(pd.DataFrame(st.session_state.vocab_list))