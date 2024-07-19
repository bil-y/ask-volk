"""
author: carlo schmid
"""

import json
from datetime import datetime
import pandas as pd

# path
json_path = "../../data/leaflets/leaflet_contents.json"
out_path = "../../data/leaflets/2004-2018.csv"

# Define the date range
start_date = datetime(2004, 1, 1)
end_date = datetime(2018, 12, 31)

# column names
column_names = ["date", "subject", "short_summary", "detail", "initiative", "referendum", "council"]

# set up dataframe
df = pd.DataFrame(columns=column_names)

with open(json_path, encoding="utf8") as json_data:
    votation_dict = json.load(json_data)
    json_data.close()
    filtered_results = {
        date_str: result
        for date_str, result in votation_dict.items()
        if start_date <= datetime.strptime(date_str.strip(), "%Y-%m-%d") <= end_date
    }
    for date, data in filtered_results.items():
        try:
            subjects = filtered_results[date]["de"]
            for subject, details in subjects.items():
                subject_dict = {}
                subject_dict["date"] = date
                subject_dict["subject"] = subject
                for key in details.keys():
                    subject_dict[key] = details[key]
                df = pd.concat([df, pd.DataFrame([subject_dict])], ignore_index=True)
        except KeyError:
            print(f"no german leaflet for date {date}")
print(df)
df.to_csv(out_path)