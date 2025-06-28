import os
import threading
import time
import json
from collections import Counter, deque
import streamlit as st
from kafka import KafkaConsumer
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle
from datetime import datetime

# --- CONFIGURAZIONE ---
KAFKA_BOOTSTRAP = os.popen(
    "kubectl get service iototal-kafka-controller-0-external --namespace default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
).read().strip() + ":9094"
TOPIC = "network-predictions"
POLL_INTERVAL = 1.0

# --- BUFFER ---
predictions_buffer = deque(maxlen=1000)
label_color_map = {
    'Normal': '#2E8B57',      # Sea Green
    'DoS': '#DC143C',         # Crimson
    'Probe': '#FF8C00',       # Dark Orange
    'R2L': '#9932CC',         # Dark Orchid
    'U2R': '#B22222',         # Fire Brick
}
color_palette = cycle(plt.get_cmap('tab20').colors)

# --- FUNZIONE LETTURA KAFKA ---
def kafka_reader():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='dashboard-predictions-group',
        value_deserializer=lambda x: x.decode('utf-8'),
    )
    
    for msg in consumer:
        try:
            # Parse JSON message from Spark
            prediction_data = json.loads(msg.value.strip())
            predictions_buffer.append(prediction_data)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            continue

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="🔒 IoTotal Network Security Dashboard", layout="wide")
st.title("🔒 IoTotal Network Security Dashboard - Real-time Predictions")

# Lancia il thread Kafka solo una volta
if 'kafka_thread' not in st.session_state:
    thread = threading.Thread(target=kafka_reader, daemon=True)
    thread.start()
    st.session_state.kafka_thread = thread

# SIDEBAR
with st.sidebar:
    st.markdown("## Dashboard Settings")
    interval = st.number_input("Refresh interval (s)", min_value=0.1, max_value=10.0, value=float(POLL_INTERVAL))
    max_predictions = st.number_input("Max predictions in memory", min_value=100, max_value=5000, value=1000)
    if max_predictions != predictions_buffer.maxlen:
        predictions_buffer = deque(predictions_buffer, maxlen=max_predictions)
    
    st.markdown("## Legend")
    st.markdown("**Prediction Labels:**")
    st.markdown("- 🟢 **0.0**: Normal Traffic")
    st.markdown("- 🔴 **1.0**: DoS Attack")
    st.markdown("- 🟠 **2.0**: Probe Attack")
    st.markdown("- 🟣 **3.0**: R2L Attack")
    st.markdown("- 🔴 **4.0**: U2R Attack")

# MAIN DASHBOARD
col1, col2 = st.columns([2, 1])

with col1:
    chart_placeholder = st.empty()

with col2:
    metrics_placeholder = st.empty()
    recent_predictions_placeholder = st.empty()

# LOOP DI AGGIORNAMENTO
while True:
    time.sleep(interval)
    
    if not predictions_buffer:
        with chart_placeholder.container():
            st.info("Waiting for predictions from Kafka...")
        continue
    
    # Convert predictions to DataFrame for analysis
    df_predictions = pd.DataFrame(list(predictions_buffer))
    
    # Count predictions by label
    prediction_counts = Counter([pred['predicted_label'] for pred in predictions_buffer])
    
    # Map numeric predictions to labels
    label_mapping = {
        0.0: 'Normal',
        1.0: 'DoS',
        2.0: 'Probe', 
        3.0: 'R2L',
        4.0: 'U2R'
    }
    
    # Create chart data
    chart_data = {}
    for pred_label, count in prediction_counts.items():
        label_name = label_mapping.get(pred_label, f'Unknown ({pred_label})')
        chart_data[label_name] = count
    
    if chart_data:
        df_chart = pd.DataFrame.from_dict(chart_data, orient='index', columns=['Count'])
        df_chart = df_chart.sort_values(by='Count', ascending=False)
        
        # Get colors for each label
        bar_colors = [label_color_map.get(label, next(color_palette)) for label in df_chart.index]
        
        # Create the chart
        with chart_placeholder.container():
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(df_chart.index, df_chart['Count'], color=bar_colors)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
            
            ax.set_xlabel("Prediction Type")
            ax.set_ylabel("Count")
            ax.set_title("Network Traffic Predictions Distribution")
            ax.set_xticklabels(df_chart.index, rotation=45, ha='right')
            
            # Set Y axis to integers only
            max_count = df_chart['Count'].max()
            ax.set_yticks(np.arange(0, max_count + 1, max(1, max_count // 10)))
            
            plt.tight_layout()
            st.pyplot(fig)
    
    # Display metrics
    with metrics_placeholder.container():
        st.markdown("### 📊 Current Metrics")
        
        total_predictions = len(predictions_buffer)
        normal_count = prediction_counts.get(0.0, 0)
        attack_count = total_predictions - normal_count
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Total Predictions", total_predictions)
        
        with col_b:
            st.metric("Normal Traffic", normal_count)
        
        with col_c:
            st.metric("Potential Attacks", attack_count)
        
        if total_predictions > 0:
            attack_percentage = (attack_count / total_predictions) * 100
            st.metric("Attack Rate", f"{attack_percentage:.1f}%")
    
    # Display recent predictions
    with recent_predictions_placeholder.container():
        st.markdown("### 🕐 Recent Predictions")
        
        # Get last 10 predictions
        recent_preds = list(predictions_buffer)[-10:]
        recent_preds.reverse()  # Show most recent first
        
        for i, pred in enumerate(recent_preds):
            predicted_label = pred.get('predicted_label', 'Unknown')
            actual_label = pred.get('actual_label', 'Unknown')
            rate = pred.get('rate', 'Unknown')
            protocol_type = pred.get('protocol_type', 'Unknown')
            
            # Get prediction type name
            pred_name = label_mapping.get(predicted_label, f'Unknown ({predicted_label})')
            
            # Color code based on prediction
            if predicted_label == 0.0:
                status_color = "🟢"
            else:
                status_color = "🔴"
            
            timestamp = pred.get('prediction_timestamp', 'Unknown')
            
            with st.expander(f"{status_color} {pred_name} - Rate: {rate}", expanded=(i < 3)):
                col_x, col_y = st.columns(2)
                with col_x:
                    st.write(f"**Predicted:** {pred_name}")
                    st.write(f"**Actual:** {actual_label}")
                    st.write(f"**Rate:** {rate}")
                with col_y:
                    st.write(f"**Protocol:** {protocol_type}")
                    st.write(f"**Timestamp:** {timestamp}")