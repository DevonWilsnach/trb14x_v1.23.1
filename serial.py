import serial
import json
import time
import paho.mqtt.client as mqtt

def read_config():
    with open('serial.json', 'r') as file:
        config = json.load(file)
    return config

def open_uart(port):
    ser = serial.Serial(port, baudrate=9600, timeout=1)
    return ser

def read_uart(serial_port):
    return serial_port.read(10)  # Adjust the number of bytes to read based on your device's response

def send_to_mqtt(value, topic, mqtt_client):
    mqtt_client.publish(topic, value)
    print(f"Published to {topic}: {value}")

def main():
    config = read_config()

    uart_port = config['uart_port']
    mqtt_broker = config['mqtt_broker']
    mqtt_port = config['mqtt_port']
    mqtt_topic = config['mqtt_topic']
    hex_command = config['hex_command']

    mqtt_client = mqtt.Client()
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)

    previous_value = None

    try:
        with open(uart_port, 'rb', 0) as serial_port:
            while True:
                serial_port = open_uart(uart_port)
                serial_port.write(bytes.fromhex(hex_command))
                response = read_uart(serial_port).hex()

                if response != previous_value:
                    send_to_mqtt(response, mqtt_topic, mqtt_client)
                    previous_value = response

                time.sleep(300)  # 5 minutes

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
