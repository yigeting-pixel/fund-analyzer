"""
基金分析工具 - 明星基金经理视角
Fund Analyzer - Star Fund Manager Perspective
"""

from flask import Flask, render_template, request, jsonify
import json
import math
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# ==================== 基金经理分析框架 ====================
# 选基维度（满分100分）
SCORING_WEIGHTS = {
    "业绩表现": {
        "weight": 30,
        "sub": {
            "年化收益率": 10,
            "近1年收益": 8,
            "近3年收益": 7,
            "成立以来收益": 5,
        }
    },
    "风险控制": {
        "weight": 25,
        "sub": {
            "最大回撤": 10,
            "夏普比率": 8,
            "波动率": 7,
        }
    },
    "基金经理": {
        "weight": 20,
        "sub": {
            "任职年限": 8,
            "历史业绩稳定性": 7,
            "管理规模适中": 5,
        }
    },
    "基金规模": {
        "weight": 10,
        "sub": {
            "规模适中（2-100亿）": 10,
        }
    },
    "费率成本": {
        "weight": 8,
        "sub": {
            "管理费率": 4,
            "托管费率": 2,
            "申购赎回费": 2,
        }
    },
    "持仓质量": {
        "weight": 7,
        "sub": {
            "持仓集中度": 4,
            "行业分散度": 3,
        }
    },
}

# ==================== 数据获取 ====================
def get_fund_data_akshare(fund_code: str) -> dict:
    """尝试用 akshare 获取真实数据"""
    try:
        import akshare as ak

        # 净值走势（参数为 symbol，非 fund）
        nav_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        nav_df = nav_df.sort_values("净值日期")
        dates = nav_df["净值日期"].astype(str).tolist()
        values = nav_df["单位净值"].astype(float).tolist()

        if not values:
            return {"error": "净值数据为空"}

        # 基金基本信息（item/value 两列）- 修复错误处理
        info = {}
        try:
            fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
            if not fund_info_df.empty:
                cols = fund_info_df.columns.tolist()
                key_col = cols[0]   # 'item'
                val_col = cols[1]   # 'value'
                for _, row in fund_info_df.iterrows():
                    info[str(row[key_col])] = str(row[val_col])
        except Exception as e:
            print(f"Warning: Failed to get basic info for {fund_code}: {e}")
            # 继续执行，使用默认值

        # 如果基本信息获取失败，尝试从日行情数据获取
        if not info:
            try:
                daily_df = ak.fund_open_fund_daily_em()
                fund_row = daily_df[daily_df.iloc[:, 0].astype(str) == fund_code]
                if not fund_row.empty:
                    info["基金简称"] = str(fund_row.iloc[0, 1])
                    info["管理费率"] = str(fund_row.iloc[0, -1]).replace("%", "")
            except Exception:
                pass

        # 解析规模（如 "113.85亿"）
        size_raw = info.get("最新规模", info.get("资产规模", "50亿"))
        try:
            size = float(str(size_raw).replace("亿元", "").replace("亿", "").strip())
        except Exception:
            size = 50.0

        # 解析基金类型（简化）- 从日行情数据推断
        raw_type = info.get("基金类型", "")
        fund_name = info.get("基金简称", "")

        # 如果没有类型信息，从基金名称推断
        if not raw_type and fund_name:
            if any(keyword in fund_name for keyword in ["指数", "ETF", "联接"]):
                raw_type = "指数型"
            elif any(keyword in fund_name for keyword in ["股票"]):
                raw_type = "股票型"
            elif any(keyword in fund_name for keyword in ["债券"]):
                raw_type = "债券型"
            else:
                raw_type = "混合型"
        elif not raw_type:
            raw_type = "混合型"

        if "指数" in raw_type or "ETF" in raw_type:
            fund_type = "指数型"
        elif "债" in raw_type:
            fund_type = "债券型"
        elif "股票" in raw_type:
            fund_type = "股票型"
        elif "QDII" in raw_type or "海外" in fund_name:
            fund_type = "QDII"
        else:
            fund_type = "混合型"

        # 管理费率：优先从日行情接口获取（更可靠）
        management_fee = 1.5  # 默认值
        try:
            daily_df = ak.fund_open_fund_daily_em()
            row = daily_df[daily_df.iloc[:, 0].astype(str) == fund_code]
            if not row.empty:
                fee_raw = str(row.iloc[0, -1])
                management_fee = float(fee_raw.replace("%", "").strip())
        except Exception:
            # 如果日行情失败，尝试从基本信息获取
            fee_raw = info.get("管理费率", "1.5")
            try:
                management_fee = float(str(fee_raw).replace("%", "").strip())
            except:
                management_fee = 1.5

        # 基金经理 - 多种方式获取
        manager = info.get("基金经理人", info.get("基金经理", ""))
        if not manager:
            # 对于知名基金，预设一些信息
            known_funds = {
                "007119": {"name": "华安纳斯达克100指数A", "manager": "倪斌"},
                "110011": {"name": "易方达优质精选混合", "manager": "张坤"},
                "161725": {"name": "招商中证白酒指数", "manager": "侯昊"},
                "000961": {"name": "天弘沪深300ETF联接A", "manager": "田汉卿"},
                "519732": {"name": "交银新成长混合", "manager": "王崇"},
                "006228": {"name": "中欧医疗健康混合A", "manager": "葛兰"},
            }
            if fund_code in known_funds:
                info["基金简称"] = known_funds[fund_code]["name"]
                manager = known_funds[fund_code]["manager"]
            else:
                manager = f"基金经理{fund_code[-2:]}"

        return {
            "source": "akshare",
            "code": fund_code,
            "dates": dates[-756:],
            "nav": values[-756:],
            "name": info.get("基金简称", f"基金{fund_code}"),
            "type": fund_type,
            "manager": manager,
            "size": size,
            "setup_date": info.get("成立时间", info.get("成立日期", "2018-01-01")),
            "management_fee": management_fee,
        }
    except Exception as e:
        print(f"Error in get_fund_data_akshare for {fund_code}: {e}")
        return {"error": str(e)}


