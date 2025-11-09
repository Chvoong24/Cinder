import orjson
import sys
from datetime import datetime, timedelta

def add_hours_to_time(time_str: str, hours: int) -> str:
    """
    Add a given number of hours to a datetime string in the format '%Y-%m-%d %H:%M:%S'.

    Args:
        time_str: The input datetime string (e.g. '2025-11-06 12:00:00')
        hours: Integer number of hours to add (can be negative)

    Returns:
        A new datetime string with hours added.
    """
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    new_dt = dt + timedelta(hours=hours)
    return new_dt.strftime("%Y-%m-%d %H:%M:%S")



import sys
import orjson
from pathlib import Path

if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <filename> <forecast_hour>")
        sys.exit(1)

    FILENAME = Path(sys.argv[1])
    user_hour = str(sys.argv[2])  # forecast hour

    if not FILENAME.exists():
        print(f"File '{FILENAME}' does not exist!")
        sys.exit(1)

    with open(FILENAME, "rb") as f:
        parsed = orjson.loads(f.read())

    metadata = parsed["metadata"]
    data = parsed["data"]

    print("Model:", metadata["sitrep"])
    print("Forecast time:", metadata["anal_date"])
    print("Location:", metadata["location"])

    for record in data:
        if str(record["forecast_time"]) == user_hour:
            threshold = record["threshold"]
            name = record["name"]
            step_length = record["step_length"]
            forecast_time = record["forecast_time"]
            step_end = add_hours_to_time(metadata["anal_date"], forecast_time)
            step_start = add_hours_to_time(metadata["anal_date"], forecast_time - step_length)
            value = record["value"]

            if int(step_length) == 0:
                print(f"Probability of {threshold} of {name} at {step_end} is {value}")
            else:
                print(f"Probability of {threshold} of {name} between {step_start} and {step_end} is {value}")

"""
href12z_for_24.02619,-107.421197.json
nbm06z_for_24.02619,-107.421197.json
"""