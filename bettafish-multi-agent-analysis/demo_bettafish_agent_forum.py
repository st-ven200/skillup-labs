#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BettaFish (微舆) 多智能体协同舆情研判引擎实战演练
模拟 QueryAgent、MediaAgent、InsightAgent 辩论碰撞拓扑与结构化研报生成

运行方式:
    python demo_bettafish_agent_forum.py --topic "某新能源汽车智能驾驶OTA升级续航争议"
"""

import os
import sys
import time
import json
import random
import argparse
from typing import Dict, List, Any

class QueryAgent:
    """查询智能体：全网社交网络与新闻源实时捕捉检索"""
    def __init__(self, name: str = "QueryAgent-Alpha"):
        self.name = name

    def execute(self, topic: str) -> List[Dict[str, Any]]:
        print(f"  🔍 [{self.name}] 正在全网检索话题: '{topic}'...")
        time.sleep(0.3)
        return [
            {"source": "社交媒体博主", "text": "新版智驾系统更新后，高速开空调电耗从16升到21，续航缩水明显！", "platform": "微博/抖音", "heat": 89200},
            {"source": "科技媒体评测", "text": "官方回应称升级增加了前置激光雷达与高精度点云实时渲染占用，属于算法自适应过程。", "platform": "科技专栏", "heat": 43500},
            {"source": "车主社群反馈", "text": "北方低温环境掉电符合物理规律，但官方升级公告未做前置预警导致车主心理落差。", "platform": "论坛/社群", "heat": 62100}
        ]

class MediaAgent:
    """多模态智能体：分析截图、图表走势与关键帧情感"""
    def __init__(self, name: str = "MediaAgent-Vision"):
        self.name = name

    def execute(self, text_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        print(f"  🖼️ [{self.name}] 解析多模态图文特征、视频热评弹幕分布...")
        time.sleep(0.3)
        return {
            "image_ocr_evidence": "截图中能耗曲线在升级首日存在阶跃式陡升，随后48小时平缓回调",
            "video_sentiment_ratio": {"positive": 0.18, "neutral": 0.32, "negative": 0.50},
            "visual_meme_detected": False,
            "risk_warning": "负面短视频传播裂变系数为 2.8（处于中高风险区）"
        }

class InsightAgent:
    """洞察智能体：对接品牌资产库与历史同类危机事件推演"""
    def __init__(self, name: str = "InsightAgent-Core"):
        self.name = name

    def execute(self, topic: str) -> Dict[str, Any]:
        print(f"  🧠 [{self.name}] 检索知识图谱，匹配历史 12 起智驾能耗舆情样本...")
        time.sleep(0.3)
        return {
            "historical_precedent": "2024Q3 同竞品曾因算法温控策略调整引发为期 5 天的讨论，发文说明后 72 小时平息",
            "brand_loyalty_impact": "核心车主群情绪可控，泛化潜客群观望态度增加 14%",
            "recommended_action": "技术高管发文公开实测点云功耗开销，并承诺下个小版本推送温控补偿策略"
        }

class ForumEngine:
    """
    BettaFish 核心特色：多智能体论坛链式辩论与幻觉消除引擎
    """
    def __init__(self):
        self.host = "ForumModerator-AI"

    def arbitrate_debate(self, query_data: List[Dict], media_data: Dict, insight_data: Dict) -> Dict[str, Any]:
        print(f"\n🏛️ [{self.host}] 启动多 Agent 交叉质询与一致性评估会话:")
        
        # 轮次 1: Query Agent vs Media Agent 交叉校验
        print(f"   💬 [轮次 1] 主持人: 'QueryAgent 提交的文本热度与 MediaAgent 的多模态情绪分布是否存在矛盾？'")
        time.sleep(0.2)
        print(f"       -> QueryAgent: '社群文本关注点聚焦在“续航缩水”，情绪较为激烈。'")
        print(f"       -> MediaAgent: '仪表盘OCR实测截图表明能耗增幅在18%以内，网传“续航腰斩”属于极端夸大谣言。'")
        
        # 轮次 2: 引入 Insight Agent 进行定性降噪
        print(f"   💬 [轮次 2] 主持人: '结合历史知识库，当前舆情是技术认知偏差还是产品硬缺陷？'")
        time.sleep(0.2)
        print(f"       -> InsightAgent: '属于新功能上线时未做用户预期管理导致的信息代沟，非底层三电硬件事故。'")
        
        consensus = {
            "is_rumor_amplified": True,
            "core_contradiction": "OTA新增点云实时算法增耗 vs 用户未感知预期",
            "sentiment_consensus": "负面情绪主要源自告知不透明，公关解释可对冲",
            "confidence_score": 0.94
        }
        print(f"   🎯 会议达成共识！置信度评分: {consensus['confidence_score'] * 100:.1f}%\n")
        return consensus

class ReportAgent:
    """研报智能体：生成结构化舆情决策报告"""
    def __init__(self, name: str = "ReportAgent-Executive"):
        self.name = name

    def generate_report(self, topic: str, consensus: Dict[str, Any], insight: Dict[str, Any]) -> str:
        report = f"""
======================================================================
📊 BettaFish (微舆) 智能体舆情研判综合报告
======================================================================
【监测议题】: {topic}
【生成时间】: {time.strftime('%Y-%m-%d %H:%M:%S')}
【综合置信度】: {consensus['confidence_score'] * 100:.1f}%

一、 舆情定性与核心事实
  • 核心矛盾: {consensus['core_contradiction']}
  • 夸大/谣言甄别: {'检测到部分夸大宣称（如续航腰斩），已被多模态 OCR 证据证伪' if consensus['is_rumor_amplified'] else '基本属实'}
  • 情绪共识: {consensus['sentiment_consensus']}

二、 历史经验对照与走势预测
  • 对照样本: {insight['historical_precedent']}
  • 品牌影响: {insight['brand_loyalty_impact']}

三、 协同应对建议 (Actionable Strategy)
  • 战术建议: {insight['recommended_action']}
  • 应对窗口期: 建议在 12 小时内发布技术原理解析白皮书与 OTA 补偿计划。
======================================================================
"""
        return report

def main():
    parser = argparse.ArgumentParser(description="BettaFish Multi-Agent Sentiment Analysis Demo")
    parser.add_argument("--topic", default="某新能源汽车智能驾驶OTA升级续航争议", help="Monitored topic")
    args = parser.parse_args()

    print("=" * 70)
    print("🤖 BettaFish 24k Star 开源多智能体舆情分析系统仿真运行")
    print(f"   当前目标议题: {args.topic}")
    print("=" * 70 + "\n")

    # 1. 实例化各个 Agent
    query_agent = QueryAgent()
    media_agent = MediaAgent()
    insight_agent = InsightAgent()
    forum_engine = ForumEngine()
    report_agent = ReportAgent()

    # 2. 管道流水线执行
    query_results = query_agent.execute(args.topic)
    media_results = media_agent.execute(query_results)
    insight_results = insight_agent.execute(args.topic)

    # 3. 论坛多轮辩论碰撞消除幻觉
    consensus = forum_engine.arbitrate_debate(query_results, media_results, insight_results)

    # 4. 报告生成
    report_text = report_agent.generate_report(args.topic, consensus, insight_results)
    print(report_text)
    print("✅ 演练完成！已成功模拟 BettaFish 多 Agent 协同、质询辩论与结构化舆情决策研报流程。")

if __name__ == "__main__":
    main()
