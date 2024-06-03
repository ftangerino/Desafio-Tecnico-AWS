# Desafio Técnico: Integração de um ERP-CRM

## Descrição

Implementação de uma integração simples de pedidos entre dois sistemas fictícios (ERP e CRM) usando AWS Lambda e S3, configurada pelo Serverless Framework.

## Requisitos

- AWS CLI configurado (Certifique-se de ele star com todas permissões necessárias)
- Node.js e npm
- Serverless Framework instalado
- Python 3.8 ou superior

## Configuração

1. Clone o repositório:
    ```bash
    git clone https://github.com/ftangerino/Desafio-flashCRM
    cd Desafio-flashCRM
    ```

2. Instale as dependências do Serverless Framework:
    ```bash
    npm install
    ```

3. Configure suas credenciais AWS usando `aws configure`.

4. Ajuste o arquivo `serverless.yml` conforme necessário, incluindo os nomes dos buckets S3.

## Estrutura do Projeto

## Deploy

Para fazer o deploy da infraestrutura e das funções Lambda, execute:
    ```bash
    serverless deploy
    ```
Este comando irá empacotar e implantar o serviço na AWS. Ele criará as funções AWS Lambda necessárias, o API Gateway e o bucket S3.

## Uso

### Acione a Função `processErpData`

Envie uma solicitação POST para o endpoint criado pelo Serverless Framework. Use ferramentas como curl ou Postman para isso (Ou via FastAPI e Swagger).

### Verifique os Dados no S3

Verifique o bucket S3 especificado na variável de ambiente `BUCKET_NAME` (ela vai estar com o horário e data da criação e deploy) para garantir que os dados transformados foram salvos.

### Verifique a Atualização da Configuração do CRM

Verifique ainda no bucket do S3 o arquivo `updated_crm_swagger.json` atualizado.