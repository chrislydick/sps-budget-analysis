import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from streamlit.components.v1 import html


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


# Load data
data = pd.read_csv('data/performance_data_2023.csv')

# Clean data\
data = data.rename(columns=lambda x: x.strip()).drop(columns=['Unnamed: 0'])
data['Necessary Budget'] = 500000 + data['Total Budget (BUDGET)']
data['Budget Efficiency'] = data['Total Budget (BUDGET)'] / data['Total AAFTE* Enrollment (ENROLLMENT)']
data['Landmark'] = data['Landmark'].fillna('N')
data['Building Condition Score'] = data['Building Condition Score'].fillna(0)
data['Building Condition'] = data['Building Condition'].fillna('0. None')
data['Landmark'] = data['Landmark'].replace({'None': 'N', 'NA': 'N', '0': 'N', 0:'N'})
data['Use'] = data['Use'].replace({'0':'K-12', 0:'K-12'})
data.drop(columns='Year', inplace=True)

                                    

# Move the rightmost column to the leftmost position
#columns = data.columns.tolist()
#columns = [columns[-1]] + columns[:-1]
#data = data[columns]

# Rename latitude and longitude columns to lowercase due to nuances with folium
data = data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'})

# Title
st.title('Simulation of School Closures in Seattle Public Schools 2025+')
st.write('Seattle Public Schools (SPS) has initiated a program dubbed as <a href="https://www.seattleschools.org/resources/well-resourced-schools/">Well-Resourced Schools</a>, which began upon board approval for analysis of up to 20 elementary schools to be closed in Seattle. The hope is to close a growing budget gap in excess of $100M/year and increasing from years 2026+. This analysis utilizes <a href="https://github.com/chrislydick/sps-budget-analysis/tree/main/data">publicly available data</a> in order to understand outcomes of potential school closures. This data and analysis is provided for informational purposes only and is not intended to be a recommendation for or against any specific school closure. All code and data is available on <a href="https://github.com/chrislydick/sps-budget-analysis">GitHub here</a>.', unsafe_allow_html=True)
st.write('Author Information <a href="https://chrislydick.com">here</a>.', unsafe_allow_html=True)
st.write('')











# Sidebar for filtering
st.sidebar.header('Identify Schools to Close by Filters')


selected_options =  st.sidebar.multiselect("Metrics to Find Schools to Close...",
        ['School Budget','School Type','Building Condition Score', 'Distance to Closest School','Excess Budget per Student', 'Disadvantage Score','Enrollment Toal', 'Capacity Total','School Landmark Status'], ['Enrollment Toal', 'Capacity Total'])

color_options = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige',
                 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink',
                 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']


# Landmark status filter
landmark_options = ['Y', 'N', 'P']
if 'School Landmark Status' in selected_options:
    selected_landmark = st.sidebar.multiselect("School's Landmark Status:", options=landmark_options, default=landmark_options)
else:
    selected_landmark = landmark_options

# Budget range filter using sliders
if 'School Budget' in selected_options:
    budget_range = st.sidebar.slider("School's Budget Range:", 
                                 min_value=0, 
                                 max_value=int(data['Total Budget (BUDGET)'].max()), 
                                 value=(0, int(data['Total Budget (BUDGET)'].max())),format='$%d')
else:
    budget_range = (0, int(data['Total Budget (BUDGET)'].max()))

# Excess Budget per Student filter using sliders
if 'Excess Budget per Student' in selected_options:
    excess_budget_range = st.sidebar.slider("School's Excess Budget per Student Range:", 
                                        min_value=float(data['Excess Budget per Student'].min()), 
                                        max_value=float(data['Excess Budget per Student'].max()), 
                                        value=(float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max())),format='$%d')
else:
    excess_budget_range = (float(data['Excess Budget per Student'].min()), float(data['Excess Budget per Student'].max()))

# Budget Efficiency filter using sliders
if 'Budget Efficiency' in selected_options:
    budget_efficiency_range = st.sidebar.slider("School's Budget per Student Range:", 
                                            min_value=float(data['Budget Efficiency'].min()), 
                                            max_value=float(data['Budget Efficiency'].max()), 
                                            value=(float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max())),format='$%d')
else:
    budget_efficiency_range = (float(data['Budget Efficiency'].min()), float(data['Budget Efficiency'].max()))


# Disadvantage Score filter using sliders
if 'Disadvantage Score' in selected_options:
    disadvantage_score_range = st.sidebar.slider("School's Disadvantage Score Range:", 
                                             min_value=0.0, 
                                             max_value=float(data['Disadvantage Score'].max()), 
                                             value=(0.0, float(data['Disadvantage Score'].max())))
else:
    disadvantage_score_range = (0.0, float(data['Disadvantage Score'].max()))


# Distance to nearest school using sliders
if 'Distance to Closest School' in selected_options:
    distance_range = st.sidebar.slider("School's Distance to Closest School Range:", 
                                     min_value=0.0, 
                                     max_value=float(data['Distance to Closest School (miles)'].max()), 
                                     value=(0.0, float(data['Distance to Closest School (miles)'].max())))
else:
    distance_range = (0.0, float(data['Distance to Closest School (miles)'].max()))


