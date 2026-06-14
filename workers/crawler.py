import pika
import json

def process_message(ch, method, properties, body):
    message = json.loads(body)
    print(f"Worker received job:")
    print(f"  URL: {message['url']}")
    print(f"  Webhook: {message['webhook_url']}")
    print(f"  Zones: {message['zones_to_watch']}")
    
    # Acknowledge the message — tells RabbitMQ to remove it from queue
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"  Job acknowledged and removed from queue")

def start_worker():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Make sure queue exists
    channel.queue_declare(queue='crawl_tasks', durable=True)

    # Only pick up one message at a time
    channel.basic_qos(prefetch_count=1)

    # Start listening
    channel.basic_consume(
        queue='crawl_tasks',
        on_message_callback=process_message
    )

    print("Worker is waiting for jobs. Press CTRL+C to stop.")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()