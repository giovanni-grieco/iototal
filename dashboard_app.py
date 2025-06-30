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

# Load label mapping from JSON file
def load_label_mapping():
    try:
        with open('/home/giovanni/Projects/iototal/labels-to-code.json', 'r') as f:
            labels_data = json.load(f)
        return labels_data['index_to_label']
    except Exception as e:
        print(f"Error loading label mapping: {e}")
        return {}

LABEL_MAPPING = load_label_mapping()

# Define color mapping for different attack categories
def get_label_color(label):
    """Assign colors based on attack type categories"""
    label_upper = label.upper()
    
    if label_upper == 'BENIGN':
        return '#2E8B57'  # Sea Green for normal traffic
    elif 'DDOS' in label_upper:
        return '#DC143C'  # Crimson for DDoS attacks
    elif 'DOS' in label_upper:
        return '#B22222'  # Fire Brick for DoS attacks
    elif 'MIRAI' in label_upper:
        return '#8B0000'  # Dark Red for Mirai botnet
    elif 'RECON' in label_upper:
        return '#FF8C00'  # Dark Orange for reconnaissance
    elif 'VULNERABILITY' in label_upper:
        return '#FF4500'  # Orange Red for vulnerability scans
    elif 'MITM' in label_upper or 'SPOOFING' in label_upper:
        return '#9932CC'  # Dark Orchid for man-in-the-middle/spoofing
    elif 'BRUTEFORCE' in label_upper:
        return '#4B0082'  # Indigo for brute force
    elif 'INJECTION' in label_upper:
        return '#8B008B'  # Dark Magenta for injection attacks
    elif 'XSS' in label_upper:
        return '#DA70D6'  # Orchid for XSS
    elif 'HIJACKING' in label_upper:
        return '#9370DB'  # Medium Slate Blue for hijacking
    elif 'BACKDOOR' in label_upper or 'MALWARE' in label_upper:
        return '#800080'  # Purple for malware/backdoors
    elif 'UPLOADING' in label_upper:
        return '#20B2AA'  # Light Sea Green for upload attacks
    else:
        return '#696969'  # Dim Gray for unknown/other

