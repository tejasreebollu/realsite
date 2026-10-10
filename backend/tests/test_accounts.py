"""Account ownership, session revocation and reviewed-public-profile coverage."""
import io
from datetime import timedelta
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, select
from test_portal import client, register, new_listing, FakeRedis
from app import main, accounts
from app.models import Base, SessionLocal, User, AuthSession, EmailChange, AccountAudit
from app.migrations import migrate

PASSWORD = "long-password-123"

@pytest.fixture(autouse=True)
def account_config(monkeypatch, tmp_path):
    monkeypatch.setenv("ACCOUNT_EMAIL_MODE", "demo")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))


def admin(client):
    client.cookies.clear()
    result = client.post('/api/auth/login', json={'email':'admin@demo.example.com','password':'AdminDemo@2026'})
    assert result.status_code == 200,result.text
    return result.json()


def cookie(client, token):
    client.cookies.clear();client.cookies.set('portal_session',token,path='/api')


def application(**extra):
    return {'agency':'Example Agency','bio':'A local property professional helping clients find homes.','service_areas':['Hyderabad','Pune'],'experience_years':4,'registration_number':'DEMO-REFERENCE','publish_phone':False,**extra}


def update_body(user, **extra):
    return {key:user.get(key,'') for key in ['name','phone','city','bio','avatar_url']} | {'active':True,'reason':'Account review completed',**extra}


def test_profile_requires_login_and_has_no_secret_fields(client):
    assert client.get('/api/me/profile').status_code == 401
    register(client)
    data=client.get('/api/me/profile').json()
    assert data['role']=='user' and data['active'] and data['phone']==''
    assert not {'password_hash','token_hash'} & data.keys()
    assert data['agent_profile'] is None


def test_profile_owner_edit_and_role_email_injection_rejected(client):
    first=register(client);token=client.cookies.get('portal_session')
    body={'name':'Updated Name','phone':'9876543210','city':'Hyderabad','bio':'Private profile biography','avatar_url':''}
    assert client.patch('/api/me/profile',json=body).status_code==200
    for extra in [{'role':'admin'},{'email':'hijack@example.com'},{'active':False}]:
        assert client.patch('/api/me/profile',json=body|extra).status_code==422
    client.cookies.clear();second=register(client,'second@example.com')
    assert client.get('/api/me/profile').json()['name']=='Test Owner'
    cookie(client,token)
    assert client.get('/api/me/profile').json()['name']=='Updated Name'
    assert client.get('/api/admin/users').status_code==403
    assert first['id']!=second['id']


@pytest.mark.parametrize('field,value',[('name','  '),('phone','123'),('avatar_url','https://tracker.example/photo.jpg')])
def test_invalid_profile_fields(client,field,value):
    register(client)
    body={'name':'Valid Name','phone':'','city':'','bio':'','avatar_url':'',field:value}
    assert client.patch('/api/me/profile',json=body).status_code==422


def test_avatar_upload_is_owner_scoped(client):
    register(client)
    stream=io.BytesIO();Image.new('RGB',(32,32),'blue').save(stream,'PNG')
    result=client.post('/api/uploads',files={'file':('avatar.png',stream.getvalue(),'image/png')})
    assert result.status_code==201,result.text
    url=result.json()['url']
    assert client.patch('/api/me/profile',json={'name':'Photo Owner','avatar_url':url}).status_code==200
    client.cookies.clear();register(client,'other@example.com')
    assert client.patch('/api/me/profile',json={'name':'Other Owner','avatar_url':url}).status_code==422


def test_password_change_revokes_other_sessions_and_preserves_current(client):
    user=register(client);old_token=client.cookies.get('portal_session')
    client.post('/api/auth/login',json={'email':user['email'],'password':PASSWORD});current=client.cookies.get('portal_session')
    assert current!=old_token
    assert client.post('/api/me/password',json={'current_password':'wrong','new_password':'new-password-456'}).status_code==400
    assert client.post('/api/me/password',json={'current_password':PASSWORD,'new_password':'new-password-456'}).status_code==204
    assert client.get('/api/auth/me').status_code==200
    cookie(client,old_token);assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':user['email'],'password':PASSWORD}).status_code==401
    assert client.post('/api/auth/login',json={'email':user['email'],'password':'new-password-456'}).status_code==200
    admin(client)
    history=client.get('/api/admin/account-audit').json()['items']
    assert any(a['action']=='password_changed' for a in history)
    assert 'new-password-456' not in str(history) and PASSWORD not in str(history)


