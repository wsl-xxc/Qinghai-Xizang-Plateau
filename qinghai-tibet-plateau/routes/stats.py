import json

from flask import Blueprint, render_template

from db import get_db

bp = Blueprint("stats", __name__, url_prefix="/stats")


@bp.route("/")
def index():
    """统计可视化：年度发文量、来源占比、专题分布、关键词热度/词云。"""
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

    return render_template(
        "stats.html",
        totals=totals,
        by_year=json.dumps(by_year, ensure_ascii=False),
        by_source=json.dumps(by_source, ensure_ascii=False),
        by_topic=json.dumps(by_topic, ensure_ascii=False),
        keywords=json.dumps(keywords, ensure_ascii=False),
    )
