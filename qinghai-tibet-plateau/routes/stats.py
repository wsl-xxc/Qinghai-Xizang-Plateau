import json

from flask import Blueprint, render_template

from db import get_db
from nlp import predict_yearly

bp = Blueprint("stats", __name__, url_prefix="/stats")


@bp.route("/")
def index():
    """统计可视化：年度发文量、来源占比、专题分布、关键词热度/词云、趋势预测。"""
    cur = get_db().cursor()

    totals = {}
    for key, table in (("article", "article"), ("source", "source"),
                       ("keyword", "keyword"), ("user", "user")):
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}`")
        totals[key] = cur.fetchone()["n"]

    # 按年份统计发文量
    cur.execute(
        """SELECT YEAR(publish_date) AS y, COUNT(*) AS c
           FROM `article`
           WHERE publish_date IS NOT NULL
           GROUP BY y ORDER BY y"""
    )
    by_year = cur.fetchall()

    # 来源发文量 TOP10
    cur.execute(
        """SELECT s.source_name AS name, COUNT(*) AS c
           FROM `article` a JOIN `source` s ON a.source_id = s.source_id
           GROUP BY a.source_id ORDER BY c DESC LIMIT 10"""
    )
    by_source = cur.fetchall()

    # 专题分布
    cur.execute(
        """SELECT t.topic_name AS name, COUNT(*) AS c
           FROM `article` a JOIN `topic` t ON a.topic_id = t.topic_id
           GROUP BY a.topic_id ORDER BY c DESC"""
    )
    by_topic = cur.fetchall()

    # 关键词热度 TOP40（词云与条形图共用）
    cur.execute(
        """SELECT k.keyword_name AS name, COUNT(*) AS c
           FROM `article_keyword` ak JOIN `keyword` k ON ak.keyword_id = k.keyword_id
           GROUP BY ak.keyword_id ORDER BY c DESC LIMIT 40"""
    )
    keywords = cur.fetchall()
    cur.close()

    # 发文量趋势预测：线性回归拟合历史数据，外推未来 3 年
    history, forecast, r2 = predict_yearly(
        [(r["y"], r["c"]) for r in by_year], future_years=3)
    hist_fmt = [{"y": str(y), "c": n} for y, n in history]
    fcst_fmt = [{"y": str(y), "c": n} for y, n in forecast]
    trend_x = [d["y"] for d in hist_fmt] + [d["y"] for d in fcst_fmt]
    trend_actual = [d["c"] for d in hist_fmt] + [None] * len(fcst_fmt)
    # 预测线从最后一个历史点衔接，避免图中断线
    trend_pred = [None] * (len(hist_fmt) - 1) + (
        [hist_fmt[-1]["c"]] if hist_fmt else []) + [d["c"] for d in fcst_fmt]

    return render_template(
        "stats.html",
        totals=totals,
        by_year=json.dumps(by_year, ensure_ascii=False),
        by_source=json.dumps(by_source, ensure_ascii=False),
        by_topic=json.dumps(by_topic, ensure_ascii=False),
        keywords=json.dumps(keywords, ensure_ascii=False),
        trend_x=json.dumps(trend_x, ensure_ascii=False),
        trend_actual=json.dumps(trend_actual),
        trend_pred=json.dumps(trend_pred),
        trend_r2=r2,
        trend_future_years=[d["y"] for d in fcst_fmt],
    )
