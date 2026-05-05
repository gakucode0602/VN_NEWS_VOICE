import pika
import json
import logging

logger = logging.getLogger(__name__)


class MessageConsumer:
    def __init__(
        self,
        rabbitmq_url: str,
        worker,  # IndexingWorker instance
    ) -> None:
        """Initialize RabbitMQ consumer with worker.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            worker: IndexingWorker instance to process messages
        """
        self.worker = worker

        logger.info("Connecting to RabbitMQ...")
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            self.channel = self.connection.channel()
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise

    def declare_queue(self, queue_name: str):
        """Declare a durable queue.

        Args:
            queue_name: Name of the queue to declare
        """
        try:
            logger.info(f"Declaring queue: {queue_name}")
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,  # CRITICAL: Survive RabbitMQ restart
            )
            logger.info(f"Successfully declared queue: {queue_name}")
        except Exception as e:
            logger.error(f"Error declaring queue {queue_name}: {e}")
            raise

    def _on_article_created(self, ch, method, properties, body):
        """Handle article.created event.

        Args:
            ch: Channel
            method: Delivery method
            properties: Message properties
            body: Message body (JSON)
        """
        try:
            logger.info("Received article.created event")
            article_data = json.loads(body)

            # TODO: Validate article_data schema

            # Process article
            self.worker.index_article(article_data)

            # ACK message (success)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            data = article_data.get("result", article_data)
            article_id = data.get("article", {}).get("id")
            logger.info(f"Successfully indexed article: {article_id}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            # NACK without requeue (bad message format)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing article.created: {e}")
            # NACK with requeue (temporary error, retry later)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _on_article_updated(self, ch, method, properties, body):
        """Handle article.updated event.

        Args:
            ch: Channel
            method: Delivery method
            properties: Message properties
            body: Message body (JSON)
        """
        try:
            logger.info("Received article.updated event")
            article_data = json.loads(body)

            # Delete old version
            self.worker.delete_article(article_data["id"])

            # Index new version
            self.worker.index_article(article_data)

            # ACK message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully updated article: {article_data.get('id')}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing article.updated: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _on_article_deleted(self, ch, method, properties, body):
        """Handle article.deleted event.

        Args:
            ch: Channel
            method: Delivery method
            properties: Message properties
            body: Message body (JSON)
        """
        try:
            logger.info("Received article.deleted event")
            data = json.loads(body)

            # Delete article
            self.worker.delete_article(data["article_id"])

            # ACK message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully deleted article: {data.get('article_id')}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing article.deleted: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Start consuming messages from all queues."""
        try:
            # Declare all queues
            self.declare_queue("article.created")
            self.declare_queue("article.updated")
            self.declare_queue("article.deleted")

            # Register consumers
            self.channel.basic_consume(
                queue="article.created",
                on_message_callback=self._on_article_created,
                auto_ack=False,  # CRITICAL: Manual ACK for reliability
            )
            self.channel.basic_consume(
                queue="article.updated",
                on_message_callback=self._on_article_updated,
                auto_ack=False,
            )
            self.channel.basic_consume(
                queue="article.deleted",
                on_message_callback=self._on_article_deleted,
                auto_ack=False,
            )

            logger.info("Started consuming messages from all queues...")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
            self.connection.close()
            logger.info("Consumer stopped gracefully")

        except Exception as e:
            logger.error(f"Error during message consumption: {e}")
            raise
