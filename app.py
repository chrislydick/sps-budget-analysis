import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from streamlit.components.v1 import html
import numpy as np
import shutil
from bs4 import BeautifulSoup
import pathlib



st.set_page_config(layout="wide")

def determine_color(capacity_percent):
    if float(capacity_percent) < 0.75:
        return low_range_color
    elif float(capacity_percent) < 0.95 and float(capacity_percent) >= 0.75:
        return mid_range_color
    else:
        return high_range_color
    
def sync_dataframes(df1, df2, column_name):
    # Ensure the column exists in both dataframes
    if column_name not in df1.columns or column_name not in df2.columns:
        raise ValueError(f"Column '{column_name}' not found in both dataframes.")
    
    # Iterate over the rows of the second dataframe
    for idx, row in df2.iterrows():
        if idx in df1.index:
            df1.at[idx, column_name] = row[column_name]
        else:
            df1.loc[idx] = row
    
    return df1

def move_column(dataframe, column, position):
    cols = list(dataframe.columns)
    cols.insert(position, cols.pop(cols.index(column)))
    return dataframe[cols]


def reallocate_student_counts(student_counts, redistribution_matrix, closed_schools):
    # Convert input lists to numpy arrays for easy manipulation
    student_counts = np.array(student_counts, dtype=float)
    redistribution_matrix = np.array(redistribution_matrix, dtype=float)
    closed_schools = set(closed_schools)

    # Initialize current student counts
    current_student_counts = np.copy(student_counts)
    num_schools = len(student_counts)
    
    while True:
        new_counts = np.copy(current_student_counts)
        any_redistributed = False
        
        for school in closed_schools:
            if current_student_counts[school] > 0:
                any_redistributed = True
                total_redistributed = current_student_counts[school]
                
                # Adjust redistribution percentages to only consider open schools
                redistribution_percentages = np.copy(redistribution_matrix[school])
                redistribution_percentages[list(closed_schools)] = 0
                total_percentage = np.sum(redistribution_percentages)
                
                if total_percentage > 0:
                    redistribution_percentages /= total_percentage
                
                for i in range(num_schools):
                    if i not in closed_schools:
                        new_counts[i] += total_redistributed * redistribution_percentages[i]
                
                new_counts[school] = 0
        
        if not any_redistributed:
            break
        
        current_student_counts = new_counts
    
    return current_student_counts

# Load data
data = pd.read_csv('data/performance_data_2023.csv')
matrix = pd.read_csv('data/redistribution_matrix.csv',index_col=0)
counts = data[['Total AAFTE* Enrollment (ENROLLMENT)']].transpose().values[0]


# Clean data\
data = data.rename(columns=lambda x: x.strip()).drop(columns=['Unnamed: 0'])
data['Necessary Budget'] = 500000 + data['Total Budget (BUDGET)']
data['Budget Efficiency'] = data['Total Budget (BUDGET)'] / data['Total AAFTE* Enrollment (ENROLLMENT)']
data['Landmark'] = data['Landmark'].fillna('N')
data['Building Condition Score'] = data['Building Condition Score'].fillna(0)
data['Building Condition'] = data['Building Condition'].fillna('0. None')
data['Landmark'] = data['Landmark'].replace({'None': 'N', 'NA': 'N', '0': 'N', 0:'N'})
data['Use'] = data['Use'].replace({'0':'K-12', 0:'K-12'})
data['Enrollment from Redistribution'] = 0
data['Redistribution Capacity'] = data['Capacity Percent']
data['Total Enrollment'] = data['Total AAFTE* Enrollment (ENROLLMENT)']
data.drop(columns='Year', inplace=True)

                                    

# Move the rightmost column to the leftmost position
#columns = data.columns.tolist()
#columns = [columns[-1]] + columns[:-1]
#data = data[columns]

# Rename latitude and longitude columns to lowercase due to nuances with folium
data = data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'})

# Title



# Sidebar for filtering
st.sidebar.header('Adjust Filters to Identify Schools to Simulate Closing:')

selected_options =  st.sidebar.multiselect("Choose any number of metrics for Targeting Schools...", 
                                           ['Building Capacity','School Budget','School Type','Building Condition Score', 'Distance to Closest School','Excess Budget per Student', 'Disadvantage Score','Enrollment Total', 'Capacity Total','School Landmark Status'], ['Enrollment Total'], key='selected_options')

