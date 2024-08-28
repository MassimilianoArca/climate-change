import os
import pickle

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Define Paths and Load Data
data_folder = os.path.join("..", "..", "..", "..", "data", "berlin")
clean_data_folder = os.path.join(data_folder, "clean_data")
surface_df = pd.read_excel(os.path.join(clean_data_folder, "surface.xlsx"))
ground_df = pd.read_excel(os.path.join(clean_data_folder, "ground.xlsx"))

bacteria_columns = [
    "E.Coli (MPN/100ml)",
    "Enterococcus (MPN/100ml)",
    "Coliform (MPN/100ml)"
]

# Prepare the data for the models
df = surface_df[surface_df['Station'] == 105]

# Add the year and month columns
df["Year"] = df["DateTime"].dt.year
df["Month"] = df["DateTime"].dt.month

# Drop unnecessary columns
df = df.drop(columns=["DateTime", "Station"] + bacteria_columns).dropna()

X = df.drop(columns=["DOC (mg/l)"])
y = df[["DOC (mg/l)"]]

# Load the precomputed results
xgb_results = pickle.load(open("XGBoost-Station105.pickle", "rb"))

# Get the subset with the best RMSE
best_subset = tuple(sorted(min(xgb_results, key=lambda x: xgb_results[x]["rmse"])))

# Initialize the session state
if 'attempts' not in st.session_state:
    st.session_state.attempts = 2
    st.session_state.game_over = False
    st.session_state.success = False

st.title("Feature-Based Prediction Viewer")

# Create two columns
col1, col2 = st.columns([1, 2.5])


def plot_result():
    
    with col1:
        
        for feature in X.columns:
            st.session_state.checkbox_values[feature] = feature in best_subset
    
    with col2:
        
        st.header("Final Result")
        
        y_pred = xgb_results[best_subset]["y_pred"]
        y_true = xgb_results[best_subset]["y_true"]
        rmse = xgb_results[best_subset]["rmse"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=y_true.index, y=y_true["DOC (mg/l)"], mode="lines", name="True"))    
        fig.add_trace(go.Scatter(x=y_true.index, y=y_pred, mode="lines", name="Predicted"))
        st.plotly_chart(fig)
        
        st.markdown(f"<h2 style='text-align: center; font-size: 24px;'>RMSE: {rmse:.3f}</h2>", unsafe_allow_html=True)
            
def process_selection(selected_features_tuple):
    with col2:
        st.header("Prediction Result")

        if selected_features_tuple and not st.session_state.game_over:
            if selected_features_tuple in xgb_results:
                if selected_features_tuple == best_subset:
                    y_pred = xgb_results[selected_features_tuple]["y_pred"]
                    y_true = xgb_results[selected_features_tuple]["y_true"]
                    rmse = xgb_results[selected_features_tuple]["rmse"]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=y_true.index, y=y_true["DOC (mg/l)"], mode="lines", name="True"))
                    fig.add_trace(go.Scatter(x=y_true.index, y=y_pred, mode="lines", name="Predicted"))
                    st.plotly_chart(fig)

                    st.markdown(f"<h2 style='text-align: center; font-size: 24px;'>RMSE: {rmse:.3f}</h2>", unsafe_allow_html=True)

                    st.session_state.success = True
                    st.success("You got it right!")

                else:
                    
                    y_pred = xgb_results[selected_features_tuple]["y_pred"]
                    y_true = xgb_results[selected_features_tuple]["y_true"]
                    rmse = xgb_results[selected_features_tuple]["rmse"]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=y_true.index, y=y_true["DOC (mg/l)"], mode="lines", name="True"))
                    fig.add_trace(go.Scatter(x=y_true.index, y=y_pred, mode="lines", name="Predicted"))
                    st.plotly_chart(fig)

                    st.markdown(f"<h2 style='text-align: center; font-size: 24px;'>RMSE: {rmse:.3f}</h2>", unsafe_allow_html=True)


                    if st.session_state.attempts > 0:
                        
                        st.warning(f"Wrong! You have {st.session_state.attempts} attempts left.")
                    else:
                        st.session_state.game_over = True
                        st.error("Game Over! You've used all your attempts.")
                        
                        st.button("Show Final Result", key="show_result", on_click=plot_result)
                        
                    st.session_state.attempts -= 1
                    
                    
# Create checkboxes in the left column (col1)
selected_features = []
with col1:
    st.header("Select Features")

    # Initialize the checkboxes based on the session state or default values
    if 'checkbox_values' not in st.session_state:
        st.session_state.checkbox_values = {feature: False for feature in sorted(X.columns)}

    # Display the checkboxes and handle their state
    for feature in sorted(X.columns):
        st.session_state.checkbox_values[feature] = st.checkbox(
            feature,
            key=f"checkbox_{feature}",  # Ensures each checkbox has a unique key
            value=st.session_state.checkbox_values[feature],
            disabled=st.session_state.attempts < 0
        )
        if st.session_state.checkbox_values[feature]:
            selected_features.append(feature)
       
# Button to submit the selected subset
st.button("Submit", disabled=st.session_state.game_over, on_click=process_selection, args=(tuple(selected_features),))

# Show success celebration if the user got it right
if st.session_state.success:
    st.balloons()
    st.stop()
