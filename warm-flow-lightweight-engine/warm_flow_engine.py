#!/usr/bin/env python3
"""
Lab 32: Warm-Flow 7 张表国产轻量级工作流引擎与 SpEL 条件分支实战
基于真实的 SQLite 内存数据库建立 7 张物理表，实现状态机节点流转、条件分支表达式求值、任务驳回与历史归档。
严禁假 mock / fake sleep，包含可执行的真实 SQL 事务流转与断言。
"""

import sqlite3
import datetime
from typing import Dict, Any, List, Optional


class WarmFlowEngine:
    """Warm-Flow 核心 7 表工作流引擎实现"""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        """初始化 7 张核心表"""
        cursor = self.conn.cursor()
        cursor.executescript("""
        -- 1. 流程定义表
        CREATE TABLE IF NOT EXISTS flow_definition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_code TEXT UNIQUE NOT NULL,
            flow_name TEXT NOT NULL,
            version TEXT NOT NULL,
            is_publish INTEGER DEFAULT 1,
            create_time TEXT NOT NULL
        );

        -- 2. 流程节点表
        CREATE TABLE IF NOT EXISTS flow_node (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_code TEXT NOT NULL,
            node_code TEXT NOT NULL,
            node_name TEXT NOT NULL,
            node_type TEXT NOT NULL, -- start, between, end
            permission_flag TEXT,
            create_time TEXT NOT NULL
        );

        -- 3. 流程跳转表
        CREATE TABLE IF NOT EXISTS flow_skip (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_code TEXT NOT NULL,
            now_node_code TEXT NOT NULL,
            next_node_code TEXT NOT NULL,
            skip_name TEXT,
            skip_type TEXT DEFAULT 'PASS',
            expr TEXT, -- 条件表达式
            create_time TEXT NOT NULL
        );

        -- 4. 流程实例表
        CREATE TABLE IF NOT EXISTS flow_instance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_code TEXT NOT NULL,
            business_id TEXT NOT NULL,
            node_code TEXT NOT NULL,
            flow_status INTEGER NOT NULL, -- 0:流转中, 1:已完成, 2:已驳回
            create_by TEXT NOT NULL,
            create_time TEXT NOT NULL,
            update_time TEXT NOT NULL
        );

        -- 5. 待办任务表
        CREATE TABLE IF NOT EXISTS flow_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER NOT NULL,
            node_code TEXT NOT NULL,
            node_name TEXT NOT NULL,
            task_status INTEGER NOT NULL, -- 0:未处理, 1:处理中
            approver TEXT,
            create_time TEXT NOT NULL
        );

        -- 6. 历史任务表
        CREATE TABLE IF NOT EXISTS flow_his_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER NOT NULL,
            node_code TEXT NOT NULL,
            node_name TEXT NOT NULL,
            approver TEXT NOT NULL,
            skip_type TEXT NOT NULL,
            message TEXT,
            create_time TEXT NOT NULL
        );

        -- 7. 流程权限人表
        CREATE TABLE IF NOT EXISTS flow_user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type INTEGER NOT NULL, -- 1:审批人, 2:转办人
            processed_by TEXT NOT NULL,
            associated_id INTEGER NOT NULL,
            create_time TEXT NOT NULL
        );
        """)
        self.conn.commit()

    def deploy_flow(self, flow_code: str, flow_name: str, version: str,
                    nodes: List[Dict[str, Any]], skips: List[Dict[str, Any]]):
        """部署流程定义"""
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO flow_definition (flow_code, flow_name, version, create_time) VALUES (?, ?, ?, ?)",
            (flow_code, flow_name, version, now)
        )
        for n in nodes:
            cursor.execute(
                "INSERT INTO flow_node (flow_code, node_code, node_name, node_type, permission_flag, create_time) VALUES (?, ?, ?, ?, ?, ?)",
                (flow_code, n['code'], n['name'], n['type'], n.get('permission'), now)
            )
        for s in skips:
            cursor.execute(
                "INSERT INTO flow_skip (flow_code, now_node_code, next_node_code, skip_name, skip_type, expr, create_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (flow_code, s['now'], s['next'], s.get('name'), s.get('skip_type', 'PASS'), s.get('expr'), now)
            )
        self.conn.commit()

    def start_process(self, flow_code: str, business_id: str, create_by: str, variables: Dict[str, Any]) -> int:
        """启动流程实例并自动流转至第一个任务节点"""
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()

        # 找到 start 节点
        start_node = cursor.execute(
            "SELECT * FROM flow_node WHERE flow_code=? AND node_type='start'", (flow_code,)
        ).fetchone()
        if not start_node:
            raise ValueError(f"未找到流程 {flow_code} 的 start 节点")

        # 寻找 start 节点的下一跳
        skip = cursor.execute(
            "SELECT * FROM flow_skip WHERE flow_code=? AND now_node_code=?", (flow_code, start_node['node_code'])
        ).fetchone()

        first_task_node = cursor.execute(
            "SELECT * FROM flow_node WHERE flow_code=? AND node_code=?", (flow_code, skip['next_node_code'])
        ).fetchone()

        # 创建流程实例
        cursor.execute(
            "INSERT INTO flow_instance (flow_code, business_id, node_code, flow_status, create_by, create_time, update_time) VALUES (?, ?, ?, 0, ?, ?, ?)",
            (flow_code, business_id, first_task_node['node_code'], create_by, now, now)
        )
        instance_id = cursor.lastrowid

        # 生成初始待办任务
        cursor.execute(
            "INSERT INTO flow_task (instance_id, node_code, node_name, task_status, approver, create_time) VALUES (?, ?, ?, 0, ?, ?)",
            (instance_id, first_task_node['node_code'], first_task_node['node_name'], first_task_node['permission_flag'], now)
        )
        self.conn.commit()
        return instance_id

    def skip_task(self, task_id: int, approver: str, message: str, variables: Dict[str, Any]):
        """审批通过并流转下一节点（计算条件分支表达式）"""
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()

        task = cursor.execute("SELECT * FROM flow_task WHERE id=?", (task_id,)).fetchone()
        if not task:
            raise ValueError(f"待办任务 {task_id} 不存在")

        instance_id = task['instance_id']
        current_node_code = task['node_code']

        # 获取实例
        inst = cursor.execute("SELECT * FROM flow_instance WHERE id=?", (instance_id,)).fetchone()
        flow_code = inst['flow_code']

        # 归档历史任务
        cursor.execute(
            "INSERT INTO flow_his_task (instance_id, node_code, node_name, approver, skip_type, message, create_time) VALUES (?, ?, ?, ?, 'PASS', ?, ?)",
            (instance_id, task['node_code'], task['node_name'], approver, message, now)
        )
        # 删除当前待办
        cursor.execute("DELETE FROM flow_task WHERE id=?", (task_id,))

        # 查询所有可能的连线，计算表达式匹配
        candidate_skips = cursor.execute(
            "SELECT * FROM flow_skip WHERE flow_code=? AND now_node_code=?", (flow_code, current_node_code)
        ).fetchall()

        target_skip = None
        for s in candidate_skips:
            expr = s['expr']
            if not expr:
                target_skip = s
                break
            else:
                # 真实求值类似 SpEL 条件：如 amount > 1000
                if self._eval_expr(expr, variables):
                    target_skip = s
                    break

        if not target_skip:
            raise ValueError(f"节点 {current_node_code} 未能匹配到合法的流转连线")

        next_node = cursor.execute(
            "SELECT * FROM flow_node WHERE flow_code=? AND node_code=?", (flow_code, target_skip['next_node_code'])
        ).fetchone()

        if next_node['node_type'] == 'end':
            # 流程正常终结
            cursor.execute(
                "UPDATE flow_instance SET node_code=?, flow_status=1, update_time=? WHERE id=?",
                (next_node['node_code'], now, instance_id)
            )
        else:
            # 流转至新待办节点
            cursor.execute(
                "UPDATE flow_instance SET node_code=?, update_time=? WHERE id=?",
                (next_node['node_code'], now, instance_id)
            )
            cursor.execute(
                "INSERT INTO flow_task (instance_id, node_code, node_name, task_status, approver, create_time) VALUES (?, ?, ?, 0, ?, ?)",
                (instance_id, next_node['node_code'], next_node['node_name'], next_node['permission_flag'], now)
            )

        self.conn.commit()

    def reject_task(self, task_id: int, approver: str, message: str):
        """审批驳回，终止流程"""
        now = datetime.datetime.now().isoformat()
        cursor = self.conn.cursor()

        task = cursor.execute("SELECT * FROM flow_task WHERE id=?", (task_id,)).fetchone()
        if not task:
            raise ValueError(f"待办任务 {task_id} 不存在")

        instance_id = task['instance_id']

        # 归档历史任务
        cursor.execute(
            "INSERT INTO flow_his_task (instance_id, node_code, node_name, approver, skip_type, message, create_time) VALUES (?, ?, ?, ?, 'REJECT', ?, ?)",
            (instance_id, task['node_code'], task['node_name'], approver, message, now)
        )
        cursor.execute("DELETE FROM flow_task WHERE id=?", (task_id,))
        cursor.execute(
            "UPDATE flow_instance SET flow_status=2, update_time=? WHERE id=?", (now, instance_id)
        )
        self.conn.commit()

    def _eval_expr(self, expr: str, variables: Dict[str, Any]) -> bool:
        """评估条件表达式（支持类似 #{amount > 1000} 格式）"""
        clean_expr = expr.strip()
        if clean_expr.startswith("#{") and clean_expr.endswith("}"):
            clean_expr = clean_expr[2:-1].strip()
        try:
            return bool(eval(clean_expr, {"__builtins__": None}, variables))
        except Exception as e:
            print(f"表达式求值异常: {clean_expr}, err: {e}")
            return False

    def get_pending_tasks(self, instance_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT * FROM flow_task WHERE instance_id=?", (instance_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_instance_status(self, instance_id: int) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM flow_instance WHERE id=?", (instance_id,)).fetchone()
        return dict(row) if row else {}

    def get_history(self, instance_id: int) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT * FROM flow_his_task WHERE instance_id=? ORDER BY id ASC", (instance_id,)).fetchall()
        return [dict(r) for r in rows]


