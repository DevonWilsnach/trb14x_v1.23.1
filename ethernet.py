import socket
import json
import time
import binascii
import paho.mqtt.client as mqtt

# Constants
STX = b'\x02'  # Replace with the actual STX byte value
ETX = b'\r'    # Replace with the actual ETX byte value
SLEEP_DURATION = 5  # Seconds to sleep between iterations
POST_INTERVAL = 15 * 60  # 15 minutes in seconds

def read_config():
    with open('/etc/bridge.json', 'r') as file:
        config = json.load(file)
    return config

def open_ethernet(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.connect((host, port))
            return sock
        except socket.error as e:
            print(f"Connection failed: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)  # Retry after 5 minutes

def read_response(socket_conn):
    return socket_conn.recv(1024)

def send_to_mqtt(value, topic, mqtt_client):
    mqtt_client.publish(topic, value)
    print(f"Published to {topic}: {value}")

def extract_payload(data):
    start_index = data.find(STX)
    end_index = data.find(ETX)

    if start_index != -1 and end_index != -1:
        payload = data[start_index + 1:end_index].decode('utf-8')  # Assuming the payload is in UTF-8 encoding
        return payload
    else:
        return None

def main():
    config = read_config()

    ethernet_host = config['ethernet_host']
    ethernet_port = config['ethernet_port']
    mqtt_broker = config['mqtt_broker']
    mqtt_port = config['mqtt_port']
    mqtt_topic = config['mqtt_topic']

    mqtt_client = mqtt.Client()
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)

    previous_value = None
    last_post_time = time.time()

    try:
        while True:
            with open_ethernet(ethernet_host, ethernet_port) as ethernet_conn:
                while True:
                    response = read_response(ethernet_conn)
                    payload = extract_payload(response)

                    if payload != previous_value:
                        send_to_mqtt(payload, mqtt_topic, mqtt_client)
                        previous_value = payload

                    # Post payload every 15 minutes
                    current_time = time.time()
                    if current_time - last_post_time >= POST_INTERVAL:
                        send_to_mqtt(payload, mqtt_topic, mqtt_client)
                        last_post_time = current_time

                    time.sleep(SLEEP_DURATION)

    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
