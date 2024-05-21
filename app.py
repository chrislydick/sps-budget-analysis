#Streamlit App - Beta and draft

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load data
data = pd.read_csv('performance_data_2023.csv')

# Clean data
data = data.rename(columns=lambda x: x.strip()).drop(columns=['Unnamed: 0'])
data['Necessary Budget'] = 500000 + data['Total Budget (BUDGET)']
data['Budget Efficiency'] = data['Total Budget (BUDGET)'] / data['Total AAFTE* Enrollment (ENROLLMENT)']
data['Landmark'] = data['Landmark'].fillna('N')
data['Landmark'] = data['Landmark'].replace({'None': 'N', 'NA': 'N'})

# Title
st.title('Seattle Elementary Schools Budget Analysis')

# Sidebar for filtering
st.sidebar.header('Filter options')

# Landmark status filter
landmark_options = ['N', 'Y','P']
selected_landmark = st.sidebar.multiselect('Select Landmark Status', options=landmark_options, default=landmark_options)

# Budget range filter using sliders
budget_range = st.sidebar.slider('Select Total Budget Range', 
                                 min_value=int(data['Total Budget (BUDGET)'].min()), 
                                 max_value=int(data['Total Budget (BUDGET)'].max()), 
                                 value=(int(data['Total Budget (BUDGET)'].min()), int(data['Total Budget (BUDGET)'].max())))

# Excess Budget per Student filter using sliders
excess_budget_range = st.sidebar.slider('Select Excess Budget per Student Range', 
                                        min_value=float(data['Excess Budget per Student'].min()), 
                                        max_value=float(data['Excess Budget per Student'].max()), 
                                        value=(float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max())))

# Budget Efficiency filter using sliders
budget_efficiency_range = st.sidebar.slider('Select Budget Efficiency Range', 
                                            min_value=float(data['Budget Efficiency'].min()), 
                                            max_value=float(data['Budget Efficiency'].max()), 
                                            value=(float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max())))

# Disadvantage Score filter using sliders
disadvantage_score_range = st.sidebar.slider('Select Disadvantage Score Range', 
                                             min_value=float(data['Disadvantage Score'].min()), 
                                             max_value=float(data['Disadvantage Score'].max()), 
                                             value=(float(data['Disadvantage Score'].min()), float(data['Disadvantage Score'].max())))

# Total AAFTE Enrollment range filter using sliders
enrollment_range = st.sidebar.slider('Select Total AAFTE Enrollment Range', 
                                     min_value=int(data['Total AAFTE* Enrollment (ENROLLMENT)'].min()), 
                                     max_value=int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()), 
                                     value=(int(data['Total AAFTE* Enrollment (ENROLLMENT)'].min()), int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max())))

# Apply filters
filtered_data = data[(data['Landmark'].isin(selected_landmark)) &
                     (data['Total Budget (BUDGET)'] >= budget_range[0]) & 
                     (data['Total Budget (BUDGET)'] <= budget_range[1]) & 
                     (data['Excess Budget per Student'] >= excess_budget_range[0]) &
                     (data['Excess Budget per Student'] <= excess_budget_range[1]) &
                     (data['Budget Efficiency'] >= budget_efficiency_range[0]) &
                     (data['Budget Efficiency'] <= budget_efficiency_range[1]) &
                     (data['Disadvantage Score'] >= disadvantage_score_range[0]) &
                     (data['Disadvantage Score'] <= disadvantage_score_range[1]) &
                     (data['Total AAFTE* Enrollment (ENROLLMENT)'] >= enrollment_range[0]) & 
                     (data['Total AAFTE* Enrollment (ENROLLMENT)'] <= enrollment_range[1])]

# Main panel
st.subheader(f'Filtered Data: ({filtered_data.shape[0]})')
st.write(filtered_data)

# Plotting
st.subheader('Budget Efficiency Distribution')
fig, ax = plt.subplots()
ax.hist(filtered_data['Budget Efficiency'], bins=20, color='skyblue', edgecolor='black')
ax.set_title('Distribution of Budget Efficiency of Schools')
ax.set_xlabel('Budget Efficiency (Budget per Student)')
ax.set_ylabel('Number of Schools')
st.pyplot(fig)

# Scatter plot of two selected dimensions
st.subheader('2D Scatter Plot of Selected Dimensions')

# Dropdown menus for selecting dimensions
x_dimension = st.selectbox('Select X Dimension', options=data.columns, index=data.columns.get_loc('Total Budget (BUDGET)'))
y_dimension = st.selectbox('Select Y Dimension', options=data.columns, index=data.columns.get_loc('Budget Efficiency'))

# Create scatter plot
fig, ax = plt.subplots()
ax.scatter(data[x_dimension], data[y_dimension], color='gray', edgecolor='black', alpha=0.5, label='Not in Filter')
ax.scatter(filtered_data[x_dimension], filtered_data[y_dimension], color='salmon', edgecolor='black', label='In Filter')
ax.set_title(f'Scatter Plot of {x_dimension} vs {y_dimension}')
ax.set_xlabel(x_dimension)
ax.set_ylabel(y_dimension)
ax.legend()
st.pyplot(fig)