color_options = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige',
                 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink',
                 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']


# Landmark status filter
landmark_options = ['Y', 'N', 'P']
if 'School Landmark Status' in selected_options:
    selected_landmark = st.sidebar.multiselect("School's Landmark Status:", options=landmark_options, default=landmark_options, key='landmark')
else:
    selected_landmark = landmark_options

# Budget range filter using sliders
if 'School Budget' in selected_options:
    budget_range = st.sidebar.slider("School's Budget Range:", key='budget',
                                 min_value=0, 
                                 max_value=int(data['Total Budget (BUDGET)'].max()), 
                                 value=(0, int(data['Total Budget (BUDGET)'].max())),format='$%d')
else:
    budget_range = (0, int(data['Total Budget (BUDGET)'].max()))

# Excess Budget per Student filter using sliders
if 'Excess Budget per Student' in selected_options:
    excess_budget_range = st.sidebar.slider("School's Excess Budget per Student Range:", key='excess_budget',
                                        min_value=float(data['Excess Budget per Student'].min()), 
                                        max_value=float(data['Excess Budget per Student'].max()), 
                                        value=(float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max())),format='$%d')
else:
    excess_budget_range = (float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max()))

# Budget Efficiency filter using sliders
if 'Budget Efficiency' in selected_options:
    budget_efficiency_range = st.sidebar.slider("School's Budget per Student Range:", key='budget_efficiency',
                                            min_value=float(data['Budget Efficiency'].min()), 
                                            max_value=float(data['Budget Efficiency'].max()), 
                                            value=(float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max())),format='$%d')
else:
    budget_efficiency_range = (float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max()))


# Disadvantage Score filter using sliders
if 'Disadvantage Score' in selected_options:
    disadvantage_score_range = st.sidebar.slider("School's Disadvantage Score Range:", key='disadvantage_score', 
                                             min_value=0.0, 
                                             max_value=float(data['Disadvantage Score'].max()), 
                                             value=(0.0, float(data['Disadvantage Score'].max())))
else:
    disadvantage_score_range = (0.0, float(data['Disadvantage Score'].max()))


# Distance to nearest school using sliders
if 'Distance to Closest School' in selected_options:
    distance_range = st.sidebar.slider("School's Distance to Closest School Range:", key='distance',
                                     min_value=0.0, 
                                     max_value=float(data['Distance to Closest School (miles)'].max()), 
                                     value=(0.0, float(data['Distance to Closest School (miles)'].max())))
else:
    distance_range = (0.0, float(data['Distance to Closest School (miles)'].max()))


# Total AAFTE Enrollment range filter using sliders
if 'Enrollment Total' in selected_options:
    enrollment_range = st.sidebar.slider("School's total Enrollment Range:", key='enrollment_range',
                                     min_value=0, 
                                     max_value=int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()), 
                                     value=(0,0),format='%i')
else:
    enrollment_range = (0, int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()))

if 'Building Capacity' in selected_options:
    capacity_range = st.sidebar.slider("School's Capacity Range:", key='building_capacity',
                                     min_value=0, 
                                     max_value=int(data['Capacity'].max()), 
                                     value=(0, 300),format='%i')
else:
    capacity_range = (0, int(data['Capacity'].max()))

# School Capacity range filter using sliders
if 'Capacity Total' in selected_options:
    capacity = st.sidebar.slider("School's Capacity Percent Range:", key='capacity',
                                     min_value=0.0, 
                                     max_value=float(data['Capacity Percent'].max()*100.0), 
                                     value=(0.0, 65.0), format='%i%%')
    capacity = tuple(element / 100.0 for element in capacity)
else:
    capacity = (0.0, float(data['Capacity Percent'].max()))

# Building Condition Score filter using sliders
if 'Building Condition Score' in selected_options:
    building_condition_score = st.sidebar.slider("School's Building Condition Score Range:", key='building_condition_score', 
                                     min_value=0.0, 
                                     max_value=float(data['Building Condition Score'].max()), 
                                     value=(0.0, float(data['Building Condition Score'].max())))
