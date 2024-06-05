import json
import logging
from handler import process_erp_data, store_transformed_data

# Configuração do logger para imprimir no console
logger = logging.getLogger()
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Simulação do evento e contexto para process_erp_data
event_erp = {}
context_erp = {}

print("Executando process_erp_data...")
response_erp = process_erp_data(event_erp, context_erp)
print(json.dumps(response_erp, indent=2))

# Simulação do evento e contexto para store_transformed_data
event_s3 = {
    "Records": [
        {
            "s3": {
                "bucket": {
                    "name": "try3-erp-crm-transformed-data-us-east-1"
                },
                "object": {
                    "key": "order_2024-06-05 00:15:31.390700.json"
                }
            }
        }
    ]
}
context_s3 = {}

print("\nExecutando store_transformed_data...")
response_s3 = store_transformed_data(event_s3, context_s3)
print(json.dumps(response_s3, indent=2))