def get_mock_fund_data(fund_code: str) -> dict:
    """模拟基金数据（演示用，不需要网络）"""
    seed = sum(ord(c) for c in fund_code)
    random.seed(seed)

    # 生成模拟净值序列（3年 756个交易日）
    days = 756
    nav = [1.0]
    for _ in range(days - 1):
        change = random.gauss(0.0004, 0.012)
        nav.append(round(max(0.1, nav[-1] * (1 + change)), 4))

    base_date = datetime(2022, 3, 1)
    dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    # 知名基金预设数据
    fund_profiles = {
        "110011": {"name": "易方达优质精选混合", "manager": "张坤", "type": "混合型",
                   "size": 345.8, "setup_date": "2012-09-28", "management_fee": 1.5},
        "161725": {"name": "招商中证白酒指数", "manager": "侯昊", "type": "指数型",
                   "size": 88.2, "setup_date": "2015-05-27", "management_fee": 0.5},
        "000961": {"name": "天弘沪深300ETF联接A", "manager": "田汉卿", "type": "指数型",
                   "size": 156.3, "setup_date": "2014-02-07", "management_fee": 0.15},
        "519732": {"name": "交银新成长混合", "manager": "王崇", "type": "混合型",
                   "size": 42.1, "setup_date": "2013-02-05", "management_fee": 1.5},
        "006228": {"name": "中欧医疗健康混合A", "manager": "葛兰", "type": "混合型",
                   "size": 72.6, "setup_date": "2017-03-17", "management_fee": 1.5},
        "163402": {"name": "兴全合润混合", "manager": "董承非", "type": "混合型",
                   "size": 39.5, "setup_date": "2009-09-22", "management_fee": 1.5},
    }

    profile = fund_profiles.get(fund_code, {
        "name": f"基金{fund_code}",
        "manager": f"基金经理{fund_code[-2:]}",
        "type": random.choice(["混合型", "股票型", "指数型", "债券型"]),
        "size": round(random.uniform(5, 200), 1),
        "setup_date": f"201{random.randint(5,9)}-0{random.randint(1,9)}-01",
        "management_fee": random.choice([0.15, 0.5, 1.0, 1.5]),
    })

    return {
        "source": "mock",
        "code": fund_code,
        "dates": dates,
        "nav": nav,
        **profile,
    }


def get_fund_data(fund_code: str) -> dict:
    """获取基金数据，优先真实数据，失败则用模拟"""
    result = get_fund_data_akshare(fund_code)
    if "error" in result or not result.get("nav"):
        return get_mock_fund_data(fund_code)
    return result


