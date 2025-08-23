import os, json, threading, time
import traceback
from kafka import KafkaConsumer

def start_consumer(handler) -> None:
    broker = os.getenv("KAFKA_BROKER","kafka:9092")
    topic = os.getenv("KAFKA_TOPIC","complaints.v1")
    group = os.getenv("KAFKA_GROUP","emailer-group")

    def run():
        backoff = 1
        while True:
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=broker,
                    group_id=group,
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                    auto_offset_reset="earliest",
                    enable_auto_commit=True
                )
                for msg in consumer:
                    handler(msg.value)
                consumer.close()
            except Exception as e:
                print("Kafka consumer error:", e)
                traceback.print_exc()
                time.sleep(min(backoff, 30))
                backoff = min(backoff * 2, 30)

    t = threading.Thread(target=run, daemon=True)
    t.start()
