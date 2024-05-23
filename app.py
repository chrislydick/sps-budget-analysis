# Save this as app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium


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


# Load data
data = pd.read_csv('data/performance_data_2023.csv')

# Clean data
data = data.rename(columns=lambda x: x.strip()).drop(columns=['Unnamed: 0'])
data['Necessary Budget'] = 500000 + data['Total Budget (BUDGET)']
data['Budget Efficiency'] = data['Total Budget (BUDGET)'] / data['Total AAFTE* Enrollment (ENROLLMENT)']
data['Landmark'] = data['Landmark'].fillna('N')
data['Landmark'] = data['Landmark'].replace({'None': 'N', 'NA': 'N'})
data['In Filter'] = True
data.drop(columns='Year', inplace=True)

                                    

# Move the rightmost column to the leftmost position
columns = data.columns.tolist()
columns = [columns[-1]] + columns[:-1]
data = data[columns]

# Rename latitude and longitude columns to lowercase
data = data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'})

# Title
st.title('Seattle Elementary Schools Budget Analysis')

# Sidebar for filtering
st.sidebar.header('Filter options')

color_options = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige',
                 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink',
                 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']


# Landmark status filter
landmark_options = ['Y', 'N', 'P']
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

# School Capacity range filter using sliders
capacity = st.sidebar.slider('Select Total Capacity Percent Range', 
                                     min_value=float(data['Capacity Percent'].min()), 
                                     max_value=float(data['Capacity Percent'].max()), 
                                     value=(float(data['Capacity Percent'].min()), float(data['Capacity Percent'].max())))

low_range_color = st.sidebar.selectbox('Capacity Low Range Color (< 75%)', color_options, index=color_options.index('lightgreen'))
mid_range_color = st.sidebar.selectbox('Capacity Mid Range Color (75% - 95%)', color_options, index=color_options.index('green'))
high_range_color = st.sidebar.selectbox('Capacity High Range Color (> 95%)', color_options, index=color_options.index('darkgreen'))
closed_school_color = st.sidebar.selectbox('Closed School Color', color_options, index=color_options.index('black'))

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
                     (data['Total AAFTE* Enrollment (ENROLLMENT)'] <= enrollment_range[1]) & 
                     (data['Capacity Percent'] >= capacity[0]) & 
                     (data['Capacity Percent'] <= capacity[1]) & 
                     (data['In Filter'] == True)
]





# Main panel
st.subheader(f'Filtered Data: ({filtered_data.shape[0]})')


data['In Filter'] = data['School'].isin(filtered_data['School'])
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
    (data['Total AAFTE* Enrollment (ENROLLMENT)'] <= enrollment_range[1]) &
    (data['Capacity Percent'] >= capacity[0]) & 
    (data['Capacity Percent'] <= capacity[1]) & 
    (data['In Filter'] == True)]
t1 = st.data_editor(data[['In Filter','School', 'Total AAFTE* Enrollment (ENROLLMENT)','Predicted Total Budget (BUDGET)','Total Budget (BUDGET)','Excess Budget per Student','Capacity','Capacity Percent']]) 

sync_dataframes(data, t1, 'In Filter')


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
    (data['Total AAFTE* Enrollment (ENROLLMENT)'] <= enrollment_range[1]) &
    (data['Capacity Percent'] >= capacity[0]) & 
    (data['Capacity Percent'] <= capacity[1]) & 
    (data['In Filter'] == True)]




# Map of school locations with different colors for filtered and non-filtered schools
st.subheader('Map of School Locations')

# Create a map centered around Seattle with a dark base map
m = folium.Map(location=[filtered_data['latitude'].mean(), filtered_data['longitude'].mean()], zoom_start=11, tiles='CartoDB dark_matter')

# Add all schools to the map with different colors
for _, row in data.iterrows():
    color = closed_school_color if row['School'] in filtered_data['School'].values else determine_color(row['Capacity Percent'])
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=row['School'],
        icon=folium.Icon(color=color)
    ).add_to(m)


# Display the map
st_folium(m, width=700, height=500)

# Plotting
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
###st.pyplot(fig)


st.subheader("All Data:")
st.dataframe(data)


