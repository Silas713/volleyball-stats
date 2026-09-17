# -*- coding: utf-8 -*-
"""
排球比赛统计引擎
- 口径严格对齐《排球比赛统计模板_v2》
- 输入: 逐球记录列表（dict 或 pandas.DataFrame），12 字段
- 输出: 汇总指标、得分构成、一攻/防反、进攻方式分布、球员分项效率
作者: 小舒（开发） for Silas
"""
from __future__ import annotations
import pandas as pd

COLUMNS = ["日期", "对手", "局", "球次", "队伍", "号码", "环节", "效果",
           "进攻方式", "落点区域", "轮次", "备注"]

# 六环节 -> 合法效果（二级联动，与 v2 _配置 表一致）
EFFECT_MAP = {
    "发球": ["ACE得分", "破攻", "一般", "失误"],
    "一传": ["到位", "半到位", "无攻过网", "失误"],
    "二传": ["到位", "调整", "失误"],
    "扣球": ["得分", "被防起", "被拦回", "被拦死", "失误"],
    "拦网": ["拦死", "拦回", "拦起", "失误"],
    "防守": ["起球到位", "起球无攻", "防失"],
}
# 仅扣球环节出现的进攻方式（与 v2 一致）
ATTACK_TYPES = ["4号位", "3号位快球", "2号位快变", "后排攻",
                "二次球", "吊球", "探头", "处理球"]
ROTATIONS = ["发球轮", "接发轮"]
TEAMS_DEFAULT = ["本队", "对手"]


def to_df(rows) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        df = rows.copy()
    else:
        df = pd.DataFrame(rows, columns=COLUMNS)
    if df.empty:
        return df
    # 类型规整
    df["局"] = pd.to_numeric(df["局"], errors="coerce")
    df["号码"] = pd.to_numeric(df["号码"], errors="coerce")
    return df


def rally_count(df: pd.DataFrame) -> int:
    """当前球次 = 发球环节累计次数（同一次发球=同一分球）"""
    if df.empty:
        return 0
    return int((df["环节"] == "发球").sum())


def fill_rally(rows) -> pd.DataFrame:
    """按顺序填充球次：每遇到一次发球球次+1，同一分球内其余触球共享该编号（对齐v2）"""
    df = to_df(rows)
    if df.empty:
        return df
    rally = 0
    out = []
    for _, r in df.iterrows():
        if r["环节"] == "发球":
            rally += 1
        nr = r.copy()
        nr["球次"] = rally
        out.append(nr)
    return pd.DataFrame(out, columns=COLUMNS)


# ---------------- 单环节效率 ----------------
def _serve(df: pd.DataFrame) -> dict:
    d = df[df["环节"] == "发球"]
    n = len(d)
    ace = (d["效果"] == "ACE得分").sum()
    err = (d["效果"] == "失误").sum()
    po = (d["效果"] == "破攻").sum()
    return {"次数": n, "ACE": int(ace), "失误": int(err), "破攻": int(po),
            "ACE率": round(ace / n, 3) if n else 0.0,
            "失误率": round(err / n, 3) if n else 0.0}


def _reception(df: pd.DataFrame) -> dict:
    d = df[df["环节"] == "一传"]
    n = len(d)
    good = (d["效果"] == "到位").sum()
    half = (d["效果"] == "半到位").sum()
    free = (d["效果"] == "无攻过网").sum()
    err = (d["效果"] == "失误").sum()
    return {"次数": n, "到位": int(good), "半到位": int(half),
            "无攻过网": int(free), "失误": int(err),
            "到位率": round((good + half) / n, 3) if n else 0.0}


def _spike(df: pd.DataFrame) -> dict:
    d = df[df["环节"] == "扣球"]
    n = len(d)
    kill = (d["效果"] == "得分").sum()
    blocked = (d["效果"] == "被拦死").sum()
    err = (d["效果"] == "失误").sum()
    return {"次数": n, "得分": int(kill), "被拦死": int(blocked), "失误": int(err),
            # 进攻效率 = (%得分) - (%被拦死) - (%失误)
            "进攻效率": round((kill - blocked - err) / n, 3) if n else 0.0}


def _block(df: pd.DataFrame) -> dict:
    d = df[df["环节"] == "拦网"]
    n = len(d)
    stuff = (d["效果"] == "拦死").sum()
    back = (d["效果"] == "拦回").sum()
    up = (d["效果"] == "拦起").sum()
    err = (d["效果"] == "失误").sum()
    return {"次数": n, "拦死": int(stuff), "拦回": int(back), "拦起": int(up),
            "失误": int(err),
            "拦网效率": round((stuff + back) / n, 3) if n else 0.0}


def _dig(df: pd.DataFrame) -> dict:
    d = df[df["环节"] == "防守"]
    n = len(d)
    up = (d["效果"] == "起球到位").sum()
    no = (d["效果"] == "起球无攻").sum()
    err = (d["效果"] == "防失").sum()
    return {"次数": n, "起球到位": int(up), "起球无攻": int(no), "防失": int(err),
            "起球率": round((up + no) / n, 3) if n else 0.0}