else:
    building_condition_score = (0.0, float(data['Building Condition Score'].max()))

if 'School Type' in selected_options:
    school_type = st.sidebar.multiselect('Select School Type', data['Use'].unique(), default=data['Use'].unique(), key='school_type', placeholder='No School Types Selected')
else:
    school_type = data['Use'].unique()




manual_school = st.sidebar.multiselect('Manually Select Additional Schools to Close:', data['School'].unique(), key='manual_school', placeholder='No Manual Schools Selected')


if 'manual_school' not in st.session_state:
    st.session_state['manual_school'] = []
if 'selected_landmark' not in st.session_state:
    st.session_state['selected_landmark'] = []
if 'budget_range' not in st.session_state:
    st.session_state['budget_range'] = (0, int(data['Total Budget (BUDGET)'].max()))
if 'excess_budget_range' not in st.session_state:
    st.session_state['excess_budget_range'] = (float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max()))
if 'budget_efficiency_range' not in st.session_state:
    st.session_state['budget_efficiency_range'] = (float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max()))
if 'disadvantage_score_range' not in st.session_state:
    st.session_state['disadvantage_score_range'] = (0.0, float(data['Disadvantage Score'].max()))
if 'distance_range' not in st.session_state:
    st.session_state['distance_range'] = (0.0, float(data['Distance to Closest School (miles)'].max()))
if 'enrollment_range' not in st.session_state:
    st.session_state['enrollment_range'] = (0, int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()))
if 'capacity' not in st.session_state:
    st.session_state['capacity'] = (0.0, float(data['Capacity Percent'].max()))
if 'building_condition_score' not in st.session_state:
    st.session_state['building_condition_score'] = (0.0, float(data['Building Condition Score'].max()))
if 'school_type' not in st.session_state:
    st.session_state['school_type'] = ['K-12','E','K-8']
if 'building_capacity' not in st.session_state:
    st.session_state['building_capacity'] = (0, int(data['Capacity'].max()))

def reset_all_states():
    st.session_state.manual_school = []
    st.session_state.selected_landmark = ['Y','N','P']
    st.session_state.budget_range = (0, int(data['Total Budget (BUDGET)'].max()))
    st.session_state.excess_budget_range = (float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max()))
    st.session_state.budget_efficiency_range = (float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max()))
    st.session_state.disadvantage_score_range = (0.0, float(data['Disadvantage Score'].max()))
    st.session_state.distance_range = (0.0, float(data['Distance to Closest School (miles)'].max()))
    st.session_state.enrollment_range = (0, int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()))
    st.session_state.capacity = (0.0, float(data['Capacity Percent'].max()))
    st.session_state.building_condition_score = (0.0, float(data['Building Condition Score'].max()))
    st.session_state.school_type = ['E','K-12','K-8']
    st.session_state.building_capacity = (0, int(data['Capacity'].max()))

                                                 

                                       


def set_example_1():
    reset_all_states()
    st.session_state.enrollment_range = (0, 300)
    st.session_state.capacity = (0, 75)
    st.session_state.selected_options = ['Enrollment Total', 'Capacity Total']

def set_example_2():
    reset_all_states()
    st.session_state.enrollment_range = (0, int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()))
    st.session_state.capacity = (0, 65)
    st.session_state.building_condition_score = (3, 5)
    st.session_state.selected_options = ['Capacity Total', 'Building Condition Score']

def set_example_3():
    reset_all_states()
    st.session_state.school_type = ['K-8']
    st.session_state.distance = (0.0, 0.5)
    st.session_state.selected_options = ['School Type','Distance to Closest School']


def set_example_4():
    reset_all_states()
    st.session_state.enrollment_range = (0, 300)
    st.session_state.school_type = ['K-8','E']
    st.session_state.building_capacity = (0, 300)
    st.session_state.selected_options = ['School Type','Enrollment Total', 'Building Capacity']

