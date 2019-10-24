from moto import mock_s3, mock_dynamodb2
import boto3, pytest, os, json

import responses # because moto breaks requests
responses.add_passthru('https://')# moto+requests needs this
responses.add_passthru('http://')# moto+requests needs this

def setup_vault(s3_client):
   """A helper function to instantiate the SOCless vault bucket with test files.

   This needs to be wrapped in moto's mock_s3 decorator before calling.
   Returns:
      boto3 s3 client
   """
   bucket_name = os.environ['SOCLESS_VAULT']
   s3_client = boto3.client('s3')
   s3_client.create_bucket(Bucket=bucket_name)
   s3_client.put_object(Bucket=bucket_name, Key="socless_vault_tests.txt", Body="this came from the vault")
   s3_client.put_object(Bucket=bucket_name, Key="socless_vault_tests.json", Body='{"hello":"world"}')
   return s3_client

def setup_tables(dynamodb_client):
   """A helper function to instantiate SOCless dynamoDB tables.
   
   This needs to be wrapped in moto's mock_dynamodb2 decorator before calling.

   Returns:
      boto3 dynamodb client in case you need to put_object for tests.
   """
   dynamodb_client = boto3.client('dynamodb')

   events_table_name = os.environ['SOCLESS_EVENTS_TABLE']
   events_table = dynamodb_client.create_table(
      TableName=events_table_name,
      KeySchema=[{'AttributeName': 'id','KeyType': 'HASH'}],
      AttributeDefinitions=[])
   
   results_table_name = os.environ['SOCLESS_RESULTS_TABLE']
   results_table = dynamodb_client.create_table(
      TableName=results_table_name,
      KeySchema=[{'AttributeName': 'execution_id','KeyType': 'HASH'}],
      AttributeDefinitions=[])
   
   dedup_table_name = os.environ['SOCLESS_DEDUP_TABLE']
   dedup_table = dynamodb_client.create_table(
      TableName=dedup_table_name,
      KeySchema=[{'AttributeName': 'dedup_hash','KeyType': 'HASH'}],
      AttributeDefinitions=[])

   return dynamodb_client

@pytest.fixture(scope='session', autouse=True)
def aws_credentials():
   """Mocked AWS Credentials for moto, auto runs in every test.
   
   Instantiate fake AWS Credentials that will be used to start up moto/boto3
   for tests. This fixture will be called by other fixtures to initialize
   their respective boto3 clients (s3, dynamodb, ssm, etc..) which are used for
   each each testing function that needs to interact with AWS.

   This fixture will also run automatically in every test to further prevent
   accidental live boto3 API calls.
   """
   os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
   os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
   os.environ['AWS_SECURITY_TOKEN'] = 'testing'
   os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='session', autouse=True)
def setup_socless(aws_credentials):
   """Sets up a mock s3 bucket and dynamo tables in every test automatically.
   
   This uses moto's mock_s3 and mock_dynamodb2 decorators to instantiate
   SOCless vault s3 bucket and SOCless dynamoDB tables needed to run.

   This fixture is automatically run at the start of every test, and will 
   wrap that test in the required moto decorators. Further boto3 calls can be
   made to the dynamodb and s3 clients in tests, other AWS clients will need 
   their respective moto decorator to function properly. 
   """
   with mock_dynamodb2(), mock_s3(): # use moto decorators to mock boto3 calls
      # ensure boto3 is instantiated now, inside the decorators
      boto3.setup_default_session()

      dynamodb_client = boto3.client('dynamodb')
      setup_tables(dynamodb_client)

      s3_client = boto3.client('s3')
      setup_vault(s3_client)

      yield dynamodb_client
