import functools

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

bp = Blueprint("auth", __name__)


def login_required(view):
    """登录校验装饰器，未登录跳转到登录页。"""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        if not nickname or not password:
            flash("昵称和密码不能为空", "danger")
        elif password != password2:
            flash("两次输入的密码不一致", "danger")
        else:
            cur = get_db().cursor()
            cur.execute("SELECT user_id FROM `user` WHERE nickname = %s", (nickname,))
            if cur.fetchone():
                flash("该昵称已被注册", "danger")
                cur.close()
            else:
                # password_hash 字段为 VARCHAR(128)，pbkdf2:sha256 哈希长度约 100 字符，可安全存放
                cur.execute(
                    "INSERT INTO `user` (nickname, password_hash) VALUES (%s, %s)",
                    (nickname, generate_password_hash(password, method="pbkdf2:sha256")),
                )
                cur.close()
                flash("注册成功，请登录", "success")
                return redirect(url_for("auth.login"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "")
        cur = get_db().cursor()
        cur.execute("SELECT * FROM `user` WHERE nickname = %s", (nickname,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["nickname"] = user["nickname"]
            flash("登录成功", "success")
            return redirect(request.args.get("next") or url_for("article.index"))
        flash("昵称或密码错误", "danger")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("article.index"))


@bp.route("/favorite/<int:article_id>", methods=["POST"])
@login_required
def toggle_favorite(article_id):
    uid = session["user_id"]
    cur = get_db().cursor()
    cur.execute("SELECT 1 FROM `favorite` WHERE user_id = %s AND article_id = %s",
                (uid, article_id))
    if cur.fetchone():
        cur.execute("DELETE FROM `favorite` WHERE user_id = %s AND article_id = %s",
                    (uid, article_id))
        flash("已取消收藏", "info")
    else:
        cur.execute("INSERT INTO `favorite` (user_id, article_id) VALUES (%s, %s)",
                    (uid, article_id))
        flash("收藏成功", "success")
    cur.close()
    return redirect(request.referrer or url_for("article.index"))


@bp.route("/favorites")
@login_required
def favorites():
    cur = get_db().cursor()
    cur.execute(
        """SELECT a.*, s.source_name, t.topic_name, f.favorite_time
           FROM `favorite` f
           JOIN `article` a ON f.article_id = a.article_id
           LEFT JOIN `source` s ON a.source_id = s.source_id
           LEFT JOIN `topic` t ON a.topic_id = t.topic_id
           WHERE f.user_id = %s
           ORDER BY f.favorite_time DESC""",
        (session["user_id"],),
    )
    articles = cur.fetchall()
    cur.close()
    return render_template("favorites.html", articles=articles)
