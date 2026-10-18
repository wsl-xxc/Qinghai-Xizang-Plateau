from flask import Flask, render_template, request, url_for

import db
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from routes.article import bp as article_bp
    from routes.auth import bp as auth_bp
    from routes.source import bp as source_bp
    from routes.stats import bp as stats_bp

    app.register_blueprint(article_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(source_bp)
    app.register_blueprint(stats_bp)

    @app.context_processor
    def inject_nav_topics():
        """向所有模板注入生态专题列表，用于导航栏分类菜单。"""
        try:
            cur = db.get_db().cursor()
            cur.execute("SELECT topic_id, topic_name FROM `topic` ORDER BY topic_id")
            topics = cur.fetchall()
            cur.close()
        except Exception:
            topics = []
        return dict(nav_topics=topics)

    @app.template_global()
    def page_url(page):
        """保留当前查询参数，仅替换页码，供分页宏使用。"""
        args = request.args.to_dict()
        args["page"] = page
        return url_for(request.endpoint, **args)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
