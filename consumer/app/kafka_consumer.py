import os
import json
import threading
import time
import traceback
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable, CommitFailedError, NotCoordinatorForGroupError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for consumer health monitoring
consumer_running = False
consumer_lock = threading.Lock()
consumer_thread = None

def set_consumer_running(val: bool):
    """Thread-safe setter for consumer running state"""
    global consumer_running
    with consumer_lock:
        consumer_running = val
        logger.info(f"Consumer running state updated: {val}")

def get_consumer_running() -> bool:
    """Thread-safe getter for consumer running state"""
    global consumer_running
    with consumer_lock:
        return consumer_running

def wait_for_kafka(broker: str, max_wait_time: int = 60) -> bool:
    """Wait for Kafka to be available before creating consumer"""
    logger.info(f"Waiting for Kafka broker {broker} to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # Try to create a temporary consumer to test connection
            test_consumer = KafkaConsumer(
                bootstrap_servers=broker,
                consumer_timeout_ms=1000
            )
            test_consumer.close()
            logger.info("Kafka broker is ready!")
            return True
        except Exception as e:
            logger.debug(f"Kafka not ready yet: {e}")
            time.sleep(2)
    
    logger.warning(f"Kafka broker {broker} not ready after {max_wait_time} seconds")
    return False

def create_consumer(broker: str, topic: str, group_id: str) -> KafkaConsumer:
    """Create and configure Kafka consumer with optimal settings"""
    # Ensure group_id is not None or empty
    if not group_id or group_id.strip() == "":
        group_id = "emailer-group"
        logger.warning(f"Empty group_id provided, using default: {group_id}")
    
    logger.info(f"Creating consumer with group_id: '{group_id}'")
    
    consumer_config = {
        'bootstrap_servers': broker,
        'group_id': group_id,
        'value_deserializer': lambda v: json.loads(v.decode("utf-8")) if v else None,
        'auto_offset_reset': os.getenv("KAFKA_OFFSET", "latest"),
        'enable_auto_commit': True,
        'auto_commit_interval_ms': 5000,
        
        # Connection and session settings for stability
        'session_timeout_ms': 30000,           # 30 seconds
        'heartbeat_interval_ms': 10000,        # 10 seconds
        'max_poll_interval_ms': 300000,        # 5 minutes
        'request_timeout_ms': 40000,           # 40 seconds
        'connections_max_idle_ms': 540000,     # 9 minutes
        'retry_backoff_ms': 1000,              # 1 second
        
        # Consumer fetch settings
        'fetch_min_bytes': 1,
        'fetch_max_wait_ms': 5000,
        'max_partition_fetch_bytes': 1048576,  # 1MB
        
        # Security settings (if needed)
        'security_protocol': os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
    }
    
    # Add SASL settings if configured
    if os.getenv("KAFKA_SASL_MECHANISM"):
        consumer_config.update({
            'sasl_mechanism': os.getenv("KAFKA_SASL_MECHANISM"),
            'sasl_plain_username': os.getenv("KAFKA_SASL_USERNAME"),
            'sasl_plain_password': os.getenv("KAFKA_SASL_PASSWORD"),
        })
    
    return KafkaConsumer(topic, **consumer_config)

def process_complaint_message(message: dict):
    """
    Process a single complaint message
    Replace this with your actual message processing logic
    """
    try:
        # Example processing - replace with your actual logic
        complaint_id = message.get('id', 'unknown')
        complaint_text = message.get('complaint_text', '')
        user_email = message.get('email', '')
        
        logger.info(f"Processing complaint {complaint_id} for {user_email}")
        
        # Add your email sending logic here
        # send_email(user_email, complaint_text)
        
        # Simulate processing time
        time.sleep(0.1)
        
        logger.info(f"Successfully processed complaint {complaint_id}")
        
    except Exception as e:
        logger.error(f"Error processing complaint message: {e}")
        raise

def start_kafka_consumer() -> threading.Thread:
    """Start the Kafka consumer with robust error handling and reconnection logic"""
    # Get configuration from environment
    broker = os.getenv("KAFKA_BROKER", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "complaints.v1")
    group = os.getenv("KAFKA_GROUP", "emailer-group")
    
    logger.info(f"Starting Kafka consumer: broker={broker}, topic={topic}, group={group}")
    
    # Validate and clean group_id
    group_id = group.strip() if group and group.strip() else "emailer-group"
    logger.info(f"Using group_id: '{group_id}'")
    
    def run():
        backoff = 1
        max_backoff = 60
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        # Wait for Kafka to be ready
        if not wait_for_kafka(broker, max_wait_time=120):
            logger.error("Failed to connect to Kafka broker initially, but will keep trying...")
        
        while True:
            consumer = None
            try:
                logger.info(f"Creating Kafka consumer (attempt after {consecutive_errors} consecutive errors)")
                
                # Create consumer with retry logic
                consumer = create_consumer(broker, topic, group_id)
                
                # Log partition assignment for debugging
                logger.info(f"Consumer assigned to partitions: {consumer.assignment()}")
                
                logger.info("Successfully created Kafka consumer, starting message consumption...")
                set_consumer_running(True)
                consecutive_errors = 0
                backoff = 1
                
                # Main message consumption loop
                for message in consumer:
                    try:
                        if message.value is None:
                            logger.warning("Received message with null value, skipping...")
                            continue
                            
                        logger.debug(f"Processing message: offset={message.offset}, partition={message.partition}")
                        
                        # Process the complaint message
                        process_complaint_message(message.value)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON message: {e}")
                        logger.debug(f"Raw message value: {message.value}")
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        traceback.print_exc()
                        
                        # Don't break the loop for message processing errors
                        # The message will be committed and we'll continue
                        
            except NotCoordinatorForGroupError as e:
                consecutive_errors += 1
                logger.error(f"NotCoordinatorForGroupError: {e} - Group coordinator not available")
                set_consumer_running(False)
                
            except NoBrokersAvailable as e:
                consecutive_errors += 1
                logger.error(f"No Kafka brokers available: {e}")
                set_consumer_running(False)
                
            except CommitFailedError as e:
                consecutive_errors += 1
                logger.error(f"Failed to commit offset: {e}")
                set_consumer_running(False)
                
            except KafkaError as e:
                consecutive_errors += 1
                logger.error(f"Kafka error: {e}")
                set_consumer_running(False)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Unexpected consumer error: {e}")
                set_consumer_running(False)
                traceback.print_exc()
                
            finally:
                # Clean up consumer resources
                if consumer:
                    try:
                        logger.info("Closing Kafka consumer...")
                        consumer.close()
                    except Exception as e:
                        logger.warning(f"Error closing consumer: {e}")
                
                set_consumer_running(False)
            
            # Backoff logic with circuit breaker pattern
            if consecutive_errors >= max_consecutive_errors:
                logger.warning(f"Too many consecutive errors ({consecutive_errors}), increasing backoff time")
                backoff = min(backoff * 2, max_backoff)
            
            if consecutive_errors > 0:
                logger.info(f"Waiting {backoff} seconds before reconnecting... (consecutive errors: {consecutive_errors})")
                time.sleep(backoff)
    
    # Start consumer in daemon thread
    consumer_thread = threading.Thread(target=run, daemon=True, name="KafkaConsumer")
    consumer_thread.start()
    logger.info("Kafka consumer thread started")
    
    return consumer_thread

# FastAPI lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop Kafka consumer"""
    global consumer_thread
    
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Add startup delay for Kafka coordination stabilization
    logger.info("Waiting for Kafka coordination to stabilize...")
    await asyncio.sleep(10)
    
    consumer_thread = start_kafka_consumer()
    
    # Wait a moment to let consumer initialize
    await asyncio.sleep(2)
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    set_consumer_running(False)
    
    if consumer_thread and consumer_thread.is_alive():
        logger.info("Waiting for consumer thread to finish...")
        consumer_thread.join(timeout=10)

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Complaints Consumer Service",
    description="Kafka consumer service for processing complaint messages",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "ok",
        "service": "complaints-consumer",
        "timestamp": time.time()
    }

