import os
import logging
from typing import Dict, Any, Callable
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
DATA_COLLECTED_QUEUE = os.getenv("DATA_COLLECTED_QUEUE", "data_collected")
SCRIPT_GENERATED_EXCHANGE = os.getenv("SCRIPT_GENERATED_EXCHANGE", "script_generated")
SCRIPT_GENERATED_ROUTING_KEY = os.getenv("SCRIPT_GENERATED_ROUTING_KEY", "script.generated")

logger = logging.getLogger(__name__)

class ScriptGeneratorMessageBroker:
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.queue: AbstractQueue = None

    async def connect(self):
        """Connect to RabbitMQ and setup exchanges/queues"""
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
            self.channel = await self.connection.channel()
            
            # Declare exchange
            await self.channel.declare_exchange(
                SCRIPT_GENERATED_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                DATA_COLLECTED_QUEUE,
                durable=True
            )
            
            logger.info("Connected to RabbitMQ and setup exchanges/queues")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def consume_data_collected(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]):
        """Consume messages from the data collected queue"""
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            data = message.body.decode()
                            headers = message.headers or {}
                            await callback(data, headers)
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
            logger.info("Started consuming data collected messages")
        except Exception as e:
            logger.error(f"Failed to start consuming data collected messages: {str(e)}")
            raise

    async def publish_script_generated(self, data: Dict[str, Any]):
        """Publish a message when a script is generated"""
        try:
            exchange = await self.channel.declare_exchange(
                SCRIPT_GENERATED_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            message = aio_pika.Message(
                body=str(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(
                message,
                routing_key=SCRIPT_GENERATED_ROUTING_KEY
            )
            logger.info(f"Published script generated message: {data}")
        except Exception as e:
            logger.error(f"Failed to publish script generated message: {str(e)}")
            raise

    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection") 