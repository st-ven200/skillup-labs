import json

def get_weather(city: str) -> dict:
    # Safe implementation using public weather endpoint format
    return {
        "city": city,
        "temperature": "22C",
        "condition": "Sunny",
        "humidity": "45%"
    }

if __name__ == "__main__":
    print(json.dumps(get_weather("Beijing")))
