import pandas as pd
from ydata_profiling import ProfileReport

file = "stop_times"
df = pd.read_csv(f'sncf-gtfs-theorique\{file}.txt')
ProfileReport(df, title="Trips Summary", explorative=True).to_file(f"data-reports/{file}-report.html")