def test_email_change_one_time_owner_verification_and_old_sessions(client):
    register(client);old_token=client.cookies.get('portal_session')
    client.post('/api/auth/login',json={'email':'first@example.com','password':PASSWORD})
    result=client.post('/api/me/email-change',json={'email':'new@example.com','current_password':PASSWORD})
    assert result.status_code==200,result.text
    token=result.json()['demo_token'];current=client.cookies.get('portal_session')
    assert client.get('/api/auth/me').json()['email']=='first@example.com'
    assert client.post('/api/me/email-change/verify',json={'token':'wrong-token-value-with-length'}).status_code==400
    client.cookies.clear();register(client,'second@example.com')
    assert client.post('/api/me/email-change/verify',json={'token':token}).status_code==400
    cookie(client,current)
    assert client.post('/api/me/email-change/verify',json={'token':token}).json()['email']=='new@example.com'
    assert client.post('/api/me/email-change/verify',json={'token':token}).status_code==400
    cookie(client,old_token);assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':'new@example.com','password':PASSWORD}).status_code==200


def test_email_expiry_resend_cancel_and_duplicates(client):
    user=register(client)
    assert client.post('/api/me/email-change',json={'email':'admin@demo.example.com','current_password':PASSWORD}).status_code==409
    first=client.post('/api/me/email-change',json={'email':'next@example.com','current_password':PASSWORD}).json()['demo_token']
    second=client.post('/api/me/email-change',json={'email':'next@example.com','current_password':PASSWORD}).json()['demo_token']
    assert client.post('/api/me/email-change/verify',json={'token':first}).status_code==400
    with SessionLocal() as db:
        db.get(EmailChange,user['id']).expires_at=accounts.now()-timedelta(seconds=1);db.commit()
    assert client.post('/api/me/email-change/verify',json={'token':second}).status_code==400
    assert client.get('/api/me/profile').json()['pending_email'] is None
    assert client.delete('/api/me/email-change').status_code==204
    assert client.post('/api/me/email-change/verify',json={'token':second}).status_code==400


def test_email_delivery_configuration_and_secure_demo_guard(client,monkeypatch):
    register(client)
    monkeypatch.setenv('COOKIE_SECURE','true')
    assert client.post('/api/me/email-change',json={'email':'next@example.com','current_password':PASSWORD}).status_code==503
    monkeypatch.setenv('COOKIE_SECURE','false');monkeypatch.setenv('ACCOUNT_EMAIL_MODE','smtp');monkeypatch.delenv('SMTP_HOST',raising=False)
    assert client.post('/api/me/email-change',json={'email':'next@example.com','current_password':PASSWORD}).status_code==503
    assert client.get('/api/me/profile').json()['pending_email'] is None


