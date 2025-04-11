import os
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import html, dcc, Input, Output, State, exceptions
from openai import AzureOpenAI
import re
from dotenv import load_dotenv

load_dotenv()

# ==============================
# Load CSV Files into DataFrames
# ==============================
csv_urls = {
    'person': 'https://raw.githubusercontent.com/jhajagos/SyntheaData520/main/person.csv',
    'death': 'https://raw.githubusercontent.com/jhajagos/SyntheaData520/main/death.csv',
    'visit_occurrence': 'https://raw.githubusercontent.com/jhajagos/SyntheaData520/main/visit_occurrence.csv',
    'concept': 'https://raw.githubusercontent.com/jhajagos/SyntheaData520/main/concept.csv',
    'condition_occurrence': 'https://raw.githubusercontent.com/jhajagos/SyntheaData520/main/condition_occurrence.csv',
    'location': 'https://raw.githubusercontent.com/jhajagos/SyntheaData520/main/location.csv'
}

# Load DataFrames globally for use in callbacks
dataframes = {key: pd.read_csv(url) for key, url in csv_urls.items()}

# ==============================
# Azure OpenAI Configuration
# ==============================
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION")
)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define app layout
app.layout = html.Div([
    html.H2("Clinical Chart Builder", style={'textAlign': 'center'}),
    dcc.Textarea(
        id='prompt',
        placeholder='Ask for a chart (e.g., "Bar chart of average age at death by gender" or "Bar chart of visit counts by state")',
        style={'width': '100%', 'height': 100}
    ),
    html.Button('Generate Chart', id='submit', n_clicks=0, className='btn btn-primary'),
    dcc.Loading(id="loading", type="circle", children=dcc.Graph(id='output-chart')),
    html.Div(id='feedback', style={'marginTop': 10}),
    html.Div(
        id='error',
        style={'color': 'red', 'marginTop': 10, 'padding': 10, 'border': '1px solid #ffcccc', 'borderRadius': 5}
    ),
    html.Button('Retry', id='retry', n_clicks=0, className='btn btn-secondary',
                style={'display': 'none', 'marginTop': 10}),
], style={'maxWidth': '800px', 'margin': 'auto', 'padding': 20})


