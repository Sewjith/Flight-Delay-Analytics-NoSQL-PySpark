# Databricks notebook source
# MAGIC %md
# MAGIC Install Kaggle package in a notebook cell

# COMMAND ----------

# MAGIC %pip install kaggle

# COMMAND ----------

# MAGIC %md
# MAGIC Set the Kaggle token in the notebook session

# COMMAND ----------

import os

if not os.environ.get("KAGGLE_API_TOKEN"):
    raise ValueError("Set the KAGGLE_API_TOKEN environment variable before running this notebook.")

print("Kaggle token loaded from environment")

# COMMAND ----------

# MAGIC %md
# MAGIC Test whether Kaggle is working

# COMMAND ----------

!kaggle competitions list

# COMMAND ----------

!kaggle datasets list -s "airline delay cancellation"

# COMMAND ----------

# MAGIC %md
# MAGIC Download the dataset directly into Databricks

# COMMAND ----------

import os

download_dir = "/tmp/airline_delay_data"
os.makedirs(download_dir, exist_ok=True)

!kaggle datasets download -d yuanyuwendymu/airline-delay-and-cancellation-data-2009-2018 -p /tmp/airline_delay_data

# COMMAND ----------

# MAGIC %md
# MAGIC Unzip the dataset

# COMMAND ----------

import zipfile

zip_path = "/tmp/airline_delay_data/airline-delay-and-cancellation-data-2009-2018.zip"
extract_dir = "/tmp/airline_delay_data/unzipped"

os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(extract_dir)

print("Files extracted:")
print(os.listdir(extract_dir))

# COMMAND ----------

# DBTITLE 1,Create Volume
# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.default.airline_data;

# COMMAND ----------

# MAGIC %md
# MAGIC Grant Access - No need to run this one - ALREADY GAVE ACCESS TO ALL USERS

# COMMAND ----------

# %sql
# -- Grant catalog access
# GRANT USE CATALOG ON CATALOG workspace TO `jakshiganj@gmail.com`;
# GRANT USE CATALOG ON CATALOG workspace TO `mpawickramasinghe@gmail.com`;
# GRANT USE CATALOG ON CATALOG workspace TO `sanjula.nelumdeniyage@gmail.com`;
# GRANT USE CATALOG ON CATALOG workspace TO `sewjithsilva@gmail.com`;
# GRANT USE CATALOG ON CATALOG workspace TO `shenonak15@gmail.com`;

# -- Grant schema access
# GRANT USE SCHEMA ON SCHEMA workspace.default TO `jakshiganj@gmail.com`;
# GRANT USE SCHEMA ON SCHEMA workspace.default TO `mpawickramasinghe@gmail.com`;
# GRANT USE SCHEMA ON SCHEMA workspace.default TO `sanjula.nelumdeniyage@gmail.com`;
# GRANT USE SCHEMA ON SCHEMA workspace.default TO `sewjithsilva@gmail.com`;
# GRANT USE SCHEMA ON SCHEMA workspace.default TO `shenonak15@gmail.com`;

# -- Grant volume read access
# GRANT READ VOLUME ON VOLUME workspace.default.airline_data TO `jakshiganj@gmail.com`;
# GRANT READ VOLUME ON VOLUME workspace.default.airline_data TO `mpawickramasinghe@gmail.com`;
# GRANT READ VOLUME ON VOLUME workspace.default.airline_data TO `sanjula.nelumdeniyage@gmail.com`;
# GRANT READ VOLUME ON VOLUME workspace.default.airline_data TO `sewjithsilva@gmail.com`;
# GRANT READ VOLUME ON VOLUME workspace.default.airline_data TO `shenonak15@gmail.com`;

# COMMAND ----------

import os

try:    print(os.listdir("/Volumes/workspace/default/airline_data"))
except PermissionError:
    print("Permission denied: cannot access the directory.")


# COMMAND ----------

df_2016 = spark.read.option("header", True).csv("/Volumes/workspace/default/airline_data/2016.csv")
df_2017 = spark.read.option("header", True).csv("/Volumes/workspace/default/airline_data/2017.csv")
df_2018 = spark.read.option("header", True).csv("/Volumes/workspace/default/airline_data/2018.csv")