def test_smtp_verification_never_returns_code(client,monkeypatch):
    sent=[]
    class SMTP:
        def __init__(self,*args,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def starttls(self,**kwargs):sent.append('TLS')
        def login(self,*args):pass
        def send_message(self,message):sent.append(message)
    monkeypatch.setenv('ACCOUNT_EMAIL_MODE','smtp');monkeypatch.setenv('SMTP_HOST','smtp.example.com');monkeypatch.setenv('SMTP_FROM','no-reply@example.com')
    monkeypatch.setattr(accounts.smtplib,'SMTP',SMTP)
    register(client)
    result=client.post('/api/me/email-change',json={'email':'next@example.com','current_password':PASSWORD})
    assert result.status_code==200 and 'demo_token' not in result.json()
    assert sent[0]=='TLS' and sent[1]['To']=='next@example.com'


def test_demo_credentials_are_stable(client):
    admin(client)
    assert client.post('/api/me/password',json={'current_password':'AdminDemo@2026','new_password':'changed-password'}).status_code==422
    assert client.post('/api/me/email-change',json={'email':'other@example.com','current_password':'AdminDemo@2026'}).status_code==422


def test_agent_application_approval_ownership_directory_and_re_review(client):
    owner=register(client);owner_token=client.cookies.get('portal_session')
    assert client.put('/api/me/agent-profile',json=application()).status_code==200
    assert client.get('/api/agents').json()['total']==0
    assert client.patch('/api/admin/agents/'+str(owner['id']),json={'status':'approved','reason':'Profile reviewed'}).status_code==403
    listing=client.post('/api/properties',json=new_listing()).json()
    admin(client)
    assert client.get('/api/admin/agents').json()['total']==1
    assert client.patch('/api/admin/agents/'+str(owner['id']),json={'status':'approved','reason':'Profile reviewed'}).status_code==200
    public=client.get('/api/agents?city=Hyderabad').json()['items'][0]
    assert public['listing_count']==1 and 'email' not in public and public['phone']==''
    assert client.get('/api/agents?city=Hyder').json()['total']==0
    ids=[p['id'] for p in client.get('/api/properties',params={'agent_id':owner['id']}).json()['items']]
    assert ids==[listing['id']]
    cookie(client,owner_token);assert client.get('/api/auth/me').json()['role']=='agent'
    assert client.put('/api/me/agent-profile',json=application(agency='Updated Agency')).status_code==200
    assert client.get('/api/auth/me').json()['role']=='user' and client.get('/api/agents').json()['total']==0
    assert client.put('/api/properties/'+str(listing['id']),json=new_listing()).status_code==200


def test_agent_phone_consent_and_suspension_visibility(client):
    owner=register(client)
    assert client.put('/api/me/agent-profile',json=application(publish_phone=True)).status_code==422
    assert client.patch('/api/me/profile',json={'name':'Phone Agent','phone':'9876543210'}).status_code==200
    assert client.put('/api/me/agent-profile',json=application(publish_phone=True)).status_code==200
    admin(client)
    client.patch('/api/admin/agents/'+str(owner['id']),json={'status':'approved','reason':'Profile reviewed'})
    assert client.get('/api/agents').json()['items'][0]['phone']=='9876543210'
    account=next(u for u in client.get('/api/admin/users').json()['items'] if u['id']==owner['id'])
    assert client.patch('/api/admin/users/'+str(owner['id']),json=update_body(account,active=False)).status_code==200
    assert client.get('/api/agents').json()['total']==0


def test_admin_suspend_reactivate_search_audit_and_no_privilege_escalation(client):
    owner=register(client);token=client.cookies.get('portal_session')
    admin_account=admin(client)
    result=client.get('/api/admin/users',params={'q':owner['email']}).json()
    assert result['total']==1
    account=result['items'][0]
    assert client.patch('/api/admin/users/'+str(owner['id']),json=update_body(account,active=False,role='admin')).status_code==422
    assert client.patch('/api/admin/users/'+str(owner['id']),json=update_body(account,active=False)).status_code==200
    audit=client.get('/api/admin/account-audit',params={'user_id':owner['id']}).json()['items']
    assert audit[0]['action']=='admin_account_updated' and audit[0]['changes']['active']['after'] is False
    assert client.get('/api/admin/users?status=suspended').json()['total']==1
    assert client.patch('/api/admin/users/'+str(admin_account['id']),json=update_body(admin_account,active=False)).status_code==422
    cookie(client,token);assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':owner['email'],'password':PASSWORD}).status_code==403
    admin(client)
    assert client.patch('/api/admin/users/'+str(owner['id']),json=update_body(account,active=True)).status_code==200
    cookie(client,token);assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':owner['email'],'password':PASSWORD}).status_code==200
    assert client.get('/api/admin/account-audit').status_code==403


def test_admin_cannot_self_approve_and_rejection_retains_user_account(client):
    user=register(client);token=client.cookies.get('portal_session')
    client.put('/api/me/agent-profile',json=application())
    administrator=admin(client)
    client.put('/api/me/agent-profile',json=application())
    assert client.patch('/api/admin/agents/'+str(administrator['id']),json={'status':'approved','reason':'Self approval'}).status_code==422
    assert client.patch('/api/admin/agents/'+str(user['id']),json={'status':'rejected','reason':'Missing professional details'}).status_code==200
    cookie(client,token)
    profile=client.get('/api/me/profile').json()
    assert profile['role']=='user' and profile['agent_profile']['status']=='rejected'
    assert client.get('/api/agents').json()['total']==0


def test_additive_migration_keeps_legacy_user_values():
    isolated=create_engine('sqlite:///:memory:')
    with isolated.begin() as c:
        c.execute(text("CREATE TABLE users(id INTEGER PRIMARY KEY,name VARCHAR(100),email VARCHAR(254),password_hash VARCHAR(256),role VARCHAR(20),demo BOOLEAN,created_at DATETIME)"))
        c.execute(text("INSERT INTO users VALUES(1,'Existing','existing@example.com','hash-value','user',0,'2026-10-10')"))
    Base.metadata.create_all(isolated);migrate(isolated);migrate(isolated)
    with isolated.connect() as c:
        row=c.execute(text('SELECT name,email,password_hash,role,active,phone,city,bio,avatar_url FROM users')).one()
        assert tuple(row)==('Existing','existing@example.com','hash-value','user',1,'','','','')
    isolated.dispose()


def test_security_limit_is_scoped_to_account_and_client(client,monkeypatch):
    class CountingRedis(FakeRedis):
        def incr(self,key):
            self.last_count=super().incr(key)
            return self.last_count
        def execute(self):return (self.last_count,True)
    monkeypatch.setattr(main,'cache',CountingRedis())
    register(client)
    for _ in range(10):
        assert client.post('/api/me/password',json={'current_password':'wrong','new_password':'new-password-456'}).status_code==400
    assert client.post('/api/me/password',json={'current_password':'wrong','new_password':'new-password-456'}).status_code==429
    client.cookies.clear();register(client,'independent@example.com')
    assert client.post('/api/me/password',json={'current_password':PASSWORD,'new_password':'new-password-456'}).status_code==204