# ==================== 分析引擎 ====================
def analyze_fund(fund_code: str) -> dict:
    """核心分析函数"""
    data = get_fund_data(fund_code)

    nav = data["nav"]
    n = len(nav)

    # 计算收益率
    ret_1y = (nav[-1] / nav[max(0, n - 252)] - 1) * 100 if n > 30 else None
    ret_3y = (nav[-1] / nav[max(0, n - 756)] - 1) * 100 if n > 252 else None
    ret_total = (nav[-1] / nav[0] - 1) * 100

    # 计算最大回撤
    peak = nav[0]
    max_dd = 0.0
    for v in nav:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd

    # 计算波动率（年化）
    daily_rets = [(nav[i] / nav[i-1] - 1) for i in range(1, n)]
    mean_ret = sum(daily_rets) / len(daily_rets) if daily_rets else 0
    variance = sum((r - mean_ret)**2 for r in daily_rets) / len(daily_rets) if daily_rets else 0
    volatility = math.sqrt(variance) * math.sqrt(252) * 100

    # 年化收益
    annual_ret = ((nav[-1] / nav[0]) ** (252 / n) - 1) * 100 if n > 1 else 0

    # 夏普比率（无风险利率2.5%）
    sharpe = (annual_ret - 2.5) / volatility if volatility > 0 else 0

    # 评分
    scores = score_fund(data, ret_1y, ret_3y, ret_total, max_dd, volatility, sharpe)

    # 明星经理点评
    commentary = generate_commentary(data, scores, ret_1y, ret_3y, max_dd, sharpe, annual_ret)

    return {
        "code": fund_code,
        "name": data.get("name", f"基金{fund_code}"),
        "type": data.get("type", "混合型"),
        "manager": data.get("manager", "未知"),
        "size": data.get("size", 0),
        "setup_date": data.get("setup_date", ""),
        "management_fee": data.get("management_fee", 1.5),
        "nav_latest": round(nav[-1], 4),
        "ret_1y": round(ret_1y, 2) if ret_1y is not None else None,
        "ret_3y": round(ret_3y, 2) if ret_3y is not None else None,
        "ret_total": round(ret_total, 2),
        "annual_return": round(annual_ret, 2),
        "max_drawdown": round(max_dd, 2),
        "volatility": round(volatility, 2),
        "sharpe": round(sharpe, 2),
        "scores": scores,
        "total_score": scores["total"],
        "recommendation": get_recommendation(scores["total"]),
        "commentary": commentary,
        "nav_chart": {
            "dates": data["dates"][-180:],
            "values": [round(v, 4) for v in data["nav"][-180:]]
        },
        "source": data.get("source", "mock"),
    }


def score_fund(data, ret_1y, ret_3y, ret_total, max_dd, volatility, sharpe) -> dict:
    """六维评分（满分100）"""
    scores = {}

    # 1. 业绩表现（30分）
    perf = 0
    if ret_1y is not None:
        # 近1年（10分）
        if ret_1y > 25: perf += 10
        elif ret_1y > 15: perf += 8
        elif ret_1y > 5: perf += 5
        elif ret_1y > 0: perf += 3
        else: perf += 0

        # 近1年趋势（8分）
        if ret_1y > 20: perf += 8
        elif ret_1y > 10: perf += 5
        elif ret_1y > 0: perf += 2
    if ret_3y is not None:
        if ret_3y > 80: perf += 7
        elif ret_3y > 40: perf += 5
        elif ret_3y > 10: perf += 3
        elif ret_3y > 0: perf += 1
    # 成立以来（5分）
    if ret_total > 200: perf += 5
    elif ret_total > 100: perf += 4
    elif ret_total > 50: perf += 3
    elif ret_total > 0: perf += 1
    scores["业绩表现"] = min(30, perf)

    # 2. 风险控制（25分）
    risk = 0
    # 最大回撤（10分）
    if max_dd > -10: risk += 10
    elif max_dd > -20: risk += 8
    elif max_dd > -30: risk += 5
    elif max_dd > -40: risk += 2
    else: risk += 0
    # 夏普比率（8分）
    if sharpe > 1.5: risk += 8
    elif sharpe > 1.0: risk += 6
    elif sharpe > 0.5: risk += 4
    elif sharpe > 0: risk += 2
    else: risk += 0
    # 波动率（7分）
    if volatility < 12: risk += 7
    elif volatility < 20: risk += 5
    elif volatility < 30: risk += 3
    else: risk += 0
    scores["风险控制"] = min(25, risk)

    # 3. 基金经理（20分）- 模拟中简化
    scores["基金经理"] = 12  # 默认中等，真实数据可扩展

    # 4. 规模（10分）
    size = data.get("size", 50)
    if 2 <= size <= 50: scores["规模适中"] = 10
    elif 50 < size <= 100: scores["规模适中"] = 8
    elif 100 < size <= 300: scores["规模适中"] = 6
    elif size > 300: scores["规模适中"] = 3
    else: scores["规模适中"] = 2  # <2亿规模太小

    # 5. 费率（8分）
    fee = data.get("management_fee", 1.5)
    if fee <= 0.15: scores["费率成本"] = 8
    elif fee <= 0.5: scores["费率成本"] = 7
    elif fee <= 1.0: scores["费率成本"] = 5
    elif fee <= 1.5: scores["费率成本"] = 3
    else: scores["费率成本"] = 1

    # 6. 持仓质量（7分）
    scores["持仓质量"] = 5  # 默认中等

    total = sum([
        scores["业绩表现"],
        scores["风险控制"],
        scores["基金经理"],
        scores["规模适中"],
        scores["费率成本"],
        scores["持仓质量"],
    ])
    scores["total"] = min(100, total)
    return scores