def _set(df: pd.DataFrame) -> dict:
    d = df[df["环节"] == "二传"]
    n = len(d)
    good = (d["效果"] == "到位").sum()
    adj = (d["效果"] == "调整").sum()
    err = (d["效果"] == "失误").sum()
    return {"次数": n, "到位": int(good), "调整": int(adj), "失误": int(err),
            "到位率": round(good / n, 3) if n else 0.0}


# ---------------- 汇总看板 ----------------
def score_composition(df: pd.DataFrame, team: str | None = None) -> dict:
    """得分方式构成（本方主动得分）"""
    d = df if team is None else df[df["队伍"] == team]
    return {
        "扣球得分": int(((d["环节"] == "扣球") & (d["效果"] == "得分")).sum()),
        "拦网得分": int(((d["环节"] == "拦网") & (d["效果"] == "拦死")).sum()),
        "发球ACE": int(((d["环节"] == "发球") & (d["效果"] == "ACE得分")).sum()),
    }


def errors_total(df: pd.DataFrame, team: str | None = None) -> int:
    """各环节直接失误合计（送给对方的分）"""
    d = df if team is None else df[df["队伍"] == team]
    serve_e = ((d["环节"] == "发球") & (d["效果"] == "失误")).sum()
    rec_e = ((d["环节"] == "一传") & (d["效果"] == "失误")).sum()
    set_e = ((d["环节"] == "二传") & (d["效果"] == "失误")).sum()
    spk_e = ((d["环节"] == "扣球") & (d["效果"].isin(["失误", "被拦死"]))).sum()
    blk_e = ((d["环节"] == "拦网") & (d["效果"] == "失误")).sum()
    return int(serve_e + rec_e + set_e + spk_e + blk_e)


def attack_phase(df: pd.DataFrame, team: str | None = None) -> pd.DataFrame:
    """一攻 vs 防反（按扣球发生时所处轮次：接发轮=一攻，发球轮=防反）"""
    d = df[df["环节"] == "扣球"]
    if team is not None:
        d = d[d["队伍"] == team]
    rows = []
    for label, rot in [("一攻(接发轮)", "接发轮"), ("防反(发球轮)", "发球轮")]:
        x = d[d["轮次"] == rot]
        n = len(x)
        kill = (x["效果"] == "得分").sum()
        blocked = (x["效果"] == "被拦死").sum()
        err = (x["效果"] == "失误").sum()
        rows.append({
            "阶段": label, "扣球次数": n, "得分": int(kill),
            "被拦死": int(blocked), "失误": int(err),
            "扣球得分率": round(kill / n, 3) if n else 0.0,
            "进攻效率": round((kill - blocked - err) / n, 3) if n else 0.0,
        })
    return pd.DataFrame(rows)


def attack_type_dist(df: pd.DataFrame, team: str | None = None) -> pd.DataFrame:
    """进攻方式分布（仅扣球环节）"""
    d = df[(df["环节"] == "扣球")]
    if team is not None:
        d = d[d["队伍"] == team]
    total = len(d)
    rows = []
    for t in ATTACK_TYPES:
        x = d[d["进攻方式"] == t]
        n = len(x)
        if n == 0:
            continue
        kill = (x["效果"] == "得分").sum()
        blocked = (x["效果"] == "被拦死").sum()
        err = (x["效果"] == "失误").sum()
        rows.append({
            "进攻方式": t, "次数": n,
            "占比": round(n / total, 3) if total else 0.0,
            "得分": int(kill),
            "效率": round((kill - blocked - err) / n, 3) if n else 0.0,
        })
    return pd.DataFrame(rows).sort_values("次数", ascending=False).reset_index(drop=True)


def player_summary(df: pd.DataFrame, team: str | None = None) -> pd.DataFrame:
    """球员分项效率表（每个号码一行）"""
    if team is not None:
        df = df[df["队伍"] == team]
    rows = []
    for num in sorted(df["号码"].dropna().unique()):
        p = df[df["号码"] == num]
        s, r, k, b, dg, st = _serve(p), _reception(p), _spike(p), _block(p), _dig(p), _set(p)
        rows.append({
            "号码": int(num),
            "发球次": s["次数"], "ACE": s["ACE"], "发球失误": s["失误"],
            "一传次": r["次数"], "一传到位率": r["到位率"],
            "扣球次": k["次数"], "扣球得分": k["得分"], "进攻效率": k["进攻效率"],
            "拦网次": b["次数"], "拦死": b["拦死"], "拦网效率": b["拦网效率"],
            "防守次": dg["次数"], "防守起球率": dg["起球率"],
            "二传次": st["次数"], "二传到位率": st["到位率"],
        })
    return pd.DataFrame(rows)


def overview(df: pd.DataFrame, team: str | None = None) -> dict:
    """六环节总览"""
    d = df if team is None else df[df["队伍"] == team]
    return {
        "发球": _serve(d), "一传": _reception(d), "二传": _set(d),
        "扣球": _spike(d), "拦网": _block(d), "防守": _dig(d),
    }
