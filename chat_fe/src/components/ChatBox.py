#Base Imports
import sys, os
from dash import html, dcc, callback, Output, Input, no_update
import dash_mantine_components as dmc
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from InputBox import InputBox

def ChatArea():
    return dmc.Container(
        style = {
            "minWidth": "65em",
        },
        children = [
            html.Div(
                id='chat-window',
                style={
                    "backgroundColor": "#8A828200",
                    "width": "100%",
                    "flex": "1",
                    "display": "flex",
                    "flexDirection": "column-reverse",
                    "overflowY": "auto",
                    "padding": "10px",
                    "maxHeight": "35em",
                },
            )
        ])

def ChatBox():
    return html.Div(
        children=[
            # Burayı flex column olarak ayarlıyoruz
            html.Div(
                children=[
                    ChatArea(),
                    # InputBox’ın kendi style’ı da burada sabitlenecek
                    html.Div(
                        InputBox(),
                        style={
                            "flex": "0",        # yükseklik değişmesin
                            "flexShrink": 0,    # küçülmesin
                            "width": "80%",     # ChatArea ile hizalı olsun
                            "padding": "10px",
                        }
                    )
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "height": "100vh",        # tam ekran
                    "boxSizing": "border-box",
                    "justifyContent": "flex-end"
                }
            )
        ],
        style={
            'width': '100%',
            'height': '100%',
            "margin": "5px 0px",
            "borderRadius": "20px",
            "backgroundColor": "#f1f1f1",
            "justify-content": "center",
            "display": "flex",
            "align-items": "center",
        },
    )