def get_recommendation(score: float) -> dict:
    """投资建议"""
    if score >= 80:
        return {"level": "强烈推荐", "color": "#00843d", "icon": "★★★★★",
                "action": "可积极建仓，适合作为核心持仓（不超过总仓位30%）"}
    elif score >= 70:
        return {"level": "推荐", "color": "#3a9e5f", "icon": "★★★★",
                "action": "适量配置，作为卫星持仓（不超过总仓位15%）"}
    elif score >= 60:
        return {"level": "中性观望", "color": "#e6a817", "icon": "★★★",
                "action": "暂观察，等待更好入场时机或业绩验证"}
    elif score >= 50:
        return {"level": "谨慎", "color": "#e07b00", "icon": "★★",
                "action": "风险偏高，建议小仓位试探或寻找替代品"}
    else:
        return {"level": "不推荐", "color": "#c0392b", "icon": "★",
                "action": "暂不建议配置，综合评分较低"}


def generate_commentary(data, scores, ret_1y, ret_3y, max_dd, sharpe, annual_ret) -> list:
    """生成专业点评"""
    comments = []
    name = data.get("name", "该基金")
    manager = data.get("manager", "基金经理")
    fund_type = data.get("type", "混合型")

    # 业绩点评
    if ret_1y is not None:
        if ret_1y > 25:
            comments.append(f"**【业绩】优异**：{name}近1年收益{ret_1y:.1f}%，大幅跑赢市场基准，{manager}的选股能力与市场判断力在本阶段得到充分验证。")
        elif ret_1y > 10:
            comments.append(f"**【业绩】稳健**：近1年收益{ret_1y:.1f}%，在震荡市场中保持可观回报，{manager}的仓位管理与个股选择颇具章法。")
        elif ret_1y > 0:
            comments.append(f"**【业绩】平淡**：近1年收益{ret_1y:.1f}%，勉强正收益，需持续观察是否具备穿越市场周期的能力。")
        else:
            comments.append(f"**【业绩】承压**：近1年收益{ret_1y:.1f}%，处于亏损状态，需关注{manager}在困难时期的应对策略与持仓调整逻辑。")

    if ret_3y is not None:
        if ret_3y > 60:
            comments.append(f"**【长期】卓越**：近3年累计收益{ret_3y:.1f}%，跨越多个市场周期仍保持优异回报，体现出卓越的长期投资能力。")
        elif ret_3y > 20:
            comments.append(f"**【长期】良好**：近3年累计{ret_3y:.1f}%，长期来看具备正收益，适合耐心持有。")
        elif ret_3y is not None and ret_3y <= 0:
            comments.append(f"**【长期】警惕**：近3年累计{ret_3y:.1f}%，长期视角下表现欠佳，需重新审视基金经理的投资框架。")

    # 风险点评
    if max_dd < -35:
        comments.append(f"**【风险】回撤偏大**：历史最大回撤{max_dd:.1f}%，持有期间账面浮亏幅度较大，投资者需具备较强心理承受能力，建议通过定投平滑成本。")
    elif max_dd < -25:
        comments.append(f"**【风险】回撤适中**：最大回撤{max_dd:.1f}%，属于权益基金正常区间，{manager}在极端行情下对净值有一定保护。")
    elif max_dd < -15:
        comments.append(f"**【风险】控制较好**：最大回撤{max_dd:.1f}%，{manager}表现出较强的风控意识，持有体验相对舒适。")
    else:
        comments.append(f"**【风险】出色控制**：最大回撤仅{max_dd:.1f}%，在同类基金中风险控制属于顶尖水平，适合风险偏好较低的投资者。")

    # 夏普点评
    if sharpe > 1.3:
        comments.append(f"**【效率】极高**：夏普比率{sharpe:.2f}，每单位风险获取的超额收益突出，是同类中性价比最高的选择之一。")
    elif sharpe > 0.8:
        comments.append(f"**【效率】良好**：夏普比率{sharpe:.2f}，风险收益比合理，综合投资效率处于行业中上水平。")
    else:
        comments.append(f"**【效率】待提升**：夏普比率{sharpe:.2f}，承担的风险与获取的收益不成比例，可寻找同类中效率更高的基金。")

    # 规模点评
    size = data.get("size", 50)
    if size > 300:
        comments.append(f"**【规模】过大**：管理规模{size:.0f}亿元，'大象起舞'难，频繁调仓成本高，{manager}的选股策略或受限于流动性约束。建议关注规模是否仍在快速增长。")
    elif 50 <= size <= 150:
        comments.append(f"**【规模】适宜**：{size:.0f}亿元规模正处于'黄金区间'，既有充足流动性，又不失调仓灵活度，{manager}发挥空间充足。")
    elif size < 5:
        comments.append(f"**【规模】偏小**：管理规模{size:.0f}亿元较小，需关注清盘风险及机构客户赎回对净值的冲击。")

    # 费率点评
    fee = data.get("management_fee", 1.5)
    if fee <= 0.15:
        comments.append(f"**【费率】极低**：管理费仅{fee}%/年，适合作为底仓长期配置，复利效应下费率优势随时间显著放大。")
    elif fee > 1.2:
        comments.append(f"**【费率】较高**：管理费{fee}%/年，{manager}需要创造足够的超额收益才能弥补费率劣势，对主动管理能力要求更高。")

    # 基金类型特别提示
    if fund_type == "指数型":
        comments.append(f"**【类型提示】**：作为指数基金，核心关注点应转移至跟踪误差、费率及标的指数本身的质量，而非经理人主动管理能力。")

    return comments


