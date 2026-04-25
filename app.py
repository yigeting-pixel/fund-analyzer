"""
最小内存版本 - 基金分析工具
Minimal Memory Version - Fund Analyzer
"""

from flask import Flask, render_template, request, jsonify
import json
import math
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# 预设基金数据（最简化）
PRESET_FUNDS = {
    "110011": {"name": "易方达优质精选混合", "manager": "张坤", "type": "混合型", "size": 345.8, "fee": 1.5, "nav": 3.2, "return": 0.15},
    "161725": {"name": "招商中证白酒指数", "manager": "侯昊", "type": "指数型", "size": 88.2, "fee": 0.5, "nav": 1.2, "return": 0.22},
    "000961": {"name": "天弘沪深300ETF联接A", "manager": "田汉卿", "type": "指数型", "size": 156.3, "fee": 0.15, "nav": 1.5, "return": 0.08},
    "519732": {"name": "交银新成长混合", "manager": "王崇", "type": "混合型", "size": 42.1, "fee": 1.5, "nav": 2.8, "return": 0.18},
    "006228": {"name": "中欧医疗健康混合A", "manager": "葛兰", "type": "混合型", "size": 72.6, "fee": 1.5, "nav": 1.8, "return": 0.25},
    "007119": {"name": "华安纳斯达克100指数A", "manager": "倪斌", "type": "QDII", "size": 50.0, "fee": 1.5, "nav": 1.5, "return": 0.16},
    "163402": {"name": "兴全合润混合", "manager": "董承非", "type": "混合型", "size": 39.5, "fee": 1.5, "nav": 3.5, "return": 0.12},
}

def generate_simple_analysis(fund_code):
    """生成简化分析结果"""
    if fund_code not in PRESET_FUNDS:
        return {"error": "不支持该基金代码"}

    fund = PRESET_FUNDS[fund_code]

    # 简化计算
    ret_1y = fund["return"] * 100 + random.uniform(-5, 5)
    ret_3y = fund["return"] * 300 + random.uniform(-10, 10)
    max_dd = random.uniform(-15, -35)
    volatility = random.uniform(15, 25)
    sharpe = random.uniform(0.3, 1.2)

    # 简化评分
    score = 60
    if ret_1y > 15: score += 15
    if ret_3y > 40: score += 10
    if max_dd > -20: score += 10
    if sharpe > 0.8: score += 5
    score = min(100, score)

    # 确保scores对象包含所有字段
    scores_data = {
        "业绩表现": min(30, 20 if ret_1y > 15 else 10),
        "风险控制": min(25, 15 if max_dd > -20 else 10),
        "基金经理": 15,
        "规模适中": 8 if fund["size"] < 200 else 5,
        "费率成本": 6 if fund["fee"] < 1.0 else 3,
        "持仓质量": 5,
        "total": score
    }

    return {
        "code": fund_code,
        "name": fund["name"],
        "manager": fund["manager"],
        "type": fund["type"],
        "size": fund["size"],
        "nav_latest": fund["nav"],
        "ret_1y": round(ret_1y, 2),
        "ret_3y": round(ret_3y, 2),
        "ret_total": round(ret_3y, 2),
        "annual_return": round(fund["return"] * 100, 2),
        "max_drawdown": round(max_dd, 2),
        "volatility": round(volatility, 2),
        "sharpe": round(sharpe, 2),
        "scores": scores_data,
        "total_score": score,
        "recommendation": {
            "level": "推荐" if score >= 70 else "中性观望" if score >= 60 else "谨慎",
            "icon": "★★★★" if score >= 70 else "★★★" if score >= 60 else "★★",
            "action": "适量配置" if score >= 70 else "暂观察" if score >= 60 else "小仓位试探"
        },
        "commentary": [
            f"{fund['name']}由{fund['manager']}管理，{fund['type']}基金",
            f"近1年收益{ret_1y:.1f}%，表现{'良好' if ret_1y > 10 else '一般'}",
            f"最大回撤{max_dd:.1f}%，风险控制{'较好' if max_dd > -25 else '一般'}"
        ],
        "source": "preset-lite",
        "nav_chart": {
            "dates": ["2024-01", "2024-04", "2024-07", "2024-10", "2025-01", "2025-04", "2025-07", "2025-10", "2026-01", "2026-04"],
            "values": [fund["nav"]] * 10  # 简化图表
        }
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "minimal",
        "memory": "<50MB",
        "supported_funds": list(PRESET_FUNDS.keys())
    })

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    try:
        data = request.get_json()
        codes = data.get("codes", [])

        if not codes:
            return jsonify({"error": "请输入基金代码"}), 400

        results = []
        for code in codes[:3]:  # 最多3个
            code = code.strip()
            if code in PRESET_FUNDS:
                result = generate_simple_analysis(code)
                results.append(result)
            else:
                results.append({"code": code, "error": f"支持代码：{', '.join(PRESET_FUNDS.keys())}"})

        return jsonify({
            "results": results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": "最小内存版本"
        })

    except Exception as e:
        return jsonify({"error": f"处理失败：{str(e)}"}), 500

