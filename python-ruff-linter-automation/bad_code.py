import sys, os
import collections
import json

# 1. 坏味道：可变默认参数 (Mutable default parameter B006)
def add_user(name, meta={}):
    meta["created"] = True
    return {"name": name, "meta": meta}

# 2. 坏味道：无意义的双重判断 (SIM103)
def is_admin(user_role):
    if user_role == "admin":
        return True
    else:
        return False

# 3. 坏味道：无效的异常捕获 (B001 / E722)
def parse_payload(raw):
    try:
        data = json.loads(raw)
        return data
    except:
        return None

if __name__ == "__main__":
    print(add_user("Alice"))
    print(add_user("Bob"))  # 注意观察 Alice 和 Bob 的字典污染！
