#Dash Imports
from dash import html, dcc, callback, Output, Input,no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify



def InputSendButton():
    layout = dmc.ActionIcon(
        DashIconify(icon="ic:round-send", width=24),
        id='send-btn',
        variant="subtle",
        color="#303030",
        size="lg",
        radius="md",
    )

    return layout

def InputTextArea():
    layout = dmc.Textarea(
        id='input-msg',
        placeholder="Your comment",
        size="md",
        radius="lg",
        required=True,
        rightSection= InputSendButton(),
        rightSectionWidth=80,
        autosize=True,
        maxRows=5,
        miw=1000,
        pb=50,
        debounce=True,
    )

    return layout

def InputBox():
    layout = html.Div(
        children = [
            InputTextArea(),
        ],
        style = {
            'width': '100%',
            "border-radius": "20px",
            "display": "flex",
        },
    )

    return layout