# --- BUFFER ---
predictions_buffer = deque(maxlen=1000)
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
    st.markdown("**Attack Categories:**")
    st.markdown("- 🟢 **BENIGN**: Normal Traffic")
    st.markdown("- 🔴 **DDOS**: Distributed Denial of Service")
    st.markdown("- 🔥 **DOS**: Denial of Service")
    st.markdown("- ⚫ **MIRAI**: Mirai Botnet Attacks")
    st.markdown("- 🟠 **RECON**: Reconnaissance/Scanning")
    st.markdown("- 🟡 **VULNERABILITY**: Vulnerability Scans")
    st.markdown("- 🟣 **MITM/SPOOFING**: Man-in-the-Middle/Spoofing")
    st.markdown("- 🟦 **INJECTION**: Code Injection Attacks")
    st.markdown("- � **MALWARE**: Backdoors/Malware")
    st.markdown("- 💙 **OTHER**: Other Attack Types")

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
    prediction_counts = Counter([pred.get('predicted_label', 'Unknown') for pred in predictions_buffer])
    
    # Create chart data using actual label names
    chart_data = {}
    for pred_label, count in prediction_counts.items():
        # Convert numeric index to label name if possible
        if isinstance(pred_label, (int, float)) and str(int(pred_label)) in LABEL_MAPPING:
            label_name = LABEL_MAPPING[str(int(pred_label))]
        elif isinstance(pred_label, str) and pred_label in LABEL_MAPPING:
            label_name = LABEL_MAPPING[pred_label]
        else:
            label_name = str(pred_label)
        chart_data[label_name] = count
    
    if chart_data:
        df_chart = pd.DataFrame.from_dict(chart_data, orient='index', columns=['Count'])
        df_chart = df_chart.sort_values(by='Count', ascending=False)
        
        # Get colors for each label
        bar_colors = [get_label_color(label) for label in df_chart.index]
        
        # Create the chart
        with chart_placeholder.container():
            # Limit to top 15 most frequent labels for readability
            df_chart_display = df_chart.head(15)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.bar(range(len(df_chart_display)), df_chart_display['Count'], 
                         color=[get_label_color(label) for label in df_chart_display.index])
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', fontsize=9)
            
            ax.set_xlabel("Attack Types")
            ax.set_ylabel("Count")
            ax.set_title(f"Network Traffic Predictions Distribution (Top {len(df_chart_display)} Types)")
            
            # Set x-axis labels with rotation
            ax.set_xticks(range(len(df_chart_display)))
            ax.set_xticklabels(df_chart_display.index, rotation=45, ha='right', fontsize=8)
            
            # Set Y axis to integers only
            max_count = df_chart_display['Count'].max()
            if max_count > 0:
                ax.set_yticks(np.arange(0, max_count + 1, max(1, max_count // 10)))
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Show summary of remaining types if any
            if len(df_chart) > 15:
                remaining_count = df_chart.iloc[15:]['Count'].sum()
                st.info(f"+ {len(df_chart) - 15} more attack types with {remaining_count} total predictions")
    
    # Display metrics
    with metrics_placeholder.container():
        st.markdown("### 📊 Current Metrics")
        
        total_predictions = len(predictions_buffer)
        # Count benign vs attack traffic
        benign_count = 0
        attack_count = 0
        
        for pred in predictions_buffer:
            pred_label = pred.get('predicted_label', 'Unknown')
            # Convert to label name
            if isinstance(pred_label, (int, float)) and str(int(pred_label)) in LABEL_MAPPING:
                label_name = LABEL_MAPPING[str(int(pred_label))]
            elif isinstance(pred_label, str) and pred_label in LABEL_MAPPING:
                label_name = LABEL_MAPPING[pred_label]
            else:
                label_name = str(pred_label)
            
            if label_name.upper() == 'BENIGN':
                benign_count += 1
            else:
                attack_count += 1
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Total Predictions", total_predictions)
        
        with col_b:
            st.metric("Benign Traffic", benign_count)
        
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
            
            # Convert predicted label to name
            if isinstance(predicted_label, (int, float)) and str(int(predicted_label)) in LABEL_MAPPING:
                pred_name = LABEL_MAPPING[str(int(predicted_label))]
            elif isinstance(predicted_label, str) and predicted_label in LABEL_MAPPING:
                pred_name = LABEL_MAPPING[predicted_label]
            else:
                pred_name = str(predicted_label)
            
            # Convert actual label to name if available
            if isinstance(actual_label, (int, float)) and str(int(actual_label)) in LABEL_MAPPING:
                actual_name = LABEL_MAPPING[str(int(actual_label))]
            elif isinstance(actual_label, str) and actual_label in LABEL_MAPPING:
                actual_name = LABEL_MAPPING[actual_label]
            else:
                actual_name = str(actual_label)
            
            # Color code based on prediction
            if pred_name.upper() == 'BENIGN':
                status_color = "🟢"
            else:
                status_color = "🔴"
            
            timestamp = pred.get('prediction_timestamp', 'Unknown')
            
            with st.expander(f"{status_color} {pred_name} - Rate: {rate}", expanded=(i < 3)):
                col_x, col_y = st.columns(2)
                with col_x:
                    st.write(f"**Predicted:** {pred_name}")
                    st.write(f"**Actual:** {actual_name}")
                    st.write(f"**Rate:** {rate}")
                with col_y:
                    st.write(f"**Protocol:** {protocol_type}")
                    st.write(f"**Timestamp:** {timestamp}")
                    
                    # Show color coding
                    label_color = get_label_color(pred_name)
                    st.markdown(f'<div style="width: 20px; height: 20px; background-color: {label_color}; border-radius: 3px; display: inline-block; margin-right: 5px;"></div> Attack Category Color', unsafe_allow_html=True)