def set_proposed_option_a():
    reset_all_states()
    st.session_state.enrollment_range = (0, 0)
    st.session_state.manual_school = ['Licton Springs/Webster', 'Monroe/Salmon Bay','North Beach Elementary', 'Broadview-Thomson','Green Lake Elementary','Decatur Elementary','Sacajawea Elementary','Cedar Park Elementary','Laurelhurst Elementary','Catharine Blaine K-8','John Hay Elementary',
                        'McGilvra Elementary', 'Stevens Elementary', 'TOPS/Seward', 'Orca/Whitworth', 'Graham Hill Elementary', 'Dunlap Elementary', 'Rainier View Elementary', 'Lafayette Elementary', 'Louisa Boren (STEM)', 'Sanislo Elementary']
    st.session_state.selected_options = ['Enrollment Total']
    

def set_proposed_option_b():
    reset_all_states()
    st.session_state.enrollment_range = (0, 0)
    st.session_state.manual_school = ['Licton Springs/Webster','North Beach Elementary','Broadview-Thomson', 'Green Lake Elementary','Decatur Elementary','Cedar Park Elementary','Laurelhurst Elementary', 'Catharine Blaine K-8','John Hay Elementary', 'McGilvra Elementary','Stevens Elementary',
                        'Thurgood Marshall Elementary', 'Orca/Whitworth', 'Graham Hill Elementary', 'Rainier View Elementary', 'Louisa Boren (STEM)', 'Sanislo Elementary']
    st.session_state.selected_options = ['Enrollment Total']


st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.header('Explore using Pre-Loaded Examples Below:')
st.sidebar.write("<h5>Proposed Option A (21 Closing)</h5>", unsafe_allow_html=True)
la = st.sidebar.button('Load Proposed Option A', key='example_a', on_click=set_proposed_option_a)
st.sidebar.write("<h5>Proposed Option B (17 Closing)</h5>", unsafe_allow_html=True)
lb = st.sidebar.button('Load Proposed Option B', key='example_b', on_click=set_proposed_option_b)
st.sidebar.write("<h5>Schools with Enrollment < 300 and Capacity < 75%</h5>", unsafe_allow_html=True)
l1 = st.sidebar.button('Load Example 1', key='example_1', on_click=set_example_1)
st.sidebar.write("")
st.sidebar.write("<h5>Schools with Capacity < 65%, Building Condition as Good or Fair</h5>", unsafe_allow_html=True)
l2 = st.sidebar.button('Load Example 2', key='example_2', on_click=set_example_2)
st.sidebar.write("")
st.sidebar.write("<h5>School type is K-8, within 0.5 miles of another similar school.</h5>", unsafe_allow_html=True)
l3 = st.sidebar.button('Load Example 3', key='example_3', on_click=set_example_3)
st.sidebar.write("")
st.sidebar.write("<h5>School type is K-8 or E, Building Capacity and Enrollment are both below 300.</h5>", unsafe_allow_html=True)
l3 = st.sidebar.button('Load Example 4', key='example_4', on_click=set_example_4)


# Apply filters
filtered_data = data[((data['Landmark'].isin(selected_landmark)) &
                     (data['Total Budget (BUDGET)'] >= budget_range[0]) & 
                     (data['Total Budget (BUDGET)'] <= budget_range[1]) & 
                     (data['Excess Budget per Student'] >= excess_budget_range[0]) &
                     (data['Excess Budget per Student'] <= excess_budget_range[1]) &
                     #(data['Budget Efficiency'] >= budget_efficiency_range[0]) &
                     #(data['Budget Efficiency'] <= budget_efficiency_range[1]) &
                    (data['Distance to Closest School (miles)'] >= distance_range[0]) &
                    (data['Distance to Closest School (miles)'] <= distance_range[1]) &
                     (data['Disadvantage Score'] >= disadvantage_score_range[0]) &
                     (data['Disadvantage Score'] <= disadvantage_score_range[1]) &
                     (data['Total AAFTE* Enrollment (ENROLLMENT)'] >= enrollment_range[0]) & 
                     (data['Total AAFTE* Enrollment (ENROLLMENT)'] <= enrollment_range[1]) & 
                     (data['Capacity Percent'] >= capacity[0]) & 
                     (data['Capacity Percent'] <= capacity[1]) &
                     (data['Capacity'] >= capacity_range[0]) &
                     (data['Capacity'] <= capacity_range[1]) &
                     (data['Building Condition Score'] >= building_condition_score[0]) &
                     (data['Building Condition Score'] <= building_condition_score[1]) &
                    
                        (data['Use'].isin(school_type))
                     ) |
                     (data['School'].isin(manual_school)) 
]




