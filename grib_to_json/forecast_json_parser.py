import orjson


with open("HREF12z_for_24.02619,-107.421197.json", "rb") as f:
    parsed = orjson.loads(f.read())


metadata = parsed["metadata"]
data = parsed["data"]

print("Model:", metadata["sitrep"])
print("Forecast time:", metadata["forecast_time"])
print("Location:", metadata["location"])
print("Available fields:", metadata["forecast_types"])

# Example: print the first few records
for record in data[:5]:
    print(record)