display(df_2016.limit(5))
display(df_2017.limit(5))
display(df_2018.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC Member 03

# COMMAND ----------

# MAGIC %md
# MAGIC Import required libraries

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *

# COMMAND ----------

# MAGIC %md
# MAGIC Load the required datasets

# COMMAND ----------

df_2016_raw = spark.read.csv(
    "/Volumes/workspace/default/airline_data/2016.csv",
    header=True,
    inferSchema=True
)

df_2017_raw = spark.read.csv(
    "/Volumes/workspace/default/airline_data/2017.csv",
    header=True,
    inferSchema=True
)

df_2018_raw = spark.read.csv(
    "/Volumes/workspace/default/airline_data/2018.csv",
    header=True,
    inferSchema=True
)

print("2016 rows:", df_2016_raw.count())
print("2017 rows:", df_2017_raw.count())
print("2018 rows:", df_2018_raw.count())

# COMMAND ----------

# MAGIC %md
# MAGIC Standardise column names

# COMMAND ----------

def standardize_column_name(col_name):
    return (
        col_name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )

def standardize_columns(df):
    return df.toDF(*[standardize_column_name(c) for c in df.columns])

df_2016_raw = standardize_columns(df_2016_raw)
df_2017_raw = standardize_columns(df_2017_raw)
df_2018_raw = standardize_columns(df_2018_raw)

# COMMAND ----------

# MAGIC %md
# MAGIC Select only the most relevant columns

# COMMAND ----------

selected_columns = [
    "fl_date",
    "op_unique_carrier",
    "op_carrier_fl_num",
    "origin",
    "dest",
    "crs_dep_time",
    "dep_time",
    "dep_delay",
    "taxi_out",
    "wheels_off",
    "wheels_on",
    "taxi_in",
    "crs_arr_time",
    "arr_time",
    "arr_delay",
    "cancelled",
    "cancellation_code",
    "diverted",
    "crs_elapsed_time",
    "actual_elapsed_time",
    "air_time",
    "distance",
    "carrier_delay",
    "weather_delay",
    "nas_delay",
    "security_delay",
    "late_aircraft_delay"
]

def select_existing_columns(df, columns):
    existing_cols = [c for c in columns if c in df.columns]
    return df.select(*existing_cols)

df_2016 = select_existing_columns(df_2016_raw, selected_columns)
df_2017 = select_existing_columns(df_2017_raw, selected_columns)
df_2018 = select_existing_columns(df_2018_raw, selected_columns)

# COMMAND ----------

# MAGIC %md
# MAGIC Build reusable preprocessing function
# MAGIC This function will:
# MAGIC
# MAGIC remove duplicates;
# MAGIC calculate missing value percentages;
# MAGIC drop columns with more than 50% missing values;
# MAGIC fill numeric nulls with average;
# MAGIC fill categorical nulls with "Unknown";
# MAGIC cast important columns;
# MAGIC create derived features;

# COMMAND ----------

def preprocess_airline_data(df, year_label):
    
    print(f"\n========== PREPROCESSING {year_label} ==========")
    

    # 1. Remove duplicate rows

    before_count = df.count()
    df = df.dropDuplicates()
    after_count = df.count()
    
    print(f"{year_label} - Rows before duplicate removal: {before_count}")
    print(f"{year_label} - Rows after duplicate removal : {after_count}")
    print(f"{year_label} - Duplicate rows removed       : {before_count - after_count}")

    # 2. Rename key columns

    rename_dict = {
        "fl_date": "flight_date",
        "op_unique_carrier": "airline",
        "op_carrier_fl_num": "flight_number"
    }
    
    for old_name, new_name in rename_dict.items():
        if old_name in df.columns:
            df = df.withColumnRenamed(old_name, new_name)
    

    # 3. Convert data types
 
    cast_map = {
        "dep_delay": "double",
        "arr_delay": "double",
        "cancelled": "int",
        "diverted": "int",
        "distance": "double",
        "air_time": "double",
        "crs_elapsed_time": "double",
        "actual_elapsed_time": "double",
        "carrier_delay": "double",
        "weather_delay": "double",
        "nas_delay": "double",
        "security_delay": "double",
        "late_aircraft_delay": "double",
        "crs_dep_time": "int",
        "dep_time": "int",
        "crs_arr_time": "int",
        "arr_time": "int",
        "taxi_out": "double",
        "taxi_in": "double"
    }
    
    for col_name, target_type in cast_map.items():
        if col_name in df.columns:
            df = df.withColumn(col_name, F.col(col_name).cast(target_type))
    
    if "flight_date" in df.columns:
        df = df.withColumn("flight_date", F.to_date("flight_date"))
    

    # 4. Find missing value percentages
  
    total_rows = df.count()
    
    missing_percentage_exprs = []
    for c in df.columns:
        missing_percentage_exprs.append(
            F.round(
                (F.count(F.when(F.col(c).isNull(), c)) / F.lit(total_rows)) * 100, 2
            ).alias(c)
        )
    
    missing_percentage_df = df.select(missing_percentage_exprs)
    print(f"{year_label} - Missing value percentages:")
    display(missing_percentage_df)
    
    missing_dict = missing_percentage_df.collect()[0].asDict()
    

    # 5. Drop columns with > 50% missing values

    cols_to_drop = [col_name for col_name, pct in missing_dict.items() if pct > 50]
    
    print(f"{year_label} - Columns dropped (>50% missing): {cols_to_drop}")
    
    df = df.drop(*cols_to_drop)
    

    # 6. Identify numeric and categorical columns

    numeric_types = ["int", "bigint", "double", "float", "decimal", "long", "smallint"]
    
    numeric_cols = [c for c, dtype in df.dtypes if dtype in numeric_types]
    categorical_cols = [c for c, dtype in df.dtypes if dtype not in numeric_types and c != "flight_date"]
    

    # 7. Fill missing numeric values with average
 
    for c in numeric_cols:
        avg_value = df.select(F.avg(F.col(c))).collect()[0][0]
        if avg_value is not None:
            df = df.fillna({c: float(avg_value)})
    

    # 8. Fill missing categorical values with Unknown

    for c in categorical_cols:
        df = df.fillna({c: "Unknown"})

    # 9. Drop rows with critical missing values only if still present

    critical_cols = [c for c in ["airline", "origin", "dest", "flight_date"] if c in df.columns]
    df = df.dropna(subset=critical_cols)
    

    # 10. Remove clearly invalid values

    if "dep_delay" in df.columns:
        df = df.filter((F.col("dep_delay") >= -200) & (F.col("dep_delay") <= 2000))
    
    if "arr_delay" in df.columns:
        df = df.filter((F.col("arr_delay") >= -200) & (F.col("arr_delay") <= 2000))
    
    if "distance" in df.columns:
        df = df.filter(F.col("distance") > 0)
    
    if "air_time" in df.columns:
        df = df.filter(F.col("air_time") >= 0)
    

    # 11. Create derived columns

    if "origin" in df.columns and "dest" in df.columns:
        df = df.withColumn("route", F.concat_ws("-", F.col("origin"), F.col("dest")))
    
    if "flight_date" in df.columns:
        df = df.withColumn("year", F.year("flight_date")) \
               .withColumn("month", F.month("flight_date")) \
               .withColumn("day", F.dayofmonth("flight_date")) \
               .withColumn("day_of_week", F.dayofweek("flight_date"))
    
    if "crs_dep_time" in df.columns:
        df = df.withColumn("crs_dep_time_str", F.lpad(F.col("crs_dep_time").cast("string"), 4, "0")) \
               .withColumn("scheduled_dep_hour", F.substring("crs_dep_time_str", 1, 2).cast("int"))
    
    if "arr_delay" in df.columns:
        df = df.withColumn("is_delayed", F.when(F.col("arr_delay") > 15, 1).otherwise(0))
    
    if "cancelled" in df.columns:
        df = df.withColumn("flight_status", F.when(F.col("cancelled") == 1, "Cancelled").otherwise("Operated"))
    
    if "arr_delay" in df.columns:
        df = df.withColumn(
            "delay_category",
            F.when(F.col("arr_delay") <= 15, "On Time / Minor Delay")
             .when((F.col("arr_delay") > 15) & (F.col("arr_delay") <= 60), "Moderate Delay")
             .otherwise("Severe Delay")
        )
    
    if "month" in df.columns:
        df = df.withColumn(
            "month_name",
            F.when(F.col("month") == 1, "Jan")
             .when(F.col("month") == 2, "Feb")
             .when(F.col("month") == 3, "Mar")
             .when(F.col("month") == 4, "Apr")
             .when(F.col("month") == 5, "May")
             .when(F.col("month") == 6, "Jun")
             .when(F.col("month") == 7, "Jul")
             .when(F.col("month") == 8, "Aug")
             .when(F.col("month") == 9, "Sep")
             .when(F.col("month") == 10, "Oct")
             .when(F.col("month") == 11, "Nov")
             .otherwise("Dec")
        )
    

    # 12. Final missing value check

    final_total_rows = df.count()
    
    final_missing_exprs = []
    for c in df.columns:
        final_missing_exprs.append(
            F.round(
                (F.count(F.when(F.col(c).isNull(), c)) / F.lit(final_total_rows)) * 100, 2
            ).alias(c)
        )
    
    final_missing_df = df.select(final_missing_exprs)
    print(f"{year_label} - Final missing value percentages after preprocessing:")
    display(final_missing_df)
    
    print(f"{year_label} - Final rows   : {df.count()}")
    print(f"{year_label} - Final columns: {len(df.columns)}")
    
    return df

# COMMAND ----------

# MAGIC %md
# MAGIC Apply preprocessing separately to 2016, 2017, and 2018

# COMMAND ----------

df_2016_clean = preprocess_airline_data(df_2016, "2016")
df_2017_clean = preprocess_airline_data(df_2017, "2017")
df_2018_clean = preprocess_airline_data(df_2018, "2018")

# COMMAND ----------

# MAGIC %md
# MAGIC Preview cleaned data

# COMMAND ----------

print("===== CLEANED 2016 =====")
display(df_2016_clean.limit(5))

print("===== CLEANED 2017 =====")
display(df_2017_clean.limit(5))

print("===== CLEANED 2018 =====")
display(df_2018_clean.limit(5))

# COMMAND ----------

print("Preprocessing completed successfully.")
print("2016 cleaned rows:", df_2016_clean.count())
print("2017 cleaned rows:", df_2017_clean.count())
print("2018 cleaned rows:", df_2018_clean.count())

# COMMAND ----------

# MAGIC %md
# MAGIC Member 04
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC Import required libraries

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# COMMAND ----------

# MAGIC %md
# MAGIC Combine all cleaned yearly datasets

# COMMAND ----------

df_2016_analysis = df_2016_clean.withColumn("dataset_year", F.lit(2016))
df_2017_analysis = df_2017_clean.withColumn("dataset_year", F.lit(2017))
df_2018_analysis = df_2018_clean.withColumn("dataset_year", F.lit(2018))

df_all_analysis = df_2016_analysis.unionByName(df_2017_analysis, allowMissingColumns=True) \
                                  .unionByName(df_2018_analysis, allowMissingColumns=True)

print("Combined dataset row count:", df_all_analysis.count())
print("Combined dataset column count:", len(df_all_analysis.columns))
display(df_all_analysis.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC Overall dataset summary

# COMMAND ----------

overall_summary = df_all_analysis.agg(
    F.count("*").alias("total_flights"),
    F.sum("cancelled").alias("total_cancelled_flights"),
    F.sum("diverted").alias("total_diverted_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_departure_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arrival_delay"),
    F.round(F.avg("distance"), 2).alias("avg_distance"),
    F.round(F.avg("air_time"), 2).alias("avg_air_time")
)

display(overall_summary)

# COMMAND ----------

# MAGIC %md
# MAGIC Flight volume by year

# COMMAND ----------

flights_by_year = df_all_analysis.groupBy("dataset_year").agg(
    F.count("*").alias("total_flights"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.sum("diverted").alias("diverted_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate"),
    F.round((F.sum("is_delayed") / F.count("*")) * 100, 2).alias("delay_rate")
).orderBy("dataset_year")

display(flights_by_year)

# COMMAND ----------

# MAGIC %md
# MAGIC Explicit filtering — delayed flights only

# COMMAND ----------

delayed_flights = df_all_analysis.filter(F.col("arr_delay") > 15)

print("Delayed flights count:", delayed_flights.count())
display(delayed_flights.limit(10))

print("Insight: Flights with arrival delay greater than 15 minutes are treated as delayed flights for further analysis.")

# COMMAND ----------

# MAGIC %md
# MAGIC Explicit filtering — cancelled flights only

# COMMAND ----------

cancelled_flights_only = df_all_analysis.filter(F.col("cancelled") == 1)

print("Cancelled flights count:", cancelled_flights_only.count())
display(cancelled_flights_only.limit(10))

print("Insight: This filtered subset isolates cancelled flights and helps identify which locations or time periods are associated with more cancellations.")

# COMMAND ----------

# MAGIC %md
# MAGIC Explicit filtering — long distance flights

# COMMAND ----------

long_distance_flights = df_all_analysis.filter(F.col("distance") >= 2000)

print("Long-distance flights count:", long_distance_flights.count())
display(long_distance_flights.limit(10))

print("Insight: Filtering long-distance flights helps compare whether longer routes experience different delay behaviour compared to shorter routes.")

# COMMAND ----------

# MAGIC %md
# MAGIC Busiest origin airports
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To identify airports with the highest traffic.

# COMMAND ----------

origin_flight_volume = df_all_analysis.groupBy("origin").agg(
    F.count("*").alias("total_flights")
).orderBy(F.desc("total_flights"))
display(origin_flight_volume)

print("Insight: Airports with the highest flight counts represent the busiest origin hubs in the dataset.")

# COMMAND ----------

# MAGIC %md
# MAGIC Busiest destination airports

# COMMAND ----------

destination_flight_volume = df_all_analysis.groupBy("dest").agg(
    F.count("*").alias("total_flights")
).orderBy(F.desc("total_flights"))
display(destination_flight_volume)

print("Insight: This analysis identifies the destination airports receiving the highest number of flights.")

# COMMAND ----------

# MAGIC %md
# MAGIC Origin airport delay analysis
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To identify airports with high average delays and cancellation rates.

# COMMAND ----------

origin_delay_analysis = df_all_analysis.groupBy("origin").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate")
).orderBy(F.desc("total_flights"))
display(origin_delay_analysis)

# COMMAND ----------

# MAGIC %md
# MAGIC Destination airport delay analysis

# COMMAND ----------

destination_delay_analysis = df_all_analysis.groupBy("dest").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate")
).orderBy(F.desc("avg_arr_delay"))

display(destination_delay_analysis)

print("Insight: This reveals destination airports where arriving flights experience the greatest average delay.")

# COMMAND ----------

# MAGIC %md
# MAGIC Busiest service hours
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC This directly matches the coursework example of identifying busiest service hours.

# COMMAND ----------

busiest_hours = df_all_analysis.groupBy("scheduled_dep_hour").agg(
    F.count("*").alias("total_flights")
).orderBy(F.desc("total_flights"))

display(busiest_hours)

print("Insight: The hours with the highest flight counts represent the busiest service periods in airport operations.")

# COMMAND ----------

# MAGIC %md
# MAGIC Delay by service hour
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To find whether some times of the day experience more delays.

# COMMAND ----------

hourly_delay_analysis = df_all_analysis.groupBy("scheduled_dep_hour").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate"),
    F.round((F.sum("is_delayed") / F.count("*")) * 100, 2).alias("delay_rate")
).orderBy("scheduled_dep_hour")
display(hourly_delay_analysis)