# Main panel


before = reallocate_student_counts(counts, matrix, [])
closed_schools = pd.array(filtered_data.index)
after = reallocate_student_counts(counts, matrix, closed_schools)
data['Enrollment from Redistribution'] = (after-before).astype(int)
data['Total Enrollment'] = (data['Total AAFTE* Enrollment (ENROLLMENT)'] + data['Enrollment from Redistribution']).astype(int)
data['Redistribution Capacity'] = (data['Total Enrollment'] / data['Capacity']).astype(float)

st.title('Simulation of School Closures in Seattle Public Schools 2025+')
#st.write('Seattle Public Schools (SPS) has initiated a program dubbed as <a href="https://www.seattleschools.org/resources/well-resourced-schools/">Well-Resourced Schools</a>, which began upon board approval for analysis of up to 20 elementary schools to be closed in Seattle. The hope is to close a growing budget gap in excess of $100M/year and increasing from years 2026+. This analysis utilizes <a href="https://github.com/chrislydick/sps-budget-analysis/tree/main/data">publicly available data</a> in order to understand outcomes of potential school closures. This data and analysis is provided for informational purposes only and is not intended to be a recommendation for or against any specific school closure. All code and data is available on <a href="https://github.com/chrislydick/sps-budget-analysis">GitHub here</a>.', unsafe_allow_html=True)
st.write('Seattle Public Schools (SPS) has launched the <a href="https://www.seattleschools.org/resources/well-resourced-schools/">Well-Resourced Schools program</a> following board approval to analyze the potential closure of up to 20 elementary schools in Seattle. This initiative aims to address a budget shortfall exceeding $100 million annually, projected to increase from 2026 onward. The analysis <a href="https://github.com/chrislydick/sps-budget-analysis/tree/main/data">leverages publicly available data from SPS</a> to assess the potential outcomes of school closures. The data and analysis are provided for informational purposes only and do not constitute recommendations for or against any specific school closure. All code and data can be accessed <a href="https://github.com/chrislydick/sps-budget-analysis">here</a>. Author Information <a href="https://chrislydick.com">here</a>. Contribute to the project <a href="https://github.com/chrislydick/sps-budget-analysis/tree/main">here</a>. FAQ available <a href="https://github.com/chrislydick/sps-budget-analysis?tab=readme-ov-file#faq">here</a>. ', unsafe_allow_html=True)
st.write('Start by selecting some number of metrics, or adjusting the metrics already selected on the left. You can also explore some pre-loaded examples. ', unsafe_allow_html=True)
st.write("")
col1, col2, col3, col4, col5 = st.columns(5)
#col2, col3, col4, col5 = st.columns(4)


s_under_75 = len(data[data['Redistribution Capacity'] < 0.75]) - len(filtered_data)
s_under_75_delta = -1+len(data[data['Redistribution Capacity'] < 0.75])-len(data[data['Capacity Percent'] < 0.75])
# First calculate number of schools which went into this category, then out. 



data['delta < 75'] = np.where(  
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) < 75) &\
                                (round(100*data['Redistribution Capacity'],0) == 0),\
                                'out','')

data['delta < 75'] = np.where(  
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) <= 75) & \
                                (round(100*data['Redistribution Capacity'],0) >= 75), \
                                'out', data['delta < 75'])





data['delta 75-100'] = np.where(
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) >= 75) & \
                                (round(100*data['Capacity Percent'],0) <= 100) & \
                                (round(100*data['Redistribution Capacity'],0) == 0), \
                                'out','')

data['delta 75-100'] = np.where(
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) >= 75) & \
                                (round(100*data['Capacity Percent'],0) <= 100) & \
                                (round(100*data['Redistribution Capacity'],0) > 100), \
                                'out',data['delta 75-100'])

data['delta 75-100'] = np.where(
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) >= 75) & \
                                (round(100*data['Capacity Percent'],0) <= 100) & \
                                (round(100*data['Redistribution Capacity'],0) <= 75), \
                                'out',data['delta 75-100'])

