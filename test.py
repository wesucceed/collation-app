import pyperclip
import pyotp
import time
secret_key = pyotp.random_base32(100)
print("Secret key: ", secret_key)
totp = pyotp.TOTP(secret_key)
url = totp.provisioning_uri(name = 'samuel@google.com', issuer_name = 'Collation App')
pyperclip.copy(url)
print("Sleeping")
time.sleep(30)
x= pyotp.parse_uri(url)
print(x.now())
print(totp.now())

hi
