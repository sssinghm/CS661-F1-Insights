# 🏎️ F1 Visual Analytics Dashboard

An interactive **Formula 1 analytics dashboard** built using **Dash** and **Plotly** to explore driver, constructor, circuit, championship, and race strategy data through rich interactive visualizations.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Dash](https://img.shields.io/badge/Dash-2.17-red)
![Plotly](https://img.shields.io/badge/Plotly-5.24-green)
![License](https://img.shields.io/badge/License-Educational-orange)

---

## 📌 Overview

The F1 Visual Analytics Dashboard transforms Formula 1 race data into an interactive exploration platform.

Users can analyze:

- 🏆 Championship standings
- 🏎️ Driver performance
- 🏭 Constructor evolution
- 🏁 Circuit intelligence
- 📈 Race strategies
- ⚡ Qualifying vs Race performance
- 📊 Season-level statistics

The dashboard features an F1-inspired modern interface with responsive visualizations and interactive filtering.

---

## ✨ Features

### 📊 Overview
- KPI Cards
- Season coverage
- Interactive world circuit map
- Constructor participation heatmap
- Race calendar
- Driver statistics table

### 🏆 Championship
- Top drivers
- Championship progression
- Historical champions
- Driver standings
- Team and season filters

### 🏎️ Driver Performance
- Driver comparison
- Performance KPIs
- Finish progression
- Radar chart
- Finish distribution

### 🏭 Constructor Evolution
- Constructor comparison
- Points progression
- DNF analysis
- Points share
- Leaderboards
- CSV Export

### 🏁 Circuit Intelligence
- Interactive circuit map
- Circuit rankings
- Performance heatmap
- Bubble analysis
- Dynamic insights

### 📈 Race Strategy
- Pit stop analysis
- Constructor consistency
- Strategy distribution
- Grid vs Finish movement
- Correlation analysis

### ⚡ Qualifying vs Race
- Grid vs Finish scatter plot
- Density heatmap
- Correlation matrix
- Performance KPIs

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Dash |
| Visualization | Plotly |
| Backend | Flask |
| Maps | Dash Leaflet |
| UI | Dash Bootstrap Components |
| Data Processing | Pandas, NumPy |
| Language | Python |

---

## 📂 Project Structure

```
F1-Visual-Analytics-Dashboard
│
├── app.py
├── requirements.txt
├── README.md
│
├── data
│   └── master_f1_final_dnf_fixed.csv
│
├── assets
│   └── style.css
│
└── pages
```

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/your-username/F1-Visual-Analytics-Dashboard.git
```

Move into the project

```bash
cd F1-Visual-Analytics-Dashboard
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the dashboard

```bash
python app.py
```

Open

```
http://127.0.0.1:8050
```

---

## 📁 Dataset

The dashboard uses a cleaned Formula 1 dataset containing:

- Seasons (2019–2024)
- Drivers
- Constructors
- Circuits
- Race Results
- Pit Stops
- Qualifying Results
- Championship Points

Place the dataset inside:

```
data/master_f1_final_dnf_fixed.csv
```

---

## 📸 Dashboard Preview

Add screenshots here.

```
assets/screenshots/
├── overview.png
├── championship.png
├── driver.png
├── constructor.png
├── circuit.png
├── strategy.png
└── qualifying.png
```

Example:

```markdown
![Overview](assets/screenshots/overview.png)
```

---

## 📈 Visualizations Used

- Bar Charts
- Line Charts
- Scatter Plots
- Heatmaps
- Radar Charts
- Box Plots
- Bubble Charts
- Donut Charts
- Interactive Maps
- Dumbbell Charts

---

## 🔮 Future Enhancements

- Driver head-to-head comparison
- Weather impact analysis
- Tire strategy visualization
- Race prediction
- Real-time F1 data
- Export reports
- User authentication

---

## 👥 Team

**Course:** CS661 – Visual Analytics

**Project:** F1 Visual Analytics Dashboard

---

## 📚 Acknowledgements

- Formula 1
- Plotly
- Dash
- Dash Leaflet
- OpenStreetMap
- Bootstrap
- Kaggle

---

## 📄 License

This project was developed for educational purposes as part of the **CS661 Visual Analytics** course.

---

# ⭐ If you found this project useful, consider giving it a star!
