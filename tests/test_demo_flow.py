from fastapi.testclient import TestClient
from app.main import app


def login(client,email='admin@inventoryflow.demo'):
    r=client.post('/api/v1/auth/login',json={'email':email,'password':'Demo123!'})
    assert r.status_code==200,r.text


def test_demo_catalog_dashboard_and_validation():
    with TestClient(app) as client:
        login(client)
        d=client.get('/api/v1/dashboard').json()
        assert d['catalog']==420
        assert d['history']>=1
        r=client.post('/api/v1/integrations/demo/scenario',json={'scenario':'validacao'})
        assert r.status_code==200,r.text
        v=client.get('/api/v1/validation').json()
        assert v['inventory']['status']=='VALIDACAO'
        assert v['summary']['divergente']>0
        assert v['summary']['ok']>0


def test_counting_lock_survives_same_browser_session():
    with TestClient(app) as admin, TestClient(app) as supervisor:
        login(admin);login(supervisor,'supervisor@inventoryflow.demo')
        admin.post('/api/v1/integrations/demo/scenario',json={'scenario':'contagem'})
        zones=admin.get('/api/v1/counting/zones').json()['zones']
        zone=next(x['zone'] for x in zones if x['status']!='FINALIZADA')
        session='browser-session-admin-123'
        assert admin.post(f'/api/v1/counting/zones/{zone}/reserve',json={'session_id':session}).status_code==200
        # F5/reload uses the same browser session and is idempotent.
        assert admin.post(f'/api/v1/counting/zones/{zone}/reserve',json={'session_id':session}).status_code==200
        # Another operator/browser cannot steal the active reservation.
        blocked=supervisor.post(f'/api/v1/counting/zones/{zone}/reserve',json={'session_id':'browser-session-other-999'})
        assert blocked.status_code==409


def test_recount_is_reserved_per_sku_and_returns_to_validation_if_still_wrong():
    with TestClient(app) as admin, TestClient(app) as supervisor:
        login(admin);login(supervisor,'supervisor@inventoryflow.demo')
        admin.post('/api/v1/integrations/demo/scenario',json={'scenario':'recontagem'})
        queue=admin.get('/api/v1/recounts/pending?session_id=session-admin-123').json()
        assert queue['total']>0
        item=queue['items'][0]; sku=item['sku']
        assert admin.post(f'/api/v1/recounts/{sku}/reserve',json={'session_id':'session-admin-123'}).status_code==200
        assert supervisor.post(f'/api/v1/recounts/{sku}/reserve',json={'session_id':'session-supervisor-456'}).status_code==409
        wrong=item['snapshot_stock']+1
        result=admin.post(f'/api/v1/recounts/{sku}',json={'session_id':'session-admin-123','quantity':wrong,'note':'test'}).json()
        assert result['resolved'] is False
        validation=admin.get('/api/v1/validation').json()
        row=next(x for x in validation['items'] if x['sku']==sku)
        assert row['status']=='DIVERGENTE'
