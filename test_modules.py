import pytest
import json
from moto import mock_s3
import boto3
from handler import handle_status, calculate_discount, process_erp_data, store_transformed_data

@pytest.fixture
def s3_setup():
    with mock_s3():
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        yield s3

def test_handle_status():
    orders = [
        {'status': 'finished'},
        {'status': 'in progress'},
        {'status': 'canceled'},
        {'status': 'unknown'}
    ]
    expected = [
        {'status': 'concluido'},
        {'status': 'aberto'},
        {'status': 'cancelado'},
        {'status': 'outro'}
    ]
    assert handle_status(orders) == expected

def test_calculate_discount():
    assert calculate_discount('10%', 100) == 10.0
    assert calculate_discount('R$10', 100) == 10.0
    assert calculate_discount(10, 100) == 10.0
    assert calculate_discount(None, 100) == 0.0

@pytest.fixture
def mock_erp_data(monkeypatch):
    def mock_open(*args, **kwargs):
        if args[0] == 'erp_data.json':
            return open('tests/mock_data/erp_data.json')
        elif args[0] == 'crm_swagger.json':
            return open('tests/mock_data/crm_swagger.json')
        else:
            raise FileNotFoundError
    monkeypatch.setattr('builtins.open', mock_open)

def test_process_erp_data(s3_setup, mock_erp_data, monkeypatch):
    event = {}
    context = {}
    
    monkeypatch.setenv('BUCKET_NAME', 'test-bucket')
    
    response = process_erp_data(event, context)
    assert response['statusCode'] == 200
    
    s3 = boto3.client('s3')
    result = s3.get_object(Bucket='test-bucket', Key='order_<timestamp>.json')
    data = json.loads(result['Body'].read().decode('utf-8'))
    
    assert 'Records' in data
    assert 's3' in data['Records']
    assert 'objects' in data['Records']['s3']
    assert len(data['Records']['s3']['objects']) > 0

def test_store_transformed_data(s3_setup, mock_erp_data):
    event = {
        'Records': [
            {
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'order_<timestamp>.json'}
                }
            }
        ]
    }
    context = {}
    
    # Mock S3 setup with initial data
    s3 = boto3.client('s3')
    s3.put_object(Bucket='test-bucket', Key='order_<timestamp>.json', Body=json.dumps({
        "Records": {
            "s3": {
                "bucket": {"name": 'test-bucket', "key": 'order_<timestamp>.json'},
                "objects": [
                    {"order_id": 1, "status": "concluido", "desconto": "10%", "valor": 100.0, "frete": 10.0},
                    {"order_id": 2, "status": "aberto", "desconto": "R$10", "valor": 200.0, "frete": 20.0}
                ]
            }
        }
    }))
    
    response = store_transformed_data(event, context)
    assert response['statusCode'] == 200
    
    updated_crm = s3.get_object(Bucket='test-bucket', Key='updated_crm_swagger.json')
    crm_data = json.loads(updated_crm['Body'].read().decode('utf-8'))
    
    assert 'paths' in crm_data
    assert '/post' in crm_data['paths']
    assert 'post' in crm_data['paths']['/post']
    assert 'requestBody' in crm_data['paths']['/post']['post']
    assert 'content' in crm_data['paths']['/post']['post']['requestBody']
    assert 'application/json' in crm_data['paths']['/post']['post']['requestBody']['content']
    assert 'examples' in crm_data['paths']['/post']['post']['requestBody']['content']['application/json']
    assert 'Pedidos' in crm_data['paths']['/post']['post']['requestBody']['content']['application/json']['examples']
    assert 'value0' in crm_data['paths']['/post']['post']['requestBody']['content']['application/json']['examples']['Pedidos']
    assert 'value1' in crm_data['paths']['/post']['post']['requestBody']['content']['application/json']['examples']['Pedidos']