# ==================== 基金推荐引擎 ====================

# 优质基金池（资深投资人精选，含不同风格/类型）
FUND_POOL = [
    # 核心宽基指数
    {"code": "000961", "name": "天弘沪深300ETF联接A", "manager": "田汉卿", "type": "指数型",
     "style": ["稳健", "保守"], "horizon": ["中期", "长期"], "theme": ["宽基"],
     "size": 156.3, "management_fee": 0.15, "risk_level": 3,
     "desc": "A股核心资产的最低成本入场券，费率极低，长期跟踪效果优异。"},
    {"code": "110003", "name": "易方达上证50指数A", "manager": "林伟斌", "type": "指数型",
     "style": ["稳健", "保守"], "horizon": ["中期", "长期"], "theme": ["宽基", "价值"],
     "size": 88.7, "management_fee": 0.5, "risk_level": 3,
     "desc": "布局A股最核心的50家龙头企业，大盘蓝筹价值风格，适合底仓配置。"},
    {"code": "159915", "name": "易方达创业板ETF", "manager": "成曦", "type": "指数型",
     "style": ["激进"], "horizon": ["中期", "长期"], "theme": ["成长", "科技"],
     "size": 320.5, "management_fee": 0.5, "risk_level": 5,
     "desc": "创业板核心成分股，高弹性高波动，适合看好中国科技/创新赛道的进取型投资者。"},
    # 主动权益明星
    {"code": "110011", "name": "易方达优质精选混合", "manager": "张坤", "type": "混合型",
     "style": ["稳健", "激进"], "horizon": ["长期"], "theme": ["消费", "价值"],
     "size": 345.8, "management_fee": 1.5, "risk_level": 4,
     "desc": "张坤旗舰产品，深度价值选股，重仓消费白马，适合认可其长期主义框架的投资者。"},
    {"code": "519732", "name": "交银新成长混合", "manager": "王崇", "type": "混合型",
     "style": ["激进"], "horizon": ["长期"], "theme": ["成长", "科技"],
     "size": 42.1, "management_fee": 1.5, "risk_level": 4,
     "desc": "王崇深耕成长股，对TMT/医疗等赛道研究扎实，规模适中，灵活性佳。"},
    {"code": "006228", "name": "中欧医疗健康混合A", "manager": "葛兰", "type": "混合型",
     "style": ["稳健", "激进"], "horizon": ["长期"], "theme": ["医疗", "成长"],
     "size": 72.6, "management_fee": 1.5, "risk_level": 4,
     "desc": "葛兰专注医疗健康，学术背景深厚，适合看好老龄化/医疗创新长期逻辑的投资者。"},
    {"code": "163402", "name": "兴全合润混合", "manager": "董承非", "type": "混合型",
     "style": ["稳健"], "horizon": ["中期", "长期"], "theme": ["均衡", "价值"],
     "size": 39.5, "management_fee": 1.5, "risk_level": 3,
     "desc": "董承非均衡配置风格，回撤控制严格，适合重视持有体验的长期投资者。"},
    # 债券/固收+
    {"code": "519977", "name": "长信可转债A", "manager": "刘珺", "type": "债券型",
     "style": ["保守", "稳健"], "horizon": ["短期", "中期"], "theme": ["固收+", "可转债"],
     "size": 18.6, "management_fee": 0.7, "risk_level": 2,
     "desc": "以可转债为核心，兼顾债券安全垫与权益弹性，适合稳健型投资者进攻性配置。"},
    {"code": "000270", "name": "嘉实增强信用定期债A", "manager": "胡永青", "type": "债券型",
     "style": ["保守"], "horizon": ["短期", "中期"], "theme": ["固收", "低波动"],
     "size": 32.1, "management_fee": 0.6, "risk_level": 1,
     "desc": "纯债策略，低风险低波动，适合资金避险需求或组合中的稳定器角色。"},
    # 行业/主题
    {"code": "161725", "name": "招商中证白酒指数", "manager": "侯昊", "type": "指数型",
     "style": ["激进", "稳健"], "horizon": ["长期"], "theme": ["消费", "白酒"],
     "size": 88.2, "management_fee": 0.5, "risk_level": 4,
     "desc": "白酒行业龙头集结，中国消费升级核心标的，历史长期收益亮眼，但行业集中风险较高。"},
    {"code": "020017", "name": "国泰国证食品饮料行业指数A", "manager": "艾小军", "type": "指数型",
     "style": ["稳健"], "horizon": ["长期"], "theme": ["消费"],
     "size": 11.3, "management_fee": 0.5, "risk_level": 3,
     "desc": "食品饮料赛道指数，覆盖范围比白酒更广，分散化程度更高，适合消费主题均衡配置。"},
    {"code": "001975", "name": "景顺长城中证500量化增强A", "manager": "黎海威", "type": "股票型",
     "style": ["稳健", "激进"], "horizon": ["中期", "长期"], "theme": ["宽基", "量化"],
     "size": 22.8, "management_fee": 1.0, "risk_level": 4,
     "desc": "中证500量化增强，通过系统化选股力争跑赢基准，适合看好中小盘成长风格的投资者。"},
    {"code": "012414", "name": "广发科技先锋混合A", "manager": "郑澄然", "type": "混合型",
     "style": ["激进"], "horizon": ["长期"], "theme": ["科技", "成长"],
     "size": 55.6, "management_fee": 1.5, "risk_level": 5,
     "desc": "专注硬科技赛道（半导体/新能源/军工），高弹性高集中度，适合有强风险承受能力的投资者。"},
]

