from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="kafka:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def enviar_evento(topic: str, mensaje: dict):
    producer.send(topic, mensaje)
    producer.flush()