@app.route("/api/popular")
def api_popular():
    return jsonify([
        {"code": k, "name": v["name"], "manager": v["manager"]}
        for k, v in PRESET_FUNDS.items()
    ])

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    """智能基金推荐组合"""
    try:
        data = request.get_json()
        style = data.get("style", "稳健")          # 激进/稳健/保守
        horizon = data.get("horizon", "长期")       # 短期/中期/长期
        themes = data.get("themes", [])             # 主题列表
        amount = float(data.get("amount", 100000))  # 计划投资额（元）

        if style not in ("激进", "稳健", "保守"):
            return jsonify({"error": "风格参数错误"}), 400
        if horizon not in ("短期", "中期", "长期"):
            return jsonify({"error": "期限参数错误"}), 400

        # 构建推荐组合
        result = build_recommendation_portfolio(style, horizon, themes, amount)
        return jsonify({
            **result,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "params": {"style": style, "horizon": horizon, "themes": themes, "amount": amount},
        })

    except Exception as e:
        return jsonify({"error": f"推荐失败：{str(e)}"}), 500

def build_recommendation_portfolio(style, horizon, themes, amount):
    """构建推荐投资组合"""

    # 基金池扩展（包含更多风格信息）
    FUND_POOL = []
    for code, fund in PRESET_FUNDS.items():
        fund_info = {
            "code": code,
            "name": fund["name"],
            "manager": fund["manager"],
            "type": fund["type"],
            "size": fund["size"],
            "management_fee": fund["fee"],
            "style": [],
            "horizon": ["短期", "中期", "长期"],
            "theme": [],
            "risk_level": 3,
            "desc": f"{fund['name']}，由{fund['manager']}管理"
        }

        # 根据基金类型和特点添加风格标签
        if fund["type"] == "指数型":
            fund_info["style"] = ["稳健", "保守"]
            fund_info["theme"] = ["宽基"]
            fund_info["risk_level"] = 2
        elif fund["type"] == "QDII":
            fund_info["style"] = ["激进"]
            fund_info["theme"] = ["海外", "科技"]
            fund_info["risk_level"] = 4
        elif fund["manager"] in ["张坤", "葛兰"]:
            fund_info["style"] = ["激进", "稳健"]
            fund_info["theme"] = ["成长", "价值"]
            fund_info["risk_level"] = 4
        else:
            fund_info["style"] = ["稳健"]
            fund_info["theme"] = ["均衡"]
            fund_info["risk_level"] = 3

        FUND_POOL.append(fund_info)

    # 按风格+期限筛选
    candidates = []
    for f in FUND_POOL:
        style_ok = style in f["style"]
        horizon_ok = horizon in f["horizon"]
        if style_ok and horizon_ok:
            candidates.append(f)

    # 主题优先提权
    def theme_score(fund):
        if not themes:
            return 0
        return sum(1 for t in themes if t in fund.get("theme", []))

    candidates.sort(key=lambda f: (theme_score(f), -f["management_fee"]), reverse=True)

    # 核心-卫星组合构建
    core_funds = [f for f in candidates if f["risk_level"] <= 3][:2]
    satellite_funds = [f for f in candidates if f not in core_funds][:2]

    # 确保有足够的基金
    if len(core_funds) < 1:
        core_funds = candidates[:2] if candidates else FUND_POOL[:2]
    if len(satellite_funds) < 1:
        satellite_funds = candidates[:2] if candidates else FUND_POOL[2:4]

    # 仓位分配
    if style == "激进":
        core_pct = 40
        satellite_pct = 60
    elif style == "稳健":
        core_pct = 60
        satellite_pct = 40
    else:  # 保守
        core_pct = 75
        satellite_pct = 25

    # 计算具体分配
    n_core = len(core_funds)
    n_sat = len(satellite_funds)
    core_alloc = [round(core_pct / n_core, 1)] * n_core if n_core else []
    sat_alloc = [round(satellite_pct / n_sat, 1)] * n_sat if n_sat else []

    # 修正尾差
    all_alloc = core_alloc + sat_alloc
    if all_alloc:
        diff = round(100 - sum(all_alloc), 1)
        all_alloc[-1] = round(all_alloc[-1] + diff, 1)

    # 构建组合
    portfolio = []
    for i, f in enumerate(core_funds):
        pct = core_alloc[i] if i < len(core_alloc) else 0
        amt = round(amount * pct / 100)
        portfolio.append({**f, "role": "核心", "weight_pct": pct, "amount": amt})
    for i, f in enumerate(satellite_funds):
        pct = sat_alloc[i] if i < len(sat_alloc) else 0
        amt = round(amount * pct / 100)
        portfolio.append({**f, "role": "卫星", "weight_pct": pct, "amount": amt})

    # 生成策略解读
    strategy_text = generate_strategy_text(style, horizon, themes, portfolio, amount)

    # 市场观点
    market_view = {
        "date": "2026-04",
        "overall": "震荡分化",
        "sentiment": "谨慎乐观",
        "recommended_allocation": {
            "激进": {"股票型/混合型": "75%", "指数型": "15%", "固收+": "10%"},
            "稳健": {"股票型/混合型": "45%", "指数型": "30%", "固收+": "25%"},
            "保守": {"股票型/混合型": "15%", "指数型": "20%", "固收+": "65%"},
        }
    }

    return {
        "portfolio": portfolio,
        "strategy": strategy_text,
        "market_view": market_view,
        "allocation_hint": market_view["recommended_allocation"].get(style, {}),
        "core_count": n_core,
        "satellite_count": n_sat,
        "total_funds": len(portfolio),
    }