print("Insight: This analysis shows how delay behaviour changes throughout the day and helps identify peak congestion hours.")

# COMMAND ----------

# MAGIC %md
# MAGIC Route analysis
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To identify frequently used and delay-prone routes.

# COMMAND ----------

route_analysis = df_all_analysis.groupBy("route").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate")
).orderBy(F.desc("total_flights"))

display(route_analysis)

print("Insight: Route-level analysis helps identify both high-volume routes and routes with high average delay.")

# COMMAND ----------

# MAGIC %md
# MAGIC Worst routes by arrival delay
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To focus only on meaningful routes with sufficient flight count.

# COMMAND ----------

worst_routes_by_arr_delay = df_all_analysis.groupBy("route").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay")
).filter(
    F.col("total_flights") >= 100
).orderBy(F.desc("avg_arr_delay"))
display(worst_routes_by_arr_delay.limit(20))

print("Insight: These routes have the highest average arrival delay among routes with significant traffic volume.")

# COMMAND ----------

# MAGIC %md
# MAGIC Monthly trend analysis
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To identify seasonal patterns and monthly operational trends.

# COMMAND ----------

monthly_analysis = df_all_analysis.groupBy("dataset_year", "month", "month_name").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate"),
    F.round((F.sum("is_delayed") / F.count("*")) * 100, 2).alias("delay_rate")
).orderBy("dataset_year", "month")
display(monthly_analysis)

