import json
import os
import boto3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

def handle_status(order_list: list) -> list:
    """
    Atualiza o status dos pedidos na lista de acordo com o mapeamento.

    Args:
        order_list (list): Lista de pedidos, onde cada pedido é um dicionário contendo o campo 'status'.

    Returns:
        list: Lista de pedidos com o status atualizado.
    """
    order_status_mapping = {
        'finished': 'concluido',
        'in progress': 'aberto',
        'canceled': 'cancelado',
        'other': 'outro'
    }

    for order in order_list:
        order['status'] = order_status_mapping.get(order['status'], 'outro')

    return order_list

def calculate_discount(discount, value):
    """
    Calcula o valor do desconto com base na entrada fornecida.

    Args:
        discount (str/float): O valor do desconto, que pode ser uma string percentual, string monetária ou um float.
        value (float): O valor base para o cálculo do desconto.

    Returns:
        float: O valor calculado do desconto.
    """
    if discount:
        if isinstance(discount, str) and '%' in discount:
            percentage = float(discount.replace('%', '')) / 100
            discount_value = round(value * percentage, 2)
        elif isinstance(discount, str) and 'R$' in discount:
            discount_value = float(discount.replace('R$', '').replace(',', '.'))
        else:
            discount_value = float(discount)
    else:
        discount_value = 0
    return discount_value

def process_erp_data(event, context):
    """
    Processa os dados do ERP, transforma-os e os salva no S3.

    Args:
        event: Evento do Lambda que desencadeou a função.
        context: Contexto do Lambda.

    Returns:
        dict: Resposta HTTP com status do processamento.
    
    Trigger:
        HTTP Trigger: Configurado para ser acionado por uma solicitação HTTP POST no caminho /process.
    """
    bucket_name = os.environ['BUCKET_NAME']
    s3_file_name = f"order_{datetime.now()}.json"
    s3_event_model = {
        "Records": {
            "s3": {
                "bucket": {"name": bucket_name, "key": s3_file_name},
                "objects": []
            }
        }
    }

    try:
        # Lê os dados mockados do arquivo erp_data.json
        with open('erp_data.json', 'r') as file:
            erp_orders = json.load(file)
        
        # Transforma os dados aplicando o desconto, atualizando o status e deixando formatado de acordo com as especificações do desafio.
        erp_orders = handle_status(erp_orders)

        # Uso do operador morsa := para evitar a chamada de função repetida
        erp_orders = [
            {**order, 
            'desconto': (discount_value := calculate_discount(order.get('desconto', 0), float(order['valor']))), 
            'valor_final': round(float(order['valor']) - discount_value + float(order['frete']), 2)}
            for order in erp_orders
        ]

        # Atualiza o modelo de evento S3 com os dados formatados
        s3_event_model['Records']['s3']['objects'] = erp_orders

        # Salva os dados formatados no S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_file_name,
            Body=json.dumps(s3_event_model)
        )

        logger.info(f'Dados processados e salvos no S3 com sucesso: {s3_file_name}')

        return {
            'statusCode': 200,
            'body': json.dumps('Dados processados e salvos no S3 com sucesso')
        }

    except Exception as e:
        logger.error(f"Erro ao processar os dados do ERP: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"erro": str(e)})
        }

def store_transformed_data(event, context):
    """
    Processa os dados transformados do S3 e os adiciona à configuração do CRM.

    Args:
        event: Evento do Lambda que desencadeou a função.
        context: Contexto do Lambda.

    Returns:
        dict: Resposta HTTP com a configuração atualizada do CRM.
    """
    logger.info('Evento recebido: %s', json.dumps(event, indent=2))
    
    try:
        # Lê a configuração do CRM
        with open('crm_swagger.json', 'r') as file:
            crm_config = json.load(file)
            logger.info('Configuração CRM carregada com sucesso.')

        # Extrai informações do evento S3
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        logger.info('Bucket: %s, Key: %s', bucket_name, key)

        # Obtem objeto do S3
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        processed_data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info('Dados processados obtidos do S3: %s', json.dumps(processed_data, indent=2))

        orders = processed_data['Records']['s3']['objects']
        crm_orders = crm_config['paths']['/post']['post']['requestBody']['content']['application/json']['examples']['Pedidos']

        for i, order in enumerate(orders):
            order_key = f"value{i}"  # Cria uma chave única para cada pedido
            crm_orders[order_key] = order

        updated_crm_key = "updated_crm_swagger.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=updated_crm_key,
            Body=json.dumps(crm_config)
        )

        logger.info('CRM Swagger atualizado e salvo no S3 com sucesso.')

        logger.info('Dados adicionados à configuração CRM: %s', json.dumps(crm_config, indent=2))
        return {
            'statusCode': 200,
            'body': json.dumps(crm_config)
        }

    except Exception as e:
        logger.error('Erro no processamento: %s', str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"erro": str(e)})
        }