def generate_strategy_text(style, horizon, themes, portfolio, amount):
    """生成投资策略解读"""
    texts = []

    # 策略定位
    style_desc = {
        "激进": "高弹性成长策略：重配权益，追求超额收益，需承受较大波动",
        "稳健": "核心卫星均衡策略：以低费率指数/优质主动基金为底仓，辅以主题机会增厚收益",
        "保守": "固收+防御策略：优先保护本金，适度参与权益市场上行，平滑回撤"
    }
    texts.append(f"**【策略定位】** {style_desc.get(style, '')}")

    # 持有期限
    horizon_desc = {
        "短期": "投资期限较短（1年内），建议避免重配高波动权益基金，优先流动性较好的品种。",
        "中期": "中等期限（1-3年）为完整市场周期提供了容错空间，可通过定投方式平滑买入成本。",
        "长期": "长期持有（3年以上）是A股权益基金最佳打开方式，时间复利效应显著，建议忽略短期波动。"
    }
    texts.append(f"**【持有期限】** {horizon_desc.get(horizon, '')}")

    # 主题提示
    if themes:
        texts.append(f"**【主题偏好】** 已优先纳入「{'、'.join(themes)}」相关基金，但请注意行业集中度风险。")

    # 核心-卫星解读
    core_names = [f["name"] for f in portfolio if f["role"] == "核心"]
    sat_names = [f["name"] for f in portfolio if f["role"] == "卫星"]
    if core_names:
        texts.append(f"**【核心仓位】** {' · '.join(core_names)}——作为组合压舱石，费率低/风险小/流动性好。")
    if sat_names:
        texts.append(f"**【卫星仓位】** {' · '.join(sat_names)}——把握主题/行业Beta机会，弹性更大。")

    # 建仓方式
    if style == "激进":
        texts.append("**【建仓方式】** 可分3批建仓：首批40%立即入场，剩余60%在市场回调时分批加入。")
    elif style == "稳健":
        texts.append("**【建仓方式】** 建议采用定投策略，每月固定金额买入，核心仓位可一次性建仓。")
    else:
        texts.append("**【建仓方式】** 固收类基金可一次性配置；权益类建议分4-6个月定投。")

    # 风控提示
    texts.append("**【风险提示】** 建议单只基金不超过总资产15%，整体权益仓位根据个人风险承受能力调整。")

    return texts

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)