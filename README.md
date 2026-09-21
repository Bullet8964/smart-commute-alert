# smart-commute-alert

智慧通勤風險通知系統。

## 功能

- 透過 Open-Meteo Weather API 取得：
  - 今日最高溫度
  - 今日最高降雨機率
- 透過 Open-Meteo Air Quality API 取得：
  - 今日逐小時 US AQI 的最高值
- 根據三個條件產生可同時成立的通勤建議：
  - 降雨機率 >= 60%：攜帶雨傘
  - 最高溫度 >= 33°C：防曬與補充水分
  - AQI >= 100：配戴口罩
  - 三項皆未達門檻：適合外出通勤
- 透過 Telegram Bot 傳送完整通知。
- Token 與 Chat ID 使用 GitHub Secrets。
- GitHub Actions 支援手動執行，以及台灣時間週一至週五 07:00 自動執行。

## GitHub Secrets

到：

Repository → Settings → Secrets and variables → Actions

新增：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

不要把真正的 Token 或 Chat ID 寫進 Python 程式或 YAML。

## Telegram Chat ID

先建立 Bot，並用自己的 Telegram 帳號開啟 Bot 對話、傳送一則訊息。

之後可透過 Telegram Bot API 的 `getUpdates` 查詢 chat ID。

## 修改地點

目前範例設定為桃園市：

- latitude: 24.99368
- longitude: 121.30142

若老師指定其他地點，可以修改 `.github/workflows/smart-commute.yml` 裡的：

```yaml
env:
  LOCATION_NAME: 桃園市
  LATITUDE: "24.99368"
  LONGITUDE: "121.30142"
  TIMEZONE: Asia/Taipei
```

## 手動測試

GitHub：

Actions → Smart Commute Alert → Run workflow

執行成功後，可以在 Telegram 收到通知。

## API 錯誤處理

Python 程式會：

1. 檢查 HTTP status code。
2. 檢查 JSON 是否有效。
3. 檢查必要欄位是否存在。
4. 檢查 AQI 是否有有效資料。
5. 檢查 Telegram API 回傳的 `ok`。
6. 發生錯誤時以非 0 exit code 結束，讓 GitHub Actions 顯示失敗。