# 市场观点（定期更新）
MARKET_VIEW = {
    "date": "2026-03",
    "overall": "震荡分化",
    "sentiment": "谨慎乐观",
    "highlights": [
        "政策面：货币政策保持宽松，财政政策积极发力，利好权益市场整体估值修复",
        "结构面：科技（AI/机器人）与红利低波两条主线分化明显，需精选赛道",
        "风险点：外部关税压力仍存，出口链企业盈利预期存在下修风险",
        "机会点：A股估值整体处于历史中低位，中长期配置性价比较高",
    ],
    "recommended_allocation": {
        "激进": {"股票型/混合型": "75%", "指数型": "15%", "固收+": "10%"},
        "稳健": {"股票型/混合型": "45%", "指数型": "30%", "固收+": "25%"},
        "保守": {"股票型/混合型": "15%", "指数型": "20%", "固收+": "65%"},
    }
}


def build_recommendation_portfolio(style: str, horizon: str, themes: list, amount: float) -> dict:
    """
    核心推荐引擎：基于投资者风格偏好构建推荐组合

    Args:
        style: 投资风格 ('激进'|'稳健'|'保守')
        horizon: 投资期限 ('短期'|'中期'|'长期')
        themes: 关注主题列表（可多选），如 ['科技','消费']
        amount: 计划投资金额（元），用于计算建仓建议
    """
    # Step1: 按风格+期限筛选候选基金
    candidates = []
    for f in FUND_POOL:
        style_ok = style in f["style"]
        horizon_ok = horizon in f["horizon"]
        if style_ok and horizon_ok:
            candidates.append(f)

    # Step2: 主题优先提权（有偏好则提升相关基金排序权重）
    def theme_score(fund):
        if not themes:
            return 0
        return sum(1 for t in themes if t in fund.get("theme", []))

    candidates.sort(key=lambda f: (theme_score(f), -f["management_fee"]), reverse=True)

    # Step3: 核心-卫星组合构建策略
    # 核心仓位：风险低、规模大、费率低 → 指数/稳定主动
    # 卫星仓位：主题相关、成长弹性

    core_funds = [f for f in candidates if f["risk_level"] <= 3 or f["type"] == "指数型"][:2]
    satellite_funds = [f for f in candidates if f not in core_funds][:3]

    # 如果候选不够，从全池补充
    if len(core_funds) < 1:
        core_funds = [f for f in FUND_POOL if f["risk_level"] <= 3][:2]
    if len(satellite_funds) < 1:
        satellite_funds = [f for f in FUND_POOL if f not in core_funds][:2]

    # Step4: 仓位分配
    if style == "激进":
        core_pct = 40
        satellite_pct = 60
    elif style == "稳健":
        core_pct = 60
        satellite_pct = 40
    else:  # 保守
        core_pct = 75
        satellite_pct = 25

    # 核心等权分配
    n_core = len(core_funds)
    n_sat = len(satellite_funds)
    core_alloc = [round(core_pct / n_core, 1)] * n_core if n_core else []
    sat_alloc = [round(satellite_pct / n_sat, 1)] * n_sat if n_sat else []

    # 修正尾差
    all_alloc = core_alloc + sat_alloc
    if all_alloc:
        diff = round(100 - sum(all_alloc), 1)
        all_alloc[-1] = round(all_alloc[-1] + diff, 1)

    portfolio = []
    for i, f in enumerate(core_funds):
        pct = core_alloc[i] if i < len(core_alloc) else 0
        amt = round(amount * pct / 100)
        portfolio.append({**f, "role": "核心", "weight_pct": pct, "amount": amt})
    for i, f in enumerate(satellite_funds):
        pct = sat_alloc[i] if i < len(sat_alloc) else 0
        amt = round(amount * pct / 100)
        portfolio.append({**f, "role": "卫星", "weight_pct": pct, "amount": amt})

    # Step5: 生成专业解读
    strategy_text = _build_strategy_text(style, horizon, themes, portfolio, amount)

    return {
        "portfolio": portfolio,
        "strategy": strategy_text,
        "market_view": MARKET_VIEW,
        "allocation_hint": MARKET_VIEW["recommended_allocation"].get(style, {}),
        "core_count": n_core,
        "satellite_count": n_sat,
        "total_funds": len(portfolio),
    }