print("Insight: Monthly analysis helps identify peak disruption periods and seasonal patterns in flight delays and cancellations.")

# COMMAND ----------

# MAGIC %md
# MAGIC Overall monthly pattern

# COMMAND ----------

overall_monthly_pattern = df_all_analysis.groupBy("month", "month_name").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate")
).orderBy("month")

display(overall_monthly_pattern)

print("Insight: This summarizes how delay and cancellation behaviour changes over the calendar year, regardless of specific year.")

# COMMAND ----------

# MAGIC %md
# MAGIC Day-of-week analysis
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To identify which days are operationally heavier or more delay-prone.

# COMMAND ----------

day_of_week_analysis = df_all_analysis.groupBy("day_of_week").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate"),
    F.round((F.sum("is_delayed") / F.count("*")) * 100, 2).alias("delay_rate")
).orderBy("day_of_week")
display(day_of_week_analysis)

print("Insight: This analysis helps determine whether certain weekdays are associated with higher delays or cancellations.")

# COMMAND ----------

# MAGIC %md
# MAGIC Delay category distribution
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To measure how flights are distributed across delay severity groups.

# COMMAND ----------

delay_category_distribution = df_all_analysis.groupBy("delay_category").agg(
    F.count("*").alias("flight_count")
).orderBy(F.desc("flight_count"))

display(delay_category_distribution)

print("Insight: Most flights may fall into low-delay categories, while fewer flights experience severe delays.")

# COMMAND ----------

# MAGIC %md
# MAGIC Flight status distribution

# COMMAND ----------

flight_status_distribution = df_all_analysis.groupBy("flight_status").agg(
    F.count("*").alias("flight_count")
).orderBy(F.desc("flight_count"))

display(flight_status_distribution)

print("Insight: This distinguishes operated flights from cancelled flights and provides a simple operational outcome summary.")

# COMMAND ----------

# MAGIC %md
# MAGIC Distance range analysis

# COMMAND ----------

df_distance_binned = df_all_analysis.withColumn(
    "distance_range",
    F.when(F.col("distance") < 500, "0-500")
     .when((F.col("distance") >= 500) & (F.col("distance") < 1000), "500-1000")
     .when((F.col("distance") >= 1000) & (F.col("distance") < 2000), "1000-2000")
     .otherwise("2000+")
)
distance_delay_analysis = df_distance_binned.groupBy("distance_range").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate")
).orderBy("distance_range")
display(distance_delay_analysis)

print("Insight: Grouping distance into ranges makes it easier to understand how shorter and longer flights differ in delay behaviour.")

# COMMAND ----------

# MAGIC %md
# MAGIC Taxi time analysis
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To compare ground movement times across years.

# COMMAND ----------

taxi_time_analysis = df_all_analysis.groupBy("dataset_year").agg(
    F.round(F.avg("taxi_out"), 2).alias("avg_taxi_out"),
    F.round(F.avg("taxi_in"), 2).alias("avg_taxi_in")
).orderBy("dataset_year")
display(taxi_time_analysis)

