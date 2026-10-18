from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import get_db
from routes.auth import login_required

bp = Blueprint("source", __name__, url_prefix="/sources")


@bp.route("/")
def list_sources():
    """来源机构列表，附带各机构发文量统计。"""
    cur = get_db().cursor()
    cur.execute(
        """SELECT s.*, COUNT(a.article_id) AS article_count
           FROM `source` s
           LEFT JOIN `article` a ON a.source_id = s.source_id
           GROUP BY s.source_id
           ORDER BY article_count DESC, s.source_id"""
    )
    sources = cur.fetchall()
    cur.close()
    return render_template("sources.html", sources=sources)


@bp.route("/add", methods=["POST"])
@login_required
def add_source():
    name = request.form.get("source_name", "").strip()
    stype = request.form.get("source_type", "").strip() or "科普机构"
    if not name:
        flash("来源名称不能为空", "danger")
        return redirect(url_for("source.list_sources"))
    cur = get_db().cursor()
    cur.execute("SELECT source_id FROM `source` WHERE source_name = %s", (name,))
    if cur.fetchone():
        flash("该来源机构已存在", "danger")
    else:
        cur.execute("INSERT INTO `source` (source_name, source_type) VALUES (%s, %s)",
                    (name, stype))
        flash("添加成功", "success")
    cur.close()
    return redirect(url_for("source.list_sources"))


@bp.route("/<int:source_id>/edit", methods=["POST"])
@login_required
def edit_source(source_id):
    name = request.form.get("source_name", "").strip()
    stype = request.form.get("source_type", "").strip() or "科普机构"
    if not name:
        flash("来源名称不能为空", "danger")
        return redirect(url_for("source.list_sources"))
    cur = get_db().cursor()
    cur.execute("UPDATE `source` SET source_name = %s, source_type = %s WHERE source_id = %s",
                (name, stype, source_id))
    cur.close()
    flash("修改成功", "success")
    return redirect(url_for("source.list_sources"))


@bp.route("/<int:source_id>/delete", methods=["POST"])
@login_required
def delete_source(source_id):
    cur = get_db().cursor()
    # 该机构下仍有文章时拒绝删除，避免破坏外键约束
    cur.execute("SELECT COUNT(*) AS n FROM `article` WHERE source_id = %s", (source_id,))
    if cur.fetchone()["n"] > 0:
        flash("该机构下仍有文章，无法删除", "danger")
    else:
        cur.execute("DELETE FROM `source` WHERE source_id = %s", (source_id,))
        flash("删除成功", "success")
    cur.close()
    return redirect(url_for("source.list_sources"))
