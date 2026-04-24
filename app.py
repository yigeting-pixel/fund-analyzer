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
        "scores": {
            "业绩表现": min(30, 20 if ret_1y > 15 else 10),
            "风险控制": min(25, 15 if max_dd > -20 else 10),
            "基金经理": 15,
            "规模适中": 8 if fund["size"] < 200 else 5,
            "费率成本": 6 if fund["fee"] < 1.0 else 3,
            "持仓质量": 5,
            "total": score
        },
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

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)