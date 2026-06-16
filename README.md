# India Air Quality Intelligence Platform

An analytical environmental intelligence platform that tracks and visualizes air quality trends in major Indian cities from 2015 to 2020. This platform is designed to make complex air pollution data accessible, offering insights into geographic disparities, seasonal trends, and hyperlocal differences.

## Live Application

An interactive version of this platform is deployed here:
 **[Streamlit Cloud Demo Link](https://bhuvan-desai-india-air-quality-data-analysis.streamlit.app/)** 

## Features

- **National Overview**: National air quality briefing demonstrating comparative exposure across major cities.
- **Geographic Disparities**: Interactive location maps and multi-year trend trackers.
- **Specific Pollutant Profiles**: Detailed breakdown of chemical agents (PM2.5, PM10, NO2, etc.) compared against WHO and CPCB safety standards.
- **Seasonal & Lockdown Dynamics**: Interactive tools showing winter weather inversions and the drop in pollution during the 2020 COVID lockdowns.
- **Health Risk Assessments**: Data-dense exposure metrics showing the yearly impact of air pollution on daily life.
- **Hyperlocal Analysis (Bangalore)**: Deep dive into street-level neighborhood sensors (Silk Board, Peenya, BTM Layout, etc.) to highlight local outliers.

## Getting Started

### Prerequisites

You need Python 3.8 or higher installed on your system.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the Streamlit dashboard locally:
```bash
streamlit run app.py
```

Open your browser and navigate to `http://localhost:8501`.

## Data Pipeline

If you need to reprocess the datasets, place the raw CSV files (`city_day.csv`, `station_day.csv`, and `stations.csv`) from the Kaggle dataset in `data/raw/` and run:

```bash
python notebooks/01_data_pipeline.py
```

This cleans and converts the raw data to compressed Parquet files under `data/processed/` for faster loading times.