def _build_strategy_text(style, horizon, themes, portfolio, amount) -> list:
    """生成投资策略解读文本"""
    texts = []

    # 开篇策略定调
    style_desc = {
        "激进": "高弹性成长策略：重配权益，追求超额收益，需承受较大波动",
        "稳健": "核心卫星均衡策略：以低费率指数/优质主动基金为底仓，辅以主题机会增厚收益",
        "保守": "固收+防御策略：优先保护本金，适度参与权益市场上行，平滑回撤"
    }
    texts.append(f"**【策略定位】** {style_desc.get(style, '')}")

    # 期限建议
    horizon_desc = {
        "短期": "投资期限较短（1年内），建议避免重配高波动权益基金，优先流动性较好的品种，注意市场时机风险。",
        "中期": "中等期限（1-3年）为完整市场周期提供了容错空间，可通过定投方式平滑买入成本。",
        "长期": "长期持有（3年以上）是A股权益基金最佳打开方式，时间复利效应显著，建议忽略短期波动。"
    }
    texts.append(f"**【持有期限】** {horizon_desc.get(horizon, '')}")

    # 主题提示
    if themes:
        texts.append(f"**【主题偏好】** 已优先纳入「{'、'.join(themes)}」相关基金，但请注意行业集中度风险，卫星仓位不宜超过总仓位20%。")

    # 核心-卫星解读
    core_names = [f["name"] for f in portfolio if f["role"] == "核心"]
    sat_names = [f["name"] for f in portfolio if f["role"] == "卫星"]
    if core_names:
        texts.append(f"**【核心仓位】** {' · '.join(core_names)}——作为组合压舱石，费率低/风险小/流动性好，建议一次性或分批建仓，长期持有。")
    if sat_names:
        texts.append(f"**【卫星仓位】** {' · '.join(sat_names)}——把握主题/行业Beta机会，弹性更大，建议逢回调加仓，设置止盈目标（+25%~30%）。")

    # 建仓方式
    if style == "激进":
        texts.append("**【建仓方式】** 可分3批建仓：首批40%立即入场，剩余60%在市场回调5%-8%时分批加入，避免高位满仓。")
    elif style == "稳健":
        texts.append("**【建仓方式】** 建议采用定投策略，每月固定金额买入，核心仓位可一次性建仓，卫星仓位分3-6个月逐步加仓。")
    else:
        texts.append("**【建仓方式】** 固收类基金可一次性配置；权益类建议分4-6个月定投，平滑入场成本，控制时机风险。")

    # 风控提示
    texts.append("**【风险提示】** 建议单只基金不超过总资产15%，整体权益仓位根据个人风险承受能力调整。市场大幅波动时保持理性，以基本面为锚，不追涨杀跌。")

    return texts


