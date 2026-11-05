# -*- coding: utf-8 -*-
"""智能处理算法模块。

1. similar_articles —— 相似文章推荐（jieba 分词 + TF-IDF + 余弦相似度）
2. predict_yearly  —— 发文量趋势预测（线性回归，预测未来 N 年）
"""
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics.pairwise import cosine_similarity


def _tokenize(text):
    """中文分词（jieba 精确模式）。"""
    return jieba.lcut(text or "")


def _to_text(item):
    """拼接文章文本：标题 x3 + 关键词 x2 + 摘要 x1（字段加权）。"""
    kws = " ".join(item.get("keywords") or [])
    return " ".join([item.get("title") or ""] * 3
                    + [kws] * 2
                    + [item.get("summary") or ""])


def similar_articles(target, corpus, top_n=4):
    """计算语料库中与目标文章最相似的文章。

    :param target: dict(article_id, title, summary, keywords=[str,...])
    :param corpus: 同结构的文章列表（不含 target 自身）
    :param top_n: 返回的最相似文章数量
    :return: [(article_id, 相似度0~1), ...] 按相似度降序
    """
    docs = [_to_text(target)] + [_to_text(d) for d in corpus]
    if not any(d.strip() for d in docs):
        return []
    try:
        matrix = TfidfVectorizer(tokenizer=_tokenize, token_pattern=None
                                 ).fit_transform(docs)
    except ValueError:
        return []
    sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    order = sims.argsort()[::-1][:top_n]
    return [(corpus[i]["article_id"], float(sims[i])) for i in order
            if sims[i] > 0]


def predict_yearly(counts, future_years=3):
    """基于历史年度发文量做线性回归趋势预测。

    :param counts: [(年份, 发文量), ...] 按年份升序
    :param future_years: 预测未来年数
    :return: (history, forecast, r2)
             history = [(年份, 实际量), ...]
             forecast = [(年份, 预测量), ...]（预测量为非负整数）
             r2 = 拟合优度 R²，历史点不足 3 个时为 None
    """
    history = [(int(y), int(n)) for y, n in counts]
    if len(history) < 3:
        return history, [], None

    X = np.array([y for y, _ in history], dtype=float).reshape(-1, 1)
    y = np.array([n for _, n in history], dtype=float)
    model = LinearRegression().fit(X, y)
    r2 = float(model.score(X, y))

    last_year = history[-1][0]
    years = np.array(range(last_year + 1, last_year + 1 + future_years),
                     dtype=float).reshape(-1, 1)
    preds = np.clip(np.round(model.predict(years)), 0, None).astype(int)
    return history, list(zip(years.ravel().astype(int).tolist(),
                             preds.tolist())), r2