# Total AAFTE Enrollment range filter using sliders
if 'Enrollment Toal' in selected_options:
    enrollment_range = st.sidebar.slider("School's total Enrollment Range:", 
                                     min_value=0, 
                                     max_value=int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()), 
                                     value=(0,300),format='%i')
else:
    enrollment_range = (0, int(data['Total AAFTE* Enrollment (ENROLLMENT)'].max()))


# School Capacity range filter using sliders
if 'Capacity Total' in selected_options:
    capacity = st.sidebar.slider("School's Capacity Percent Range:", 
                                     min_value=0.0, 
                                     max_value=float(data['Capacity Percent'].max()*100.0), 
                                     value=(0.0, 65.0), format='%i%%')
    capacity = tuple(element / 100.0 for element in capacity)
else:
    capacity = (0.0, float(data['Capacity Percent'].max()))

# Building Condition Score filter using sliders
if 'Building Condition Score' in selected_options:
    building_condition_score = st.sidebar.slider("School's Building Condition Score Range:", 
                                     min_value=0.0, 
                                     max_value=float(data['Building Condition Score'].max()), 
                                     value=(0.0, float(data['Building Condition Score'].max())))
else:
    building_condition_score = (0.0, float(data['Building Condition Score'].max()))

if 'School Type' in selected_options:
    school_type = st.sidebar.multiselect('Select School Type', data['Use'].unique(), default=data['Use'].unique())
else:
    school_type = data['Use'].unique()

    


manual_school = st.sidebar.multiselect('Manually Select Additional Schools to Close:', data['School'].unique())


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
                     (data['Building Condition Score'] >= building_condition_score[0]) &
                     (data['Building Condition Score'] <= building_condition_score[1]) &
                        (data['Use'].isin(school_type))
                     ) |
                     (data['School'].isin(manual_school)) 
]





# Main panel


st.subheader('')

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric('Updated Elementary Budget', value=f"${data['Total Budget (BUDGET)'].sum() - filtered_data['Total Budget (BUDGET)'].sum():,.0f}",delta=f"-{filtered_data['Total Budget (BUDGET)'].sum():,.0f}", delta_color="inverse")
col2.metric('Schools Remaining Open', f"{len(data) - len(filtered_data)}", delta=f"-{len(filtered_data)}", delta_color="inverse")
col3.metric('Total Student Enrollment', f"{data['Total AAFTE* Enrollment (ENROLLMENT)'].sum() - filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum():,.0f}", delta=f"-{filtered_data['Total AAFTE* Enrollment (ENROLLMENT)'].sum():,.0f}")
col4.metric('Schools Under 75% Capacity', f"{len(data[data['Capacity Percent'] < 0.75])-len(filtered_data[filtered_data['Capacity Percent'] < 0.75])}", delta=f"-{len(filtered_data[filtered_data['Capacity Percent'] < 0.75])}", delta_color="inverse")
col5.metric('Schools Over 100% Capacity', f"{len(data[data['Capacity Percent'] > 1.0])-len(filtered_data[filtered_data['Capacity Percent'] > 1.0])}", delta=f"-{len(filtered_data[filtered_data['Capacity Percent'] > 1.0])}", delta_color="inverse")



#identify all column names beginning with 'Cluster_'
cluster_columns = [col for col in data.columns if 'Cluster_' in col]
data_editor_data = filtered_data.drop(columns=cluster_columns)
data_moved = move_column(data_editor_data, 'Use', 1)
data_moved = move_column(data_moved, 'Total AAFTE* Enrollment (ENROLLMENT)', 2)
data_moved = move_column(data_moved, 'Capacity', 3)
data_moved = move_column(data_moved, 'Capacity Percent', 4)
data_moved['Capacity Percent'] = data_moved['Capacity Percent'].map(lambda x: f"{x:.0%}")
data_moved.rename(columns={'Total AAFTE* Enrollment (ENROLLMENT)':'Enrollment'}, inplace=True)


st.subheader('')

st.write('Simulated School Closures List:')
st.data_editor(data_moved, use_container_width=True, hide_index=True, width=10000) 

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
        color = closed_school_color if row['School'] in filtered_data['School'].values else determine_color(row['Capacity Percent'])
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['School']} ({row['Capacity Percent']*100:.0f}%)",
            icon=folium.Icon(color=color)
        ).add_to(m)
    for _, row in data.iterrows():
        color = determine_color(row['Capacity Percent'])
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"{row['School']} ({row['Capacity Percent']*100:.0f}%)",
            icon=folium.Icon(color=color)
        ).add_to(n)
except:
    st.write("")

# Before School Closures
with col1a:
    try: 
        st.subheader('Capacity Before School Closure(s)')
        st.write('Ligher Schools are of less capacity.')
        st_folium(n, width=700, height=500) 
    except:
        st.write("")



# After School Closures
with col2a: 
    try: 
        st.subheader('Capacity After School Closure(s)')
        st.write('Red Schools have simulated to close.')
        st_folium(m, width=700, height=500) 
    except:
        st.write("")
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


#st.subheader("All Data:")
#st.dataframe(data)

