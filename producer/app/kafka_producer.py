import os, json, time, logging
from kafka import KafkaProducer
from kafka.errors import KafkaError


logger = logging.getLogger("producer")

_broker = os.getenv("KAFKA_BROKER", "kafka:9092")
_producer = None

def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        logger.info(f"Kafka producer connecting to {_broker}")
        _producer = KafkaProducer(
            bootstrap_servers=_broker,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=0,  # we'll handle retries in publish()
        )
    return _producer

def publish(payload: dict):
    """Publish a JSON payload to Kafka with small retry/backoff and logs.
    Removes the legacy 'email' field if present.
    Raises the exception if all retries fail so the API can return 500.
    """
    topic = os.getenv("KAFKA_TOPIC", "complaints.v1")
    payload = dict(payload)  # avoid mutating caller's dict
    payload.pop("email", None)  # ensure old field is not sent

    # Basic validation (producer-side): ensure required keys exist
    missing = [k for k in ("email_id", "first_name", "last_name", "subject", "body") if k not in payload or payload[k] is None or (isinstance(payload[k], str) and not payload[k].strip())]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            p = _get_producer()
            logger.info(f"Publishing to topic='{topic}' (attempt {attempt}/{max_attempts}) for email_id='{payload.get('email_id')}'")
            # Ensure we wait for the send to complete for stronger delivery guarantees
            p.send(topic, payload).get(timeout=10)
            p.flush()
            logger.info(f"Published successfully to '{topic}' for email_id='{payload.get('email_id')}'")
            return
        except (KafkaError, Exception) as e:
            logger.warning(f"Kafka publish failed on attempt {attempt}: {e}")
            # If producer instance got into a bad state, drop it so it's recreated next attempt
            global _producer
            _producer = None
            if attempt == max_attempts:
                logger.error("Kafka publish failed after retries; giving up")
                raise
            time.sleep(0.5 * attempt)  # small backoff
