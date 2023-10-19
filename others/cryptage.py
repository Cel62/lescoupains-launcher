from cryptography.fernet import Fernet

key = Fernet.generate_key()
fernet = Fernet(key)
print(f"Key: {key}")

client_id = "16f390b0-ab6d-41e4-b703-3da720cac44b"
redirect_uri = "https://contoso.com/lescoupainslauncher"
secret = "N1D8Q~4ggpOrx9Axykwkpg4kQ7TyCkCAOOvuZaDf"

print(fernet.encrypt(str(client_id).encode()))
print(fernet.encrypt(str(redirect_uri).encode()))
print(fernet.encrypt(str(secret).encode()))
