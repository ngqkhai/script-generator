import os
import logging
from typing import Dict, Any, Callable
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from dotenv import load_dotenv
from app.config import settings

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBITMQ_URL = settings.RABBITMQ_URL
DATA_COLLECTED_QUEUE = settings.DATA_COLLECTED_QUEUE
SCRIPT_GENERATED_EXCHANGE = settings.SCRIPT_GENERATED_EXCHANGE
SCRIPT_GENERATED_ROUTING_KEY = settings.SCRIPT_GENERATED_ROUTING_KEY
SCRIPT_VOICE_QUEUE = settings.SCRIPT_VOICE_QUEUE
SCRIPT_IMAGE_QUEUE = settings.SCRIPT_IMAGE_QUEUE

logger = logging.getLogger(__name__)

class ScriptGeneratorMessageBroker:
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.queue: AbstractQueue = None
        self.voice_queue: AbstractQueue = None
        self.image_queue: AbstractQueue = None

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
            
            # Declare output queues for fan-out to voice and image services
            self.voice_queue = await self.channel.declare_queue(
                SCRIPT_VOICE_QUEUE,
                durable=True
            )
            self.image_queue = await self.channel.declare_queue(
                SCRIPT_IMAGE_QUEUE,
                durable=True
            )
            
            # Bind voice and image queues to the exchange for script generation
            exchange = await self.channel.declare_exchange(
                SCRIPT_GENERATED_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            await self.voice_queue.bind(exchange, routing_key=SCRIPT_VOICE_QUEUE)
            await self.image_queue.bind(exchange, routing_key=SCRIPT_IMAGE_QUEUE)
            
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
                            data_str = message.body.decode()
                            data = json.loads(data_str)
                            headers = message.headers or {}
                                
                            # Log minimal message info to avoid huge log entries
                            source_name = data.get('source_name', 'unknown')
                            collection_id = data.get('collection_id', 'unknown')
                            logger.info(f"Received message from queue - source: {source_name}, collection_id: {collection_id}")
                                # Call the callback to process the message
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
            # Ensure exchange exists
            exchange = await self.channel.declare_exchange(
                SCRIPT_GENERATED_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            # Create persistent message
            message = aio_pika.Message(
                body=str(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            # Publish to both voice and image task queues
            await exchange.publish(
                message,
                routing_key=SCRIPT_VOICE_QUEUE
            )
            await exchange.publish(
                message,
                routing_key=SCRIPT_IMAGE_QUEUE
            )
            logger.info(f"Published script to voice queue '{SCRIPT_VOICE_QUEUE}' and image queue '{SCRIPT_IMAGE_QUEUE}': {data}")
        except Exception as e:
            logger.error(f"Failed to publish script generated message: {str(e)}")
            raise

    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection") 