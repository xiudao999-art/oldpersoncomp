from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Hypothesized mapping based on user input
access_key_id = os.getenv("ALIYUN_APPKEY") # LTAI...
access_key_secret = os.getenv("ALIYUN_TOKEN") # hRAh...

# Clean up comment if present
if access_key_secret and "#" in access_key_secret:
    access_key_secret = access_key_secret.split("#")[0].strip()

print(f"Testing Token Generation with:")
print(f"AccessKey ID: {access_key_id}")
print(f"AccessKey Secret: {access_key_secret[:5]}...")

try:
    # Create Client
    client = AcsClient(access_key_id, access_key_secret, 'cn-shanghai')

    # Create Request
    request = CommonRequest()
    request.set_method('POST')
    request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
    request.set_version('2019-02-28')
    request.set_action_name('CreateToken')

    response = client.do_action_with_exception(request)
    response_json = json.loads(response)
    
    if 'Token' in response_json:
        token = response_json['Token']['Id']
        expire_time = response_json['Token']['ExpireTime']
        print(f"SUCCESS! Generated Token: {token}")
        print(f"Expire Time: {expire_time}")
    else:
        print(f"Failed to get token. Response: {response_json}")

except Exception as e:
    print(f"Exception during token generation: {e}")
