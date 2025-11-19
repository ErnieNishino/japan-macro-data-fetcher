# **🇯🇵 Japan Macro Data Fetcher**

A Python tool to fetch key macroeconomic indicators (Consumption & CPI) from the Japanese government's e-Stat API.

这是一个用于抓取日本宏观经济核心指标（消费、CPI）的 Python 工具，基于 e-Stat API。

## **Features**

* **Interactive Search**: Automatically searches for the latest datasets.  
* **Smart Recommendation**: Highlights the most relevant tables (e.g., "Total Households" for consumption).  
* **CSV Export**: Downloads and cleans data directly into CSV format.

## **Prerequisites**

1. You need an **App ID** from [e-Stat API](https://www.e-stat.go.jp/api/).  
2. Python 3.x installed.

## **Installation**

pip install \-r requirements.txt

## **Usage**

1. Open main.py.  
2. Replace APP\_ID \= 'YOUR\_APP\_ID\_HERE' with your actual API key.  
3. Run the script:  
   python main.py

4. Follow the interactive prompts to select the latest data tables.

## **Note on Wage Data**

Wage data (Monthly Labour Survey) structure changes frequently. It is recommended to download it manually from the official link provided at the end of the script execution.