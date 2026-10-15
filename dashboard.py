
import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RunWeather Bot — Погода",
    page_icon="🌤️",
    layout="wide"
)

LATITUDE = 48.5079
LONGITUDE = 32.2623
TIMEZONE = "Europe/Kyiv"


@st.cache_data(ttl=900)
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
        "forecast_days": 2,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,precipitation_probability"
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


st.title("🌤️ RunWeather Bot")
st.subheader("Погодна панель — Кропивницький")
st.caption("Джерело даних: Open-Meteo API")

if st.button("🔄 Оновити погоду"):
    get_weather.clear()

try:
    data = get_weather()
    current = data["current"]
    hourly = data["hourly"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "🌡️ Поточна температура",
        f"{current['temperature_2m']} °C"
    )
    col2.metric(
        "💨 Швидкість вітру",
        f"{current['wind_speed_10m']} км/год"
    )
    col3.metric(
        "🌧️ Опади зараз",
        f"{current['precipitation']} мм"
    )

    st.divider()

    times = pd.to_datetime(hourly["time"])
    temperatures = hourly["temperature_2m"]
    probabilities = hourly["precipitation_probability"]

    weather_df = pd.DataFrame({
        "Час": times,
        "Температура, °C": temperatures,
        "Ймовірність опадів, %": probabilities
    })

    st.subheader("📈 Графік температури")
    st.line_chart(
        weather_df.set_index("Час")[["Температура, °C"]],
        x_label="Час",
        y_label="Температура, °C"
    )

    st.subheader("🌧️ Ймовірність опадів")
    st.bar_chart(
        weather_df.set_index("Час")[["Ймовірність опадів, %"]],
        x_label="Час",
        y_label="Ймовірність, %"
    )

    st.caption(
        "Прогноз на найближчі 48 годин. "
        "Дані оновлюються автоматично кожні 15 хвилин "
        "під час повторного завантаження або після натискання кнопки."
    )

except (requests.RequestException, KeyError, ValueError) as error:
    st.error("Не вдалося отримати погодні дані. Перевір інтернет-з'єднання.")
    print(f"Помилка отримання погоди: {error}")
