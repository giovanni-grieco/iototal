#!/usr/bin/env python3
"""
Network Packet Sniffer for IoT Security Analysis

This script captures network packets from the current network interface,
calculates packet statistics in the same format as the dataset,
and sends them to a Kafka topic for real-time network security monitoring.

The output format is a CSV line with 40 columns matching the dataset format.
"""

import os
import sys
import time
import json
import socket
import struct
import threading
from collections import defaultdict, deque
from statistics import mean, stdev
from datetime import datetime, timedelta
import argparse

try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, Ether, Raw
    from kafka import KafkaProducer
    import numpy as np
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install required packages:")
    print("pip install scapy kafka-python numpy")
    sys.exit(1)


class NetworkFeatureExtractor:
    """Extracts network features from captured packets"""
    
    def __init__(self, window_size=60):
        self.window_size = window_size  # seconds
        self.packet_buffer = deque()
        self.flow_stats = defaultdict(lambda: {
            'packets': [],
            'bytes': [],
            'flags': defaultdict(int),
            'protocols': defaultdict(int),
            'start_time': None,
            'last_time': None
        })
        
    def extract_flow_key(self, packet):
        """Extract flow identifier from packet"""
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            protocol = packet[IP].proto
            
            src_port = dst_port = 0
            if TCP in packet:
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            elif UDP in packet:
                src_port = packet[UDP].sport  
                dst_port = packet[UDP].dport
                
            # Create bidirectional flow key
            if (src_ip, src_port) < (dst_ip, dst_port):
                return f"{src_ip}:{src_port}-{dst_ip}:{dst_port}-{protocol}"
            else:
                return f"{dst_ip}:{dst_port}-{src_ip}:{src_port}-{protocol}"
        return None
    
    def update_flow_stats(self, packet, timestamp):
        """Update flow statistics with new packet"""
        flow_key = self.extract_flow_key(packet)
        if not flow_key:
            return
            
        flow = self.flow_stats[flow_key]
        
        # Initialize flow
        if flow['start_time'] is None:
            flow['start_time'] = timestamp
            
        flow['last_time'] = timestamp
        flow['packets'].append(timestamp)
        
        # Packet size
        packet_size = len(packet)
        flow['bytes'].append(packet_size)
        
        # Protocol analysis
        if IP in packet:
            if TCP in packet:
                flow['protocols']['TCP'] += 1
                # TCP flags
                flags = packet[TCP].flags
                if flags & 0x01: flow['flags']['FIN'] += 1
                if flags & 0x02: flow['flags']['SYN'] += 1  
                if flags & 0x04: flow['flags']['RST'] += 1
                if flags & 0x08: flow['flags']['PSH'] += 1
                if flags & 0x10: flow['flags']['ACK'] += 1
                if flags & 0x40: flow['flags']['ECE'] += 1
                if flags & 0x80: flow['flags']['CWR'] += 1
                
            elif UDP in packet:
                flow['protocols']['UDP'] += 1
            elif ICMP in packet:
                flow['protocols']['ICMP'] += 1
                
        if ARP in packet:
            flow['protocols']['ARP'] += 1
            
        # Application layer protocols (simplified detection)
        if TCP in packet:
            dport = packet[TCP].dport
            sport = packet[TCP].sport
            if dport == 80 or sport == 80:
                flow['protocols']['HTTP'] += 1
            elif dport == 443 or sport == 443:
                flow['protocols']['HTTPS'] += 1
            elif dport == 53 or sport == 53:
                flow['protocols']['DNS'] += 1
            elif dport == 23 or sport == 23:
                flow['protocols']['Telnet'] += 1
            elif dport == 25 or sport == 25:
                flow['protocols']['SMTP'] += 1
            elif dport == 22 or sport == 22:
                flow['protocols']['SSH'] += 1
            elif dport == 194 or sport == 194:
                flow['protocols']['IRC'] += 1
                
        elif UDP in packet:
            dport = packet[UDP].dport
            sport = packet[UDP].sport
            if dport == 53 or sport == 53:
                flow['protocols']['DNS'] += 1
            elif dport == 67 or sport == 67 or dport == 68 or sport == 68:
                flow['protocols']['DHCP'] += 1
    
    def generate_features(self, packet, timestamp):
        """Generate feature vector for a packet"""
        self.update_flow_stats(packet, timestamp)
        flow_key = self.extract_flow_key(packet)
        
        if not flow_key or flow_key not in self.flow_stats:
            return None
            
        flow = self.flow_stats[flow_key]
        
        # Clean old packets (older than window_size)
        cutoff_time = timestamp - self.window_size
        flow['packets'] = [t for t in flow['packets'] if t > cutoff_time]
        flow['bytes'] = flow['bytes'][-len(flow['packets']):]
        
        if len(flow['packets']) < 2:
            return None
            
        features = {}
        
        # Basic packet features
        if IP in packet:
            features['Header_Length'] = packet[IP].ihl * 4
            features['Protocol_Type'] = packet[IP].proto  
            features['Time_To_Live'] = packet[IP].ttl
        else:
            features['Header_Length'] = 0
            features['Protocol_Type'] = 0
            features['Time_To_Live'] = 0
            
        # Flow rate (packets per second)
        duration = max(flow['last_time'] - flow['start_time'], 1)
        features['Rate'] = len(flow['packets']) / duration
        
        # TCP flags
        features['fin_flag_number'] = flow['flags']['FIN']
        features['syn_flag_number'] = flow['flags']['SYN']
        features['rst_flag_number'] = flow['flags']['RST']
        features['psh_flag_number'] = flow['flags']['PSH'] 
        features['ack_flag_number'] = flow['flags']['ACK']
        features['ece_flag_number'] = flow['flags']['ECE']
        features['cwr_flag_number'] = flow['flags']['CWR']
        
        # Flag counts (normalized)
        total_packets = len(flow['packets'])
        features['ack_count'] = flow['flags']['ACK'] / max(total_packets, 1)
        features['syn_count'] = flow['flags']['SYN'] / max(total_packets, 1)
        features['fin_count'] = flow['flags']['FIN'] / max(total_packets, 1) 
        features['rst_count'] = flow['flags']['RST'] / max(total_packets, 1)
        
        # Protocol indicators (binary)  
        features['HTTP'] = 1 if flow['protocols']['HTTP'] > 0 else 0
        features['HTTPS'] = 1 if flow['protocols']['HTTPS'] > 0 else 0
        features['DNS'] = 1 if flow['protocols']['DNS'] > 0 else 0
        features['Telnet'] = 1 if flow['protocols']['Telnet'] > 0 else 0
        features['SMTP'] = 1 if flow['protocols']['SMTP'] > 0 else 0
        features['SSH'] = 1 if flow['protocols']['SSH'] > 0 else 0
        features['IRC'] = 1 if flow['protocols']['IRC'] > 0 else 0
        features['TCP'] = 1 if flow['protocols']['TCP'] > 0 else 0
        features['UDP'] = 1 if flow['protocols']['UDP'] > 0 else 0
        features['DHCP'] = 1 if flow['protocols']['DHCP'] > 0 else 0
        features['ARP'] = 1 if flow['protocols']['ARP'] > 0 else 0
        features['ICMP'] = 1 if flow['protocols']['ICMP'] > 0 else 0
        features['IGMP'] = 0  # Not commonly detected in simple analysis
        features['IPv'] = 1 if IP in packet else 0
        features['LLC'] = 0   # Link layer not commonly analyzed
        
        # Statistical features
        if len(flow['bytes']) > 1:
            features['Tot_sum'] = sum(flow['bytes'])
            features['Min'] = min(flow['bytes']) 
            features['Max'] = max(flow['bytes'])
            features['AVG'] = mean(flow['bytes'])
            features['Std'] = stdev(flow['bytes']) if len(flow['bytes']) > 1 else 0
            features['Tot_size'] = sum(flow['bytes'])
            
            # Inter-arrival time statistics
            if len(flow['packets']) > 1:
                iats = [flow['packets'][i] - flow['packets'][i-1] 
                       for i in range(1, len(flow['packets']))]
                features['IAT'] = mean(iats) if iats else 0
                features['Variance'] = np.var(iats) if len(iats) > 1 else 0
            else:
                features['IAT'] = 0
                features['Variance'] = 0
        else:
            features['Tot_sum'] = len(packet)
            features['Min'] = len(packet)
            features['Max'] = len(packet)  
            features['AVG'] = len(packet)
            features['Std'] = 0
            features['Tot_size'] = len(packet)
            features['IAT'] = 0
            features['Variance'] = 0
            
        features['Number'] = len(flow['packets'])
        features['Label'] = 'UNKNOWN'  # Will be predicted by ML model
        
        return features


