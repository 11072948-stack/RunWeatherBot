import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

# Координати Кропивницький, Україна
LATITUDE = 48.5079
LONGITUDE = 32.2623
TIMEZONE = "Europe/Kyiv"


def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": (
            "temperature_2m,"
            "wind_speed_10m,"
            "precipitation,"
            "weather_code"
        ),
        "hourly": "precipitation_probability",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }

    response = requests.get(
        url, params=params, timeout=20
    )
    response.raise_for_status()
    data = response.json()

    current = data["current"]
    hourly = data["hourly"]

    # Знаходимо ймовірність опадів для поточної години
    current_time = current["time"]
    probability = 0

    for i, hour in enumerate(hourly["time"]):
        if hour == current_time:
            value = hourly["precipitation_probability"][i]
            probability = value if value is not None else 0
            break

    return {
        "temperature": current["temperature_2m"],
        "wind": current["wind_speed_10m"],
        "rain": current["precipitation"],
        "probability": probability,
        "weather_code": current["weather_code"],
    }


def make_recommendation(weather):
    temp = weather["temperature"]
    wind = weather["wind"]
    rain = weather["rain"]
    probability = weather["probability"]

    if wind >= 50 or rain >= 5:
        verdict = "⚠️ Краще обрати приміщення"
    elif temp >= 30 or temp <= -15:
        verdict = "⚠️ Переглянь план тренування"
    elif wind >= 30 or rain > 0 or probability >= 70:
        verdict = "🌦️ Потрібна обережність"
    else:
        verdict = "✅ Умови загалом сприятливі"

    if temp < 5:
        clothes = "Теплий спортивний одяг і захист від вітру."
    elif temp < 15:
        clothes = "Лонгслів або легка куртка."
    elif temp < 25:
        clothes = "Футболка та шорти або легкі штани."
    else:
        clothes = "Легкий, дихаючий спортивний одяг."

    if wind >= 25:
        clothes += " Додай вітрозахисний шар."

    if probability >= 60:
        clothes += " Перевір прогноз і візьми дощовий одяг."

    return verdict, clothes


def send_telegram(message):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError(
            "Не задано TELEGRAM_BOT_TOKEN або TELEGRAM_CHAT_ID."
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": message},
        timeout=20,
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError("Telegram не прийняв повідомлення.")


def main():
    try:
        weather = get_weather()
        verdict, clothes = make_recommendation(weather)

        message = (
            "🏃 RunWeather Bot — прогноз для пробіжки\n\n"
            f"🌡️ Температура: {weather['temperature']} °C\n"
            f"💨 Вітер: {weather['wind']} км/год\n"
            f"🌧️ Опади зараз: {weather['rain']} мм\n"
            f"☔ Імовірність опадів: "
            f"{weather['probability']}%\n\n"
            f"{verdict}\n"
            f"👕 Рекомендація щодо одягу: {clothes}\n\n"
            "Біжи з урахуванням власного самопочуття "
            "та погодних попереджень."
        )

        send_telegram(message)
        print("Прогноз успішно надіслано в Telegram!")

    except requests.RequestException as error:
        print("Помилка отримання погоди або Telegram:", error)
    except (KeyError, TypeError, ValueError) as error:
        print("Не вдалося обробити дані:", error)
    except RuntimeError as error:
        print(error)


if __name__ == "__main__":
    main()