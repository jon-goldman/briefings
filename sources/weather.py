"""
Weather from wttr.in — no API key required.
Returns a single human-readable line for the briefing header.
"""
import aiohttp


async def get_weather(city: str = "New+York+City") -> str:
    url = f"https://wttr.in/{city}?format=j1"
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as r:
            r.raise_for_status()
            data = await r.json(content_type=None)

    cur = data["current_condition"][0]
    today = data["weather"][0]

    desc     = cur["weatherDesc"][0]["value"]
    temp_f   = cur["temp_F"]
    feels_f  = cur["FeelsLikeF"]
    max_f    = today["maxtempF"]
    min_f    = today["mintempF"]
    humidity = cur["humidity"]
    wind_mph = cur["windspeedMiles"]
    wind_dir = cur["winddir16Point"]

    return (
        f"{desc} · {temp_f}°F (feels {feels_f}°F) · "
        f"H {max_f}° / L {min_f}° · "
        f"Humidity {humidity}% · Wind {wind_mph} mph {wind_dir}"
    )
