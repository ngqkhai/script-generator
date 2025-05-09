import os
import logging
import json
from typing import Dict, Any, Callable
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from app.config import settings
from app.utils.helpers import json_serializable

logger = logging.getLogger(__name__)

class ScriptGeneratorMessageBroker:
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.queue: AbstractQueue = None
        logger.info("Initializing ScriptGeneratorMessageBroker")

    async def connect(self):
        """Connect to RabbitMQ and setup exchanges/queues"""
        try:
            # Connect to RabbitMQ
            logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_URL}")
            try:
                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                logger.info("Successfully connected to RabbitMQ")
            except Exception as conn_err:
                logger.error(f"Failed to connect to RabbitMQ: {str(conn_err)}")
                raise
                
            try:
                self.channel = await self.connection.channel()
                logger.info("Successfully created RabbitMQ channel")
            except Exception as channel_err:
                logger.error(f"Failed to create RabbitMQ channel: {str(channel_err)}")
                raise
            
            # Declare data_collected exchange (the one used by data-collector)
            try:
                data_collected_exchange = await self.channel.declare_exchange(
                    "data_collected",  # Must match the one in data-collector
                    aio_pika.ExchangeType.TOPIC,
                    durable=True
                )
                logger.info(f"Successfully declared exchange: data_collected")
            except Exception as exchange_err:
                logger.error(f"Failed to declare data_collected exchange: {str(exchange_err)}")
                raise
            
            # Declare script_generated exchange
            try:
                await self.channel.declare_exchange(
                    settings.SCRIPT_GENERATED_EXCHANGE,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True
                )
                logger.info(f"Successfully declared exchange: {settings.SCRIPT_GENERATED_EXCHANGE}")
            except Exception as exchange_err:
                logger.error(f"Failed to declare script_generated exchange: {str(exchange_err)}")
                raise
            
            # Declare queue
            try:
                self.queue = await self.channel.declare_queue(
                    settings.DATA_COLLECTED_QUEUE,
                    durable=True
                )
                logger.info(f"Successfully declared queue: {settings.DATA_COLLECTED_QUEUE}")
            except Exception as queue_err:
                logger.error(f"Failed to declare queue: {str(queue_err)}")
                raise
            
            # Bind queue to the data_collected exchange
            try:
                await self.queue.bind(
                    exchange=data_collected_exchange,
                    routing_key="data.collected"  # Must match the routing key used in data-collector
                )
                logger.info(f"Successfully bound queue {settings.DATA_COLLECTED_QUEUE} to exchange data_collected with routing key data.collected")
            except Exception as bind_err:
                logger.error(f"Failed to bind queue to exchange: {str(bind_err)}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def consume_data_collected(self, callback: Callable[[Dict[str, Any], Dict[str, Any]], None]):
        """Consume messages from the data collected queue"""
        try:
            logger.info(f"Starting to consume messages from queue: {settings.DATA_COLLECTED_QUEUE}")
            
            # This will create a consumer and start consuming messages
            async with self.queue.iterator() as queue_iter:
                logger.info("Queue iterator created, waiting for messages...")
                # This is an infinite loop that will keep consuming messages
                async for message in queue_iter:
                    try:
                        # Process the message
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
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding JSON from message: {e}, raw data: {data_str[:100]}...")
                            except Exception as e:
                                logger.error(f"Error processing message: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error handling message in queue iterator: {str(e)}")
            
            # This line will only be reached if the queue iterator is closed
            logger.info("Queue iterator closed, consumption stopped")
            
        except Exception as e:
            logger.error(f"Failed to start consuming data collected messages: {str(e)}")
            raise

    async def publish_script_generated(self, data: Dict[str, Any]):
        """Publish a message when a script is generated"""
        try:
            logger.info(f"Publishing script generated message to exchange: {settings.SCRIPT_GENERATED_EXCHANGE}")
            exchange = await self.channel.declare_exchange(
                settings.SCRIPT_GENERATED_EXCHANGE,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Convert data to JSON string with custom serializer for datetime
            json_data = json.dumps(data, default=json_serializable)
            
            message = aio_pika.Message(
                body=json_data.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(
                message,
                routing_key=settings.SCRIPT_GENERATED_ROUTING_KEY
            )
            logger.info(f"Successfully published script generated message: {data.get('source_name', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to publish script generated message: {str(e)}")
            raise

    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Successfully closed RabbitMQ connection") 