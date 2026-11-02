-- /usr/local/openresty/nginx/lua/access_limit.lua
-- 生产级 OpenResty + Lua + Redis 接入层动态 IP 熔断防护脚本
-- 支持：白名单跳过、L1 本地内存缓存加速、L2 Redis 分布式熔断、自动解封

local redis = require "resty.redis"

-- 基础参数配置
local pool_max_idle_time = 10000 -- 连接池空闲超时 (ms)
local pool_size = 100            -- 连接池最大大小
local redis_timeout = 200        -- Redis 超时 (ms)
local redis_host = "127.0.0.1"
local redis_port = 6379
local redis_auth = nil           -- 若有密码在此配置

local ip_block_time = 300        -- 熔断封禁时间 (5分钟)
local ip_time_out = 1            -- 滑动检测窗口 (1秒)
local ip_max_count = 5           -- 窗口内最大允许请求数

-- 白名单集合
local whitelist = {
    ["127.0.0.1"] = true,
    ["10.0.0.88"] = true
}

-- 获取经过严格信任网段解析的真实客户端 IP
local function get_client_ip()
    -- 依托 Nginx realip 模块解析后的可靠地址
    return ngx.var.remote_addr or "127.0.0.1"
end

local client_ip = get_client_ip()

-- 1. 白名单前置放行
if whitelist[client_ip] then
    return
end

-- 2. L1 本地共享内存缓存检查 (避免每个请求打到 Redis)
local l1_cache = ngx.shared.ip_blacklist
if l1_cache then
    local is_l1_blocked = l1_cache:get(client_ip)
    if is_l1_blocked then
        ngx.log(ngx.WARN, "[WAF-L1] Blocked suspicious IP: ", client_ip)
        ngx.exit(ngx.HTTP_FORBIDDEN)
    end
end

-- 3. 连接 Redis
local red = redis:new()
red:set_timeout(redis_timeout)

local ok, err = red:connect(redis_host, redis_port)
if not ok then
    ngx.log(ngx.ERR, "[WAF-Redis] Connect failed: ", err)
    -- 降级保护：Redis 宕机时放行，保障核心业务可用性
    return
end

-- 连接复用与免认证优化
local reused_times, err = red:get_reused_times()
if reused_times == 0 and redis_auth then
    local auth_ok, auth_err = red:auth(redis_auth)
    if not auth_ok then
        ngx.log(ngx.ERR, "[WAF-Redis] Auth failed: ", auth_err)
        red:close()
        return
    end
end

local function close_redis(r)
    if not r then return end
    local ok, err = r:set_keepalive(pool_max_idle_time, pool_size)
    if not ok then
        ngx.log(ngx.WARN, "[WAF-Redis] Set keepalive failed: ", err)
        r:close()
    end
end

local block_key = "limit:block:" .. client_ip
local count_key = "limit:count:" .. client_ip

-- 4. 检查 L2 分布式黑名单
local is_blocked, err = red:get(block_key)
if is_blocked and is_blocked ~= ngx.null and tonumber(is_blocked) == 1 then
    -- 回填至 L1 缓存 5 秒
    if l1_cache then
        l1_cache:set(client_ip, true, 5)
    end
    close_redis(red)
    ngx.log(ngx.WARN, "[WAF-L2] Intercepted blocked IP: ", client_ip)
    ngx.exit(ngx.HTTP_FORBIDDEN)
end

-- 5. 原子计数自增与窗口过期设置
local current_count, err = red:incr(count_key)
if current_count == 1 then
    red:expire(count_key, ip_time_out)
end

-- 6. 超过阈值触发熔断
if current_count > ip_max_count then
    ngx.log(ngx.WARN, "[WAF-Trigger] IP triggered rate limit: ", client_ip, ", count: ", current_count)
    red:set(block_key, 1)
    red:expire(block_key, ip_block_time)
    if l1_cache then
        l1_cache:set(client_ip, true, math.min(ip_block_time, 10))
    end
    close_redis(red)
    ngx.exit(ngx.HTTP_FORBIDDEN)
end

close_redis(red)