print("Insight: Taxi-out and taxi-in times reflect airport surface congestion and ground handling efficiency.")

# COMMAND ----------

# MAGIC %md
# MAGIC Elapsed time analysis

# COMMAND ----------

elapsed_time_analysis = df_all_analysis.groupBy("dataset_year").agg(
    F.round(F.avg("crs_elapsed_time"), 2).alias("avg_scheduled_elapsed_time"),
    F.round(F.avg("actual_elapsed_time"), 2).alias("avg_actual_elapsed_time"),
    F.round(F.avg("air_time"), 2).alias("avg_air_time")
).orderBy("dataset_year")

display(elapsed_time_analysis)

print("Insight: Comparing scheduled and actual elapsed time helps show whether flights consistently take longer than planned.")

# COMMAND ----------

# MAGIC %md
# MAGIC Year-wise origin airport analysis
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To compare airport-level performance across years.

# COMMAND ----------

origin_year_analysis = df_all_analysis.groupBy("dataset_year", "origin").agg(
    F.count("*").alias("total_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate")
).filter(
    F.col("total_flights") >= 100
).orderBy("dataset_year", F.desc("avg_arr_delay"))

display(origin_year_analysis)

print("Insight: This compares how airport performance changes year by year.")

# COMMAND ----------

# MAGIC %md
# MAGIC Ranking worst origin airports with window functions
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To show advanced Spark usage and ranking logic.

# COMMAND ----------

origin_rank_window = Window.partitionBy("dataset_year").orderBy(F.desc("avg_arr_delay"))

worst_origin_ranked = origin_year_analysis.withColumn(
    "delay_rank_within_year",
    F.row_number().over(origin_rank_window)
)
display(worst_origin_ranked)

print("Insight: Window functions allow ranking of airports within each year based on average arrival delay.")

# COMMAND ----------

# MAGIC %md
# MAGIC Top 10 worst origin airports each year

# COMMAND ----------

top_10_worst_origins_each_year = worst_origin_ranked.filter(
    F.col("delay_rank_within_year") <= 10
).orderBy("dataset_year", "delay_rank_within_year")

display(top_10_worst_origins_each_year)

print("Insight: These are the worst-performing origin airports in each year based on average arrival delay.")

# COMMAND ----------

# MAGIC %md
# MAGIC Best origin airports each year

# COMMAND ----------

best_origin_window = Window.partitionBy("dataset_year").orderBy(F.asc("avg_arr_delay"))

best_origin_ranked = origin_year_analysis.withColumn(
    "best_rank_within_year",
    F.row_number().over(best_origin_window)
)

top_10_best_origins_each_year = best_origin_ranked.filter(
    F.col("best_rank_within_year") <= 10
).orderBy("dataset_year", "best_rank_within_year")

display(top_10_best_origins_each_year)

print("Insight: These are the best-performing origin airports in each year based on lowest average arrival delay.")

# COMMAND ----------

# MAGIC %md
# MAGIC Delayed vs non-delayed comparison by year
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC To compare delay class frequency over time.

# COMMAND ----------

delay_comparison_by_year = df_all_analysis.groupBy("dataset_year", "is_delayed").agg(
    F.count("*").alias("flight_count")
).orderBy("dataset_year", "is_delayed")

display(delay_comparison_by_year)

print("Insight: This comparison shows whether delayed flights are increasing or decreasing over time.")

# COMMAND ----------

# MAGIC %md
# MAGIC key metrics summary
# MAGIC
# MAGIC Purpose:
# MAGIC
# MAGIC A concise, report-ready summary table.

# COMMAND ----------

key_metrics_summary = df_all_analysis.groupBy("dataset_year").agg(
    F.count("*").alias("total_flights"),
    F.sum("cancelled").alias("cancelled_flights"),
    F.sum("diverted").alias("diverted_flights"),
    F.round(F.avg("dep_delay"), 2).alias("avg_dep_delay"),
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.round((F.sum("cancelled") / F.count("*")) * 100, 2).alias("cancellation_rate"),
    F.round((F.sum("is_delayed") / F.count("*")) * 100, 2).alias("delay_rate"),
    F.round(F.avg("distance"), 2).alias("avg_distance")
).orderBy("dataset_year")

display(key_metrics_summary)

print("Insight: This final summary combines the most important yearly indicators into one analytical table.")

# COMMAND ----------

# MAGIC %md
# MAGIC temporary views

# COMMAND ----------

df_2016_clean.createOrReplaceTempView("airline_2016_clean_view")
df_2017_clean.createOrReplaceTempView("airline_2017_clean_view")
df_2018_clean.createOrReplaceTempView("airline_2018_clean_view")
df_all_analysis.createOrReplaceTempView("airline_all_clean_view")

print("Temporary views created successfully.")

# COMMAND ----------

# MAGIC %md
# MAGIC temporary views

# COMMAND ----------

df_2016_clean.createOrReplaceTempView("airline_2016_clean_view")
df_2017_clean.createOrReplaceTempView("airline_2017_clean_view")
df_2018_clean.createOrReplaceTempView("airline_2018_clean_view")
df_all_analysis.createOrReplaceTempView("airline_all_clean_view")

print("Temporary views created successfully.")

# COMMAND ----------

# MAGIC %md
# MAGIC Member 05
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC Import libraries

# COMMAND ----------

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

plt.style.use("seaborn-v0_8")
plt.rcParams["figure.figsize"] = (8,5)
plt.rcParams["axes.grid"] = True

# COMMAND ----------

# MAGIC %md
# MAGIC Flight Volume Over Time
# MAGIC
# MAGIC Graph Type: Line Chart
# MAGIC
# MAGIC
# MAGIC Why:
# MAGIC Time-based data → best shown using line chart
# MAGIC Shows trend and growth clearly

# COMMAND ----------

df_plot = flights_by_year.toPandas()

plt.figure()
plt.plot(df_plot["dataset_year"], df_plot["total_flights"], marker='o')
plt.title("Flight Volume Trend")
plt.xlabel("Year")
plt.ylabel("Number of Flights")

plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Delay Comparison (Arrival vs Departure)
# MAGIC
# MAGIC Graph Type: Multi-Line Chart
# MAGIC
# MAGIC Why:
# MAGIC Comparing two trends over time
# MAGIC Line chart shows movement + relationship

# COMMAND ----------

plt.figure()

plt.plot(df_plot["dataset_year"], df_plot["avg_arr_delay"], marker='o', label="Arrival Delay")
plt.plot(df_plot["dataset_year"], df_plot["avg_dep_delay"], marker='o', label="Departure Delay")

plt.legend()
plt.title("Delay Comparison Over Years")
plt.xlabel("Year")
plt.ylabel("Delay")

plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Top Airports Analysis
# MAGIC
# MAGIC Graph Type: Horizontal Bar Chart
# MAGIC
# MAGIC
# MAGIC Why:
# MAGIC Best for categorical comparison
# MAGIC Horizontal = better readability for labels

# COMMAND ----------

top_airports = origin_flight_volume.limit(10).toPandas().sort_values("total_flights")

plt.barh(top_airports["origin"], top_airports["total_flights"])
plt.title("Top Airports by Flight Volume")
plt.xlabel("Flights")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Delay Category Distribution
# MAGIC
# MAGIC Graph Type: Donut Chart
# MAGIC
# MAGIC Why:
# MAGIC Shows proportions clearly
# MAGIC Donut is cleaner than pie chart

# COMMAND ----------

delay_df = delay_category_distribution.toPandas()

plt.pie(delay_df["flight_count"], labels=delay_df["delay_category"], autopct='%1.1f%%')

centre_circle = plt.Circle((0,0),0.70,fc='white')
plt.gca().add_artist(centre_circle)

plt.title("Delay Category Distribution")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Flight Status Distribution
# MAGIC
# MAGIC Graph Type: Pie Chart
# MAGIC
# MAGIC Why:
# MAGIC Only 2 categories → ideal for pie
# MAGIC Shows cancelled vs completed proportion

# COMMAND ----------

status_df = flight_status_distribution.toPandas()

plt.pie(status_df["flight_count"], labels=status_df["flight_status"], autopct='%1.1f%%')
plt.title("Flight Status Distribution")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Monthly Delay Pattern
# MAGIC
# MAGIC Graph Type: Line Chart
# MAGIC
# MAGIC Why:
# MAGIC Shows seasonality
# MAGIC Detects peak delay months

# COMMAND ----------

month_df = overall_monthly_pattern.toPandas().sort_values("month")

plt.plot(month_df["month_name"], month_df["avg_arr_delay"], marker='o')
plt.xticks(rotation=45)
plt.title("Monthly Delay Trend")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Delay vs Time of Day
# MAGIC
# MAGIC Graph Type: Line Chart
# MAGIC
# MAGIC Why:
# MAGIC Time-based continuous variable
# MAGIC Shows peak congestion hours

# COMMAND ----------

hour_df = hourly_delay_analysis.toPandas()

plt.plot(hour_df["scheduled_dep_hour"], hour_df["avg_arr_delay"], marker='o')
plt.title("Delay vs Departure Hour")
plt.xlabel("Hour")
plt.ylabel("Delay")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Distance vs Delay 
# MAGIC
# MAGIC Graph Type: Bar Chart
# MAGIC
# MAGIC Why this is better:
# MAGIC Removes noise from scatter plot;
# MAGIC Shows clear relationship between distance and delay;
# MAGIC Much easier to interpret 

# COMMAND ----------

from pyspark.sql import functions as F

# Create distance bins
df_binned = df_all_analysis.withColumn(
    "distance_range",
    F.when(F.col("distance") < 500, "0-500")
     .when((F.col("distance") >= 500) & (F.col("distance") < 1000), "500-1000")
     .when((F.col("distance") >= 1000) & (F.col("distance") < 2000), "1000-2000")
     .otherwise("2000+")
)

# Aggregate average delay per bin
distance_delay_analysis = df_binned.groupBy("distance_range").agg(
    F.round(F.avg("arr_delay"), 2).alias("avg_arr_delay"),
    F.count("*").alias("flight_count")
).orderBy("distance_range")

# Convert to pandas
plot_df = distance_delay_analysis.toPandas()

# Plot
plt.figure(figsize=(8,5))
plt.bar(plot_df["distance_range"], plot_df["avg_arr_delay"])

plt.title("Average Arrival Delay by Distance Range")
plt.xlabel("Distance Range")
plt.ylabel("Average Delay (minutes)")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Delay Distribution
# MAGIC
# MAGIC Graph Type: Density Plot (Better than Histogram)
# MAGIC
# MAGIC Why:
# MAGIC Smooth distribution visualization
# MAGIC Avoids noisy histogram

# COMMAND ----------

import seaborn as sns

sample_df = df_all_analysis.select("arr_delay").dropna().sample(0.05).toPandas()

sample_df = sample_df[(sample_df["arr_delay"] > -100) & (sample_df["arr_delay"] < 300)]

sns.kdeplot(sample_df["arr_delay"], fill=True)
plt.title("Delay Distribution (Density Plot)")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Correlation Analysis
# MAGIC
# MAGIC Graph Type: Heatmap
# MAGIC
# MAGIC Why:
# MAGIC Shows relationships between multiple variables
# MAGIC Very high-value visualization
# MAGIC

# COMMAND ----------

import seaborn as sns

corr_df = df_all_analysis.select(
    "dep_delay", "arr_delay", "taxi_out", "taxi_in", "air_time", "distance"
).toPandas()

corr = corr_df.corr()

sns.heatmap(corr, annot=True)
plt.title("Correlation Heatmap")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Taxi Time Comparison
# MAGIC
# MAGIC Graph Type: Multi-Line Chart
# MAGIC
# MAGIC Why:
# MAGIC Compare two trends over time

# COMMAND ----------

taxi_df = taxi_time_analysis.toPandas()

plt.plot(taxi_df["dataset_year"], taxi_df["avg_taxi_out"], marker='o', label="Taxi Out")
plt.plot(taxi_df["dataset_year"], taxi_df["avg_taxi_in"], marker='o', label="Taxi In")

