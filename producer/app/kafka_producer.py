import os, json
from kafka import KafkaProducer

broker = os.getenv("KAFKA_BROKER", "kafka:9092")
producer = KafkaProducer(
    bootstrap_servers=broker,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def publish(payload: dict):
    topic = os.getenv("KAFKA_TOPIC", "complaints.v1")
    producer.send(topic, payload)
    producer.flush()
