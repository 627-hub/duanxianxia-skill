#!/usr/bin/env python3
"""读取 pool.json 的结构化子集（替代 cron 环境会被安全拦截的 python3 -c）
用法: read_pool.py [brief|roles|warnings|stocks|all]
  brief(默认) = roles_date + warnings + 池内代码名称
"""
import json
import os
import sys

POOL = os.path.expanduser("~/.cache/duanxianxia/pool.json")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "brief"
    try:
        st = json.load(open(POOL, encoding="utf-8"))
    except Exception as e:
        print(f"POOL_READ_ERROR: {e}")
        return 2
    if mode == "roles":
        print(json.dumps(st.get("roles", {}), ensure_ascii=False, indent=1))
    elif mode == "warnings":
        print(json.dumps(st.get("warnings", {}), ensure_ascii=False, indent=1))
    elif mode == "stocks":
        print(json.dumps(st.get("stocks", []), ensure_ascii=False, indent=1))
    elif mode == "all":
        print(json.dumps(st, ensure_ascii=False, indent=1))
    else:
        out = {"roles_date": st.get("roles_date"),
               "warnings": st.get("warnings", {}),
               "codes": [s.get("code", "") + s.get("name", "") for s in st.get("stocks", [])]}
        print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