data['delta 75-100'] = np.where(
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) <= 75) & \
                                (round(100*data['Redistribution Capacity'],0) >= 75) & \
                                (round(100*data['Redistribution Capacity'],0) <= 100), \
                                'in',data['delta 75-100'])



data['delta > 100'] = np.where(
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) >= 100) & \
                                (round(100*data['Redistribution Capacity'],0) == 0),\
                                'out','')

data['delta > 100'] = np.where(
                                (round(100*data['Redistribution Capacity'],0) != round(100*data['Capacity Percent'],0)) & \
                                (round(100*data['Capacity Percent'],0) <= 100) & \
                                (round(100*data['Redistribution Capacity'],0) > 100),\
                                'in',data['delta > 100'])

data['delta closed'] = np.where((data['Redistribution Capacity'] == 0), 'in','')


s_over_100 = len(data[data['Redistribution Capacity'] > 1.0])
s_over_100_delta = len(data[data['Redistribution Capacity'] > 1.0])-len(data[data['Capacity Percent'] > 1.0])
s_remaining = len(data) - s_over_100 - s_under_75 - len(filtered_data)
#s_remaining_delta = abs(s_over_100 - s_under_75)
# 
s_remaining_delta = -1 + (len(data.query('`Capacity Percent` >= 0.75 & `Capacity Percent` <= 1.0')))\
                    - len(data.query('`Redistribution Capacity` >= 0.75 & `Redistribution Capacity` <= 1.0 ')) - len(filtered_data)

if filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum() == 0:
    col1.metric("Students' Assignments Unchanged*", f"{data['Total AAFTE* Enrollment (ENROLLMENT)'].sum() - filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum():,.0f}", delta=f"{filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum():,.0f}", delta_color="off")
else: 
    col1.metric("Students' Assignments Unchanged*", f"{data['Total AAFTE* Enrollment (ENROLLMENT)'].sum() - filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum():,.0f}", delta=f"-{filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum():,.0f}")

if len(data[data['delta closed']=='in']) == 0:
    col2.metric('Schools Remaining Open', f"{len(data) - len(filtered_data)}", delta=f"{-len(data[data['delta closed']=='in'])}", delta_color="off")
else: 
    col2.metric('Schools Remaining Open', f"{len(data) - len(filtered_data)}", delta=f"{-len(data[data['delta closed']=='in'])}", delta_color="inverse")
if len(data[data['delta < 75']=='in'])-len(data[data['delta < 75']=='out']) == 0:
    col3.metric('Schools Under 75% Capacity', f"{s_under_75}", delta=f"{len(data[data['delta < 75']=='in'])-len(data[data['delta < 75']=='out'])}", delta_color="off")
else: 
    col3.metric('Schools Under 75% Capacity', f"{s_under_75}", delta=f"{len(data[data['delta < 75']=='in'])-len(data[data['delta < 75']=='out'])}", delta_color="inverse")

if len(data[data['delta 75-100']=='in'])-len(data[data['delta 75-100']=='out']) == 0:
    col4.metric('Schools Between 75-100% Capacity', f"{s_remaining}", delta=f"{len(data[data['delta 75-100']=='in'])-len(data[data['delta 75-100']=='out'])}", delta_color="off")
else: 
    col4.metric('Schools Between 75-100% Capacity', f"{s_remaining}", delta=f"{len(data[data['delta 75-100']=='in'])-len(data[data['delta 75-100']=='out'])}", delta_color="normal")

if len(data[data['delta > 100']=='in'])-len(data[data['delta > 100']=='out']) == 0:
    col5.metric('Schools Over 100% Capacity', f"{s_over_100}", delta=f"{len(data[data['delta > 100']=='in'])-len(data[data['delta > 100']=='out'])}", delta_color="off")
else: 
    col5.metric('Schools Over 100% Capacity', f"{s_over_100}", delta=f"{len(data[data['delta > 100']=='in'])-len(data[data['delta > 100']=='out'])}", delta_color="inverse")


#col2.metric('Schools Remaining Open', f"{len(data) - len(filtered_data)}", delta=f"-{len(filtered_data)}", delta_color="inverse")
#col3.metric('Schools Under 75% Capacity', f"{s_under_75}", delta=f"{s_under_75_delta}", delta_color="inverse")
#col4.metric('Schools Between 75-100% Capacity', f"{s_remaining}", delta=f"{s_remaining_delta}")
#col5.metric('Schools Over 100% Capacity', f"{s_over_100}", delta=f"{s_over_100_delta}", delta_color="inverse")




