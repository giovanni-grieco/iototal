import os
import threading
import time
from collections import Counter, deque
import streamlit as st
from kafka import KafkaConsumer
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from itertools import cycle

# --- CONFIGURAZIONE ---
KAFKA_BOOTSTRAP = os.popen(
    "kubectl get service iototal-kafka-controller-0-external --namespace default -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
).read().strip() + ":9094"
TOPIC = "network-traffic"
POLL_INTERVAL = 1.0

# --- BUFFER ---
word_list = deque(maxlen=1000)
word_color_map = {}  # parola → colore
color_palette = cycle(plt.get_cmap('tab20').colors)  # colori ciclici

# --- FUNZIONE LETTURA KAFKA ---
def kafka_reader():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='dashboard-group',
        value_deserializer=lambda x: x.decode('utf-8'),
    )
    for msg in consumer:
        word = msg.value.strip()
        if word:
            word_list.append(word)

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="📚 Istogramma Parole Kafka", layout="wide")
st.title("📚 Frequenza Parole in Tempo Reale da Kafka")

# Lancia il thread Kafka solo una volta
if 'kafka_thread' not in st.session_state:
    thread = threading.Thread(target=kafka_reader, daemon=True)
    thread.start()
    st.session_state.kafka_thread = thread

# SIDEBAR
with st.sidebar:
    st.markdown("## Impostazioni")
    interval = st.number_input("Intervallo refresh (s)", min_value=0.1, max_value=10.0, value=float(POLL_INTERVAL))
    max_words = st.number_input("Numero massimo parole in memoria", min_value=100, max_value=5000, value=1000)
    if max_words != word_list.maxlen:
        word_list = deque(word_list, maxlen=max_words)

# GRAFICO
chart_placeholder = st.empty()

# LOOP DI AGGIORNAMENTO
while True:
    time.sleep(interval)

    word_counts = Counter(word_list)
    if not word_counts:
        continue

    df = pd.DataFrame.from_dict(word_counts, orient='index', columns=['Frequenza'])
    df = df.sort_values(by='Frequenza', ascending=False)

    # Colori assegnati a ogni parola (se nuova, assegna un colore)
    for word in df.index:
        if word not in word_color_map:
            word_color_map[word] = next(color_palette)

    # Ottieni lista colori in ordine delle parole
    bar_colors = [word_color_map[word] for word in df.index]

    fig, ax = plt.subplots()
    bars = ax.bar(df.index, df['Frequenza'], color=bar_colors)


    ax.set_xlabel("Parole")
    ax.set_ylabel("Conteggio")
    ax.set_title("Istogramma Parole")
    ax.set_xticklabels(df.index, rotation=45, ha='right')

    # Tick Y solo numeri interi
    max_freq = df['Frequenza'].max()
    ax.set_yticks(np.arange(0, max_freq + 1, 1))

    chart_placeholder.pyplot(fig)
