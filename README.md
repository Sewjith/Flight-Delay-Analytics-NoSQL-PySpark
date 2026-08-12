# Flight Delay Analysis and Prediction with PySpark

This repository contains a Databricks-based big data project for analyzing and predicting airline delays using PySpark. The workflow covers data ingestion, preprocessing, exploratory analysis, visualization, and machine learning on large-scale U.S. flight records.

## Project Overview

The project uses the Kaggle dataset `airline-delay-and-cancellation-data-2009-2018` and focuses on the 2016, 2017, and 2018 flight data files. The pipeline is designed to run in Databricks with Apache Spark and process millions of records efficiently.

Core stages:

- Download and extract the dataset with the Kaggle API
- Store raw files in a Databricks Unity Catalog volume
- Load yearly CSV files into Spark DataFrames
- Clean and standardize the data
- Engineer features for analysis and classification
- Perform EDA and generate visualizations
- Train delay-prediction models with PySpark ML
- Upload sampled flight data into MongoDB for NoSQL storage

## Tech Stack

- Python
- Apache Spark / PySpark
- Databricks
- Kaggle API
- MongoDB
- PyMongo
- Matplotlib
- Seaborn
- Pandas

## Dataset

Source dataset:

- Kaggle: `yuanyuwendymu/airline-delay-and-cancellation-data-2009-2018`

Years used in this project:

- 2016
- 2017
- 2018

## Data Pipeline

### 1. Ingestion

The notebook installs the Kaggle package, authenticates with Kaggle, downloads the airline delay dataset, extracts the archive, and reads the relevant CSV files into Spark DataFrames.

### 2. Preprocessing

The preprocessing pipeline includes:

- Standardizing column names
- Selecting relevant flight columns
- Removing duplicate rows
- Casting fields to appropriate data types
- Measuring and handling missing values
- Dropping columns with more than 50% missing data
- Filling numeric nulls with averages
- Filling categorical nulls with `"Unknown"`
- Filtering invalid values and anomalies

### 3. Feature Engineering

Derived fields include:

- `route`
- `year`
- `month`
- `day`
- `day_of_week`
- `month_name`
- `scheduled_dep_hour`
- `is_delayed`
- `flight_status`
- `delay_category`

### 4. Exploratory Analysis

The analysis section examines:

- Flight volume by year
- Delay and cancellation rates
- Busiest origin and destination airports
- Delay patterns by hour and month
- Airport-level performance
- Distance-based delay behavior
- Taxi time trends

### 5. Visualization

The project generates charts such as:

- Line charts for yearly flight and delay trends
- Bar charts for top airports
- Pie and donut charts for flight status and delay categories
- Density plots for arrival delay distribution
- Heatmaps for correlation analysis

### 6. Machine Learning

The notebook builds classification models to predict whether a flight is delayed.

Models used:

- Decision Tree Classifier
- Random Forest Classifier
- Gradient Boosted Tree Classifier

Evaluation metrics:

- Accuracy
- Precision
- Recall
- ROC AUC

### 7. MongoDB NoSQL Storage

The repository also includes a NoSQL data-loading script in `Upload_Data.py` for sending sampled CSV data into MongoDB.

MongoDB workflow:

- Connects to MongoDB using `pymongo.MongoClient`
- Verifies the connection with a `ping` request
- Uses the database `US_Flight_Cancellation_Delay_History`
- Uses the collection `flights`
- Reads sampled CSV files from the `data/` directory
- Converts each CSV into JSON-like records with Pandas
- Inserts the records into MongoDB with `insert_many`

Expected sample files:

- `data/sample_2016.csv`
- `data/sample_2017.csv`
- `data/sample_2018.csv`

This section supports a NoSQL storage use case alongside the Spark-based analytics workflow, making it easier to persist subsets of the flight dataset for document-oriented querying and downstream application use.

## Repository Structure

- `Big Data Analytics.ipynb`: notebook version of the project
- `Big Data Analytics.py`: exported Databricks notebook as a Python script
- `Big Data Analytics.html`: exported HTML version of the notebook
- `Upload_Data.py`: MongoDB upload script for sampled CSV files
- `Web/`: static website built from the notebook outputs and visualizations
- `README.md`: project documentation

## Web Deployment

The repository now includes a GitHub Pages workflow that deploys the `Web/` folder as a static site.

Expected public URL after deployment:

- `https://thimira-hansana.github.io/Flight-Delay-Analytics-NoSQL-PySpark/`

To publish it:

1. Push the repository changes to GitHub.
2. In the GitHub repository, open `Settings` -> `Pages`.
3. Under `Build and deployment`, set `Source` to `GitHub Actions`.
4. Wait for the `Deploy Web To GitHub Pages` workflow to finish.
5. Open the Pages URL above.

Notes:

- The workflow runs on pushes to `main` and `dev`.
- It deploys the contents of `Web/` directly, so the site opens from the repository Pages URL without extra routing.
- If you open the site locally with `file://`, the 3D aircraft falls back to a static preview. On GitHub Pages it will load through normal HTTPS requests.

## How to Run

### Prerequisites

- A Databricks workspace
- A Spark cluster with PySpark support
- Kaggle account and API credentials
- Access to Unity Catalog volumes if using the same storage workflow
- MongoDB instance or MongoDB Atlas cluster for the NoSQL upload step

### Steps

1. Clone this repository.
2. Import `Big Data Analytics.ipynb` into Databricks, or use `Big Data Analytics.py` as the notebook source.
3. Install the Kaggle package inside the notebook environment.
4. Configure Kaggle authentication securely in Databricks.
5. Create or reuse the Unity Catalog volume used for raw data storage.
6. Run the notebook cells in order from ingestion through model evaluation.
7. For the NoSQL section, install `pymongo` and `pandas`, set your MongoDB connection URI in `Upload_Data.py`, and run the script after preparing the sample CSV files in the `data/` folder.

## Notes

- The code is written for a Databricks notebook workflow rather than a standalone local Python application.
- Some sections convert Spark results to Pandas for plotting, so driver memory should be sized accordingly.
- Kaggle credentials should be handled securely and should not be committed directly into source files.
- The MongoDB upload script expects sample CSV files and a valid MongoDB URI; connection secrets should be provided securely and not committed to source control.

## Outcome

This project demonstrates an end-to-end big data analytics workflow for airline delay analysis, combining scalable PySpark processing in Databricks with optional MongoDB-based NoSQL storage for sampled flight records.
