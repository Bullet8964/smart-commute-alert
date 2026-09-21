import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

WEATHER_API = "https://api.open-meteo.com/v1/forecast"
AIR_API = "https://air-quality-api.open-meteo.com/v1/air-quality"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# 可直接修改成老師指定的地點
LOCATION_NAME = os.getenv("LOCATION_NAME", "桃園市")
LATITUDE = float(os.getenv("LATITUDE", "24.99368"))
LONGITUDE = float(os.getenv("LONGITUDE", "121.30142"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Taipei")

TEMP_THRESHOLD = 33
RAIN_THRESHOLD = 60
AQI_THRESHOLD = 100

TIMEOUT = 20


def get_json(url, params):
    """呼叫 REST API，檢查 HTTP 狀態碼並回傳 JSON。"""
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"API 請求失敗：{exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("API 回應不是有效的 JSON。") from exc


def get_weather():
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": "temperature_2m_max,precipitation_probability_max",
        "forecast_days": 1,
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
    }

    data = get_json(WEATHER_API, params)

    try:
        date = data["daily"]["time"][0]
        max_temp = float(data["daily"]["temperature_2m_max"][0])
        max_rain = int(data["daily"]["precipitation_probability_max"][0])
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("天氣 API 回應缺少必要資料。") from exc

    return date, max_temp, max_rain


def get_aqi():
    # 取得今天 00:00 起的逐小時 US AQI，再取今天的最高值。
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": "us_aqi",
        "forecast_days": 1,
        "timezone": TIMEZONE,
    }

    data = get_json(AIR_API, params)

    try:
        values = [
            float(value)
            for value in data["hourly"]["us_aqi"]
            if value is not None
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("空氣品質 API 回應缺少必要資料。") from exc

    if not values:
        raise RuntimeError("空氣品質 API 沒有可用的 AQI 資料。")

    return max(values)


def build_message(date, max_temp, max_rain, aqi):
    """多個 if 可以同時成立，因此會同時列出所有符合的提醒。"""
    suggestions = []

    if max_rain >= RAIN_THRESHOLD:
        suggestions.append("☔ 降雨機率達 60%，提醒攜帶雨傘。")

    if max_temp >= TEMP_THRESHOLD:
        suggestions.append("☀️ 最高溫達 33°C，提醒做好防曬並補充水分。")

    if aqi >= AQI_THRESHOLD:
        suggestions.append("😷 AQI 達 100，提醒配戴口罩並留意空氣品質。")

    if not suggestions:
        suggestions.append("✅ 今日各項條件正常，適合外出通勤。")

    lines = [
        "🚦 智慧通勤風險通知",
        "",
        f"📍 地點：{LOCATION_NAME}",
        f"📅 日期：{date}",
        "",
        f"🌡️ 最高溫度：{max_temp:.1f}°C",
        f"🌧️ 最高降雨機率：{max_rain}%",
        f"💨 最高 AQI：{aqi:.0f}",
        "",
        "📢 通勤建議：",
        *suggestions,
    ]

    return "\n".join(lines)


def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError(
            "找不到 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID。"
            "請設定 GitHub Secrets / 環境變數。"
        )

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Telegram 傳送失敗：{exc}") from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError("Telegram 回應不是有效的 JSON。") from exc

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram API 回報錯誤：{result.get('description', '未知錯誤')}"
        )


def main():
    try:
        date, max_temp, max_rain = get_weather()
        aqi = get_aqi()

        message = build_message(date, max_temp, max_rain, aqi)

        print(message)
        print("\n開始傳送 Telegram...")
        send_telegram(message)
        print("Telegram 傳送成功！")

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
