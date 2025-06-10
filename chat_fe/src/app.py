#Base Imports
import sys
import os
import json
import re
import pandas as pd
#Dash Imports
from dash import Dash,_dash_renderer,html, dcc, Output, Input, State,dash_table
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

#Local Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from components.SideBar import SideBar
from components.ChatBox import ChatBox
from components.InputBox import InputBox

#Custom Imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
_dash_renderer._set_react_version("18.2.0")

app = Dash(__name__,external_stylesheets=[dmc.styles.ALL,dbc.themes.SANDSTONE,dbc_css],
           prevent_initial_callbacks="initial_duplicate")

server = app.server
app.title = 'Multi Agent Analytics Portal'
app.layout = dmc.MantineProvider(
    theme={"fontFamily": 'Montserrat',},
    children = [
        dcc.Store(id='chat-history', data=[]),
        dcc.Interval(id='check-messages', interval=1000, n_intervals=0,disabled=True),
        html.Div(
            children = [
                dmc.Grid(
                    children=[
                        dmc.GridCol(html.Div(
                            SideBar(), 
                        ), span=2),

                        dmc.GridCol(html.Div(
                            ChatBox(),
                        ), span=10),
                    ],
                )
            ],
            style={
                "overflow-y": "hidden",
                "overflow-x": "hidden",
                "backgroundColor": "#394652fd"
            }
        )
    ])

@app.callback(
    Output('chat-history', 'data', allow_duplicate=True),
    Output('input-msg', 'value'),
    Output('check-messages', 'disabled'),
    Input('send-btn', 'n_clicks'),
    State('input-msg', 'value'),
    State('chat-history', 'data'),
    prevent_initial_call=True
)
def update_history(n, new_msg, history):
    if not new_msg:
        return history
    # Kullanıcı mesajı
    history = [{'sender': 'user', 'text': new_msg,'type':'string'}] + history
    return history,"", False

@app.callback(
    Output('chat-history', 'data'),
    Input('check-messages', 'n_intervals'),
    State('chat-history', 'data')
)

def check_messages(n_intervals, history):
    if n_intervals:
        try:
            with open('chat_fe/src/messages.json', 'r') as f:
                messages = json.load(f)
        except:
            messages = []

        for msg in messages:
            if msg["type"] == "AIMessage":
                if msg["value"]["name"] == "api_agent":
                    # if message is not in history
                    chat_msg = [{'sender': 'agent', 'text': msg["value"]["content"],'type':'data'}]
                    #if chat_msg  is not added to history
                    if chat_msg[0] not in history:
                        history = chat_msg + history
                elif msg["value"]["name"] == "process_agent":
                    # if message is not in history
                    msg_text = msg["value"]["content"]
                    msg_text = msg_text.replace("'", '"')
                    msg_text = re.sub(r'(\w+):', r'"\1":', msg_text)
                    msg_json = json.loads(msg_text)
                    chat_msg = [{'sender': 'agent', 'text': msg_json["task"],'type':'string'}]
                    #if chat_msg  is not added to history
                    if chat_msg[0] not in history:
                        history = chat_msg + history
                    
        return history
        # clear messages.json
        

    return history


@app.callback(
    Output('chat-window', 'children'),
    Input('chat-history', 'data')
)
def render_chat(history):
    elems = []
    for msg in history:
        if msg['type'] == 'data':
            plain_json = msg['text']
            plain_json = re.sub(r'^```json\s*|\s*```$', '', plain_json, flags=re.MULTILINE)
            data = json.loads(plain_json)
            data = data["response"]["items"]
            df = pd.DataFrame(data)
            #create a table
            table = dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={
                    'backgroundColor': '#f1f1f1',
                    'fontWeight': 'bold'
                },
                page_size=10,
            )
            # Card style
            card_style = {
                'padding': '10px',
                'margin': '10px 0',
                'maxWidth': '80%',
                'borderRadius': '8px',
                'backgroundColor': '#f8f9fa',
                'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
                'overflowX': 'auto'
            }

            
            elems.append(
                html.Div([
                    table
                ], style=card_style)
            )
        
        elif msg['type'] == 'string':
            is_user = msg['sender'] == 'user'
            # Balon stili
            bubble_style = {
                'padding':'8px 12px','borderRadius':'12px','margin':'4px 0',
                'maxWidth':'10em','display':'flex','alignItems':'center',
                'alignSelf': 'flex-end' if is_user else 'flex-start',
                'background': '#0084ff' if is_user else '#e5e5ea',
                'color': 'white' if is_user else 'black',
                'maxWidth': '80%',           
                'whiteSpace': 'normal',      
                'wordBreak': 'break-word',  
                'overflowWrap': 'break-word' 
            }
            elems.append(
                html.Div([
                    html.Div(msg['text'])
                ], style=bubble_style)
            )
    return elems

if __name__ == '__main__':
    app.run(debug=True)