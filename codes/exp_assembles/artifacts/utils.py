import base64
from Crypto.Cipher import AES
import os

CIPHER_KEY = 'eUMMn9zWE8EBPHt6hkNooQ=='
xquant_id = None

def decrypt(ciphertext):
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    enc = base64.b64decode(ciphertext)
    iv = enc[:AES.block_size]
    cipher = AES.new(CIPHER_KEY, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

def get_user_id():
    XQUANT_CONF_FILE = os.environ['XQUANT_CONF_FILE']
    with open(XQUANT_CONF_FILE, 'r') as f:
        r = f.readlines()
        for line in r:
            if line.startswith("userId"):
                return line.strip().split("=")[-1].strip()

