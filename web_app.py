import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import json
import uuid
from datetime import datetime
import sqlite3
import os
import threading
from threading import Thread
import queue
import time
import base64
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="dash")

# Import your existing system
from logger import setup_logger
from langchain_core.messages import HumanMessage
from core.workflow import Workflow
from core.llm import LLM
import dotenv

dotenv.load_dotenv()

# Prevent multiple initializations in development
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('FLASK_ENV') == 'development':
    # Only initialize once
    pass

class QueryDatabase:
    """Simple SQLite database to store query history"""
    
    def __init__(self, db_path="query_history.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                query TEXT,
                status TEXT,
                result_data TEXT,
                visualization_data TEXT,
                report TEXT,
                error_message TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_query(self, query_id, query, status, result_data=None, 
                   visualization_data=None, report=None, error_message=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO queries 
            (id, timestamp, query, status, result_data, visualization_data, report, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (query_id, datetime.now().isoformat(), query, status, 
              json.dumps(result_data) if result_data else None,
              json.dumps(visualization_data) if visualization_data else None,
              report, error_message))
        conn.commit()
        conn.close()
    
    def get_all_queries(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, query, status, result_data, visualization_data, report, error_message
            FROM queries ORDER BY timestamp DESC
        ''')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_query(self, query_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, query, status, result_data, visualization_data, report, error_message
            FROM queries WHERE id = ?
        ''', (query_id,))
        result = cursor.fetchone()
        conn.close()
        return result

class DataAnalyticsPortalWeb:
    """Web interface wrapper for the DataAnalyticsPortal"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.llm = LLM()
        self.workflow = Workflow(llms=self.llm.get_models())
        self.db = QueryDatabase()
        self.running_queries = {}
        
    def run_query_async(self, query_id, user_input, result_queue):
        """Run query asynchronously and put result in queue"""
        try:
            self.db.save_query(query_id, user_input, "running")
            
            graph = self.workflow.get_graph()
            events = graph.stream(
                {
                    "messages": [HumanMessage(content=user_input)],
                    "process_state": "",
                    "process_decision": "",
                    "query_state": "",
                    "retrieval_state": "",
                    "api_state": "",
                    "analysis_state": "",
                    "visualization_state": "",
                    "report_state": "",
                    "sender": "",
                },
                {"configurable": {"thread_id": query_id}, "recursion_limit": 30},
                stream_mode="values",
                debug=False
            )
            
            final_state = None
            for event in events:
                final_state = event
            
            # Extract results from final state
            result_data = None
            visualization_data = None
            report = None
            
            if final_state:
                # Extract API data
                if final_state.get("api_state"):
                    try:
                        api_content = final_state["api_state"].content
                        if api_content.startswith("compact_json:"):
                            json_str = api_content.replace("compact_json:", "").strip()
                            result_data = json.loads(json_str)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse API state: {e}")
                
                # Extract visualization data
                if final_state.get("visualization_state"):
                    try:
                        viz_content = final_state["visualization_state"].content
                        if viz_content:
                            visualization_data = json.loads(viz_content)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse visualization state: {e}")
                
                # Extract report
                if final_state.get("report_state"):
                    try:
                        report_content = final_state["report_state"].content
                        if isinstance(report_content, str):
                            # Try to parse as JSON first, fall back to raw string
                            try:
                                report_data = json.loads(report_content)
                                report = report_data.get("report", report_content)
                            except json.JSONDecodeError:
                                report = report_content
                        else:
                            report = str(report_content)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse report state: {e}")
                        if final_state.get("report_state"):
                            report = str(final_state["report_state"].content)
            
            self.db.save_query(query_id, user_input, "completed", 
                            result_data, visualization_data, report)
            
            result_queue.put({
                "status": "completed",
                "result_data": result_data,
                "visualization_data": visualization_data,
                "report": report
            })
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Query execution failed: {error_msg}")
            self.db.save_query(query_id, user_input, "error", error_message=error_msg)
            result_queue.put({"status": "error", "error": error_msg})
    
    def start_query(self, user_input):
        """Start a new query and return query ID"""
        query_id = str(uuid.uuid4())
        result_queue = queue.Queue()
        self.running_queries[query_id] = result_queue
        
        thread = Thread(target=self.run_query_async, 
                       args=(query_id, user_input, result_queue))
        thread.daemon = True
        thread.start()
        
        return query_id
    
    def get_query_status(self, query_id):
        """Get current status of a query"""
        if query_id in self.running_queries:
            try:
                result = self.running_queries[query_id].get_nowait()
                del self.running_queries[query_id]
                return result
            except queue.Empty:
                return {"status": "running"}
        
        # Check database for completed queries
        query_data = self.db.get_query(query_id)
        if query_data:
            _, timestamp, query, status, result_data, visualization_data, report, error_message = query_data
            
            # Parse JSON data safely
            parsed_result_data = None
            parsed_viz_data = None
            
            if result_data:
                try:
                    parsed_result_data = json.loads(result_data)
                except (json.JSONDecodeError, TypeError):
                    self.logger.warning(f"Failed to parse result_data for query {query_id}")
            
            if visualization_data:
                try:
                    parsed_viz_data = json.loads(visualization_data)
                except (json.JSONDecodeError, TypeError):
                    self.logger.warning(f"Failed to parse visualization_data for query {query_id}")
            
            return {
                "status": status,
                "result_data": parsed_result_data,
                "visualization_data": parsed_viz_data,
                "report": report,
                "error": error_message
            }
        
        return {"status": "not_found"}

# Initialize the portal
_portal_instance = None
_portal_lock = threading.Lock()

def get_portal():
    global _portal_instance
    if _portal_instance is None:
        with _portal_lock:
            if _portal_instance is None:
                print("Initializing portal instance...")
                _portal_instance = DataAnalyticsPortalWeb()
                print("Portal instance initialized successfully")
    return _portal_instance

# Custom CSS styles
external_stylesheets = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
]

# Initialize Dash app with custom styling
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define color scheme
colors = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'light': '#ecf0f1',
    'dark': '#34495e',
    'white': '#ffffff',
    'gray': '#7f8c8d'
}

# Custom styles
styles = {
    'container': {
        'fontFamily': 'Inter, sans-serif',
        'backgroundColor': '#f8f9fa',
        'minHeight': '100vh',
        'margin': '0',
        'padding': '0'
    },
    'header': {
        'backgroundColor': colors['primary'],
        'color': colors['white'],
        'padding': '20px',
        'marginBottom': '0',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    },
    'main_content': {
        'padding': '30px',
        'display': 'flex',
        'gap': '30px',
        'maxWidth': '1400px',
        'margin': '0 auto'
    },
    'left_panel': {
        'flex': '1',
        'minWidth': '400px'
    },
    'right_panel': {
        'flex': '2',
        'minWidth': '600px'
    },
    'card': {
        'backgroundColor': colors['white'],
        'borderRadius': '10px',
        'padding': '25px',
        'marginBottom': '20px',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
        'border': '1px solid #e9ecef'
    },
    'button_primary': {
        'backgroundColor': colors['secondary'],
        'color': colors['white'],
        'border': 'none',
        'padding': '12px 24px',
        'borderRadius': '6px',
        'cursor': 'pointer',
        'fontSize': '14px',
        'fontWeight': '500',
        'transition': 'all 0.3s ease',
        'width': '100%'
    },
    'textarea': {
        'width': '100%',
        'height': '120px',
        'padding': '12px',
        'border': '2px solid #e9ecef',
        'borderRadius': '6px',
        'fontSize': '14px',
        'fontFamily': 'Inter, sans-serif',
        'resize': 'vertical',
        'transition': 'border-color 0.3s ease'
    },
    'history_item': {
        'padding': '15px',
        'borderBottom': '1px solid #e9ecef',
        'cursor': 'pointer',
        'transition': 'background-color 0.3s ease',
        'borderRadius': '6px',
        'marginBottom': '8px'
    },
    'status_running': {
        'color': colors['warning'],
        'fontSize': '16px',
        'fontWeight': '500',
        'padding': '15px',
        'backgroundColor': '#fff3cd',
        'border': '1px solid #ffeaa7',
        'borderRadius': '6px'
    },
    'status_completed': {
        'color': colors['success'],
        'fontSize': '16px',
        'fontWeight': '500',
        'padding': '15px',
        'backgroundColor': '#d1eddb',
        'border': '1px solid #a3cfbb',
        'borderRadius': '6px'
    },
    'status_error': {
        'color': colors['danger'],
        'fontSize': '16px',
        'fontWeight': '500',
        'padding': '15px',
        'backgroundColor': '#f8d7da',
        'border': '1px solid #f1aeb5',
        'borderRadius': '6px'
    }
}

app.layout = html.Div([
    dcc.Store(id='current-query-id'),
    dcc.Store(id='selected-query-data'),
    dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    
    # Header
    html.Div([
        html.Div([
            html.H1([
                html.I(className="fas fa-bolt", style={'marginRight': '15px'}),
                "EPİAŞ Data Analytics Portal"
            ], style={'margin': '0', 'fontSize': '28px', 'fontWeight': '600'}),
            html.P("AI-Powered Electricity Market Data Analysis", 
                   style={'margin': '8px 0 0 0', 'fontSize': '16px', 'opacity': '0.9'})
        ], style={'maxWidth': '1400px', 'margin': '0 auto'})
    ], style=styles['header']),
    
    # Main content
    html.Div([
        # Left panel - Query input and history
        html.Div([
            # Query input section
            html.Div([
                html.H3([
                    html.I(className="fas fa-search", style={'marginRight': '10px', 'color': colors['secondary']}),
                    "New Query"
                ], style={'color': colors['dark'], 'marginBottom': '20px', 'fontSize': '20px'}),
                
                dcc.Textarea(
                    id='query-input',
                    placeholder='Enter your query..."',
                    style=styles['textarea']
                ),
                
                html.Button([
                    html.I(className="fas fa-play", style={'marginRight': '8px'}),
                    'Run Query'
                ], id='run-query-btn', style=styles['button_primary'])
                
            ], style=styles['card']),
            
            # Query history section
            html.Div([
                html.H3([
                    html.I(className="fas fa-history", style={'marginRight': '10px', 'color': colors['secondary']}),
                    "Query History"
                ], style={'color': colors['dark'], 'marginBottom': '20px', 'fontSize': '20px'}),
                html.Div(id='query-history')
            ], style=styles['card'])
            
        ], style=styles['left_panel']),
        
        # Right panel - Results
        html.Div([
            # Status section
            html.Div(id='query-status', style={'marginBottom': '20px'}),
            
            # Results section
            html.Div([
                dcc.Tabs(
                    id='result-tabs', 
                    value='data-tab',
                    style={'marginBottom': '20px'},
                    children=[
                        dcc.Tab(
                            label='Data',
                            value='data-tab',
                            style={'padding': '12px 20px', 'fontWeight': '500'},
                            children=[html.I(className="fas fa-table", style={'marginRight': '8px'}), 'Data']
                        ),
                        dcc.Tab(
                            label='Visualization',
                            value='viz-tab',
                            style={'padding': '12px 20px', 'fontWeight': '500'},
                            children=[html.I(className="fas fa-chart-line", style={'marginRight': '8px'}), 'Visualization']
                        ),
                        dcc.Tab(
                            label='Report',
                            value='report-tab',
                            style={'padding': '12px 20px', 'fontWeight': '500'},
                            children=[html.I(className="fas fa-file-alt", style={'marginRight': '8px'}), 'Report']
                        )
                    ]
                ),
                
                # Tab content
                html.Div(id='tab-content', style=styles['card'])
                
            ], style={'backgroundColor': colors['white'], 'borderRadius': '10px', 
                     'boxShadow': '0 4px 6px rgba(0,0,0,0.07)', 'border': '1px solid #e9ecef'})
            
        ], style=styles['right_panel'])
        
    ], style=styles['main_content'])
    
], style=styles['container'])

@app.callback(
    [Output('current-query-id', 'data'),
     Output('query-status', 'children'),
     Output('query-input', 'value')],
    [Input('run-query-btn', 'n_clicks')],
    [State('query-input', 'value')]
)
def run_new_query(n_clicks, query_text):
    if n_clicks and query_text and query_text.strip():
        query_id = get_portal().start_query(query_text.strip())
        status = html.Div([
            html.I(className="fas fa-spinner fa-spin", style={'marginRight': '10px'}),
            "Processing your query..."
        ], style=styles['status_running'])
        return query_id, status, ""  # Clear the textarea
    return dash.no_update, "", dash.no_update

@app.callback(
    [Output('query-status', 'children', allow_duplicate=True),
     Output('selected-query-data', 'data')],
    [Input('interval-component', 'n_intervals')],
    [State('current-query-id', 'data')],
    prevent_initial_call=True
)
def update_query_status(n_intervals, current_query_id):
    if not current_query_id:
        return dash.no_update, dash.no_update
    
    status_data = get_portal().get_query_status(current_query_id)
    
    if status_data["status"] == "running":
        status = html.Div([
            html.I(className="fas fa-spinner fa-spin", style={'marginRight': '10px'}),
            "Processing query... This may take a few moments."
        ], style=styles['status_running'])
        return status, dash.no_update
    elif status_data["status"] == "completed":
        status = html.Div([
            html.I(className="fas fa-check-circle", style={'marginRight': '10px'}),
            "Query completed successfully!"
        ], style=styles['status_completed'])
        return status, status_data
    elif status_data["status"] == "error":
        status = html.Div([
            html.I(className="fas fa-exclamation-triangle", style={'marginRight': '10px'}),
            f"Error: {status_data.get('error', 'Unknown error occurred')}"
        ], style=styles['status_error'])
        return status, dash.no_update
    
    return dash.no_update, dash.no_update

@app.callback(
    Output('query-history', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_query_history(n_intervals):
    queries = get_portal().db.get_all_queries()
    
    if not queries:
        return html.Div([
            html.I(className="fas fa-info-circle", style={'marginRight': '10px', 'color': colors['gray']}),
            "No queries yet. Start by entering a query above."
        ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '20px'})
    
    history_items = []
    for query_data in queries[:15]:  # Show last 15 queries
        query_id, timestamp, query, status, _, _, _, _ = query_data
        
        # Format timestamp
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%H:%M")
        date_str = dt.strftime("%m/%d")
        
        # Status icon and color
        if status == "completed":
            icon = html.I(className="fas fa-check-circle", style={'color': colors['success']})
        elif status == "running":
            icon = html.I(className="fas fa-spinner fa-spin", style={'color': colors['warning']})
        else:
            icon = html.I(className="fas fa-exclamation-triangle", style={'color': colors['danger']})
        
        item_style = dict(styles['history_item'])
        item_style.update({
            'backgroundColor': colors['white'] if status != "running" else '#fff3cd'
        })
        
        history_items.append(
            html.Div([
                html.Div([
                    icon,
                    html.Span(f" {date_str} {time_str}", 
                             style={'fontSize': '12px', 'color': colors['gray'], 'marginLeft': '8px'})
                ], style={'marginBottom': '8px'}),
                
                html.Div(
                    query[:80] + "..." if len(query) > 80 else query,
                    style={'color': colors['dark'], 'lineHeight': '1.4', 'fontSize': '14px'}
                )
            ], 
            style=item_style,
            id={'type': 'history-item', 'index': query_id},
            className='history-item'
            )
        )
    
    return history_items

@app.callback(
    Output('selected-query-data', 'data', allow_duplicate=True),
    [Input({'type': 'history-item', 'index': dash.dependencies.ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def select_historical_query(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return dash.no_update
    
    # Get the clicked item's query_id
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    query_id = json.loads(button_id)['index']
    
    # Get query data from database
    status_data = get_portal().get_query_status(query_id)
    return status_data

@app.callback(
    Output('tab-content', 'children'),
    [Input('result-tabs', 'value'),
     Input('selected-query-data', 'data')]
)
def update_tab_content(active_tab, query_data):
    if not query_data or query_data.get("status") != "completed":
        return html.Div([
            html.I(className="fas fa-info-circle", style={'marginRight': '10px', 'color': colors['gray']}),
            "No data available. Run a query to see results here."
        ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '40px'})
    
    if active_tab == 'data-tab':
        return render_data_tab(query_data.get("result_data"))
    elif active_tab == 'viz-tab':
        return render_visualization_tab(query_data.get("visualization_data"))
    elif active_tab == 'report-tab':
        return render_report_tab(query_data.get("report"))
    
    return html.Div()

def render_data_tab(result_data):
    if not result_data or "items" not in result_data:
        return html.Div([
            html.I(className="fas fa-exclamation-circle", style={'marginRight': '10px', 'color': colors['warning']}),
            "No data available"
        ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '40px'})
    
    items = result_data["items"]
    if not items:
        return html.Div([
            html.I(className="fas fa-search", style={'marginRight': '10px', 'color': colors['gray']}),
            "No records found for this query"
        ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '40px'})
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(items)
    
    # Create data table with improved styling
    return html.Div([
        html.Div([
            html.H4([
                html.I(className="fas fa-table", style={'marginRight': '10px', 'color': colors['secondary']}),
                f"Data Results ({len(items)} records)"
            ], style={'color': colors['dark'], 'marginBottom': '20px'}),
            
            dash_table.DataTable(
                data=[{str(k): v for k, v in row.items()} for row in df.to_dict('records')],
                persistence=True,
                columns=[{"name": i, "id": i} for i in df.columns],
                page_size=20,
                style_table={
                    'overflowX': 'auto',
                    'border': '1px solid #e9ecef',
                    'borderRadius': '6px'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'fontFamily': 'Inter, sans-serif',
                    'fontSize': '13px',
                    'border': '1px solid #e9ecef'
                },
                style_header={
                    'backgroundColor': colors['secondary'],
                    'color': 'white',
                    'fontWeight': '600',
                    'textAlign': 'left'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#f8f9fa'
                    }
                ]
            )
        ])
    ])

def render_visualization_tab(visualization_data):
    if not visualization_data:
        return html.Div([
            html.I(className="fas fa-chart-line", style={'marginRight': '10px', 'color': colors['warning']}),
            "No visualization data available"
        ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '40px'})
    
    # Check if visualization_data contains file paths
    if isinstance(visualization_data, dict) and "visualizations" in visualization_data:
        visualizations = visualization_data["visualizations"]
        if isinstance(visualizations, list):
            viz_components = []
            
            for i, viz in enumerate(visualizations):
                if isinstance(viz, dict) and "file" in viz:
                    file_path = viz["file"]
                    description = viz.get("description", f"Visualization {i+1}")
                    
                    # Check if file exists and create image component
                    if os.path.exists(file_path):
                        # Read the image and encode it for display
                        with open(file_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode()
                        
                        viz_components.append(
                            html.Div([
                                html.H5(description, style={'color': colors['dark'], 'marginBottom': '10px'}),
                                html.Img(
                                    src=f"data:image/png;base64,{encoded_string}",
                                    style={'maxWidth': '100%', 'height': 'auto', 'marginBottom': '20px'}
                                )
                            ])
                        )
                    else:
                        viz_components.append(
                            html.Div([
                                html.P(f"Visualization file not found: {file_path}", 
                                       style={'color': colors['danger']})
                            ])
                        )
            
            if viz_components:
                return html.Div([
                    html.H4([
                        html.I(className="fas fa-chart-line", style={'marginRight': '10px', 'color': colors['secondary']}),
                        "Data Visualizations"
                    ], style={'color': colors['dark'], 'marginBottom': '25px'}),
                    html.Div(viz_components)
                ])
    
    return html.Div([
        html.I(className="fas fa-info-circle", style={'marginRight': '10px', 'color': colors['gray']}),
        "No suitable visualization found for this data type"
    ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '40px'})

def render_report_tab(report):
    if not report:
        return html.Div([
            html.I(className="fas fa-file-alt", style={'marginRight': '10px', 'color': colors['gray']}),
            "No report available for this query"
        ], style={'textAlign': 'center', 'color': colors['gray'], 'padding': '40px'})
    
    return html.Div([
        html.H4([
            html.I(className="fas fa-file-alt", style={'marginRight': '10px', 'color': colors['secondary']}),
            "Analysis Report"
        ], style={'color': colors['dark'], 'marginBottom': '20px'}),
        
        html.Div(
            report, 
            style={
                'padding': '25px',
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #e9ecef',
                'borderRadius': '8px',
                'whiteSpace': 'pre-wrap',
                'lineHeight': '1.6',
                'fontSize': '14px',
                'color': colors['dark']
            }
        )
    ])

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .history-item:hover {
                background-color: #e3f2fd !important;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table {
                border-collapse: separate;
                border-spacing: 0;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:first-child {
                border-top-left-radius: 6px;
            }
            
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:last-child {
                border-top-right-radius: 6px;
            }
            
            .tab-content {
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .fa-spin {
                animation: fa-spin 1s infinite linear;
            }
            
            @keyframes fa-spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    print("=== EPİAŞ Data Analytics Portal ===")
    print("Starting web interface...")
    print("Open your browser and go to: http://localhost:8050")
    print("Press Ctrl+C to stop the server")
    app.run(debug=False, host='0.0.0.0', port=8050)