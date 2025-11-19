import requests
import pandas as pd
import io
import sys

# ==========================================
# 1. 配置区域
# ==========================================
# ⚠️ 注意：请替换为你自己的 e-Stat APP ID
# 申请地址：https://www.e-stat.go.jp/api/
APP_ID = 'YOUR_APP_ID_HERE' 

# 定义搜索目标
TARGETS = [
    {
        "key": "Consumption",
        "search_word": "家計調査 二人以上の世帯 月次",
        "desc": "推荐找【用途分類（総数）】(关注最新日期)",
        "recommend": "総数"
    },
    {
        "key": "CPI_",
        "search_word": "消費者物価指数",
        "desc": "推荐找【中分類】或【基本分類】(关注最新日期)",
        "recommend": "中分類"
    },
]

# ==========================================
# 2. 核心函数：搜索并选择
# ==========================================
def search_and_select(target_info):
    """调用 API 搜索，列出结果，让用户输入序号"""
    url = "http://api.e-stat.go.jp/rest/3.0/app/json/getStatsList"

    params = {
        "appId": APP_ID,
        "searchWord": target_info['search_word'],
        "limit": 30,  # 展示前30条
        "statsNameList": "N"
    }

    print(f"\n🔍 正在搜索: [{target_info['key']}] ...")
    print(f"   (提示: {target_info['desc']})")

    try:
        res = requests.get(url, params=params)
        data = res.json()

        # 检查 API 状态
        if data.get('GET_STATS_LIST', {}).get('RESULT', {}).get('STATUS') != 0:
            print("   ❌ API未返回结果。")
            return None

        datalist = data.get('GET_STATS_LIST', {}).get('DATALIST_INF', {})
        if 'TABLE_INF' not in datalist:
            print("   ⚠️ 未找到表格。")
            return None

        raw_tables = datalist['TABLE_INF']
        tables = [raw_tables] if isinstance(raw_tables, dict) else raw_tables

        # === 按更新日期降序排列 (最新的在前面) ===
        tables.sort(key=lambda x: x.get('UPDATED_DATE', '0000'), reverse=True)

        # === 展示列表 ===
        print(f"\n   {'序号':<4} | {'推荐':<4} | {'更新日期':<12} | {'统计表名称'}")
        print("   " + "-" * 100)

        for idx, t in enumerate(tables):
            date = t.get('UPDATED_DATE', 'N/A')

            title_obj = t.get('TITLE', {})
            name = title_obj.get('$') if isinstance(title_obj, dict) else str(title_obj)
            if not name: name = t.get('STATISTICS_NAME', '无标题')

            # 智能标记
            mark = ""
            if target_info.get('recommend') and target_info['recommend'] in name:
                mark = "★"

            # 截断长标题
            display_name = (name[:60] + '..') if len(name) > 60 else name

            print(f"   {idx:<4} | {mark:<4} | {date:<12} | {display_name}")

        # === 用户交互 ===
        while True:
            user_input = input(f"\n👉 请输入 [{target_info['key']}] 的序号 (输入 s 跳过): ")

            if user_input.lower() == 's':
                return None

            if user_input.isdigit() and 0 <= int(user_input) < len(tables):
                selected_id = tables[int(user_input)]['@id']
                print(f"   ✅ 已选择 ID: {selected_id}")
                return selected_id
            else:
                print("   ❌ 序号无效，请重新输入。")

    except Exception as e:
        print(f"   ❌ 搜索出错: {e}")
        return None


# ==========================================
# 3. 核心函数：CSV 直连下载
# ==========================================
def fetch_csv_direct(name, stats_id):
    """使用 getSimpleStatsData 接口下载 CSV"""
    if not stats_id: return

    print(f"⬇️ 正在下载 (ID: {stats_id})...")
    url = "http://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData"

    params = {
        "appId": APP_ID,
        "statsDataId": stats_id,
        "limit": 1000,
        "metaGetFlg": "Y",
        "sectionHeaderFlg": "2",
        "explanationGetFlg": "N",
        "annotationGetFlg": "N"
    }

    try:
        res = requests.get(url, params=params)

        if res.status_code != 200:
            print(f"   ❌ HTTP 错误: {res.status_code}")
            return

        content = res.content.decode('utf-8')

        # 检查是否返回了 XML 格式的错误信息
        if "RESULT" in content and "ERROR_MSG" in content:
            print(f"   ❌ API 返回错误 (可能是ID失效)")
            return

        # 读取 CSV
        try:
            df = pd.read_csv(io.StringIO(content), on_bad_lines='skip')
        except:
            # 容错处理：有时第一行是乱码，跳过
            df = pd.read_csv(io.StringIO(content), skiprows=1, on_bad_lines='skip')

        if df.empty:
            print("   ⚠️ 下载成功但文件为空。")
            return

        # 保存文件
        filename = f"{name}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"   🎉 成功保存: {filename} (包含 {len(df)} 行数据)")

    except Exception as e:
        print(f"   ❌ 下载处理异常: {e}")

# ==========================================
# 主程序
# ==========================================
if __name__ == "__main__":
    if APP_ID == 'YOUR_APP_ID_HERE':
        print("❌ 错误：请先在代码中填入你的 e-Stat APP ID！")
        sys.exit(1)

    print("🚀 启动日本宏观数据抓取助手\n")

    for target in TARGETS:
        # 1. 搜索并让您选择
        sid = search_and_select(target)

        # 2. 如果选了，就下载
        if sid:
            fetch_csv_direct(target['key'], sid)
        else:
            print(f"   ⚠️ 跳过 {target['key']}")
            
    print("\n💡 别忘了【毎月勤労統計調査】需要手动下载：")
    print("https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00450071&tstat=000001011791&cycle=0&tclass1=000001218880&tclass2val=0")

    print("\n🏁 所有任务结束。")