@app.get("/health/consumer")
async def consumer_health_check():
    """Detailed consumer health check"""
    return {
        "status": "healthy" if get_consumer_running() else "unhealthy",
        "consumer_running": get_consumer_running(),
        "timestamp": time.time(),
        "kafka_broker": os.getenv("KAFKA_BROKER", "kafka:9092"),
        "kafka_topic": os.getenv("KAFKA_TOPIC", "complaints.v1"),
        "kafka_group": os.getenv("KAFKA_GROUP", "emailer-group")
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Complaints Consumer Service is running"}

# For debugging - environment info
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "KAFKA_BROKER": os.getenv("KAFKA_BROKER", "not set"),
        "KAFKA_TOPIC": os.getenv("KAFKA_TOPIC", "not set"),
        "KAFKA_GROUP": os.getenv("KAFKA_GROUP", "not set"),
        "KAFKA_OFFSET": os.getenv("KAFKA_OFFSET", "not set"),
    }

# Add asyncio import for the lifespan function
import asyncio

# Compatibility function for existing imports
def start_consumer(handler):
    """
    Compatibility function for existing code that expects start_consumer()
    This wraps the new start_kafka_consumer() function
    """
    def dummy_handler(message):
        handler(message)
    
    return start_kafka_consumer()

from fastapi import Body

@app.post("/test-email")
async def test_email(
    to: str = Body(...),
    subject: str = Body(...),
    body: str = Body(...)
):
    """Send a test email using SMTP_EMAIL environment variable as sender"""
    try:
        from email_sender import send_email
        from_addr = os.getenv("SMTP_EMAIL")
        if not from_addr:
            raise HTTPException(status_code=500, detail="SMTP_EMAIL environment variable is not set.")
        send_email(
            to_addr=to,
            from_addr=from_addr,
            first_name="Test",
            subject=subject,
            body=body,
            ticket_id="TEST123",
            attachment_name=None,
            attachment_bytes=None,
        )
        return {"status": "success", "message": f"Email sent to {to}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))