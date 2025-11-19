import requests
import pandas as pd
import io
import sys

# ==========================================
# 1. Configuration
# ==========================================
# ⚠️ NOTE: Please replace with your own e-Stat APP ID
# Apply here: https://www.e-stat.go.jp/api/
APP_ID = 'YOUR_APP_ID_HERE' 

# Define search targets
TARGETS = [
    {
        "key": "Consumption",
        "search_word": "家計調査 二人以上の世帯 月次",
        "desc": "Recommended: Look for [用途分類（総数）] (Check the latest date)",
        "recommend": "総数"
    },
    {
        "key": "CPI_",
        "search_word": "消費者物価指数",
        "desc": "Recommended: Look for [中分類] or [基本分類] (Check the latest date)",
        "recommend": "中分類"
    },
]

# ==========================================
# 2. Core Function: Search & Select
# ==========================================
def search_and_select(target_info):
    """Search via API, list results, and ask user for selection."""
    url = "http://api.e-stat.go.jp/rest/3.0/app/json/getStatsList"

    params = {
        "appId": APP_ID,
        "searchWord": target_info['search_word'],
        "limit": 30,  # Show top 30 results
        "statsNameList": "N"
    }

    print(f"\n🔍 Searching for: [{target_info['key']}] ...")
    print(f"   (Hint: {target_info['desc']})")

    try:
        res = requests.get(url, params=params)
        data = res.json()

        # Check API status
        if data.get('GET_STATS_LIST', {}).get('RESULT', {}).get('STATUS') != 0:
            print("   ❌ API returned no results.")
            return None

        datalist = data.get('GET_STATS_LIST', {}).get('DATALIST_INF', {})
        if 'TABLE_INF' not in datalist:
            print("   ⚠️ No tables found.")
            return None

        raw_tables = datalist['TABLE_INF']
        tables = [raw_tables] if isinstance(raw_tables, dict) else raw_tables

        # === Sort by update date descending (newest first) ===
        tables.sort(key=lambda x: x.get('UPDATED_DATE', '0000'), reverse=True)

        # === Display List ===
        # ID | Rec | Date | Table Name
        print(f"\n   {'ID':<4} | {'Rec':<4} | {'Date':<12} | {'Table Name'}")
        print("   " + "-" * 100)

        for idx, t in enumerate(tables):
            date = t.get('UPDATED_DATE', 'N/A')

            title_obj = t.get('TITLE', {})
            name = title_obj.get('$') if isinstance(title_obj, dict) else str(title_obj)
            if not name: name = t.get('STATISTICS_NAME', 'Untitled')

            # Smart Mark (Recommendation)
            mark = ""
            if target_info.get('recommend') and target_info['recommend'] in name:
                mark = "★"

            # Truncate long titles
            display_name = (name[:60] + '..') if len(name) > 60 else name

            print(f"   {idx:<4} | {mark:<4} | {date:<12} | {display_name}")

        # === User Interaction ===
        while True:
            user_input = input(f"\n👉 Enter ID for [{target_info['key']}] (Enter 's' to skip): ")

            if user_input.lower() == 's':
                return None

            if user_input.isdigit() and 0 <= int(user_input) < len(tables):
                selected_id = tables[int(user_input)]['@id']
                print(f"   ✅ Selected ID: {selected_id}")
                return selected_id
            else:
                print("   ❌ Invalid ID. Please try again.")

    except Exception as e:
        print(f"   ❌ Search Error: {e}")
        return None


# ==========================================
# 3. Core Function: Direct CSV Download
# ==========================================
def fetch_csv_direct(name, stats_id):
    """Download CSV using getSimpleStatsData API"""
    if not stats_id: return

    print(f"⬇️ Downloading (ID: {stats_id})...")
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
            print(f"   ❌ HTTP Error: {res.status_code}")
            return

        content = res.content.decode('utf-8')

        # Check if API returned an XML error message
        if "RESULT" in content and "ERROR_MSG" in content:
            print(f"   ❌ API Error (ID might be invalid or expired)")
            return

        # Read CSV
        try:
            df = pd.read_csv(io.StringIO(content), on_bad_lines='skip')
        except:
            # Fallback: skip first line if malformed/garbage
            df = pd.read_csv(io.StringIO(content), skiprows=1, on_bad_lines='skip')

        if df.empty:
            print("   ⚠️ Download successful but file is empty.")
            return

        # Save File
        filename = f"{name}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"   🎉 Saved: {filename} ({len(df)} rows)")

    except Exception as e:
        print(f"   ❌ Download Exception: {e}")

# ==========================================
# Main Execution
# ==========================================
if __name__ == "__main__":
    if APP_ID == 'YOUR_APP_ID_HERE':
        print("❌ Error: Please fill in your e-Stat APP ID in the code first!")
        sys.exit(1)

    print("🚀 Starting Japan Macro Data Fetcher\n")

    for target in TARGETS:
        # 1. Search and Select
        sid = search_and_select(target)

        # 2. Download if selected
        if sid:
            fetch_csv_direct(target['key'], sid)
        else:
            print(f"   ⚠️ Skipped {target['key']}")
            
    print("\n💡 Don't forget: [毎月勤労統計調査] needs manual download:")
    print("https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00450071&tstat=000001011791&cycle=0&tclass1=000001218880&tclass2val=0")

    print("\n🏁 All tasks completed.")
