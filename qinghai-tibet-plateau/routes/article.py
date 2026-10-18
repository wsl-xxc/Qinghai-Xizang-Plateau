from flask import (Blueprint, abort, render_template, request, session)

from db import get_db

bp = Blueprint("article", __name__)

PER_PAGE = 12


def _load_filters():
    """加载检索页下拉框所需的来源、专题、关键词字典数据。"""
    cur = get_db().cursor()
    cur.execute("SELECT source_id, source_name FROM `source` ORDER BY source_id")
    sources = cur.fetchall()
    cur.execute("SELECT topic_id, topic_name FROM `topic` ORDER BY topic_id")
    topics = cur.fetchall()
    cur.execute("SELECT keyword_id, keyword_name FROM `keyword` ORDER BY keyword_id")
    keywords = cur.fetchall()
    cur.close()
    return sources, topics, keywords


def _attach_keywords(articles):
    """为当前页文章批量挂载关键词，避免 N+1 查询。"""
    if not articles:
        return
    ids = [a["article_id"] for a in articles]
    placeholders = ",".join(["%s"] * len(ids))
    cur = get_db().cursor()
    cur.execute(
        f"""SELECT ak.article_id, k.keyword_id, k.keyword_name
            FROM `article_keyword` ak
            JOIN `keyword` k ON ak.keyword_id = k.keyword_id
            WHERE ak.article_id IN ({placeholders})""",
        ids,
    )
    mapping = {}
    for row in cur.fetchall():
        mapping.setdefault(row["article_id"], []).append(row)
    cur.close()
    for a in articles:
        a["keywords"] = mapping.get(a["article_id"], [])


def _query_articles(title=None, keyword_id=None, source_id=None, topic_id=None,
                    date_from=None, date_to=None, page=1):
    """组合条件检索文章，返回 (当前页文章列表, 总数)。"""
    where, params = [], []
    if title:
        where.append("a.title LIKE %s")
        params.append(f"%{title}%")
    if keyword_id:
        where.append(
            "EXISTS (SELECT 1 FROM `article_keyword` ak "
            "WHERE ak.article_id = a.article_id AND ak.keyword_id = %s)"
        )
        params.append(keyword_id)
    if source_id:
        where.append("a.source_id = %s")
        params.append(source_id)
    if topic_id:
        where.append("a.topic_id = %s")
        params.append(topic_id)
    if date_from:
        where.append("a.publish_date >= %s")
        params.append(date_from)
    if date_to:
        where.append("a.publish_date <= %s")
        params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    cur = get_db().cursor()
    cur.execute(f"SELECT COUNT(*) AS n FROM `article` a {where_sql}", params)
    total = cur.fetchone()["n"]

    cur.execute(
        f"""SELECT a.*, s.source_name, t.topic_name
            FROM `article` a
            LEFT JOIN `source` s ON a.source_id = s.source_id
            LEFT JOIN `topic` t ON a.topic_id = t.topic_id
            {where_sql}
            ORDER BY a.publish_date DESC, a.article_id DESC
            LIMIT %s OFFSET %s""",
        params + [PER_PAGE, (page - 1) * PER_PAGE],
    )
    articles = cur.fetchall()
    cur.close()
    _attach_keywords(articles)
    return articles, total


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int) or 1
    topic_id = request.args.get("topic_id", type=int)
    articles, total = _query_articles(topic_id=topic_id, page=page)
    return render_template("index.html", articles=articles, total=total,
                           page=page, per_page=PER_PAGE, topic_id=topic_id)


@bp.route("/search")
def search():
    page = request.args.get("page", 1, type=int) or 1
    q = request.args.get("q", "").strip()
    keyword_id = request.args.get("keyword_id", type=int)
    source_id = request.args.get("source_id", type=int)
    topic_id = request.args.get("topic_id", type=int)
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    sources, topics, keywords = _load_filters()
    articles, total = _query_articles(
        title=q, keyword_id=keyword_id, source_id=source_id, topic_id=topic_id,
        date_from=date_from, date_to=date_to, page=page,
    )
    return render_template(
        "search.html", articles=articles, total=total, page=page, per_page=PER_PAGE,
        sources=sources, topics=topics, keywords=keywords,
    )


@bp.route("/article/<int:article_id>")
def detail(article_id):
    cur = get_db().cursor()
    cur.execute(
        """SELECT a.*, s.source_name, s.source_type, t.topic_name
           FROM `article` a
           LEFT JOIN `source` s ON a.source_id = s.source_id
           LEFT JOIN `topic` t ON a.topic_id = t.topic_id
           WHERE a.article_id = %s""",
        (article_id,),
    )
    article = cur.fetchone()
    if not article:
        cur.close()
        abort(404)

    cur.execute(
        """SELECT k.keyword_id, k.keyword_name
           FROM `article_keyword` ak
           JOIN `keyword` k ON ak.keyword_id = k.keyword_id
           WHERE ak.article_id = %s""",
        (article_id,),
    )
    keywords = cur.fetchall()

    is_fav = False
    uid = session.get("user_id")
    if uid:
        cur.execute("SELECT 1 FROM `favorite` WHERE user_id = %s AND article_id = %s",
                    (uid, article_id))
        is_fav = cur.fetchone() is not None
    cur.close()
    return render_template("article_detail.html", article=article,
                           keywords=keywords, is_fav=is_fav)
