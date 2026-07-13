# 🏎️ F1 Visual Analytics Dashboard

An interactive **Formula 1 Visual Analytics Dashboard** built with **Dash** and **Plotly** that transforms Formula 1 race data into insightful and interactive visualizations. The dashboard enables users to explore championship standings, driver and constructor performance, circuit intelligence, race strategies, and qualifying analysis through an intuitive web interface.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Dash](https://img.shields.io/badge/Dash-4.3.0-red?logo=plotly)
![Plotly](https://img.shields.io/badge/Plotly-6.8.0-blueviolet)
![Status](https://img.shields.io/badge/Status-Completed-success)

---

# 📖 Overview

The **F1 Visual Analytics Dashboard** provides an interactive platform for exploring Formula 1 data using modern visualization techniques.

The dashboard allows users to:

- 🏆 Analyze Championship Standings
- 🏎 Compare Driver Performance
- 🏭 Study Constructor Evolution
- 🏁 Explore Circuit Intelligence
- 📈 Analyze Race Strategies
- ⚡ Compare Qualifying and Race Performance
- 📊 Explore Season-wise Statistics

Built using **Dash**, **Plotly**, and **Dash Bootstrap Components**, the application features a responsive Formula 1-inspired interface with interactive filters, maps, and charts.

---

# ✨ Features

## 📊 Overview
- KPI Cards
- Season Coverage
- Interactive Circuit Map
- Constructor Participation Heatmap
- Race Calendar
- Driver Statistics Table

## 🏆 Championship Evolution
- Top Drivers
- Championship Progression
- Historical Champions
- Driver Standings
- Season Filters

## 🏎 Driver Performance
- Driver Comparison
- Performance KPIs
- Finish Position Timeline
- Radar Chart
- Finish Distribution

## 🏭 Constructor Evolution
- Constructor Comparison
- Points Progression
- DNF Analysis
- Constructor Leaderboards
- CSV Export

## 🏁 Circuit Intelligence
- Interactive Circuit Map
- Circuit Rankings
- Performance Heatmap
- Bubble Analysis
- Dynamic Insights

## 📈 Race Strategy
- Pit Stop Analysis
- Constructor Consistency
- Strategy Distribution
- Grid to Finish Analysis
- Correlation Heatmap

## ⚡ Qualifying vs Race
- Grid vs Finish Scatter Plot
- Density Heatmap
- Correlation Matrix
- Performance KPIs

---

# 🛠 Tech Stack

| Category | Technology |
|-----------|------------|
| Language | Python 3.13 |
| Framework | Dash |
| Visualization | Plotly |
| Backend | Flask |
| UI | Dash Bootstrap Components |
| Maps | Dash Leaflet |
| Data Processing | Pandas, NumPy |
| Styling | CSS |

---

# 📁 Project Structure

```text
F1-Visual-Analytics-Dashboard/
│
├── app.py
├── requirements.txt
├── README.md
├── setup.bat
├── start.bat
│
├── assets/
│   └── style.css
│
├── data/
│   └── master_f1_final_dnf_fixed.csv
│
├── pages/
│   ├── __init__.py
│   └── championship_evolution.py
│
└── src/
    ├── data_loader.py
    └── filter.py
```

---

# ⚡ Quick Start (for Windows)

Clone the repository

```bash
git clone https://github.com/sssinghm/CS661-F1-Insights.git F1-Visual-Analytics-Dashboard
cd F1-Visual-Analytics-Dashboard
```

Run the setup

```bash
setup.bat
```

Start the dashboard

```bash
start.bat
```

Open your browser

```
http://127.0.0.1:8050
```

---

# 🚀 Installation (for Windows)

## Step 1 — Clone the Repository

```bash
git clone https://github.com/sssinghm/CS661-F1-Insights.git F1-Visual-Analytics-Dashboard
cd F1-Visual-Analytics-Dashboard
```

---

## Step 2 — Run Setup

Before running the dashboard, execute:

```bash
setup.bat
```

The setup script automatically:

- ✔ Checks the installed Python version
- ✔ Installs NumPy
- ✔ Installs Pandas
- ✔ Installs Dash
- ✔ Installs Plotly
- ✔ Installs Dash Bootstrap Components
- ✔ Verifies the installation

After successful installation, you should see:

```text
✔ Dash installed!
✔ Plotly installed!
✔ Pandas installed!
✔ NumPy installed!
✔ Dash Bootstrap installed!

✔ Setup Complete!
```

> **Run `setup.bat` only once**, or whenever project dependencies are updated.

---

## Step 3 — Start the Dashboard

Once setup completes successfully, launch the dashboard by running:

```bash
start.bat
```

The application will start automatically.

Open your browser and navigate to

```
http://127.0.0.1:8050
```

---

# 📂 Dataset

Place the dataset inside the **data** folder.

```
data/
└── master_f1_final_dnf_fixed.csv
```

The dataset contains information about:

- Formula 1 Seasons
- Drivers
- Constructors
- Circuits
- Race Results
- Championship Points
- Pit Stops
- DNFs
- Fastest Laps
- Qualifying Results

---

# 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| 📊 Overview | Dataset summary and statistics |
| 🏆 Championship | Championship standings and progression |
| 🏎 Driver Performance | Driver comparison and performance analysis |
| 🏭 Constructor Evolution | Constructor comparison and historical trends |
| 🏁 Circuit Intelligence | Circuit analytics and interactive maps |
| 📈 Race Strategy | Strategy and pit stop analysis |
| ⚡ Qualifying vs Race | Qualifying vs finishing position analysis |

---
# 📦 Project Resources

The complete project package, including the source code, dataset is available on Google Drive.

📁 **Google Drive Download**

https://drive.google.com/file/d/1gGgVZrWXTU8aY6bOJCwjSZn2G129OLve/view?usp=sharing

The drive contains:

- Complete Source Code
- Formula 1 Dataset
- Presentation
- Report
---
# 📈 Visualizations Used

The dashboard combines several visualization techniques:

- 📊 Bar Charts
- 📈 Line Charts
- 🎯 Scatter Plots
- 🔥 Heatmaps
- 🕸 Radar Charts
- 📦 Box Plots
- 🫧 Bubble Charts
- 🍩 Donut Charts
- 🌍 Interactive Maps
- ↔ Dumbbell Charts

---

# 👨‍💻 Team

**Course:** CS661 – Visual Analytics

**Project:** F1 Visual Analytics Dashboard

---

# 🙏 Acknowledgements

- Formula 1
- Plotly
- Dash
- Dash Bootstrap Components
- Dash Leaflet
- OpenStreetMap
- Kaggle Formula 1 Dataset

---
