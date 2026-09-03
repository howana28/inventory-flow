import os
from pathlib import Path
TEST_DB=Path('/tmp/inventoryflow_portfolio_test.db')
if TEST_DB.exists(): TEST_DB.unlink()
os.environ['DATABASE_URL']=f'sqlite:///{TEST_DB}'
os.environ['ALLOW_EXTERNAL_CONNECTIONS']='false'
os.environ['ERP_PROVIDER']='demo'
os.environ['COOKIE_SECURE']='false'