#identify all column names beginning with 'Cluster_'
cluster_columns = [col for col in data.columns if 'Cluster_' in col]
data_editor_data = filtered_data.drop(columns=cluster_columns)
data_moved = move_column(data_editor_data, 'Use', 1)
data_moved = move_column(data_moved, 'Total AAFTE* Enrollment (ENROLLMENT)', 2)
data_moved = move_column(data_moved, 'Capacity', 3)
data_moved = move_column(data_moved, 'Capacity Percent', 4)
data_moved['Capacity Percent'] = data_moved['Capacity Percent'].map(lambda x: f"{x*100:.4}").astype(float)
data_moved.rename(columns={'Total AAFTE* Enrollment (ENROLLMENT)':'Enrollment'}, inplace=True)

data_editor_data_1 = data.drop(columns=cluster_columns)
data_moved_1 = move_column(data_editor_data_1, 'Use', 1)
data_moved_1['Ending Excess Capacity'] = data_moved_1['Capacity'] - data_moved_1['Total Enrollment']
data_moved_1 = move_column(data_moved_1, 'Total AAFTE* Enrollment (ENROLLMENT)', 2)
data_moved_1 = move_column(data_moved_1, 'Enrollment from Redistribution', 3)
data_moved_1 = move_column(data_moved_1, 'Total Enrollment', 4)
data_moved_1 = move_column(data_moved_1, 'Capacity', 5)
data_moved_1 = move_column(data_moved_1, 'Ending Excess Capacity', 6)
data_moved_1 = move_column(data_moved_1, 'Capacity Percent', 7)
data_moved_1 = move_column(data_moved_1, 'Redistribution Capacity', 8)
data_moved_1['Redistribution Capacity'] = data_moved_1['Redistribution Capacity'].map(lambda x: f"{x*100:.4}").astype(float)
data_moved_1['Capacity Percent'] = data_moved_1['Capacity Percent'].map(lambda x: f"{x*100:.4}").astype(float)
data_moved_1.rename(columns={'Capacity':'Building Capacity','Excess Capacity':'Beginning Excess Capacity','Total AAFTE* Enrollment (ENROLLMENT)':'Beginning Enrollment','Capacity Percent':'Beginning Capacity %', 'Redistribution Capacity':'Ending Capacity %', 'Enrollment from Redistribution':'Additional Students'}, inplace=True)
data_moved_1 = data_moved_1[data_moved_1['Additional Students'] > 0]
data_moved_1['Ending Capacity %'] = data_moved_1['Ending Capacity %'].astype(int)


# Map of school locations with different colors for filtered and non-filtered schools
col1a, col2a = st.columns(2)

# Create a map centered around Seattle with a dark base map
#try: 
#    m = folium.Map(location=[filtered_data['latitude'].mean(), filtered_data['longitude'].mean()], zoom_start=11, tiles='CartoDB dark_matter')
#except:
#    m = folium.Map(location=[data['latitude'].mean(), data['longitude'].mean()], zoom_start=11, tiles='CartoDB dark_matter')

m = folium.Map(location=[data['latitude'].mean(), data['longitude'].mean()], zoom_start=11, tiles='CartoDB dark_matter')
n = folium.Map(location=[data['latitude'].mean(), data['longitude'].mean()], zoom_start=11, tiles='CartoDB dark_matter')


#low_range_color = st.selectbox('Capacity Low Range Color (< 75%)', color_options, index=color_options.index('lightgreen'))
low_range_color = 'lightblue'
#mid_range_color = st.selectbox('Capacity Mid Range Color (75% - 95%)', color_options, index=color_options.index('green'))
mid_range_color = 'blue'
#high_range_color = st.selectbox('Capacity High Range Color (> 95%)', color_options, index=color_options.index('darkgreen'))
high_range_color = 'darkblue'
#closed_school_color = st.selectbox('Closed School Color', color_options, index=color_options.index('black'))
closed_school_color = 'red'



