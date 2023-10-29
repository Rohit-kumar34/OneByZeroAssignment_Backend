from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import List
import threading

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# Load intervals from environment variables or configuration
intervals = []
intervals_env = os.getenv("INTERVALS")

if intervals_env:
    interval_strings = intervals_env.split(",")
    for interval_str in interval_strings:
        start, end = interval_str.strip().split("-")
        intervals.append((float(start), float(end)))

# Initialize the samples list
samples = []

# Lock for synchronizing access to the samples list
samples_lock = threading.Lock()

# Function to check if a value is within any interval
def is_within_intervals(value, intervals):
    for interval in intervals:
        if interval[0] <= value < interval[1]:
            return True
    return False

# Request model for inserting samples
class InsertSamplesRequest(BaseModel):
    data: List[float]

# Endpoint to insert samples
@app.post("/insertSamples/")
async def insert_samples(data: InsertSamplesRequest):
    with samples_lock:
        samples.extend(data.data)
    return {"message": "Samples inserted successfully"}

# Endpoint to fetch metrics
@app.get("/metrics/")
async def get_metrics():
    with samples_lock:
        # Calculate the count of samples within each interval
        interval_counts = {str(interval): sum(1 for sample in samples if is_within_intervals(sample, [interval])) for interval in intervals}

        # Calculate sample mean and variance
        sample_mean = sum(samples) / len(samples) if samples else 0
        sample_variance = sum((x - sample_mean) ** 2 for x in samples) / len(samples) if samples else 0

        # Return the metrics in the desired format
        metrics = {
            "Interval Counts": interval_counts,
            "Sample Mean": sample_mean,
            "Sample Variance": sample_variance,
            "Outliers": [x for x in samples if not any(interval[0] <= x < interval[1] for interval in intervals)]
        }
        return metrics
