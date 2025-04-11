
# 🏥 Clinical Chart Builder

The **Clinical Chart Builder** is a Python-based web app that lets users generate interactive charts from OMOP CDM-formatted clinical data using natural language. It uses GPT-4o (via Azure OpenAI) to interpret user prompts and generate Python/Plotly code to create relevant visualizations.

This is built to prototype AI-assisted charting for clinical data teams using the OMOP CDM (Common Data Model).

## ⚙️ Features

- 🔍 Natural language to chart with GPT-4o
- 📊 Interactive visualizations with Plotly
- 🧠 Schema-aware prompting using real OMOP tables
- 🔌 Live demo on synthetic patient data from Synthea
- 🌐 Dash web app UI

## 📂 Files

- `clinical_chart_builder.py` — The main app file

## 🎮 How to Use It

1. **Setup**:
   - Ensure you have a `.env` file with your Azure OpenAI credentials (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `OPENAI_API_VERSION`, `DEPLOYMENT_NAME`).
   - Install required packages: `pip install dash dash-bootstrap-components pandas plotly openai python-dotenv`.

2. **Run the Script**:
   - Execute `python clinical_chart_builder.py` to start the Dash server. Open your browser to `http://127.0.0.1:8050/` to interact with the app.

## 🧠 Prompt Categories

### 📊 Population-Level Summaries
- Bar chart of the top 5 most common conditions
- Show the top 10 most common diagnoses
- Visualize the number of conditions by year
- Plot the distribution of visit start dates
- Bar chart of visit counts by state (joins visit + location)
- Bar chart of average age at death by gender
- Histogram of patient ages at visits

### 👤 Individual Patient Views
- Line chart of conditions over time for patient 785

### 🗺️ Geographic Distributions
- Scatter plot of visits by location

## 🗃️ Data Sources

Data sourced from **Janos Hajagos's SyntheaData520 repository**  
🔗 https://github.com/jhajagos/SyntheaData520

Synthetic OMOP CDM v5.3 data generated by **Synthea**  
🔗 https://synthea.mitre.org

## 📜 License
[MIT](LICENSE)
