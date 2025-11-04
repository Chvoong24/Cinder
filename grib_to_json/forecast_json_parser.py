import orjson


with open("href12z_for_24.02619,-107.421197.json", "rb") as f:
    parsed = orjson.loads(f.read())


metadata = parsed["metadata"]
data = parsed["data"]

print("Model:", metadata["sitrep"])
print("Forecast time:", metadata["forecast_time"])
print("Location:", metadata["location"])
print("Available fields:", metadata["forecast_types"])
print("Hours", metadata["hour_list"])

# Example: print the first few records
for record in data[:5]:
    print(record)

user_forecast = input("Enter forecast type: ")
user_threshold = input("Enter desired threshold: ")
user_hour = str(input("Enter forecast hour: "))
user_step = str(input("Enter step_length: "))


for record in data:

    if record["name"] == user_forecast and record["threshold"] == user_threshold and str(record["forecast_time"]) == user_hour and str(record["step_length"]) == user_step:
        print(record["probability"])

