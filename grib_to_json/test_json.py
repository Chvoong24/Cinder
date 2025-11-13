import orjson



with open("href12z_for_24.02619,-107.421197.json", "rb") as f:
    parsed = orjson.loads(f.read())


metadata = parsed["metadata"]
data = parsed["data"]

seen = set()
duplicates = []

for entry in data:
    key = (entry["threshold"], entry["name"], entry["forecastTime"], entry["step_length"])
    if key in seen:
        duplicates.append(entry)
    else:
        seen.add(key)

if duplicates:
    print("Duplicates found:", duplicates)
else:
    print("No duplicates found.")


