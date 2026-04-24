"""
轻量级基金分析工具 - 专为Render免费版优化
Fund Analyzer Lite - Optimized for Render Free Tier
"""

from flask import Flask, render_template, request, jsonify
import json
import math
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# ==================== 轻量级数据 ====================
# 预置基金数据，避免实时查询消耗内存
PRESET_FUNDS = {
    "110011": {
        "name": "易方达优质精选混合",
        "manager": "张坤",
        "type": "混合型",
        "size": 345.8,
        "management_fee": 1.5,
        "setup_date": "2012-09-28",
        "nav_series": generate_nav_series(3.2, 0.15, 756),  # 起始净值3.2，年化15%
        "description": "张坤旗舰产品，深度价值选股"
    },
    "161725": {
        "name": "招商中证白酒指数",
        "manager": "侯昊",
        "type": "指数型",
        "size": 88.2,
        "management_fee": 0.5,
        "setup_date": "2015-05-27",
        "nav_series": generate_nav_series(1.2, 0.22, 756),  # 白酒高波动
        "description": "白酒行业龙头集结"
    },
    "000961": {
        "name": "天弘沪深300ETF联接A",
        "manager": "田汉卿",
        "type": "指数型",
        "size": 156.3,
        "management_fee": 0.15,
        "setup_date": "2014-02-07",
        "nav_series": generate_nav_series(1.5, 0.08, 756),  # 指数稳健
        "description": "A股核心资产的最低成本入场券"
    },
    "519732": {
        "name": "交银新成长混合",
        "manager": "王崇",
        "type": "混合型",
        "size": 42.1,
        "management_fee": 1.5,
        "setup_date": "2013-02-05",
        "nav_series": generate_nav_series(2.8, 0.18, 756),  # 成长风格
        "description": "王崇深耕成长股，TMT/医疗赛道"
    },
    "006228": {
        "name": "中欧医疗健康混合A",
        "manager": "葛兰",
        "type": "混合型",
        "size": 72.6,
        "management_fee": 1.5,
        "setup_date": "2017-03-17",
        "nav_series": generate_nav_series(1.8, 0.25, 756),  # 医疗高成长
        "description": "葛兰专注医疗健康，学术背景深厚"
    },
    "007119": {
        "name": "华安纳斯达克100指数A",
        "manager": "倪斌",
        "type": "QDII",
        "size": 50.0,
        "management_fee": 1.5,
        "setup_date": "2019-03-26",
        "nav_series": generate_nav_series(1.5, 0.16, 756),  # 纳斯达克指数
        "description": "投资美国科技龙头，QDII基金"
    },
    "163402": {
        "name": "兴全合润混合",
        "manager": "董承非",
        "type": "混合型",
        "size": 39.5,
        "management_fee": 1.5,
        "setup_date": "2009-09-22",
        "nav_series": generate_nav_series(3.5, 0.12, 756),  # 均衡风格
        "description": "董承非均衡配置，回撤控制严格"
    }
}

def generate_nav_series(start_nav, annual_return, days):
    """生成净值序列"""
    nav = [start_nav]
    daily_return = (1 + annual_return) ** (1/252) - 1

    for i in range(1, days):
        # 添加随机波动
        volatility = 0.015  # 日波动率1.5%
        random_return = daily_return + random.gauss(0, volatility)
        new_nav = nav[-1] * (1 + random_return)
        nav.append(round(new_nav, 4))

    return nav

