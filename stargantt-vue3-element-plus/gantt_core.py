#!/usr/bin/env python3
"""
Lab 36: StarGantt 开源甘特图拓扑排期与关键路径调度计算引擎
包含：
1. 任务 WBS 拓扑有向无环图 (DAG) 建模与循环依赖死锁检测；
2. 正向传递 (Forward Pass) 最早开始/结束时间 (ES/EF) 计算；
3. 反向传递 (Backward Pass) 最晚开始/结束时间 (LS/LF) 计算；
4. 总时差 (Total Float) 与关键路径 (Critical Path) 自动化识别；
5. 时间刻度网格坐标投影映射算法；
6. 真实业务场景闭环单元测试与断言（0 mock print）。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional

@dataclass
class TaskNode:
    id: str
    name: str
    duration_days: int
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    
    # CPM 计算指标
    es: int = 0  # Early Start
    ef: int = 0  # Early Finish
    ls: int = 0  # Late Start
    lf: int = 0  # Late Finish
    total_float: int = 0  # lf - ef 或 ls - es
    is_critical: bool = False

class GanttScheduleEngine:
    """甘特图排期与关键路径调度核心引擎"""

    def __init__(self):
        self.tasks: Dict[str, TaskNode] = {}

    def add_task(self, task_id: str, name: str, duration_days: int, predecessors: Optional[List[str]] = None):
        if predecessors is None:
            predecessors = []
        node = TaskNode(id=task_id, name=name, duration_days=duration_days, predecessors=list(predecessors))
        self.tasks[task_id] = node

    def build_graph(self):
        """建立双向拓扑依赖树"""
        for tid, task in self.tasks.items():
            task.successors = []
        for tid, task in self.tasks.items():
            for pred_id in task.predecessors:
                if pred_id not in self.tasks:
                    raise ValueError(f"前置任务不存在: {pred_id}")
                self.tasks[pred_id].successors.append(tid)

    def detect_cycle(self) -> bool:
        """检测依赖关系是否存在死锁环路 (DFS 着色法: 0=未访问, 1=访问中, 2=已完成)"""
        visited: Dict[str, int] = {tid: 0 for tid in self.tasks}

        def dfs(node_id: str) -> bool:
            visited[node_id] = 1
            for succ_id in self.tasks[node_id].successors:
                if visited[succ_id] == 1:
                    return True  # 发现环路
                if visited[succ_id] == 0:
                    if dfs(succ_id):
                        return True
            visited[node_id] = 2
            return False

        for tid in self.tasks:
            if visited[tid] == 0:
                if dfs(tid):
                    return True
        return False

    def compute_cpm(self) -> Tuple[int, List[str]]:
        """计算关键路径 (Critical Path Method)，返回 (项目总工期, 关键路径任务ID列表)"""
        self.build_graph()
        if self.detect_cycle():
            raise RuntimeError("甘特图依赖中检测到循环依赖死锁，无法完成排期计算！")

        # 1. 拓扑排序 (Kahn 算法)
        in_degree = {tid: len(self.tasks[tid].predecessors) for tid in self.tasks}
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        topo_order: List[str] = []

        while queue:
            curr = queue.pop(0)
            topo_order.append(curr)
            for succ in self.tasks[curr].successors:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        if len(topo_order) != len(self.tasks):
            raise RuntimeError("拓扑排序节点未完全收敛！")

        # 2. 正向计算 (Forward Pass): 计算 ES, EF
        for tid in topo_order:
            node = self.tasks[tid]
            if not node.predecessors:
                node.es = 0
            else:
                node.es = max(self.tasks[p].ef for p in node.predecessors)
            node.ef = node.es + node.duration_days

        # 项目总工期即所有终点任务 EF 的最大值
        total_project_days = max(node.ef for node in self.tasks.values())

        # 3. 反向计算 (Backward Pass): 计算 LF, LS
        for tid in reversed(topo_order):
            node = self.tasks[tid]
            if not node.successors:
                node.lf = total_project_days
            else:
                node.lf = min(self.tasks[s].ls for s in node.successors)
            node.ls = node.lf - node.duration_days
            node.total_float = node.lf - node.ef
            node.is_critical = (node.total_float == 0)

        critical_path = [tid for tid in topo_order if self.tasks[tid].is_critical]
        return total_project_days, critical_path

    @staticmethod
    def project_to_pixel(day_offset: int, day_width_px: int = 40) -> int:
        """时间偏移量映射为屏幕坐标像素"""
        return day_offset * day_width_px

def run_self_test():
    print("[Lab 36] 正在启动 StarGantt 拓扑调度与关键路径引擎自测...")

    engine = GanttScheduleEngine()
    # 模拟真实中后台交付流程：
    # A(需求评审, 3天) -> B(前端架构搭建, 5天) -> D(接口集成联调, 4天) -> E(发布上线, 2天)
    # A -> C(后端原型与数据库, 7天) -> D
    engine.add_task("A", "需求分析与技术评审", 3)
    engine.add_task("B", "前端架构与组件封装", 5, predecessors=["A"])
    engine.add_task("C", "后端接口与数据库设计", 7, predecessors=["A"])
    engine.add_task("D", "前后端集成联调", 4, predecessors=["B", "C"])
    engine.add_task("E", "灰度发布与生产部署", 2, predecessors=["D"])

    # 1. 验证关键路径计算
    total_days, critical_path = engine.compute_cpm()
    print(f"  📊 项目总工期: {total_days} 天 | 关键路径节点: {' -> '.join(critical_path)}")

    # 预期路径: A(3) -> C(7) -> D(4) -> E(2) = 16 天
    assert total_days == 16, f"预期总工期 16 天，实际: {total_days}"
    assert critical_path == ["A", "C", "D", "E"], f"关键路径断言不匹配: {critical_path}"

    # 验证非关键路径任务 B 的时差:
    # B: ES=3, EF=8, LF=10, LS=5, Float=2
    task_b = engine.tasks["B"]
    assert task_b.total_float == 2, f"任务 B 预期缓冲时差 2 天，实际: {task_b.total_float}"
    assert not task_b.is_critical, "任务 B 不应标记为关键路径！"
    print("  ✅ [测试 1/3] CPM 关键路径与总时差计算验证通过！")

    # 2. 验证时间轴像素坐标映射
    x_start = GanttScheduleEngine.project_to_pixel(task_b.es, day_width_px=40)
    x_end = GanttScheduleEngine.project_to_pixel(task_b.ef, day_width_px=40)
    width = x_end - x_start
    assert x_start == 120, f"预期 X 起点 120px，实际: {x_start}"
    assert width == 200, f"预期宽度 200px (5天*40)，实际: {width}"
    print(f"  ✅ [测试 2/3] 坐标映射像素渲染计算正确 (起点={x_start}px, 宽度={width}px)！")

    # 3. 验证循环依赖环路死锁阻断
    deadlock_engine = GanttScheduleEngine()
    deadlock_engine.add_task("T1", "任务 1", 2, predecessors=["T2"])
    deadlock_engine.add_task("T2", "任务 2", 3, predecessors=["T1"])
    deadlock_engine.build_graph()
    assert deadlock_engine.detect_cycle() is True, "预期必须捕获循环依赖死锁！"
    print("  ✅ [测试 3/3] 拓扑循环依赖死锁防御拦截验证通过！")

    print("\n🎯 [Lab 36] 全部自动化断言通过，甘特图排期计算引擎验证完毕！")

if __name__ == "__main__":
    run_self_test()
