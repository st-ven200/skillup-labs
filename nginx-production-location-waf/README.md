# Lab 02: Nginx Location 匹配优先级陷阱与 WAF 安全防御靶场

[![Run in Skillup](https://img.shields.io/badge/Run_in_Browser-Skillup_Terminal-blue?logo=linux)](https://www.skillup.host/)
[![Difficulty: Intermediate](https://img.shields.io/badge/Difficulty-Intermediate-yellow)](#)

> **实操场景**：在生产环境中配置了 `/api/admin/` 仅允许内网访问，然而恶意扫描器访问 `/api/admin/login.php` 依然被后面的正则表达式 `~ \.php$` 截胡匹配并透传放行，导致越权防御失效。

---

## 🎯 练习目标

1. 深度掌握 Nginx 5 种 location 语法的物理优先级：`=` > `^~` > `~* / ~` > 最长前缀匹配；
2. 理解为什么普通前缀匹配会被后面的正则规则“劫持”；
3. 使用 `^~` 关键操作符构建不可动摇的防御规则；
4. 运行 `test_rules.sh` 脚本验证攻击流量的拦截与透传。

---

## 💻 云端免安装练习入口

> 想要直接启动测试 Nginx 容器观察现象？  
> 👉 **点击直达【[Skillup 云端 Nginx 实操终端](https://www.skillup.host/)】**，开箱即练。

---

## 🛠️ 动手练习步骤

### 步骤 1：启动轻量实验容器或测试实例
```bash
# 测试配置文件语法
nginx -t -c $(pwd)/nginx.conf
```

### 步骤 2：执行自动化命中测试
运行 `test_rules.sh` 模拟多种常见攻击 payload 与路径：
```bash
chmod +x test_rules.sh
./test_rules.sh
```

### 步骤 3：观察输出并对比规则修改前后差异
当使用 `location /api/admin/` 时，`curl http://127.0.0.1:8080/api/admin/index.php` 命中正则被放行（危险！）；  
当加上 `^~` 修改为 `location ^~ /api/admin/` 时，Nginx 停止后续正则搜索，成功返回 403 Forbidden。