plt.legend()
plt.title("Taxi Time Trend")

plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Graph Type: Radial Bar Chart
# MAGIC
# MAGIC Why:
# MAGIC Visually attractive
# MAGIC Shows ranking in circular format

# COMMAND ----------

data = top_airports.sort_values("total_flights")

plt.figure(figsize=(10,6))
plt.barh(data["origin"], data["total_flights"])

for i, v in enumerate(data["total_flights"]):
    plt.text(v, i, f"{int(v/1000)}K", va='center')

plt.title("Top 10 Busiest Airports (Clear Comparison)")
plt.xlabel("Flights")
plt.ylabel("Airport")
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ML Models

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml import Pipeline

# Limit to top 20 airports only to reduce cardinality
top_airports_list = [
    row["origin"] for row in 
    df_all_analysis.groupBy("origin").count()
    .orderBy(F.desc("count")).limit(20).collect()
]

ml_df = df_all_analysis.filter(
    F.col("origin").isin(top_airports_list) & 
    F.col("dest").isin(top_airports_list)
).select(
    "dep_delay", "distance", "taxi_out", "taxi_in",
    "scheduled_dep_hour", "day_of_week", "month",
    "origin", "dest", "is_delayed",
    "crs_elapsed_time", "crs_dep_time", "crs_arr_time"
).dropna().sample(fraction=0.3, seed=42)

print("ML dataset row count:", ml_df.count())
display(ml_df.limit(5))

# COMMAND ----------

origin_indexer = StringIndexer(inputCol="origin", outputCol="origin_idx", handleInvalid="keep")
dest_indexer   = StringIndexer(inputCol="dest",   outputCol="dest_idx",   handleInvalid="keep")

feature_cols = [
    "dep_delay", "distance", "taxi_out", "taxi_in",
    "scheduled_dep_hour", "day_of_week", "month",
    "origin_idx", "dest_idx"
]

assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="keep")
print("Features ready:", feature_cols)

# COMMAND ----------

train_df, test_df = ml_df.randomSplit([0.8, 0.2], seed=42)

print("Training rows:", train_df.count())
print("Testing rows :", test_df.count())

# COMMAND ----------

print(df_all_analysis.columns)

# COMMAND ----------

from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
import pyspark.sql.functions as F

# 1. Define predictive features exactly as they appear in your dataset
#categorical_cols = ['origin', 'dest']
numeric_cols = [
    'distance', 
    'scheduled_dep_hour', 
    'day_of_week', 
    'month', 
    'crs_elapsed_time', 
    'crs_dep_time', 
    'crs_arr_time'
]

# 2. Create StringIndexers to convert text (e.g., "JFK") into numbers (e.g., 1.0)
# indexers = [
#     StringIndexer(inputCol=col, outputCol=col+"_index", handleInvalid="keep")
#     for col in categorical_cols
# ]

# 3. Combine the newly indexed categories + your existing numeric columns
#assembler_inputs = [col+"_index" for col in categorical_cols] + numeric_cols

# 4. Create the final VectorAssembler
assembler = VectorAssembler(inputCols=numeric_cols, outputCol="features", handleInvalid="skip")

print("Preprocessing stage configured successfully with Categoricals.")

# COMMAND ----------

# Ensure is_delayed is treated as an integer
train_df = train_df.withColumn("is_delayed", F.col("is_delayed").cast("integer"))

# Separate the classes
minority_df = train_df.filter(F.col("is_delayed") == 1)
majority_df = train_df.filter(F.col("is_delayed") == 0)

minority_count = minority_df.count()
majority_count = majority_df.count()
print(f"Original Train Data -> Delayed (1): {minority_count}, On-Time (0): {majority_count}")

# Calculate ratio to downsample the majority class
ratio = minority_count / majority_count
sampled_majority_df = majority_df.sample(withReplacement=False, fraction=ratio, seed=42)

# Combine back into a perfectly balanced 50/50 training set
balanced_train_df = minority_df.unionByName(sampled_majority_df)

print("\nBalanced Train Data Distribution:")
balanced_train_df.groupBy("is_delayed").count().show()

# COMMAND ----------

print(train_df.columns)

# COMMAND ----------

# MAGIC %md
# MAGIC Decision Tree Classifier

# COMMAND ----------

from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator

param_combinations = [
    {"maxDepth": 5, "minInstancesPerNode": 10},
    {"maxDepth": 7, "minInstancesPerNode": 20},
    {"maxDepth": 10, "minInstancesPerNode": 50},
    {"maxDepth": 12, "minInstancesPerNode": 100}
]

tuning_results = []