# Add all schools to the map with different colors
try:
    for _, row in data.iterrows():
        color = determine_color(row['Capacity Percent'])
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['School']} ({row['Capacity Percent']*100:.0f}%)",
            icon=folium.Icon(icon='None',color=color)
        ).add_to(n)
    for _, row in data.iterrows():
        color = closed_school_color if row['School'] in filtered_data['School'].values else determine_color(row['Redistribution Capacity'])
        icon = folium.Icon(icon='None', color=color) if row['Enrollment from Redistribution'] == 0 else folium.Icon(color=color)
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['School']} ({row['Capacity Percent']*100:.0f}% -> {row['Redistribution Capacity']*100:.0f}%)",
            #icon=folium.Icon(icon='none', color='blue', icon_color='white'),
            icon=icon
        ).add_to(m)
except:
    st.write("")

# Before School Closures
with col1a:
    try: 
        st.subheader('Capacity Before School Closure(s)')
        st.write('* Ligher Schools are of less capacity. \n * Darker Schools have higher capacity.')
        st_folium(n, width=700, height=500) 
    except:
        st.write("")



# After School Closures
with col2a: 
    try: 
        st.subheader('Capacity After School Closure(s)')
        st.write('* Red Schools are simulated to close. \n * Schools marked: (i) have changed their capacity due to redistribution.')
        st_folium(m, width=700, height=500) 
    except:
        st.write("")
# Plotting
        

st.write(f'By closing the following {data_moved.shape[0]} schools...')
st.data_editor(data_moved, use_container_width=True, hide_index=True, width=10000)

st.write(f'You impact these {data_moved_1.shape[0]} schools...')
st.data_editor(data_moved_1, use_container_width=True, hide_index=True, width=10000)
###st.subheader('Budget Efficiency Distribution')
fig, ax = plt.subplots()
ax.hist(filtered_data['Budget Efficiency'], bins=20, color='#FF4B4B', edgecolor='black')
ax.set_facecolor('#0B0B0BFF')
ax.set_title('Distribution of Budget Efficiency of Schools')
ax.set_xlabel('Budget Efficiency (Budget per Student)')
ax.set_ylabel('Number of Schools')
###st.pyplot(fig)

# Scatter plot of two selected dimensions
###st.subheader('2D Scatter Plot of Selected Dimensions')

# Dropdown menus for selecting dimensions
#x_dimension = st.selectbox('Select X Dimension', options=data.columns, index=data.columns.get_loc('Total Budget (BUDGET)'))
#y_dimension = st.selectbox('Select Y Dimension', options=data.columns, index=data.columns.get_loc('Budget Efficiency'))

# Create scatter plot
#fig, ax = plt.subplots()
#ax.scatter(data[x_dimension], data[y_dimension], color='gray', edgecolor='black', alpha=0.5, label='Not in Filter')
#ax.scatter(filtered_data[x_dimension], filtered_data[y_dimension], color='salmon', edgecolor='black', label='In Filter')
#ax.set_title(f'Scatter Plot of {x_dimension} vs {y_dimension}')
#ax.set_xlabel(x_dimension)
#ax.set_ylabel(y_dimension)
#ax.legend()
###st.pyplot(fig)

if st.checkbox('Show All Schools and All Data'):
    data['Capacity Percent'] = data['Capacity Percent'].map(lambda x: float(f"{x*100.0:2.1f}"))
    data['Redistribution Capacity'] = data['Redistribution Capacity'].map(lambda x: float(f"{x*100.0:2.1f}"))
    st.dataframe(data)
    #st.dataframe(data[['School','Use','Total Budget (BUDGET)','Total AAFTE* Enrollment (ENROLLMENT)','Enrollment from Redistribution','Total Enrollment','Capacity','Capacity Percent','Redistribution Capacity']].rename(columns={'Total AAFTE* Enrollment (ENROLLMENT)':'Enrollment', 'Capacity Percent':'Starting Capacity Percent','Redistribution Capacity':'Ending Capacity Percent','Capacity':'Building Capacity'}), width=10000)

st.write('<br><br>*<em> Enrollment & Capacity values were normalized for K-8 and K-12 schools so numbers are comparable with Elementary.</em>', unsafe_allow_html=True)