class KafkaSnifferProducer:
    """Main class for packet sniffing and Kafka production"""
    
    def __init__(self, kafka_servers, topic, interface=None, window_size=60):
        self.kafka_servers = kafka_servers
        self.topic = topic
        self.interface = interface
        self.feature_extractor = NetworkFeatureExtractor(window_size)
        self.producer = None
        self.running = False
        self.packet_count = 0
        
        # Column order for CSV output (must match dataset format)
        self.columns = [
            'Header_Length', 'Protocol_Type', 'Time_To_Live', 'Rate',
            'fin_flag_number', 'syn_flag_number', 'rst_flag_number', 'psh_flag_number',
            'ack_flag_number', 'ece_flag_number', 'cwr_flag_number', 'ack_count',
            'syn_count', 'fin_count', 'rst_count', 'HTTP', 'HTTPS', 'DNS',
            'Telnet', 'SMTP', 'SSH', 'IRC', 'TCP', 'UDP', 'DHCP', 'ARP',
            'ICMP', 'IGMP', 'IPv', 'LLC', 'Tot_sum', 'Min', 'Max', 'AVG',
            'Std', 'Tot_size', 'IAT', 'Number', 'Variance', 'Label'
        ]
        
    def connect_kafka(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v
            )
            print(f"Connected to Kafka: {self.kafka_servers}")
            return True
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")
            return False
    
    def packet_handler(self, packet):
        """Handle captured packets"""
        try:
            timestamp = time.time()
            features = self.feature_extractor.generate_features(packet, timestamp)
            
            if features:
                # Generate CSV line
                csv_line = self.features_to_csv(features)
                
                # Send to Kafka
                if self.producer:
                    try:
                        future = self.producer.send(self.topic, value=csv_line)
                        # Optional: wait for send to complete
                        # future.get(timeout=1)
                        self.packet_count += 1
                        
                        if self.packet_count % 100 == 0:
                            print(f"Processed {self.packet_count} packets")
                    except Exception as kafka_error:
                        print(f"Kafka send error: {kafka_error}")
                        print(f"CSV line: {csv_line[:100]}...")  # First 100 chars
                else:
                    print("Producer not initialized")
                        
        except Exception as e:
            import traceback
            print(f"Error processing packet: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Packet details: {packet.summary()}")
    
    def features_to_csv(self, features):
        """Convert features dictionary to CSV line"""
        values = []
        for col in self.columns:
            if col in features:
                value = features[col]
                # Format numeric values
                if isinstance(value, float):
                    values.append(f"{value:.6f}")
                else:
                    values.append(str(value))
            else:
                values.append("0")
        return ",".join(values)
    
    def start_sniffing(self):
        """Start packet capture"""
        print(f"Starting packet capture on interface: {self.interface or 'default'}")
        print(f"Sending to Kafka topic: {self.topic}")
        
        self.running = True
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_handler,
                store=0,
                stop_filter=lambda x: not self.running
            )
        except KeyboardInterrupt:
            print("\nStopping packet capture...")
        except Exception as e:
            print(f"Error during packet capture: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop packet capture and cleanup"""
        self.running = False
        if self.producer:
            self.producer.flush()
            self.producer.close()
        print(f"Capture stopped. Total packets processed: {self.packet_count}")


def get_kafka_server():
    """Get Kafka server address from Kubernetes"""
    return os.getenv('KAFKA_SERVER', 'localhost')


def main():
    parser = argparse.ArgumentParser(description='Network Packet Sniffer for IoT Security')
    parser.add_argument('--interface', '-i', help='Network interface to capture (default: auto)')
    parser.add_argument('--kafka-server', '-k', help='Kafka server address (default: auto-detect)')
    parser.add_argument('--topic', '-t', default='network-traffic', help='Kafka topic (default: network-traffic)')
    parser.add_argument('--window', '-w', type=int, default=60, help='Flow window size in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Get Kafka server
    kafka_server = args.kafka_server or get_kafka_server()
    print(f"Using Kafka server: {kafka_server}")
    
    # Create sniffer
    sniffer = KafkaSnifferProducer(
        kafka_servers=kafka_server,
        topic=args.topic,
        interface=args.interface,
        window_size=args.window
    )
    
    # Connect to Kafka
    if not sniffer.connect_kafka():
        print("Failed to connect to Kafka. Exiting.")
        return 1
    
    # Start sniffing
    try:
        sniffer.start_sniffing()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())