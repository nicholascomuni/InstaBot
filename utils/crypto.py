from cryptography.fernet import Fernet

def generate_keys(password):
    secret_key = Fernet.generate_key()
    cipher_suite = Fernet(secret_key)
    public_key = cipher_suite.encrypt(password.encode())

    plain_text = cipher_suite.decrypt(public_key)
    print(f"key: {secret_key.decode('utf-8')}\nPublic_key: {public_key.decode('utf-8')}\n\n")


def decrypt_fernet(public_key,secret_key):
    cipher_suite = Fernet(secret_key)
    decoded_text = cipher_suite.decrypt(public_key)
    decoded = decoded_text.decode('utf-8')
    return decoded
