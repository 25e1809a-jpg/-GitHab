import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# ページ設定
st.set_page_config(page_title="習慣化草生やしトラッカー", page_icon="🌱", layout="wide")

CSV_FILE = "habit_log.csv"
HABITS = ["💪 筋トレ・運動", "📚 読書（15分以上）", "🌅 7時までに起床"]

# データの読み込み・初期化関数
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    else:
        return pd.DataFrame(columns=["date"] + HABITS + ["score"])

# データの保存関数
def save_data(date, habit_results):
    df = load_data()
    score = sum(habit_results.values())
    
    # 同じ日付のデータがあれば上書き、なければ新規追加
    df = df[df["date"] != date]
    new_row = {"date": date, **habit_results, "score": score}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = df.sort_values("date")
    df.to_csv(CSV_FILE, index=False)

# --- UI部分 ---
st.title("🌱 習慣化「草生やし」トラッカー")
st.write("毎日の習慣を達成して、カレンダーを緑色に染めましょう！")

# サイドバー：今日の記録入力
st.sidebar.header("📝 記録をつける")
target_date = st.sidebar.date_input("日付を選択", datetime.now().date())

df = load_data()
existing_row = df[df["date"] == target_date]

habit_inputs = {}
for habit in HABITS:
    # 既に記録がある場合はチェック状態を復元
    default_val = bool(existing_row[habit].values[0]) if not existing_row.empty else False
    habit_inputs[habit] = st.sidebar.checkbox(habit, value=default_val)

if st.sidebar.button("記録を保存する", type="primary"):
    save_data(target_date, habit_inputs)
    st.sidebar.success(f"{target_date} の記録を保存しました！")
    df = load_data() # 再読み込み

# --- 草生やし（ヒートマップ）の描画 ---
st.subheader("📅 過去半年間の達成状況")

# 過去180日分の日付ベースを作成
end_date = datetime.now().date()
start_date = end_date - timedelta(days=180)
all_dates = pd.date_range(start=start_date, end=end_date)

calendar_df = pd.DataFrame({"date": all_dates.date})
calendar_df = pd.merge(calendar_df, df, on="date", how="left").fillna(0)

# カレンダー配置用の座標計算（横軸：週番号、縦軸：曜日）
calendar_df["datetime"] = pd.to_datetime(calendar_df["date"])
calendar_df["weekday"] = calendar_df["datetime"].dt.weekday # 0:月曜 〜 6:日曜
calendar_df["week"] = (calendar_df["datetime"] - calendar_df["datetime"].min()).dt.days // 7

# ホバー時に表示するテキスト作成
hover_texts = []
for _, row in calendar_df.iterrows():
    done_list = [h for h in HABITS if row.get(h, 0) == 1]
    done_str = "<br>・".join(done_list) if done_list else "達成なし"
    hover_texts.append(f"<b>{row['date']}</b><br>達成数: {int(row['score'])}/{len(HABITS)}<br>・{done_str}")

# 色の段階設定（0:グレー 〜 3:濃い緑）
colorscale = [
    [0.0, "#ebedf0"],   # 0個：未達成（薄いグレー）
    [0.33, "#9be9a8"],  # 1個：薄い緑
    [0.66, "#40c463"],  # 2個：中くらいの緑
    [1.0, "#216e39"]    # 3個：濃い緑
]

fig = go.Figure(data=go.Heatmap(
    x=calendar_df["week"],
    y=calendar_df["weekday"],
    z=calendar_df["score"],
    text=hover_texts,
    hoverinfo="text",
    colorscale=colorscale,
    zmin=0,
    zmax=len(HABITS),
    xgap=4, # マス目の隙間
    ygap=4,
    showscale=False
))

fig.update_layout(
    height=240,
    margin=dict(l=20, r=20, t=20, b=20),
    yaxis=dict(
        tickmode="array",
        tickvals=[0, 1, 2, 3, 4, 5, 6],
        ticktext=["月", "火", "水", "木", "金", "土", "日"],
        autorange="reversed", # 月曜を一番上にする
        showgrid=False,
        zeroline=False
    ),
    xaxis=dict(
        showticklabels=False,
        showgrid=False,
        zeroline=False
    ),
    plot_bgcolor="white"
)

st.plotly_chart(fig, use_container_width=True)

# --- 統計データの表示 ---
col1, col2, col3 = st.columns(3)
total_days = len(df[df["score"] > 0])
perfect_days = len(df[df["score"] == len(HABITS)])

col1.metric("草を生やした日数", f"{total_days} 日")
col2.metric("全習慣パーフェクト達成", f"{perfect_days} 日")
col3.metric("直近の達成率", f"{int((total_days / 30) * 100)} %" if total_days <= 30 else "100 %")