# ==================== 分析引擎（轻量版） ====================
def analyze_fund_lite(fund_code: str) -> dict:
    """轻量级基金分析"""

    if fund_code not in PRESET_FUNDS:
        return {"error": f"基金 {fund_code} 暂不支持，请尝试：110011, 161725, 000961, 519732, 006228, 163402"}

    fund_data = PRESET_FUNDS[fund_code]
    nav_series = fund_data["nav_series"]

    # 计算收益指标
    n = len(nav_series)

    # 1年收益（252个交易日）
    ret_1y = (nav_series[-1] / nav_series[max(0, n - 252)] - 1) * 100 if n > 252 else 0

    # 3年收益（756个交易日）
    ret_3y = (nav_series[-1] / nav_series[max(0, n - 756)] - 1) * 100 if n > 756 else 0

    # 总收益
    ret_total = (nav_series[-1] / nav_series[0] - 1) * 100

    # 年化收益
    annual_ret = ((nav_series[-1] / nav_series[0]) ** (252 / n) - 1) * 100 if n > 1 else 0

    # 最大回撤
    peak = nav_series[0]
    max_dd = 0
    for val in nav_series:
        if val > peak:
            peak = val
        dd = (val - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd

    # 波动率
    daily_rets = [(nav_series[i] / nav_series[i-1] - 1) for i in range(1, n)]
    mean_ret = sum(daily_rets) / len(daily_rets) if daily_rets else 0
    variance = sum((r - mean_ret)**2 for r in daily_rets) / len(daily_rets) if daily_rets else 0
    volatility = math.sqrt(variance) * math.sqrt(252) * 100

    # 夏普比率（无风险利率2.5%）
    sharpe = (annual_ret - 2.5) / volatility if volatility > 0 else 0

    # 评分
    scores = calculate_lite_scores(fund_data, ret_1y, ret_3y, max_dd, volatility, sharpe)

    # 推荐等级
    recommendation = get_recommendation(scores["total"])

    # 生成点评
    commentary = generate_commentary(fund_data, scores, ret_1y, ret_3y, max_dd, sharpe)

    return {
        "code": fund_code,
        "name": fund_data["name"],
        "type": fund_data["type"],
        "manager": fund_data["manager"],
        "size": fund_data["size"],
        "nav_latest": round(nav_series[-1], 4),
        "ret_1y": round(ret_1y, 2),
        "ret_3y": round(ret_3y, 2),
        "ret_total": round(ret_total, 2),
        "annual_return": round(annual_ret, 2),
        "max_drawdown": round(max_dd, 2),
        "volatility": round(volatility, 2),
        "sharpe": round(sharpe, 2),
        "scores": scores,
        "total_score": scores["total"],
        "recommendation": recommendation,
        "commentary": commentary,
        "nav_chart": {
            "dates": generate_date_series(n),
            "values": nav_series[-180:]  # 最近180天
        },
        "source": "preset",
        "description": fund_data["description"]
    }

def generate_date_series(days):
    """生成日期序列"""
    base_date = datetime(2022, 3, 1)
    return [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

def calculate_lite_scores(fund_data, ret_1y, ret_3y, max_dd, volatility, sharpe):
    """轻量级评分系统"""
    scores = {}

    # 业绩表现 (30分)
    perf_score = 0
    if ret_1y > 20: perf_score += 15
    elif ret_1y > 10: perf_score += 12
    elif ret_1y > 0: perf_score += 8
    else: perf_score += 3

    if ret_3y > 50: perf_score += 15
    elif ret_3y > 20: perf_score += 12
    elif ret_3y > 0: perf_score += 8
    else: perf_score += 3

    scores["业绩表现"] = min(30, perf_score)

    # 风险控制 (25分)
    risk_score = 0
    if max_dd > -15: risk_score += 12
    elif max_dd > -25: risk_score += 8
    elif max_dd > -35: risk_score += 4
    else: risk_score += 0

    if sharpe > 1.0: risk_score += 13
    elif sharpe > 0.5: risk_score += 8
    elif sharpe > 0: risk_score += 4
    else: risk_score += 0

    scores["风险控制"] = min(25, risk_score)

    # 基金经理 (20分)
    manager_score = 15  # 默认中等
    if fund_data["manager"] in ["张坤", "葛兰", "董承非"]:
        manager_score = 18  # 知名经理加分
    scores["基金经理"] = manager_score

    # 规模 (10分)
    size = fund_data["size"]
    if 10 <= size <= 100: scores["规模适中"] = 10
    elif 100 < size <= 300: scores["规模适中"] = 8
    elif size > 300: scores["规模适中"] = 5
    else: scores["规模适中"] = 6

    # 费率 (8分)
    fee = fund_data["management_fee"]
    if fee <= 0.5: scores["费率成本"] = 8
    elif fee <= 1.0: scores["费率成本"] = 6
    elif fee <= 1.5: scores["费率成本"] = 4
    else: scores["费率成本"] = 2

    # 持仓质量 (7分)
    scores["持仓质量"] = 5  # 默认中等

    total = sum(scores.values())
    scores["total"] = min(100, total)

    return scores

def get_recommendation(score):
    """投资建议"""
    if score >= 80:
        return {"level": "强烈推荐", "color": "#00843d", "icon": "★★★★★",
                "action": "可积极建仓，适合作为核心持仓"}
    elif score >= 70:
        return {"level": "推荐", "color": "#3a9e5f", "icon": "★★★★",
                "action": "适量配置，作为卫星持仓"}
    elif score >= 60:
        return {"level": "中性观望", "color": "#e6a817", "icon": "★★★",
                "action": "暂观察，等待更好入场时机"}
    elif score >= 50:
        return {"level": "谨慎", "color": "#e07b00", "icon": "★★",
                "action": "风险偏高，建议小仓位试探"}
    else:
        return {"level": "不推荐", "color": "#c0392b", "icon": "★",
                "action": "暂不建议配置"}

def generate_commentary(fund_data, scores, ret_1y, ret_3y, max_dd, sharpe):
    """生成专业点评"""
    comments = []
    name = fund_data["name"]
    manager = fund_data["manager"]
    fund_type = fund_data["type"]

    # 业绩点评
    if ret_1y > 20:
        comments.append(f"**【业绩】优异**：{name}近1年收益{ret_1y:.1f}%，大幅跑赢市场基准。")
    elif ret_1y > 10:
        comments.append(f"**【业绩】稳健**：{name}近1年收益{ret_1y:.1f}%，表现良好。")
    else:
        comments.append(f"**【业绩】一般**：{name}近1年收益{ret_1y:.1f}%，有待提升。")

    # 风险点评
    if max_dd < -30:
        comments.append(f"**【风险】回撤较大**：最大回撤{max_dd:.1f}%，波动性较高。")
    elif max_dd < -20:
        comments.append(f"**【风险】回撤适中**：最大回撤{max_dd:.1f}%，在可接受范围。")
    else:
        comments.append(f"**【风险】控制良好**：最大回撤仅{max_dd:.1f}%，风险控制出色。")

    # 经理点评
    if manager in ["张坤", "葛兰"]:
        comments.append(f"**【经理】明星经理**：{manager}管理经验丰富，投资风格成熟。")

    # 类型提示
    if fund_type == "指数型":
        comments.append(f"**【类型】指数基金**：费率低廉，适合长期定投。")
    elif fund_type == "QDII":
        comments.append(f"**【类型】QDII基金**：投资海外市场，需关注汇率风险。")

    return comments

# ==================== 路由 ====================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Fund Analyzer Lite is running",
        "supported_funds": list(PRESET_FUNDS.keys())
    })

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    try:
        data = request.get_json()
        fund_codes = data.get("codes", [])

        if not fund_codes:
            return jsonify({"error": "请输入基金代码"}), 400

        results = []
        for code in fund_codes[:5]:  # 最多处理5个
            code = code.strip()
            if code and code.isdigit() and len(code) == 6:
                result = analyze_fund_lite(code)
                results.append(result)
            elif code:
                results.append({"code": code, "error": "基金代码格式错误"})

        # 过滤错误结果
        results_ok = [r for r in results if "error" not in r]
        results_ok.sort(key=lambda x: x["total_score"], reverse=True)

        return jsonify({
            "results": results_ok,
            "errors": [r for r in results if "error" in r],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": "轻量版模式，使用预设数据"
        })

    except Exception as e:
        return jsonify({"error": f"分析失败：{str(e)}"}), 500

@app.route("/api/popular")
def api_popular():
    popular = [
        {"code": "110011", "name": "易方达优质精选混合", "manager": "张坤"},
        {"code": "161725", "name": "招商中证白酒指数", "manager": "侯昊"},
        {"code": "000961", "name": "天弘沪深300ETF联接A", "manager": "田汉卿"},
        {"code": "519732", "name": "交银新成长混合", "manager": "王崇"},
        {"code": "006228", "name": "中欧医疗健康混合A", "manager": "葛兰"},
        {"code": "007119", "name": "华安纳斯达克100指数A", "manager": "倪斌"},
    ]
    return jsonify(popular)

if __name__ == "__main__":
    import os
    print("=" * 50)
    print("   基金分析工具 - 轻量版 v1.0")
    print("   专为Render免费版优化")
    print("=" * 50)
    port = int(os.environ.get("PORT", 5000))
    print(f"访问: http://127.0.0.1:{port}")
    print("=" * 50)
    app.run(debug=False, port=port, host="0.0.0.0")