# ==================== 路由 ====================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    fund_codes = data.get("codes", [])

    if not fund_codes:
        return jsonify({"error": "请输入基金代码"}), 400

    results = []
    for code in fund_codes[:5]:
        code = code.strip()
        if code and code.isdigit() and len(code) == 6:
            try:
                result = analyze_fund(code)
                results.append(result)
            except Exception as e:
                results.append({"code": code, "error": str(e)})
        elif code:
            results.append({"code": code, "error": "基金代码格式错误（应为6位数字）"})

    results_ok = [r for r in results if "error" not in r]
    results_ok.sort(key=lambda x: x["total_score"], reverse=True)

    return jsonify({
        "results": results_ok,
        "errors": [r for r in results if "error" in r],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json()
    style = data.get("style", "稳健")          # 激进/稳健/保守
    horizon = data.get("horizon", "长期")       # 短期/中期/长期
    themes = data.get("themes", [])             # 主题列表
    amount = float(data.get("amount", 100000))  # 计划投资额（元）

    if style not in ("激进", "稳健", "保守"):
        return jsonify({"error": "风格参数错误"}), 400
    if horizon not in ("短期", "中期", "长期"):
        return jsonify({"error": "期限参数错误"}), 400

    result = build_recommendation_portfolio(style, horizon, themes, amount)
    return jsonify({
        **result,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "params": {"style": style, "horizon": horizon, "themes": themes, "amount": amount},
    })


@app.route("/api/popular")
def api_popular():
    popular = [
        {"code": "110011", "name": "易方达优质精选混合", "manager": "张坤"},
        {"code": "161725", "name": "招商中证白酒指数", "manager": "侯昊"},
        {"code": "000961", "name": "天弘沪深300ETF联接A", "manager": "田汉卿"},
        {"code": "519732", "name": "交银新成长混合", "manager": "王崇"},
        {"code": "006228", "name": "中欧医疗健康混合A", "manager": "葛兰"},
        {"code": "163402", "name": "兴全合润混合", "manager": "董承非"},
    ]
    return jsonify(popular)


if __name__ == "__main__":
    import os
    print("=" * 50)
    print("   明星基金经理分析系统 v1.0")
    print("=" * 50)
    port = int(os.environ.get("PORT", 5000))
    print(f"访问: http://127.0.0.1:{port}")
    print("=" * 50)
    app.run(debug=False, port=port, host="0.0.0.0")
