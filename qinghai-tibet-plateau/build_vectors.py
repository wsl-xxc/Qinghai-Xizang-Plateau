# -*- coding: utf-8 -*-
"""构建文章语义向量并写入 article_vector 表。

用法：
    python build_vectors.py            # 只处理尚未编码的文章（增量）
    python build_vectors.py --force    # 全量重建

依赖本地模型目录 models/bge-small-zh（见 README）。
"""
import argparse
import json

import pymysql
from pymysql.cursors import DictCursor

from config import Config
from nlp import MODEL_NAME, article_text, encode_texts

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS article_vector (
  article_id INT PRIMARY KEY,
  vector     LONGTEXT NOT NULL,
  model      VARCHAR(64) NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_vec_article FOREIGN KEY (article_id)
    REFERENCES article(article_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

SELECT_ARTICLES = """
SELECT a.article_id, a.title, a.summary,
       GROUP_CONCAT(k.keyword_name SEPARATOR ' ') AS kws
FROM `article` a
LEFT JOIN `article_keyword` ak ON ak.article_id = a.article_id
LEFT JOIN `keyword` k ON ak.keyword_id = k.keyword_id
{where}
GROUP BY a.article_id, a.title, a.summary
ORDER BY a.article_id
"""

UPSERT = """
INSERT INTO article_vector (article_id, vector, model)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE vector = VALUES(vector), model = VALUES(model)
"""


def fetch_articles(cur, only_missing=True):
    where = ""
    if only_missing:
        where = "WHERE a.article_id NOT IN (SELECT article_id FROM article_vector)"
    cur.execute(SELECT_ARTICLES.format(where=where))
    rows = cur.fetchall()
    for r in rows:
        r["keywords"] = (r["kws"] or "").split()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="全量重建向量")
    args = parser.parse_args()

    conn = pymysql.connect(
        host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME,
        charset="utf8mb4", cursorclass=DictCursor, autocommit=True,
    )
    cur = conn.cursor()
    cur.execute(CREATE_TABLE)

    articles = fetch_articles(cur, only_missing=not args.force)
    if not articles:
        print("没有需要编码的文章（可用 --force 全量重建）")
    else:
        print("待编码文章：%d 篇，正在加载模型…" % len(articles))
        vecs = encode_texts([article_text(a) for a in articles])
        for article, vec in zip(articles, vecs):
            cur.execute(UPSERT, (article["article_id"],
                                 json.dumps([round(float(x), 6) for x in vec]),
                                 MODEL_NAME))
        print("已写入 %d 条向量，维度 %d" % (len(articles), len(vecs[0])))

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