for params in param_combinations:
    # 1. Define estimator
    dt_tuned = DecisionTreeClassifier(
        labelCol="is_delayed",
        featuresCol="features",
        maxDepth=params["maxDepth"],
        minInstancesPerNode=params["minInstancesPerNode"],
        maxBins=100
    )
    
    # 2. Define pipeline
    pipeline = Pipeline(stages=[assembler, dt_tuned])
    
    # 3. Fit and Predict
    model = pipeline.fit(balanced_train_df)
    preds = model.transform(test_df)
    
    # 4. Evaluators
    binary_eval = BinaryClassificationEvaluator(labelCol="is_delayed", metricName="areaUnderROC")
    
    acc_eval = MulticlassClassificationEvaluator(
        labelCol="is_delayed", predictionCol="prediction", metricName="accuracy"
    )
    
    precision_eval = MulticlassClassificationEvaluator(
        labelCol="is_delayed", predictionCol="prediction", metricName="weightedPrecision"
    )
    
    recall_eval = MulticlassClassificationEvaluator(
        labelCol="is_delayed", predictionCol="prediction", metricName="weightedRecall"
    )
    
    # 5. Calculate metrics
    auc = binary_eval.evaluate(preds)
    acc = acc_eval.evaluate(preds)
    precision = precision_eval.evaluate(preds)
    recall = recall_eval.evaluate(preds)
    
    tuning_results.append({
        "maxDepth": params["maxDepth"],
        "minInstancesPerNode": params["minInstancesPerNode"],
        "Accuracy": round(acc, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "ROC_AUC": round(auc, 4)
    })
    
    print(f"maxDepth={params['maxDepth']}, minInstances={params['minInstancesPerNode']} "
          f"-> Acc={acc:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, AUC={auc:.4f}")

# Find best combination based on AUC (you can change this)
best = max(tuning_results, key=lambda x: x["ROC_AUC"])

print(f"\nBest params -> maxDepth={best['maxDepth']}, minInstancesPerNode={best['minInstancesPerNode']}")

# COMMAND ----------

# MAGIC %md
# MAGIC Feature Importance

# COMMAND ----------

# Re-train pipeline with the absolute best parameters to inspect it
best_dt = DecisionTreeClassifier(
    labelCol="is_delayed",
    featuresCol="features",
    maxDepth=best["maxDepth"],
    minInstancesPerNode=best["minInstancesPerNode"],
    maxBins=100
)

best_pipeline = Pipeline(stages=[assembler, best_dt])
best_model = best_pipeline.fit(balanced_train_df)

# The Decision Tree is the last stage in the pipeline
tree_model = best_model.stages[-1]

print("Feature Importances:")
for feature, importance in zip(feature_cols, tree_model.featureImportances):
    print(f"{feature}: {importance:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC Random Forest Classifier

# COMMAND ----------

from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml import Pipeline

# Random Forest Hyperparameters
rf_param_combinations = [
    {"maxDepth": 5, "minInstancesPerNode": 10},
    {"maxDepth": 7, "minInstancesPerNode": 20},
    {"maxDepth": 10, "minInstancesPerNode": 50}
]

rf_tuning_results = []

# Evaluators
roc_evaluator = BinaryClassificationEvaluator(labelCol="is_delayed", metricName="areaUnderROC")

acc_evaluator = MulticlassClassificationEvaluator(
    labelCol="is_delayed", predictionCol="prediction", metricName="accuracy"
)

precision_evaluator = MulticlassClassificationEvaluator(
    labelCol="is_delayed", predictionCol="prediction", metricName="weightedPrecision"
)

recall_evaluator = MulticlassClassificationEvaluator(
    labelCol="is_delayed", predictionCol="prediction", metricName="weightedRecall"
)

print("Training Random Forest Models...")

for params in rf_param_combinations:
    rf = RandomForestClassifier(
        labelCol="is_delayed",
        featuresCol="features",
        numTrees=50,
        maxDepth=params["maxDepth"],
        minInstancesPerNode=params["minInstancesPerNode"],
        maxBins=100,
        seed=42
    )
    
    pipeline = Pipeline(stages=[assembler, rf])
    model = pipeline.fit(balanced_train_df)
    preds = model.transform(test_df)
    
    # Metrics
    auc = roc_evaluator.evaluate(preds)
    acc = acc_evaluator.evaluate(preds)
    precision = precision_evaluator.evaluate(preds)
    recall = recall_evaluator.evaluate(preds)
    
    rf_tuning_results.append({
        "maxDepth": params["maxDepth"],
        "minInstancesPerNode": params["minInstancesPerNode"],
        "Accuracy": round(acc, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "ROC_AUC": round(auc, 4),
        "model": model
    })
    
    print(f"RF (maxDepth={params['maxDepth']}, minInstances={params['minInstancesPerNode']}) "
          f"-> Acc={acc:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, AUC={auc:.4f}")

# Best model based on AUC
best_rf_result = max(rf_tuning_results, key=lambda x: x["ROC_AUC"])
best_rf_model = best_rf_result["model"]

print(f"\nBest RF params -> maxDepth={best_rf_result['maxDepth']}, minInstancesPerNode={best_rf_result['minInstancesPerNode']}")
print(f"Best RF -> Accuracy={best_rf_result['Accuracy']:.4f}, AUC={best_rf_result['ROC_AUC']:.4f}")

# COMMAND ----------

# Extract the Random Forest model from the pipeline
rf_tree_model = best_rf_model.stages[-1]

print("=== RANDOM FOREST FEATURE IMPORTANCES ===")
# Zip the feature names with their importance scores
importances = list(zip(feature_cols, rf_tree_model.featureImportances))

# Sort them from most important to least important
importances.sort(key=lambda x: x[1], reverse=True)

for feature, importance in importances:
    print(f"{feature}: {importance:.4f}")

# COMMAND ----------

# MAGIC %md
# MAGIC Gradient Boosted Tree Classifier

# COMMAND ----------

from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator

# Model
gbt = GBTClassifier(
    labelCol="is_delayed",
    featuresCol="features",
    maxIter=50,
    maxDepth=7,
    maxBins=100,
    seed=42
)

# Pipeline
gbt_pipeline = Pipeline(stages=[assembler, gbt])

print("Training Gradient Boosted Tree (This may take a few minutes)...")
gbt_model = gbt_pipeline.fit(balanced_train_df)

# Predictions
gbt_preds = gbt_model.transform(test_df)

# Evaluators
roc_evaluator = BinaryClassificationEvaluator(labelCol="is_delayed", metricName="areaUnderROC")

acc_evaluator = MulticlassClassificationEvaluator(
    labelCol="is_delayed", predictionCol="prediction", metricName="accuracy"
)

precision_evaluator = MulticlassClassificationEvaluator(
    labelCol="is_delayed", predictionCol="prediction", metricName="weightedPrecision"
)

recall_evaluator = MulticlassClassificationEvaluator(
    labelCol="is_delayed", predictionCol="prediction", metricName="weightedRecall"
)

# Metrics
gbt_auc = roc_evaluator.evaluate(gbt_preds)
gbt_acc = acc_evaluator.evaluate(gbt_preds)
gbt_precision = precision_evaluator.evaluate(gbt_preds)
gbt_recall = recall_evaluator.evaluate(gbt_preds)

print(f"""
Gradient Boosted Tree Results:
Accuracy  = {gbt_acc:.4f}
Precision = {gbt_precision:.4f}
Recall    = {gbt_recall:.4f}
AUC       = {gbt_auc:.4f}
""")
