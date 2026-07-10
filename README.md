# 🏎️ F1 Visual Analytics Dashboard

An interactive **Formula 1 Visual Analytics Dashboard** built using **Dash** and **Plotly**. The dashboard enables users to explore Formula 1 data through interactive visualizations covering championship evolution, driver performance, constructor analysis, circuit intelligence, race strategy, and qualifying insights.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Dash](https://img.shields.io/badge/Dash-4.3.0-red?logo=plotly)
![Plotly](https://img.shields.io/badge/Plotly-6.8.0-blueviolet)
![License](https://img.shields.io/badge/License-Educational-green)

---

# 📖 Overview

The **F1 Visual Analytics Dashboard** transforms Formula 1 race data into an interactive analytics platform.

Users can:

- 📊 Explore season-wise race statistics
- 🏆 Analyze championship standings
- 🏎 Compare driver performances
- 🏭 Study constructor evolution
- 🏁 Visualize circuit intelligence
- 📈 Understand race strategies
- ⚡ Compare qualifying and race performance

The dashboard is built with a modern Formula 1 inspired interface featuring responsive layouts, interactive filters, maps, and advanced visualizations.

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
- Leaderboards
- CSV Export

## 🏁 Circuit Intelligence
- Interactive World Map
- Circuit Rankings
- Performance Heatmap
- Bubble Analysis
- Dynamic Insights

## 📈 Race Strategy
- Pit Stop Analysis
- Constructor Consistency
- Grid to Finish Analysis
- Strategy Correlations

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

# 🚀 Installation

## 1. Clone the repository

```bash
git clone https://github.com/your-username/F1-Visual-Analytics-Dashboard.git
cd F1-Visual-Analytics-Dashboard
```

---

## 2. Install Dependencies

### Recommended (Windows)

Simply run

```bash
setup.bat
```

The setup script automatically:

- ✔ Checks Python installation
- ✔ Installs all required packages
- ✔ Verifies installation
- ✔ Prepares the dashboard for execution

---

### Manual Installation

```bash
pip install -r requirements.txt
```

---

# ▶️ Run the Dashboard

If you used the setup script

```bash
start.bat
```

or

```bash
python app.py
```

Open your browser and visit

```
http://127.0.0.1:8050
```

---

# 📂 Dataset

The dashboard uses a cleaned Formula 1 dataset.

Place the dataset inside

```
data/master_f1_final_dnf_fixed.csv
```

Dataset includes:

- Seasons (2019–2024)
- Drivers
- Constructors
- Circuits
- Race Results
- Championship Points
- Pit Stops
- Qualifying Results
- DNFs
- Fastest Laps

---

# 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| 📊 Overview | High-level dataset summary |
| 🏆 Championship | Championship standings and progression |
| 🏎 Driver Performance | Individual driver analysis |
| 🏭 Constructor Evolution | Team performance comparison |
| 🏁 Circuit Intelligence | Circuit analytics and insights |
| 📈 Race Strategy | Pit stop and strategy analysis |
| ⚡ Qualifying vs Race | Grid position vs finishing position |

---

# 📸 Screenshots

Add screenshots inside

```
assets/screenshots/
```

Example

```markdown
![Overview](assets/screenshots/overview.png)

![Championship](assets/screenshots/championship.png)

![Drivers](assets/screenshots/drivers.png)

![Constructors](assets/screenshots/constructors.png)

![Circuits](assets/screenshots/circuits.png)

![Race Strategy](assets/screenshots/strategy.png)

![Qualifying](assets/screenshots/qualifying.png)
```

---

# 📈 Visualizations Used

The dashboard combines multiple visualization techniques including:

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

# 🔮 Future Enhancements

- Driver Head-to-Head Comparison
- Tire Strategy Analysis
- Weather Impact Analysis
- Race Prediction Models
- Real-Time Formula 1 Data
- Export Dashboard Reports
- User Authentication
- Advanced Filtering

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
If you found this project useful, please consider giving it a ⭐ on GitHub.

It helps others discover the project and motivates future improvements.
