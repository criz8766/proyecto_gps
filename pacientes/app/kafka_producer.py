from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

def enviar_evento(topic, mensaje):
    print(f"Enviando evento a Kafka: {mensaje}")
    producer.send(topic, mensaje)
    producer.flush()