@app.callback(
    [
        Output('output-chart', 'figure'),
        Output('error', 'children'),
        Output('feedback', 'children'),
        Output('retry', 'style')
    ],
    [
        Input('submit', 'n_clicks'),
        Input('retry', 'n_clicks')
    ],
    [State('prompt', 'value')],
    prevent_initial_call=True
)
def generate_chart(submit_clicks, retry_clicks, prompt):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise exceptions.PreventUpdate

    # Clear previous chart and error
    fig = {}
    error_msg = ""
    feedback = ""

    # Check if prompt is empty or just whitespace
    if not prompt or not prompt.strip():
        return fig, "Error: Please enter a prompt.", feedback, {'display': 'none'}

    # Provide initial feedback
    feedback = "Generating chart... This may take a moment."
    retry_style = {'display': 'none'}

    try:
        # Call Azure OpenAI Chat Completion
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python developer tasked with generating only Plotly Express code for clinical data in the OMOP Common Data Model format. "
                        "The data is pre-loaded in pandas DataFrames named: 'person', 'death', 'visit_occurrence', 'concept', 'condition_occurrence', and 'location'. "
                        "Do NOT use pd.read_csv or attempt to load data from files; use the existing DataFrames directly. "

                        "Table relationships:\n"
                        "- person joins to death on person_id\n"
                        "- person joins to visit_occurrence on person_id\n"
                        "- person joins to condition_occurrence on person_id\n"
                        "- condition_occurrence joins to concept on condition_concept_id\n"
                        "- visit_occurrence joins to concept on visit_concept_id\n"
                        "- condition_occurrence joins to visit_occurrence on visit_occurrence_id\n"

                        "Concept table is used to decode concept_id fields into concept_name values.\n"

                        "Column caveats:\n"
                        "- location has: location_id, address_1, address_2, city, state, zip, county, location_source_value\n"
                        "- location does NOT have latitude or longitude.\n"
                        "- visit_occurrence has care_site_id, but care_site is not available; skip joins to it.\n"
                        "- Some columns like location_id, latitude may be missing — use alternatives like state, zip, or plot empty chart if needed.\n"

                        "Your response must contain ONLY the Python code — no explanations, no markdown, no comments.\n"
                        "Always include required imports (e.g., import plotly.express as px, import pandas as pd).\n"
                        # "Assign the final chart to a variable named 'fig'. Do NOT use fig.show() or display().\n"
                        "Always include the data date or range in the chart title if dates are involved.\n"
                        "When converting dates, use pd.to_datetime(..., utc=False) or .dt.tz_localize(None) to remove timezones.\n"
                        "If no rows match the query after filtering, return an empty chart like px.bar(title='No data found')."
                    )

                },
                {
                    "role": "user",
                    "content": (
                        f"Generate only the Plotly Express Python code for: {prompt}. "
                        "Use the pre-loaded pandas DataFrames: person, death, visit_occurrence, concept, condition_occurrence, location as needed."
                    )
                }
            ],
            model=os.getenv("DEPLOYMENT_NAME"),
            max_tokens=1000,  # Increased to handle complex joins and queries
            temperature=0.2,
            top_p=0.1
        )

        # Extract the generated code
        code = response.choices[0].message.content.strip()
        code = re.sub(r"```(?:python)?|```", "", code).strip()

        # Remove specific unwanted lines or text
        unwanted_lines = [
            "YF.download() has changed argument auto_adjust default to True",
            "[*********************100%***********************]  1 of 1 completed"
        ]
        for unwanted in unwanted_lines:
            code = code.replace(unwanted, "")

        # Filter out lines that start with unwanted keywords
        unwanted_starts = ['here is', 'below is', 'the code', 'this code', 'note:']
        code_lines = [
            line for line in code.split('\n')
            if not any(line.lower().startswith(start.lower()) for start in unwanted_starts)
            and line.strip()
        ]
        code = '\n'.join(code_lines)

        # print("Generated code:\n", code)

        # Ensure there's still some code left
        if not code:
            raise ValueError("No valid code remaining after filtering.")

        # Execute the code with access to DataFrames
        local_vars = {
            'px': px,
            'pd': pd,
            'person': dataframes['person'],
            'death': dataframes['death'],
            'visit_occurrence': dataframes['visit_occurrence'],
            'concept': dataframes['concept'],
            'condition_occurrence': dataframes['condition_occurrence'],
            'location': dataframes['location']
        }
        exec(code, {}, local_vars)

        if 'fig' not in local_vars or local_vars['fig'] is None:
            raise ValueError("Failed to generate a valid Plotly figure. The figure object is None.")

        # Return the new figure (error/feedback cleared)
        return local_vars['fig'], "", "", {'display': 'none'}

    except Exception as e:
        error_msg = "Error: An issue occurred while generating the chart. "

        if "API" in str(e) or "OpenAI" in str(e):
            error_msg += "Please check your API key or network connection."
        elif "invalid syntax" in str(e) or "NameError" in str(e):
            error_msg += "The AI generated invalid code. Please refine your prompt and try again."
        elif "unexpected text" in str(e):
            error_msg += "The AI included extra text instead of just code. Please try again or adjust the prompt."
        elif "No valid code" in str(e) or "Failed to generate a valid Plotly figure" in str(e):
            error_msg += (
                "The chart could not be created. Check if the data or prompt is valid, "
                "or try a different chart type."
            )
        else:
            error_msg += (
                f"Unexpected error: {str(e)}. "
                "Please try a different prompt or contact support."
            )

        print("Error:", e)
        return {}, error_msg, "", {'display': 'block'}


if __name__ == '__main__':
    app.run(debug=True)
