import streamlit as st
import pandas as pd
from gtts import gTTS
import os
from io import BytesIO
import random
import base64

DATA_FILE = "my_wordbook.csv"

# ==========================================
# 関数定義 (キャッシュ・データ処理)
# ==========================================

def load_data():
    if not os.path.exists(DATA_FILE): 
        # ファイルがない場合は初期データを作成
        return [{"word": "example", "meaning": "例", "miss_count": 0}]
    try:
        df = pd.read_csv(DATA_FILE, header=None, names=["word", "meaning", "miss_count"])
        return df.to_dict('records')
    except:
        return []

def save_data(vocab_list):
    df = pd.DataFrame(vocab_list)
    df.to_csv(DATA_FILE, header=False, index=False)

# 音声生成 (キャッシュして高速化)
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

# 自動再生タグ生成
def get_autoplay_html(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    return f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """

# ==========================================
# アプリ本体
# ==========================================
st.set_page_config(page_title="Ultimate Wordbook", layout="centered")

# セッション初期化
if 'vocab_list' not in st.session_state:
    st.session_state.vocab_list = load_data()
if 'study_queue' not in st.session_state:
    st.session_state.study_queue = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
# study_mode: True=学習中, False=メニュー
if 'study_mode' not in st.session_state:
    st.session_state.study_mode = False

st.title("📱 Ultimate Wordbook")

# タブで「学習」と「編集」を分ける
tab1, tab2 = st.tabs(["📚 学習モード", "📝 単語データ編集"])

# ---------------------------------------------------------
# タブ1: 学習モード
# ---------------------------------------------------------
with tab1:
    if not st.session_state.study_mode:
        # --- メニュー画面 ---
        st.info("👇 設定を選んでスタートしてください")
        
        col1, col2 = st.columns(2)
        with col1:
            filter_mode = st.radio("出題対象", ["すべて", "苦手のみ (Miss≧1)"])
        with col2:
            order_mode = st.radio("順番", ["番号順", "ランダム"])
        
        # スタートボタン
        if st.button("▶ 学習スタート", type="primary", use_container_width=True):
            target_list = st.session_state.vocab_list.copy()
            
            # フィルター処理
            if filter_mode == "苦手のみ (Miss≧1)":
                target_list = [w for w in target_list if w["miss_count"] >= 1]
            
            if not target_list:
                st.error("条件に合う単語がありません！")
            else:
                if order_mode == "ランダム":
                    random.shuffle(target_list)
                
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
            
            # ヘッダー (進捗と終了ボタン)
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.progress((idx + 1) / total)
                st.caption(f"Question {idx + 1} / {total}")
            with h_col2:
                if st.button("中断", use_container_width=True):
                    st.session_state.study_mode = False
                    st.rerun()

            # === 問題カード ===
            st.markdown(f"""
            <div style="background-color:#ffffff; padding:20px; border-radius:10px; text-align:center; border: 1px solid #ddd; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h1 style="color:#2c3e50; font-size: 36px; margin:0;">{data['word']}</h1>
            </div>
            """, unsafe_allow_html=True)

            # 音声処理
            audio_bytes = get_audio_bytes(data['word'])
            if audio_bytes:
                # 自動再生 (隠しHTML)
                st.markdown(get_autoplay_html(audio_bytes), unsafe_allow_html=True)
                # 再生バー (聞き直し用)
                st.audio(audio_bytes, format='audio/mp3')

            # ミスバッジ
            if data['miss_count'] > 0:
                st.markdown(f"<p style='color:red; text-align:right;'>⚠️ Miss: {data['miss_count']}</p>", unsafe_allow_html=True)

            # === ★ここが新機能: クリックでパッと開く答え ===
            # ボタンではなく expander を使うことで、再読み込みなしで即表示できます
            with st.expander("👁️ 答えを表示 (タップして開く)", expanded=False):
                st.markdown(f"""
                <div style="text-align:center; padding: 10px;">
                    <h2 style="color:#27ae60; margin:0;">{data['meaning']}</h2>
                    <br>
                    <a href="https://dictionary.cambridge.org/ja/dictionary/english/{data['word']}" target="_blank">📖 辞書で見る</a>
                </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                
                # 判定ボタン
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button("🙆 次へ (Next)", type="primary", use_container_width=True):
                        st.session_state.current_index += 1
                        st.rerun()
                with b_col2:
                    if st.button("🙅 ミス (Miss)", use_container_width=True):
                        # ミス回数を増やして保存
                        word_to_update = data['word']
                        for item in st.session_state.vocab_list:
                            if item['word'] == word_to_update:
                                item['miss_count'] += 1
                        save_data(st.session_state.vocab_list)
                        
                        st.session_state.current_index += 1
                        st.rerun()
        else:
            # 完了画面
            st.success("🎉 学習完了！ Great Job!")
            st.balloons()
            if st.button("メニューに戻る", type="primary"):
                st.session_state.study_mode = False
                st.rerun()

# ---------------------------------------------------------
# タブ2: 単語データ編集 (Excelライクな編集機能)
# ---------------------------------------------------------
with tab2:
    st.header("📝 単語リストの編集")
    st.info("下の表を直接クリックして、書き換えや追加ができます。")

    # 現在のデータをDataFrameに変換
    df = pd.DataFrame(st.session_state.vocab_list)

    # ★Data Editor: 超便利機能
    # num_rows="dynamic" で行の追加・削除が可能になります
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "word": st.column_config.TextColumn("単語", required=True),
            "meaning": st.column_config.TextColumn("意味", required=True),
            "miss_count": st.column_config.NumberColumn("ミス回数", min_value=0, format="%d")
        },
        use_container_width=True,
        key="editor"
    )

    # 保存ボタン
    if st.button("💾 変更を保存する", type="primary"):
        # 編集されたデータをリスト形式に戻して保存
        new_vocab_list = edited_df.to_dict('records')
        # 空行などを除外する簡単なクリーニング
        new_vocab_list = [d for d in new_vocab_list if d['word'] and d['meaning']]
        
        st.session_state.vocab_list = new_vocab_list
        save_data(new_vocab_list)
        st.success("保存しました！")
    
    st.divider()
    
    # バックアップダウンロード
    csv = edited_df.to_csv(header=False, index=False).encode('utf-8')
    st.download_button(
        label="📥 CSVをダウンロード (バックアップ)",
        data=csv,
        file_name='my_wordbook_backup.csv',
        mime='text/csv',
    )
