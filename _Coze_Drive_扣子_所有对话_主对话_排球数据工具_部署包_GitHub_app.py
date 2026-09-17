# -*- coding: utf-8 -*-
"""
排球比赛数据统计系统 · Streamlit 版
模块A：快速采集（场边逐球录入）+ 实时表现看板
口径对齐 排球比赛统计模板_v2
运行: streamlit run app.py
"""
import io
from datetime import date

import pandas as pd
import streamlit as st

import stats as S

st.set_page_config(page_title="排球比赛数据统计系统", page_icon="🏐", layout="wide")

# ---------------- 初始化会话状态 ----------------
def init_state():
    if "rows" not in st.session_state:
        st.session_state.rows = []
    if "match" not in st.session_state:
        st.session_state.match = {"日期": date.today(), "对手": ""}
    if "roster" not in st.session_state:
        st.session_state.roster = {t: [n for n in range(1, 19)] for t in S.TEAMS_DEFAULT}
    if "last_rally" not in st.session_state:
        st.session_state.last_rally = 0

init_state()

# ---------------- 侧边栏：比赛与队员设置 ----------------
with st.sidebar:
    st.header("⚙️ 比赛设置")
    st.session_state.match["对手"] = st.text_input("对手", value=st.session_state.match["对手"])
    st.session_state.match["日期"] = st.date_input("比赛日期", value=st.session_state.match["日期"])
    st.markdown("---")
    st.caption("队员名单可在每场比赛前按实际号码调整（默认 1–18 号）")
    home_nums = st.text_input("本队号码（逗号分隔）", value=",".join(map(str, st.session_state.roster["本队"])))
    opp_nums = st.text_input("对手号码（逗号分隔）", value=",".join(map(str, st.session_state.roster["对手"])))
    try:
        st.session_state.roster["本队"] = [int(x) for x in home_nums.replace("，", ",").split(",") if x.strip() != ""]
        st.session_state.roster["对手"] = [int(x) for x in opp_nums.replace("，", ",").split(",") if x.strip() != ""]
    except ValueError:
        st.warning("号码需为数字，逗号分隔")

    st.markdown("---")
    st.subheader("📥 / 📤 数据")
    up = st.file_uploader("导入 v2 Excel 或 CSV", type=["xlsx", "csv"])
    if up is not None:
        try:
            if up.name.endswith(".csv"):
                idf = pd.read_csv(up)
            else:
                idf = pd.read_excel(up, sheet_name="比赛录入", header=1)
            idf = idf.dropna(subset=["环节", "号码"])
            st.session_state.rows = idf[S.COLUMNS].to_dict("records")
            st.success(f"已导入 {len(st.session_state.rows)} 行")
        except Exception as e:
            st.error(f"导入失败：{e}")

    if st.session_state.rows:
        df_exp = S.fill_rally(st.session_state.rows)
        st.download_button("⬇️ 导出 CSV", df_exp.to_csv(index=False).encode("utf-8-sig"),
                           "排球比赛数据.csv", "text/csv", use_container_width=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_exp.to_excel(w, index=False, sheet_name="比赛录入")
        st.download_button("⬇️ 导出 Excel", buf.getvalue(),
                           "排球比赛数据.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    if st.button("🗑️ 清空数据", use_container_width=True):
        st.session_state.rows = []
        st.rerun()

st.title("🏐 排球比赛数据统计系统")
tab_log, tab_stat = st.tabs(["📝 逐球录入", "📊 技术统计"])

# ================= 录入页 =================
with tab_log:
    df = S.to_df(st.session_state.rows)
    rally = S.rally_count(df)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("已录球次（发球数）", rally)
    k2.metric("已录触球行数", len(df))
    k3.metric("本队得分(主动)", sum(S.score_composition(df, "本队").values()))
    k4.metric("对手得分(主动)", sum(S.score_composition(df, "对手").values()))

    st.markdown("#### 录入本次触球")
    with st.form("entry", clear_on_submit=True):
        a, b, c, d = st.columns(4)
        set_no = a.number_input("局", min_value=1, max_value=5, value=1, step=1)
        team = b.selectbox("队伍", S.TEAMS_DEFAULT)
        num = c.selectbox("号码", st.session_state.roster[team])
        phase = d.selectbox("环节", list(S.EFFECT_MAP.keys()))

        effects = S.EFFECT_MAP[phase]
        e, f, g = st.columns(3)
        effect = e.selectbox("效果", effects)
        # 进攻方式仅扣球出现
        if phase == "扣球":
            atk = f.selectbox("进攻方式", S.ATTACK_TYPES)
        else:
            atk = f.selectbox("进攻方式", ["—（本环节不填）"], disabled=True)
        zone = g.selectbox("落点区域", [f"{i}区" for i in range(1, 7)])
        rotation = st.radio("轮次", S.ROTATIONS, horizontal=True)
        note = st.text_input("备注（可空）", "")

        submitted = st.form_submit_button("➕ 添加这一行", use_container_width=True, type="primary")
        if submitted:
            row = {
                "日期": st.session_state.match["日期"], "对手": st.session_state.match["对手"],
                "局": int(set_no), "球次": "", "队伍": team, "号码": int(num),
                "环节": phase, "效果": effect,
                "进攻方式": atk if phase == "扣球" else None,
                "落点区域": zone, "轮次": rotation,
                "备注": note,
            }
            st.session_state.rows.append(row)
            st.success("已添加")
            st.rerun()

    st.markdown("#### 已录数据（最新在上，可删最后一行）")
    if not df.empty:
        show = S.fill_rally(st.session_state.rows).sort_index(ascending=False)
        st.dataframe(show[["局", "球次", "队伍", "号码", "环节", "效果", "进攻方式", "落点区域", "轮次"]],
                     use_container_width=True, height=320, hide_index=True)
        if st.button("🗑️ 删除最后录入的一行"):
            st.session_state.rows.pop()
            st.rerun()
    else:
        st.info("还没有数据，从上方录入第一行；或在左侧导入 v2 Excel。")

# ================= 统计页 =================
with tab_stat:
    df = S.to_df(st.session_state.rows)
    if df.empty:
        st.info("暂无数据。先在「逐球录入」录入，或左侧导入 v2 Excel。")
    else:
        sel_team = st.radio("查看队伍", ["本队", "对手"], horizontal=True)
        d = df[df["队伍"] == sel_team]

        st.markdown(f"### {sel_team} · 得分方式构成")
        sc = S.score_composition(df, sel_team)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("扣球得分", sc["扣球得分"])
        m2.metric("拦网得分(拦死)", sc["拦网得分"])
        m3.metric("发球ACE", sc["发球ACE"])
        m4.metric("自身失误送分", S.errors_total(df, sel_team))

        st.markdown("### 一攻 vs 防反")
        st.dataframe(S.attack_phase(df, sel_team), use_container_width=True, hide_index=True)

        left, right = st.columns(2)
        with left:
            st.markdown("### 进攻方式分布")
            at = S.attack_type_dist(df, sel_team)
            if not at.empty:
                st.dataframe(at, use_container_width=True, hide_index=True)
                st.bar_chart(at.set_index("进攻方式")["次数"])
            else:
                st.caption("暂无扣球数据")
        with right:
            st.markdown("### 六环节总览")
            ov = S.overview(df, sel_team)
            for name, vals in ov.items():
                with st.expander(f"{name}（{vals['次数']} 次）"):
                    st.json(vals)

        st.markdown("### 球员分项效率表")
        st.dataframe(S.player_summary(df, sel_team), use_container_width=True, hide_index=True)
