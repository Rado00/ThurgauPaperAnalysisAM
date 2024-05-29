# Import necessary libraries
from common import *
import pandas as pd
import warnings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

if __name__ == '__main__':
    setup_logging("03_plot_the_clean_csv_files.log")

    data_path, zone_name, scenario, csv_folder, output_folder, percentile, clean_csv_folder = read_config()

    pre_processed_data_path = os.path.join(data_path, zone_name, csv_folder, percentile)

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, 'plots')

    # Read the clean csv files
    data_path_clean = os.path.join(data_path, zone_name, clean_csv_folder, percentile)
    df_trips_mic = pd.read_csv(f'{data_path_clean}\\trips_mic.csv')
    df_trips_synt = pd.read_csv(f'{data_path_clean}\\trips_synt.csv')
    df_trips_sim = pd.read_csv(f'{data_path_clean}\\trips_sim.csv')

    df_activity_chains_syn = pd.read_csv(f'{data_path_clean}\\activity_chains_syn.csv')
    df_activity_chains_sim = pd.read_csv(f'{data_path_clean}\\activity_chains_sim.csv')
    df_activity_chains_mic = pd.read_csv(f'{data_path_clean}\\activity_chains_mic.csv')

    df_population_mic = pd.read_csv(f'{data_path_clean}\\population_clean_mic.csv')
    df_persons_synt = pd.read_csv(f'{data_path_clean}\\population_clean_synth.csv')
    df_persons_sim = pd.read_csv(f'{data_path_clean}\\population_clean_sim.csv')
    df_legs_synt = pd.read_csv(f'{data_path_clean}\\legs_clean_synt.csv')
    df_legs_sim = pd.read_csv(f'{data_path_clean}\\legs_clean_sim.csv')

    df_households_synt = pd.read_csv(f'{pre_processed_data_path}\\df_households_synt.csv')
    df_activity_synt = pd.read_csv(f'{pre_processed_data_path}\\df_activity_synt.csv')
    df_activity_sim = pd.read_csv(f'{pre_processed_data_path}\\df_activity_sim.csv')

    if 'household_weight_x' in df_trips_mic.columns:
        df_trips_mic.rename(columns={'household_weight_x': 'household_weight'}, inplace=True)

    # Count the frequency of each gender for df_persons_synt
    gender_counts_synt = df_persons_synt['sex'].value_counts().reset_index()
    gender_counts_synt.columns = ['gender', 'count']

    # Group by gender and sum the weights
    gender_counts_mic = df_population_mic.groupby('sex')['household_weight'].sum().reset_index()
    gender_counts_mic.columns = ['gender', 'count']

    # Creating subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]])

    # Adding the pie chart for Synthetic Population
    fig.add_trace(
        go.Pie(labels=gender_counts_synt['gender'], values=gender_counts_synt['count'],
               title='Gender Distribution Synthetic Population'),
        row=1, col=1
    )

    # Adding the pie chart for Microcensus
    fig.add_trace(
        go.Pie(labels=gender_counts_mic['gender'], values=gender_counts_mic['count'],
               title='Gender Distribution - Microcensus'),
        row=1, col=2
    )

    # Updating layout and showing the figure
    fig.update_layout(title_text="Comparative Gender Distribution", width=1200, height=600)
    # TODO for showing the figure just uncomment the following line
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_gender_distribution.png", scale=4)

    # Calculate value counts and percentages for df_households_synt
    income_counts_synt = df_households_synt['incomeClass'].value_counts().reset_index()
    income_counts_synt.columns = ['Income Class', 'Count']
    income_counts_synt['Percentage'] = (income_counts_synt['Count'] / income_counts_synt['Count'].sum()) * 100

    # Remove rows where any value in any column is greater than 0
    df_population_mic_filtered = df_population_mic[df_population_mic.ne(-1).all(axis=1)]

    # Calculate value counts and percentages for df_population_mic

    income_counts_mic = df_population_mic_filtered.groupby('income_class')['household_weight'].sum().reset_index()
    income_counts_mic.columns = ['Income Class', 'Count']

    income_counts_mic['Percentage'] = (income_counts_mic['Count'] / income_counts_mic['Count'].sum()) * 100

    income_class_labels = {
        1: 'Under CHF 2000',
        2: 'CHF 2000 to 4000',
        3: 'CHF 4001 to 6000',
        4: 'CHF 6001 to 8000',
        5: 'CHF 8001 to 10000',
        6: 'CHF 10001 to 12000',
        7: 'CHF 12001 to 14000',
        8: 'CHF 14001 to 16000',
        9: 'More than CHF 16000'
    }

    income_counts_synt['Income Class'] = income_counts_synt['Income Class'].map(income_class_labels)
    income_counts_mic['Income Class'] = income_counts_mic['Income Class'].map(income_class_labels)

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus income class percentage
    fig.add_trace(go.Bar(
        x=income_counts_mic['Income Class'],
        y=income_counts_mic['Percentage'],
        name='Microcensus - Percentage',
        marker_color='blue'
    ))

    # Add bars for synthetic households income class percentage
    fig.add_trace(go.Bar(
        x=income_counts_synt['Income Class'],
        y=income_counts_synt['Percentage'],
        name='Synthetic - Percentage',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Income Class Distribution - Percentage',
        xaxis_title='Income Class',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_income_distribution.png", scale=4)

    # Create a custom order for the x-axis categories
    custom_order = ['0', '1', '2', '3+']

    # Calculate value counts and percentages for df_population_mic
    car_counts_mic = df_population_mic.groupby('number_of_cars')['household_weight'].sum().reset_index()
    car_counts_mic.columns = ['Number of Cars', 'Count']
    car_counts_mic['Percentage'] = (car_counts_mic['Count'] / car_counts_mic['Count'].sum()) * 100

    # Calculate value counts and percentages for df_households_synt
    car_counts_synt = df_households_synt['numberOfCars'].value_counts().reset_index()
    car_counts_synt.columns = ['Number of Cars', 'Count']
    car_counts_synt['Percentage'] = (car_counts_synt['Count'] / car_counts_synt['Count'].sum()) * 100

    # Ensure the order of categories is as specified
    car_counts_mic['Number of Cars'] = pd.Categorical(car_counts_mic['Number of Cars'], categories=custom_order,
                                                      ordered=True)
    car_counts_mic = car_counts_mic.sort_values('Number of Cars')

    car_counts_synt['Number of Cars'] = pd.Categorical(car_counts_synt['Number of Cars'], categories=custom_order,
                                                       ordered=True)
    car_counts_synt = car_counts_synt.sort_values('Number of Cars')

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus car ownership percentage
    fig.add_trace(go.Bar(
        x=car_counts_mic['Number of Cars'],
        y=car_counts_mic['Percentage'],
        name='Microcensus - Car Ownership',
        marker_color='blue'
    ))

    # Add bars for synthetic households car ownership percentage
    fig.add_trace(go.Bar(
        x=car_counts_synt['Number of Cars'],
        y=car_counts_synt['Percentage'],
        name='Synthetic - Car Ownership',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Car Ownership Distribution - Percentage',
        xaxis_title='Number of Cars',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_car_ownership_distribution.png", scale=4)

    # Calculate total counts for each type
    type_counts_synt = df_activity_synt['type'].value_counts().reset_index()
    type_counts_synt.columns = ['Type', 'Count']
    type_counts_synt['Percentage'] = (type_counts_synt['Count'] / type_counts_synt['Count'].sum()) * 100

    # Group by purpose and sum the household weights for each purpose
    purpose_counts = df_trips_mic.groupby('purpose')['household_weight'].sum().reset_index()
    purpose_counts.columns = ['Purpose', 'Weighted_Count']

    # Calculate the total weight
    total_weight = purpose_counts['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    purpose_counts['Percentage'] = (purpose_counts['Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for synthetic activity types percentage
    fig.add_trace(go.Bar(
        x=type_counts_synt['Type'],
        y=type_counts_synt['Percentage'],
        name='Synthetic - Percentage',
        marker_color='blue'
    ))

    # Add bars for microcensus trip purposes percentage
    fig.add_trace(go.Bar(
        x=purpose_counts['Purpose'],
        y=purpose_counts['Percentage'],
        name='Microcensus - Percentage',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Activity Types and Trip Purposes (Percentage)',
        xaxis_title='Activity Types and Trip Purposes',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_trip_purpose_distribution.png", scale=4)

    # Now calculate the value counts and percentages for the cleaned-up modes
    mode_counts_synt = df_legs_synt['mode'].value_counts().reset_index()
    mode_counts_synt.columns = ['Mode', 'Count']
    mode_counts_synt['Percentage'] = (mode_counts_synt['Count'] / mode_counts_synt['Count'].sum()) * 100

    # # Calculate total counts for each mode
    # mode_counts_mic = df_trips_mic['mode'].value_counts().reset_index()
    # mode_counts_mic.columns = ['Mode', 'Count']

    # # Calculate percentage distribution for each mode
    # mode_counts_mic['Percentage'] = (mode_counts_mic['Count'] / mode_counts_mic['Count'].sum()) * 100

    # Group by mode and sum the household weights for each mode
    weighted_mode_counts = df_trips_mic.groupby('mode')['household_weight'].sum().reset_index()
    weighted_mode_counts.columns = ['Mode', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_mode_counts['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_mode_counts['Percentage'] = (weighted_mode_counts['Weighted_Count'] / total_weight) * 100

    # Rename the DataFrame to mode_counts_mic for consistency
    mode_counts_mic = weighted_mode_counts

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_mic['Mode'],
        y=mode_counts_mic['Percentage'],
        name='Microcensus - Percentage',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic - Percentage',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_trip_mode_share_distribution.png", scale=4)

    # Group by age and sum the weights for each age
    weighted_age_counts = df_population_mic.groupby('age')['household_weight'].sum().reset_index()
    weighted_age_counts.columns = ['Age', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_age_counts['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_age_counts['Percentage_weighted'] = (weighted_age_counts['Weighted_Count'] / total_weight) * 100

    # Calculate age distribution for df_persons_synt
    age_counts_persons = df_persons_synt['age'].value_counts().sort_index().reset_index()
    age_counts_persons.columns = ['Age', 'Count_persons']
    age_counts_persons['Percentage_persons'] = (age_counts_persons['Count_persons'] / age_counts_persons[
        'Count_persons'].sum()) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add the first bar for df_population_mic percentage
    fig.add_trace(go.Bar(
        x=weighted_age_counts['Age'],
        y=weighted_age_counts['Percentage_weighted'],
        name='Population Microcensus',
        marker_color='blue'
    ))

    # Add the second bar for df_persons_synt percentage
    fig.add_trace(go.Bar(
        x=age_counts_persons['Age'],
        y=age_counts_persons['Percentage_persons'],
        name='Population Synthetic',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Age Distribution',
        xaxis_title='Age',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_age_distribution.png", scale=4)

    # Count occurrences in each 15-minute bin
    departure_counts = df_trips_mic.groupby('departure_time').size().reset_index(name='Count')
    departure_counts['Type'] = 'Microcensus'

    # Normalize departure counts
    departure_counts['Count'] = departure_counts['Count'] / df_trips_mic.shape[0]

    departure_counts = departure_counts.rename(columns={'departure_time': 'Time'})

    arrival_counts = df_trips_synt.groupby('departure_time').size().reset_index(name='Count')
    arrival_counts['Type'] = 'Synthetic'

    # Normalize arrival counts
    arrival_counts['Count'] = arrival_counts['Count'] / df_trips_synt.shape[0]

    arrival_counts = arrival_counts.rename(columns={'departure_time': 'Time'})

    # Combine data
    time_counts = pd.concat([departure_counts, arrival_counts], axis=0)

    # Plot using Plotly Express
    fig = px.bar(time_counts, x='Time', y='Count', color='Type',
                 title='Departure Times over a Day',
                 labels={'Count': 'Count', 'Time': 'Time of Day'},
                 barmode='group')

    # Customize x-axis ticks and scale y-axis
    fig.update_xaxes(type='category', tickangle=45, dtick=1)
    fig.update_yaxes(range=[0, time_counts['Count'].max()])

    # Show plot
    fig.update_layout(width=1200, height=600)
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_day_time_distribution.png", scale=4)

    departure_counts_mic = df_trips_mic.groupby('departure_time').size().reset_index(name='Count')
    arrival_counts_mic = df_trips_mic.groupby('arrival_time').size().reset_index(name='Count')

    departure_counts_synt = df_legs_synt.groupby('departure_time').size().reset_index(name='Count')
    arrival_counts_synt = df_legs_synt.groupby('arrival_time').size().reset_index(name='Count')

    # Normalize the counts for df_trips_mic
    departure_counts_mic['Normalized_Count'] = departure_counts_mic['Count'] / df_trips_mic.shape[0]
    arrival_counts_mic['Normalized_Count'] = arrival_counts_mic['Count'] / df_trips_mic.shape[0]

    # Normalize the counts for df_legs_synt
    departure_counts_synt['Normalized_Count'] = departure_counts_synt['Count'] / df_legs_synt.shape[0]
    arrival_counts_synt['Normalized_Count'] = arrival_counts_synt['Count'] / df_legs_synt.shape[0]

    departure_counts_mic = departure_counts_mic.rename(columns={'departure_time': 'Time'})
    arrival_counts_mic = arrival_counts_mic.rename(columns={'arrival_time': 'Time'})

    departure_counts_synt = departure_counts_synt.rename(columns={'departure_time': 'Time'})
    arrival_counts_synt = arrival_counts_synt.rename(columns={'arrival_time': 'Time'})

    # Combine the normalized counts into one DataFrame for departures and arrivals
    combined_departures = pd.concat(
        [departure_counts_mic.assign(Dataset='mic'), departure_counts_synt.assign(Dataset='synt')])
    combined_arrivals = pd.concat(
        [arrival_counts_mic.assign(Dataset='mic'), arrival_counts_synt.assign(Dataset='synt')])

    # Combine departures and arrivals into one DataFrame
    combined_data = pd.concat(
        [combined_departures.assign(Type='Departures'), combined_arrivals.assign(Type='Arrivals')])

    # Plot using Plotly Express
    fig = px.bar(
        combined_data,
        x='Time',
        y='Normalized_Count',
        color='Type',
        pattern_shape='Dataset',  # Differentiates between 'mic' and 'synt' with pattern
        title='Normalized Departure and Arrival Times over a Day',
        labels={'Normalized_Count': 'Normalized Count', 'Time': 'Time of Day'},
        barmode='group'
    )

    # Customize the layout
    fig.update_layout(
        xaxis={'type': 'category', 'tickangle': 45},
        yaxis={'title': 'Normalized Count'},
        legend_title_text='Type',
        width=1200,
        height=600
    )

    # Show plot
    # fig.show()

    fig.write_image(f"{plots_directory}\\comparative_day_time_distribution_normalized.png", scale=4)

    # Assuming df_activity_chains_syn and df_activity_chains_mic are your DataFrames

    # Calculate total counts for each activity chain for Synthetic Population
    chain_counts_syn = df_activity_chains_syn['activity_chain'].value_counts().reset_index()
    chain_counts_syn.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Synthetic Population
    total_count_syn = chain_counts_syn['Count'].sum()
    chain_counts_syn['Normalized Count'] = (chain_counts_syn['Count'] / total_count_syn) * 100

    # Select the top 10 most common activity chains for Synthetic Population
    top_chain_counts_syn = chain_counts_syn.nlargest(20, 'Normalized Count')

    # Calculate total counts for each activity chain for Microcensus Population
    chain_counts_mic = df_activity_chains_mic['activity_chain'].value_counts().reset_index()
    chain_counts_mic.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Microcensus Population
    total_count_mic = chain_counts_mic['Count'].sum()
    chain_counts_mic['Normalized Count'] = (chain_counts_mic['Count'] / total_count_mic) * 100

    # Select the top 10 most common activity chains for Microcensus Population
    top_chain_counts_mic = chain_counts_mic.nlargest(20, 'Normalized Count')

    # Merge the two DataFrames
    merged_df = pd.merge(top_chain_counts_syn, top_chain_counts_mic, on='Activity Chain', suffixes=('_syn', '_mic'))

    # Creating a figure with grouped bar chart
    fig = go.Figure()

    # Add bars for Synthetic Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_syn'],
        name='Synthetic Population',
        marker_color='blue'
    ))

    # Add bars for Microcensus Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_mic'],
        name='Microcensus Population',
        marker_color='red'
    ))

    # Update the layout
    fig.update_layout(
        barmode='group',
        title_text="Comparison of Top 10 Activity Chains Between Synthetic and Microcensus Population",
        xaxis_title="Activity Chain",
        yaxis_title="Normalized Count (%)",
        width=1600,
        height=800
    )

    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_activity_chain_distribution.png", scale=4)

    # Calculate total counts for each activity chain for Synthetic Population
    chain_counts_syn = df_activity_chains_syn['activity_chain'].value_counts().reset_index()
    chain_counts_syn.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Synthetic Population
    total_count_syn = chain_counts_syn['Count'].sum()
    chain_counts_syn['Normalized Count'] = (chain_counts_syn['Count'] / total_count_syn) * 100

    # Calculate total counts for each activity chain for Microcensus Population
    chain_counts_mic = df_activity_chains_mic['activity_chain'].value_counts().reset_index()
    chain_counts_mic.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Microcensus Population
    total_count_mic = chain_counts_mic['Count'].sum()
    chain_counts_mic['Normalized Count'] = (chain_counts_mic['Count'] / total_count_mic) * 100

    # Merge the two DataFrames
    merged_df = pd.merge(chain_counts_syn, chain_counts_mic, on='Activity Chain', suffixes=('_syn', '_mic'))

    # Creating a figure with grouped bar chart
    fig = go.Figure()

    # Add bars for Synthetic Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_syn'],
        name='Synthetic Population',
        marker_color='blue'
    ))

    # Add bars for Microcensus Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_mic'],
        name='Microcensus Population',
        marker_color='red'
    ))

    # Update the layout
    fig.update_layout(
        barmode='group',
        title_text="Comparison of Activity Chains Between Synthetic and Microcensus Population",
        xaxis_title="Activity Chain",
        yaxis_title="Normalized Count (%)",
        width=1600,
        height=800
    )

    # fig.show()

    fig.write_image(f"{plots_directory}\\comparative_activity_chain_distribution.png", scale=4)

    # Now calculate the value counts and percentages for the cleaned-up modes
    mode_counts_synt = df_legs_synt['mode'].value_counts().reset_index()
    mode_counts_synt.columns = ['Mode', 'Count']
    mode_counts_synt['Percentage'] = (mode_counts_synt['Count'] / mode_counts_synt['Count'].sum()) * 100

    # Now calculate the value counts and percentages for the cleaned-up modes
    mode_counts_sim = df_legs_sim['mode'].value_counts().reset_index()
    mode_counts_sim.columns = ['Mode', 'Count']
    mode_counts_sim['Percentage'] = (mode_counts_sim['Count'] / mode_counts_sim['Count'].sum()) * 100

    # Group by mode and sum the household weights for each mode
    weighted_mode_counts = df_trips_mic.groupby('mode')['household_weight'].sum().reset_index()
    weighted_mode_counts.columns = ['Mode', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_mode_counts['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_mode_counts['Percentage'] = (weighted_mode_counts['Weighted_Count'] / total_weight) * 100

    # Rename the DataFrame to mode_counts_mic for consistency
    mode_counts_mic = weighted_mode_counts

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_mic['Mode'],
        y=mode_counts_mic['Percentage'],
        name='Microcensus - Percentage',
        marker_color='red'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic - Percentage',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_sim['Mode'],
        y=mode_counts_sim['Percentage'],
        name='Simulation - Percentage',
        marker_color='navy'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\validation_mode_distribution.png", scale=4)

    # Count occurrences in each 15-minute bin
    departure_counts_mic = df_trips_mic.groupby('departure_time').size().reset_index(name='Count')
    departure_counts_mic['Type'] = 'Microcensus'

    # Normalize departure counts
    departure_counts_mic['Count'] = departure_counts_mic['Count'] / df_trips_mic.shape[0]

    departure_counts_mic = departure_counts_mic.rename(columns={'departure_time': 'Time'})

    departure_counts_synth = df_trips_synt.groupby('departure_time').size().reset_index(name='Count')
    departure_counts_synth['Type'] = 'Synthetic'

    # Normalize arrival counts
    departure_counts_synth['Count'] = departure_counts_synth['Count'] / df_trips_synt.shape[0]

    departure_counts_synth = departure_counts_synth.rename(columns={'departure_time': 'Time'})

    departure_counts_sim = df_trips_sim.groupby('departure_time').size().reset_index(name='Count')
    departure_counts_sim['Type'] = 'Simulation'

    # Normalize arrival counts
    departure_counts_sim['Count'] = departure_counts_sim['Count'] / df_trips_sim.shape[0]

    departure_counts_sim = departure_counts_sim.rename(columns={'departure_time': 'Time'})

    # Combine data
    time_counts = pd.concat([departure_counts_mic, departure_counts_synth, departure_counts_sim], axis=0)

    # Plot using Plotly Express
    fig = px.bar(time_counts, x='Time', y='Count', color='Type',
                 title='Departure Times over a Day',
                 labels={'Count': 'Count', 'Time': 'Time of Day'},
                 barmode='group',
                 color_discrete_map={'Microcensus': 'red', 'Synthetic': 'blue', 'Simulation': 'navy'})

    # Customize x-axis ticks and scale y-axis
    fig.update_xaxes(type='category', tickangle=45, dtick=1)
    fig.update_yaxes(range=[0, time_counts['Count'].max()])

    # Show plot
    fig.update_layout(width=1200, height=600)
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\validation_time_distribution.png", scale=4)

    # Calculate total counts for each type
    type_counts_synt = df_activity_synt['type'].value_counts().reset_index()
    type_counts_sim = df_activity_sim['type'].value_counts().reset_index()
    type_counts_synt.columns = ['Type', 'Count']
    type_counts_sim.columns = ['Type', 'Count']

    # Calculate percentage distribution for each type and purpose
    type_counts_synt['Percentage'] = (type_counts_synt['Count'] / type_counts_synt['Count'].sum()) * 100
    type_counts_sim['Percentage'] = (type_counts_sim['Count'] / type_counts_sim['Count'].sum()) * 100

    # Group by purpose and sum the household weights for each purpose
    purpose_counts = df_trips_mic.groupby('purpose')['household_weight'].sum().reset_index()
    purpose_counts.columns = ['Purpose', 'Weighted_Count']

    # Calculate the total weight
    total_weight = purpose_counts['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    purpose_counts['Percentage'] = (purpose_counts['Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for synthetic activity types percentage
    fig.add_trace(go.Bar(
        x=type_counts_synt['Type'],
        y=type_counts_synt['Percentage'],
        name='Synthetic - Percentage',
        marker_color='blue'
    ))

    # Add bars for synthetic activity types percentage
    fig.add_trace(go.Bar(
        x=type_counts_sim['Type'],
        y=type_counts_sim['Percentage'],
        name='Simulation - Percentage',
        marker_color='green'
    ))

    # Add bars for microcensus trip purposes percentage
    fig.add_trace(go.Bar(
        x=purpose_counts['Purpose'],
        y=purpose_counts['Percentage'],
        name='Microcensus - Percentage',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Activity Types and Trip Purposes (Percentage)',
        xaxis_title='Activity Types and Trip Purposes',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # TODO for showing the figure just uncomment the following line
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\validation_trip_purpose_distribution.png", scale=4)

    # Assuming df_activity_chains_syn and df_activity_chains_mic are your DataFrames

    # Calculate total counts for each activity chain for Synthetic Population
    chain_counts_syn = df_activity_chains_syn['activity_chain'].value_counts().reset_index()
    chain_counts_syn.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Synthetic Population
    total_count_syn = chain_counts_syn['Count'].sum()
    chain_counts_syn['Normalized Count'] = (chain_counts_syn['Count'] / total_count_syn) * 100

    # Select the top 10 most common activity chains for Synthetic Population
    top_chain_counts_syn = chain_counts_syn.nlargest(20, 'Normalized Count')

    # Calculate total counts for each activity chain for Simulated Population
    chain_counts_sim = df_activity_chains_sim['activity_chain'].value_counts().reset_index()
    chain_counts_sim.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Simulated Population
    total_count_sim = chain_counts_sim['Count'].sum()
    chain_counts_sim['Normalized Count'] = (chain_counts_sim['Count'] / total_count_sim) * 100

    # Select the top 10 most common activity chains for Simulated Population
    top_chain_counts_sim = chain_counts_sim.nlargest(20, 'Normalized Count')

    # Calculate total counts for each activity chain for Microcensus Population
    chain_counts_mic = df_activity_chains_mic['activity_chain'].value_counts().reset_index()
    chain_counts_mic.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Microcensus Population
    total_count_mic = chain_counts_mic['Count'].sum()
    chain_counts_mic['Normalized Count'] = (chain_counts_mic['Count'] / total_count_mic) * 100

    # Select the top 10 most common activity chains for Microcensus Population
    top_chain_counts_mic = chain_counts_mic.nlargest(20, 'Normalized Count')

    # Merge the first two DataFrames
    merged_df = pd.merge(top_chain_counts_syn, top_chain_counts_sim, on='Activity Chain', suffixes=('_syn', '_sim'))

    # Merge the result with the third DataFrame
    merged_df = pd.merge(merged_df, top_chain_counts_mic, on='Activity Chain')
    merged_df.rename(columns={'Normalized Count': 'Normalized Count_mic'}, inplace=True)

    # Creating a figure with grouped bar chart
    fig = go.Figure()

    # Add bars for Synthetic Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_syn'],
        name='Synthetic Population',
        marker_color='blue'
    ))

    # Add bars for Synthetic Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_sim'],
        name='Simulation Population',
        marker_color='navy'
    ))

    # Add bars for Microcensus Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_mic'],
        name='Microcensus Population',
        marker_color='red'
    ))

    # Update the layout
    fig.update_layout(
        barmode='group',
        title_text="Comparison of Top 10 Activity Chains Between Synthetic and Microcensus Population",
        xaxis_title="Activity Chain",
        yaxis_title="Normalized Count (%)",
        width=1600,
        height=800
    )

    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\validation_activity_chain_distribution.png", scale=4)