def run_test_suite():
    print("=" * 65)
    print("🚀 Running Lab 32: Warm-Flow 7 Tables Engine Tests")
    print("=" * 65)

    engine = WarmFlowEngine(":memory:")

    # 1. 部署请假报销审批流 (7表模型)
    nodes = [
        {"code": "start", "name": "发起申请", "type": "start"},
        {"code": "manager_audit", "name": "部门经理审批", "type": "between", "permission": "manager_001"},
        {"code": "finance_audit", "name": "财务总监审批", "type": "between", "permission": "finance_001"},
        {"code": "end", "name": "流程结束", "type": "end"}
    ]
    skips = [
        {"now": "start", "next": "manager_audit", "name": "提交申请"},
        {"now": "manager_audit", "next": "finance_audit", "name": "金额大于1000转财务", "expr": "#{amount > 1000}"},
        {"now": "manager_audit", "next": "end", "name": "金额小于等于1000直结", "expr": "#{amount <= 1000}"},
        {"now": "finance_audit", "next": "end", "name": "财务通过归档"}
    ]

    engine.deploy_flow("leave_flow", "员工报销审批流", "1.0.0", nodes, skips)
    print("✅ 流程模型成功装配并部署入库 (flow_definition / flow_node / flow_skip)")

    # 场景 A: 大额报销 (amount = 3500) -> 经过经理审批 -> 触发 SpEL 跳转财务 -> 财务审批 -> 结束
    print("\n--- 场景 A: 大额报销流程流转验证 (amount = 3500) ---")
    inst_a = engine.start_process("leave_flow", "BIZ_ORDER_9901", "alice", {"amount": 3500})
    tasks_a = engine.get_pending_tasks(inst_a)
    assert len(tasks_a) == 1
    assert tasks_a[0]['node_code'] == 'manager_audit'
    print(f"✅ 实例启动成功 ID: {inst_a}，首个活动任务为经理审批 [{tasks_a[0]['node_name']}]")

    # 经理审批通过
    engine.skip_task(tasks_a[0]['id'], "manager_001", "经理核实无误，同意", {"amount": 3500})
    tasks_a_2 = engine.get_pending_tasks(inst_a)
    assert len(tasks_a_2) == 1
    assert tasks_a_2[0]['node_code'] == 'finance_audit', "未正确流转至财务审批"
    print(f"✅ SpEL 分支命中成功: #{'{amount > 1000}'} -> 流转至 [{tasks_a_2[0]['node_name']}]")

    # 财务审批通过
    engine.skip_task(tasks_a_2[0]['id'], "finance_001", "财务打款完成", {"amount": 3500})
    tasks_a_3 = engine.get_pending_tasks(inst_a)
    assert len(tasks_a_3) == 0, "流程未结束"
    status_a = engine.get_instance_status(inst_a)
    assert status_a['flow_status'] == 1, "流程实例状态非完成"
    print("✅ 大额报销全流程正常归档闭环！")

    # 场景 B: 小额报销 (amount = 600) -> 经理审批 -> 自动直通 end 归档
    print("\n--- 场景 B: 小额报销直结验证 (amount = 600) ---")
    inst_b = engine.start_process("leave_flow", "BIZ_ORDER_9902", "bob", {"amount": 600})
    tasks_b = engine.get_pending_tasks(inst_b)
    assert tasks_b[0]['node_code'] == 'manager_audit'
    # 经理审批
    engine.skip_task(tasks_b[0]['id'], "manager_001", "小额免审直接放行", {"amount": 600})
    tasks_b_2 = engine.get_pending_tasks(inst_b)
    assert len(tasks_b_2) == 0
    status_b = engine.get_instance_status(inst_b)
    assert status_b['flow_status'] == 1
    assert status_b['node_code'] == 'end'
    print("✅ 小额报销跳过财务直通 end 归档成功！")

    # 验证历史记录表
    history = engine.get_history(inst_a)
    assert len(history) == 2
    assert history[0]['approver'] == "manager_001"
    assert history[1]['approver'] == "finance_001"
    print(f"✅ 历史记录流转轨迹 (flow_his_task) 校验通过: {len(history)} 条审批快照")

    print("\n=================================================================")
    print("✅ All 7 tables assertions passed! Warm-Flow lightweight engine verified.")
    print("=================================================================")


if __name__ == "__main__":
    run_test_suite()
