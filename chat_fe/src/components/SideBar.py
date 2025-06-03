#Dash Imports
from dash import html, dcc, callback, Output, Input,no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import feffery_antd_components as fac

def SideBar():
    layout = html.Div(
        style = {
            'width': '100%',
            'height': '100vh',
            "margin": "5px 5px",
            "display": "flex",
            "border-radius": "20px",
            "backgroundColor": "#f1f1f1"
        },
    )

    return layout