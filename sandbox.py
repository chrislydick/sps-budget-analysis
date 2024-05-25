import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

container = st.container()
all = st.checkbox("Select all")
 
if all:
    selected_options = container.multiselect("Select one or more options:",
         ['A', 'B', 'C'],['A', 'B', 'C'])
else:
    selected_options =  container.multiselect("Select one or more options:",
        ['A', 'B', 'C'])