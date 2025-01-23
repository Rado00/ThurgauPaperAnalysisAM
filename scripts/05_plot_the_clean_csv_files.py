# Import necessary libraries
import logging
from common import *
import pandas as pd
import warnings
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

warnings.filterwarnings('ignore')

if __name__ == '__main__':
    setup_logging("05_plot_the_clean_csv_files.log")

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")

    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, f'plots\\plots_{analysis_zone_name}')
    if not os.path.exists(plots_directory):
        os.makedirs(plots_directory)

    # Read the clean csv files
    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)
    df_trips_mic = pd.read_csv(f'{data_path_clean}\\trips_mic.csv')
    df_trips_synt = pd.read_csv(f'{data_path_clean}\\trips_synt.csv')
    # df_trips_sim = pd.read_csv(f'{data_path_clean}\\trips_sim.csv')

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
    logging.info("All the csv files have been read successfully.")

    df_persons_synt.loc[df_persons_synt['sex'] == 'male', 'sex'] = 'Male'
    df_persons_synt.loc[df_persons_synt['sex'] == 'female', 'sex'] = 'Female'
    df_population_mic.loc[df_population_mic['sex'] == 'male', 'sex'] = 'Male'
    df_population_mic.loc[df_population_mic['sex'] == 'female', 'sex'] = 'Female'

    if 'household_weight_x' in df_trips_mic.columns:
        df_trips_mic.rename(columns={'household_weight_x': 'household_weight'}, inplace=True)

    # Count the frequency of each gender for df_persons_synt
    gender_counts_synt = df_persons_synt['sex'].value_counts().reset_index()
    gender_counts_synt.columns = ['gender', 'count']

    # Group by gender and sum the weights
    gender_counts_mic_with_household_weight = df_population_mic.groupby('sex')['household_weight'].sum().reset_index()

    gender_counts_mic_with_household_weight.columns = ['gender', 'count']

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
        go.Pie(labels=gender_counts_mic_with_household_weight['gender'],
               values=gender_counts_mic_with_household_weight['count'],
               title='Gender Distribution - Microcensus'),
        row=1, col=2
    )

    # Updating layout and showing the figure
    fig.update_layout(title_text="Comparative Gender Distribution With Household Weight", width=1200, height=600)
    # TODO for showing the figure just uncomment the following line
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_gender_distribution_with_household_weight.png", scale=4)
    logging.info("Gender comparison with household weight has been plotted successfully.")

    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # gender_counts_mic_by_number = df_population_mic['sex'].value_counts().reset_index()
    #
    # gender_counts_mic_by_number.columns = ['gender', 'count']
    #
    # # Creating subplots
    # fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]])
    #
    # # Adding the pie chart for Synthetic Population
    # fig.add_trace(
    #     go.Pie(labels=gender_counts_synt['gender'], values=gender_counts_synt['count'],
    #            title='Gender Distribution Synthetic Population'),
    #     row=1, col=1
    # )
    #
    # # Adding the pie chart for Microcensus
    # fig.add_trace(
    #     go.Pie(labels=gender_counts_mic_by_number['gender'],
    #            values=gender_counts_mic_by_number['count'],
    #            title='Gender Distribution - Microcensus'),
    #     row=1, col=2
    # )
    #
    # # Updating layout and showing the figure
    # fig.update_layout(title_text="Comparative Gender Distribution By Number", width=1200, height=600)
    # # TODO for showing the figure just uncomment the following line
    # # fig.show()
    #
    # # Save the figure as an image with higher resolution
    # fig.write_image(f"{plots_directory}\\comparative_gender_distribution_by_number.png", scale=4)
    # logging.info("Gender comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate value counts and percentages for df_households_synt
    income_counts_synt = df_households_synt['incomeClass'].value_counts().reset_index()
    income_counts_synt.columns = ['Income Class', 'Count']
    income_counts_synt['Percentage'] = (income_counts_synt['Count'] / income_counts_synt['Count'].sum()) * 100

    # Remove rows where any value in any column is greater than 0
    df_population_mic_filtered = df_population_mic[df_population_mic.ne(-1).all(axis=1)]

    income_class_labels = {
        0: 'Under CHF 2000',
        1: 'CHF 2000 to 4000',
        2: 'CHF 4001 to 6000',
        3: 'CHF 6001 to 8000',
        4: 'CHF 8001 to 10000',
        5: 'CHF 10001 to 12000',
        6: 'CHF 12001 to 14000',
        7: 'CHF 14001 to 16000',
        8: 'More than CHF 16000'
    }

    # Calculate value counts and percentages for df_population_mic
    income_counts_mic_with_household_weight = df_population_mic_filtered.groupby('income_class')[
        'household_weight'].sum().reset_index()
    income_counts_mic_with_household_weight.columns = ['Income Class', 'Count']

    income_counts_mic_with_household_weight['Percentage'] = (income_counts_mic_with_household_weight['Count'] /
                                                             income_counts_mic_with_household_weight[
                                                                 'Count'].sum()) * 100

    income_counts_synt['Income Class'] = income_counts_synt['Income Class'].map(income_class_labels)
    income_counts_mic_with_household_weight['Income Class'] = income_counts_mic_with_household_weight[
        'Income Class'].map(income_class_labels)

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus income class percentage
    fig.add_trace(go.Bar(
        x=income_counts_mic_with_household_weight['Income Class'],
        y=income_counts_mic_with_household_weight['Percentage'],
        name='Microcensus',
        text=income_counts_mic_with_household_weight['Percentage'].round(1),
        textposition='outside',
        marker_color="blue"
    ))

    # Add bars for synthetic households income class percentage
    fig.add_trace(go.Bar(
        x=income_counts_synt['Income Class'],
        y=income_counts_synt['Percentage'],
        name='Synthetic',
        text=income_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Income Class Distribution - Percentage With Household Weight',
        xaxis_title='Income Class',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_income_distribution_with_household_weight.png", scale=4)
    logging.info("Income comparison with household weight has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate value counts and percentages for df_population_mic
    income_counts_mic_by_number = df_population_mic_filtered['income_class'].value_counts().reset_index().sort_values(
        'income_class')
    income_counts_mic_by_number.columns = ['Income Class', 'Count']

    income_counts_mic_by_number['Percentage'] = (income_counts_mic_by_number['Count'] /
                                                 income_counts_mic_by_number[
                                                     'Count'].sum()) * 100

    income_counts_mic_by_number['Income Class'] = income_counts_mic_by_number[
        'Income Class'].map(income_class_labels)

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus income class percentage
    fig.add_trace(go.Bar(
        x=income_counts_mic_by_number['Income Class'],
        y=income_counts_mic_by_number['Percentage'],
        name='Microcensus',
        text=income_counts_mic_by_number['Percentage'].round(1),
        textposition='outside',
        marker_color="blue"
    ))

    # Add bars for synthetic households income class percentage
    fig.add_trace(go.Bar(
        x=income_counts_synt['Income Class'],
        y=income_counts_synt['Percentage'],
        name='Synthetic',
        text=income_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Income Class Distribution - Percentage By Number',
        xaxis_title='Income Class',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_income_distribution_by_number.png", scale=4)
    logging.info("Income comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Create a custom order for the x-axis categories
    custom_order = ['0', '1', '2', '3+']

    # Calculate value counts and percentages for df_population_mic
    car_counts_mic_with_household_weight = df_population_mic.groupby('number_of_cars')[
        'household_weight'].sum().reset_index()
    car_counts_mic_with_household_weight.columns = ['Number of Cars', 'Count']
    car_counts_mic_with_household_weight['Percentage'] = (car_counts_mic_with_household_weight['Count'] /
                                                          car_counts_mic_with_household_weight['Count'].sum()) * 100

    # Calculate value counts and percentages for df_households_synt
    car_counts_synt = df_households_synt['numberOfCars'].value_counts().reset_index()
    car_counts_synt.columns = ['Number of Cars', 'Count']
    car_counts_synt['Percentage'] = (car_counts_synt['Count'] / car_counts_synt['Count'].sum()) * 100

    # Ensure the order of categories is as specified
    car_counts_mic_with_household_weight['Number of Cars'] = pd.Categorical(
        car_counts_mic_with_household_weight['Number of Cars'], categories=custom_order,
        ordered=True)
    car_counts_mic = car_counts_mic_with_household_weight.sort_values('Number of Cars')

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
        text=car_counts_mic['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    # Add bars for synthetic households car ownership percentage
    fig.add_trace(go.Bar(
        x=car_counts_synt['Number of Cars'],
        y=car_counts_synt['Percentage'],
        name='Synthetic - Car Ownership',
        text=car_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Car Ownership Distribution - Percentage With Household Weight',
        xaxis_title='Number of Cars',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_car_ownership_distribution_with_household_weight.png", scale=4)
    logging.info("Car ownership comparison with household weight has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # car_counts_mic_by_number = df_population_mic['number_of_cars'].value_counts().reset_index().sort_values(
    #     'number_of_cars')
    # car_counts_mic_by_number.columns = ['Number of Cars', 'Count']
    #
    # car_counts_mic_by_number['Percentage'] = (car_counts_mic_by_number['Count'] / car_counts_mic_by_number[
    #     'Count'].sum()) * 100
    #
    # car_counts_mic_by_number['Number of Cars'] = pd.Categorical(car_counts_mic_by_number['Number of Cars'],
    #                                                             categories=custom_order,
    #                                                             ordered=True)
    #
    # car_counts_mic_by_number = car_counts_mic_by_number.sort_values('Number of Cars')
    #
    # # Create a figure with subplots
    # fig = go.Figure()
    #
    # # Add bars for microcensus car ownership percentage
    # fig.add_trace(go.Bar(
    #     x=car_counts_mic_by_number['Number of Cars'],
    #     y=car_counts_mic_by_number['Percentage'],
    #     name='Microcensus - Car Ownership',
    #     text=car_counts_mic_by_number['Percentage'].round(1),
    #     textposition='outside',
    #     marker_color='blue'
    # ))
    #
    # # Add bars for synthetic households car ownership percentage
    # fig.add_trace(go.Bar(
    #     x=car_counts_synt['Number of Cars'],
    #     y=car_counts_synt['Percentage'],
    #     name='Synthetic - Car Ownership',
    #     text=car_counts_synt['Percentage'].round(1),
    #     textposition='outside',
    #     marker_color='red'
    # ))
    #
    # # Update the layout for a grouped bar chart
    # fig.update_layout(
    #     barmode='group',
    #     title='Comparison of Car Ownership Distribution - Percentage By Number',
    #     xaxis_title='Number of Cars',
    #     yaxis_title='Percentage (%)',
    #     legend_title='Dataset',
    #     width=1200,
    #     height=600
    # )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    # fig.write_image(f"{plots_directory}\\comparative_car_ownership_distribution_by_number.png", scale=4)
    # logging.info("Car ownership comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate total counts for each type
    type_counts_synt = df_activity_synt['type'].value_counts().reset_index()
    type_counts_synt.columns = ['Type', 'Count']
    type_counts_synt['Percentage'] = (type_counts_synt['Count'] / type_counts_synt['Count'].sum()) * 100

    # Group by purpose and sum the household weights for each purpose
    purpose_counts_with_household_weight = df_trips_mic.groupby('purpose')['household_weight'].sum().reset_index()
    purpose_counts_with_household_weight.columns = ['Purpose', 'Weighted_Count']

    # Calculate the total weight
    total_weight = purpose_counts_with_household_weight['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    purpose_counts_with_household_weight['Percentage'] = (purpose_counts_with_household_weight[
                                                              'Weighted_Count'] / total_weight) * 100

    # Standardize purpose labels for microcensus data
    purpose_counts_with_household_weight['Purpose'] = purpose_counts_with_household_weight['Purpose'].str.lower()

    # Standardize type labels for synthetic data
    type_counts_synt['Type'] = type_counts_synt['Type'].str.lower()

    # Filter out the specified activities
    excluded_activities = ['outside', 'freight_loading', 'freight_unloading', 'pt interaction']

    # Filter and recompute percentages for synthetic data
    filtered_type_counts_synt = type_counts_synt[~type_counts_synt['Type'].isin(excluded_activities)].copy()

    # Recompute percentages
    filtered_type_counts_synt['Percentage'] = (filtered_type_counts_synt['Count'] / filtered_type_counts_synt[
        'Count'].sum()) * 100

    # Filter and recompute percentages for microcensus data
    filtered_purpose_counts_with_household_weight = purpose_counts_with_household_weight[
        ~purpose_counts_with_household_weight['Purpose'].isin(excluded_activities)].copy()

    # Recompute percentages
    filtered_purpose_counts_with_household_weight['Percentage'] = (filtered_purpose_counts_with_household_weight[
                                                                       'Weighted_Count'] /
                                                                   filtered_purpose_counts_with_household_weight[
                                                                       'Weighted_Count'].sum()) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for synthetic activity types percentage
    fig.add_trace(go.Bar(
        x=filtered_type_counts_synt['Type'],
        y=filtered_type_counts_synt['Percentage'],
        name='Synthetic',
        text=filtered_type_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    # Add bars for microcensus trip purposes percentage
    fig.add_trace(go.Bar(
        x=filtered_purpose_counts_with_household_weight['Purpose'],
        y=filtered_purpose_counts_with_household_weight['Percentage'],
        name='Microcensus',
        text=filtered_purpose_counts_with_household_weight['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Activity Types and Trip Purposes (Percentage) With Household Weight',
        xaxis_title='Activity Types and Trip Purposes',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_trip_purpose_distribution_with_household_weight.png", scale=4)
    logging.info("Trip purpose comparison with household weight has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Group by purpose and sum the household weights for each purpose
    purpose_counts_by_number = df_trips_mic['purpose'].value_counts().reset_index().sort_values('purpose')
    purpose_counts_by_number.columns = ['Purpose', 'Weighted_Count']

    # Calculate the total weight
    total_weight = purpose_counts_by_number['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    purpose_counts_by_number['Percentage'] = (purpose_counts_by_number[
                                                  'Weighted_Count'] / total_weight) * 100

    # Standardize purpose labels for microcensus data
    purpose_counts_by_number['Purpose'] = purpose_counts_by_number['Purpose'].str.lower()

    # Filter and recompute percentages for microcensus data
    purpose_counts_by_number = purpose_counts_by_number[
        ~purpose_counts_by_number['Purpose'].isin(excluded_activities)].copy()

    # Recompute percentages
    purpose_counts_by_number['Percentage'] = (purpose_counts_by_number[
                                                  'Weighted_Count'] /
                                              purpose_counts_by_number[
                                                  'Weighted_Count'].sum()) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for synthetic activity types percentage
    fig.add_trace(go.Bar(
        x=filtered_type_counts_synt['Type'],
        y=filtered_type_counts_synt['Percentage'],
        name='Synthetic',
        text=filtered_type_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    # Add bars for microcensus trip purposes percentage
    fig.add_trace(go.Bar(
        x=purpose_counts_by_number['Purpose'],
        y=purpose_counts_by_number['Percentage'],
        name='Microcensu',
        text=purpose_counts_by_number['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Activity Types and Trip Purposes (Percentage) By Number',
        xaxis_title='Activity Types and Trip Purposes',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_trip_purpose_distribution_by_number.png", scale=4)
    logging.info("Trip purpose comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Now calculate the value counts and percentages for the cleaned-up modes
    mode_counts_synt = df_legs_synt['mode'].value_counts().reset_index()
    mode_counts_synt.columns = ['Mode', 'Count']
    mode_counts_synt['Percentage'] = (mode_counts_synt['Count'] / mode_counts_synt['Count'].sum()) * 100

    # Group by mode and sum the household weights for each mode
    mode_counts_mic_with_household_weight = df_trips_mic.groupby('mode')['household_weight'].sum().reset_index()
    mode_counts_mic_with_household_weight.columns = ['Mode', 'Weighted_Count']

    # Calculate the total weight
    total_weight = mode_counts_mic_with_household_weight['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    mode_counts_mic_with_household_weight['Percentage'] = (mode_counts_mic_with_household_weight[
                                                               'Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_mic_with_household_weight['Mode'],
        y=mode_counts_mic_with_household_weight['Percentage'],
        name='Microcensus',
        text=mode_counts_mic_with_household_weight['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic',
        text=mode_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage With Household Weight',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_trip_mode_share_distribution_with_household_weight.png", scale=4)
    logging.info("Trip mode share comparison with household weight has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Group by age and sum the weights for each age
    mode_counts_mic_by_number = df_trips_mic['mode'].value_counts().reset_index().sort_values('mode')
    mode_counts_mic_by_number.columns = ['Mode', 'Weighted_Count']

    # Calculate the total weight
    total_weight = mode_counts_mic_by_number['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    mode_counts_mic_by_number['Percentage'] = (mode_counts_mic_by_number[
                                                   'Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_mic_by_number['Mode'],
        y=mode_counts_mic_by_number['Percentage'],
        name='Microcensus',
        text=mode_counts_mic_by_number['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic',
        text=mode_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - PercentageBy Number',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_trip_mode_share_distribution_by_number.png", scale=4)
    logging.info("Trip mode share comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Group by age and sum the weights for each age
    weighted_age_counts_with_household_weight = df_population_mic.groupby('age')['household_weight'].sum().reset_index()
    weighted_age_counts_with_household_weight.columns = ['Age', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_age_counts_with_household_weight['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_age_counts_with_household_weight['Percentage_weighted'] = (weighted_age_counts_with_household_weight[
                                                                            'Weighted_Count'] / total_weight) * 100

    # Calculate age distribution for df_persons_synt
    age_counts_persons = df_persons_synt['age'].value_counts().sort_index().reset_index()
    age_counts_persons.columns = ['Age', 'Count_persons']
    age_counts_persons['Percentage_persons'] = (age_counts_persons['Count_persons'] / age_counts_persons[
        'Count_persons'].sum()) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add the first bar for df_population_mic percentage
    fig.add_trace(go.Bar(
        x=weighted_age_counts_with_household_weight['Age'],
        y=weighted_age_counts_with_household_weight['Percentage_weighted'],
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
        title='Comparison of Age Distribution With Household Weight',
        xaxis_title='Age',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_age_distribution_with_household_weight.png", scale=4)
    logging.info("Age comparison with household weight has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    weighted_age_counts_by_number = df_population_mic['age'].value_counts().reset_index().sort_values('age')
    weighted_age_counts_by_number.columns = ['Age', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_age_counts_by_number['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_age_counts_by_number['Percentage_weighted'] = (weighted_age_counts_by_number[
                                                                'Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add the first bar for df_population_mic percentage
    fig.add_trace(go.Bar(
        x=weighted_age_counts_by_number['Age'],
        y=weighted_age_counts_by_number['Percentage_weighted'],
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
        title='Comparison of Age Distribution By Number',
        xaxis_title='Age',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_age_distribution_by_number.png", scale=4)
    logging.info("Age comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    departure_counts_mic = df_trips_mic.groupby('departure_time').size().reset_index(name='Count')
    departure_counts_mic['Type'] = 'Microcensus'

    departure_counts_mic['Count'] = departure_counts_mic['Count'] / df_trips_mic.shape[0]

    departure_counts_mic = departure_counts_mic.rename(columns={'departure_time': 'Time'})

    departure_counts_synt = df_trips_synt.groupby('departure_time').size().reset_index(name='Count')
    departure_counts_synt['Type'] = 'Synthetic'

    departure_counts_synt['Count'] = departure_counts_synt['Count'] / df_trips_synt.shape[0]

    departure_counts_synt = departure_counts_synt.rename(columns={'departure_time': 'Time'})

    # Combine data
    time_counts = pd.concat([departure_counts_mic, departure_counts_synt], axis=0)

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
    fig.write_image(f"{plots_directory}\\comparative_departure_time_distribution.png", scale=4)
    logging.info("Departure time comparison has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------

    arrival_counts_mic = df_trips_mic.groupby('arrival_time').size().reset_index(name='Count')
    arrival_counts_mic['Type'] = 'Microcensus'

    arrival_counts_mic['Count'] = arrival_counts_mic['Count'] / df_trips_mic.shape[0]

    arrival_counts_mic = arrival_counts_mic.rename(columns={'arrival_time': 'Time'})

    arrival_counts_synt = df_trips_synt.groupby('arrival_time').size().reset_index(name='Count')
    arrival_counts_synt['Type'] = 'Synthetic'

    arrival_counts_synt['Count'] = arrival_counts_synt['Count'] / df_trips_synt.shape[0]

    arrival_counts_synt = arrival_counts_synt.rename(columns={'arrival_time': 'Time'})

    # Combine data
    time_counts = pd.concat([arrival_counts_mic, arrival_counts_synt], axis=0)

    # Plot using Plotly Express
    fig = px.bar(time_counts, x='Time', y='Count', color='Type',
                 title='Arrival Times over a Day',
                 labels={'Count': 'Count', 'Time': 'Time of Day'},
                 barmode='group')

    # Customize x-axis ticks and scale y-axis
    fig.update_xaxes(type='category', tickangle=45, dtick=1)
    fig.update_yaxes(range=[0, time_counts['Count'].max()])

    # Show plot
    fig.update_layout(width=1200, height=600)
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_arrival_time_distribution.png", scale=4)
    logging.info("Arrival time comparison has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Calculate total counts for each activity chain for Synthetic Population
    chain_counts_syn = df_activity_chains_syn['activity_chain'].value_counts().reset_index()
    chain_counts_syn.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Synthetic Population
    total_count_syn = chain_counts_syn['Count'].sum()
    chain_counts_syn['Normalized Count'] = (chain_counts_syn['Count'] / total_count_syn) * 100

    # Select the most common activity chains for Synthetic Population
    top_chain_counts_syn = chain_counts_syn.nlargest(10, 'Normalized Count')

    # Calculate total counts for each activity chain for Microcensus Population
    chain_counts_mic = df_activity_chains_mic['activity_chain'].value_counts().reset_index().sort_values(
        'activity_chain')
    chain_counts_mic.columns = ['Activity Chain', 'Count']
    # Normalize the counts for Microcensus Population
    total_count_mic = chain_counts_mic['Count'].sum()
    chain_counts_mic['Normalized Count'] = (chain_counts_mic['Count'] / total_count_mic) * 100

    # Select the top 10 most common activity chains for Microcensus Population
    top_chain_counts_mic = chain_counts_mic.nlargest(10, 'Normalized Count')

    # Merge the two DataFrames
    merged_df = pd.merge(top_chain_counts_syn, top_chain_counts_mic, on='Activity Chain', suffixes=('_syn', '_mic'))

    # Creating a figure with grouped bar chart
    fig = go.Figure()

    # Add bars for Synthetic Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_syn'],
        text=merged_df['Normalized Count_syn'].round(1),
        textposition='outside',
        name='Synthetic Population',
        marker_color='blue'
    ))

    # Add bars for Microcensus Population
    fig.add_trace(go.Bar(
        x=merged_df['Activity Chain'],
        y=merged_df['Normalized Count_mic'],
        name='Microcensus Population',
        text=merged_df['Normalized Count_mic'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Update the layout
    fig.update_layout(
        barmode='group',
        title_text="Comparison of Top Activity Chains Between Synthetic and Microcensus Population",
        xaxis_title="Activity Chain",
        yaxis_title="Normalized Count (%)",
        width=1600,
        height=800
    )

    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparative_top_activity_chain_distribution.png", scale=4)
    logging.info("Top 10 ctivity chain comparison has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
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
    logging.info("Activity chain comparison has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Now calculate the value counts and percentages for the cleaned-up modes
    mode_counts_synt = df_legs_synt['mode'].value_counts().reset_index()
    mode_counts_synt.columns = ['Mode', 'Count']
    mode_counts_synt['Percentage'] = (mode_counts_synt['Count'] / mode_counts_synt['Count'].sum()) * 100

    # Now calculate the value counts and percentages for the cleaned-up modes
    mode_counts_sim = df_legs_sim['mode'].value_counts().reset_index()
    mode_counts_sim.columns = ['Mode', 'Count']
    mode_counts_sim['Percentage'] = (mode_counts_sim['Count'] / mode_counts_sim['Count'].sum()) * 100

    # Group by mode and sum the household weights for each mode
    weighted_mode_counts_with_household_weight = df_trips_mic.groupby('mode')['household_weight'].sum().reset_index()
    weighted_mode_counts_with_household_weight.columns = ['Mode', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_mode_counts_with_household_weight['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_mode_counts_with_household_weight['Percentage'] = (weighted_mode_counts_with_household_weight[
                                                                    'Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=weighted_mode_counts_with_household_weight['Mode'],
        y=weighted_mode_counts_with_household_weight['Percentage'],
        text=weighted_mode_counts_with_household_weight['Percentage'].round(1),
        textposition='outside',
        name='Microcensus',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic',
        text=mode_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_sim['Mode'],
        y=mode_counts_sim['Percentage'],
        name='Simulation',
        text=mode_counts_sim['Percentage'].round(1),
        textposition='outside',
        marker_color='green'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage With Household Weight',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\validation_mode_share_distribution_with_household_weight.png", scale=4)
    logging.info("Mode share comparison with household weight has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------
    # Group by mode and sum the household weights for each mode
    weighted_mode_counts_by_number = df_trips_mic['mode'].value_counts().reset_index().sort_values('mode')
    weighted_mode_counts_by_number.columns = ['Mode', 'Weighted_Count']

    # Calculate the total weight
    total_weight = weighted_mode_counts_by_number['Weighted_Count'].sum()

    # Calculate percentage distribution based on weighted counts
    weighted_mode_counts_by_number['Percentage'] = (weighted_mode_counts_by_number[
                                                        'Weighted_Count'] / total_weight) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=weighted_mode_counts_by_number['Mode'],
        y=weighted_mode_counts_by_number['Percentage'],
        name='Microcensus',
        text=weighted_mode_counts_by_number['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic',
        text=mode_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_sim['Mode'],
        y=mode_counts_sim['Percentage'],
        name='Simulation',
        text=mode_counts_sim['Percentage'].round(1),
        textposition='outside',
        marker_color='green'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage By Number',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\validation_mode_share_distribution_by_number.png", scale=4)
    logging.info("Mode share comparison by number has been plotted successfully.")
    # ------------------------------------------------------------------------------------------------------------------------------------------------

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage
    fig.add_trace(go.Bar(
        x=weighted_mode_counts_by_number['Mode'],
        y=weighted_mode_counts_by_number['Percentage'],
        name='Microcensus by Number',
        text=weighted_mode_counts_by_number['Percentage'].round(1),
        textposition='outside',
        marker_color='blue'
    ))

    fig.add_trace(go.Bar(
        x=weighted_mode_counts_with_household_weight['Mode'],
        y=weighted_mode_counts_with_household_weight['Percentage'],
        name='Microcensus - Household',
        text=weighted_mode_counts_with_household_weight['Percentage'].round(1),
        textposition='outside',
        marker_color='yellow'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_synt['Mode'],
        y=mode_counts_synt['Percentage'],
        name='Synthetic',
        text=mode_counts_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_counts_sim['Mode'],
        y=mode_counts_sim['Percentage'],
        name='Simulation',
        text=mode_counts_sim['Percentage'].round(1),
        textposition='outside',
        marker_color='green'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution all Together',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{plots_directory}\\comparison_mode_share_distribution_all_together.png", scale=4)
    logging.info("Mode share comparison all together has been plotted successfully.")

    # Save the Mode share distribution for all the datasets in a csv data file
    df_household = weighted_mode_counts_with_household_weight.rename(columns={"Weighted_Count": "Household_Count", "Percentage": "Household_Percentage"})
    df_number = weighted_mode_counts_by_number.rename(columns={"Weighted_Count": "Number_Count", "Percentage": "Number_Percentage"})
    df_sim = mode_counts_sim.rename(columns={"Count": "Simulation_Count", "Percentage": "Simulation_Percentage"})
    df_synt = mode_counts_synt.rename(columns={"Count": "Synthetic_Count", "Percentage": "Synthetic_Percentage"})

    mode_share_directory = os.path.join(plots_directory, 'mode_share')

    mode_share_comparison = df_household.merge(df_number, on='Mode', how='outer').merge(df_sim, on='Mode', how='outer').merge(df_synt, on='Mode', how='outer')

    mode_share_rounded_df = mode_share_comparison.round(2)
    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    mode_share_rounded_df.to_csv(f"{mode_share_directory}\\mode_share_trip_comparison.csv", index=False)
    logging.info("Mode share comparison data has been saved successfully.")