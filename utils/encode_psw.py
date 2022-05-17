from cryptography.fernet import Fernet
import getpass

def generate_keys(password):
    secret_key = Fernet.generate_key()
    cipher_suite = Fernet(secret_key)
    public_key = cipher_suite.encrypt(password.encode())

    plain_text = cipher_suite.decrypt(public_key)
    print(f"\nPublic_key: {public_key.decode('utf-8')}\nSecret Key: {secret_key.decode('utf-8')}\n")
    print()


def decrypt(public_key,secret_key):
    cipher_suite = Fernet(secret_key)
    decoded_text = cipher_suite.decrypt(public_key)
    decoded = decoded_text.decode('utf-8')
    print(f"Decrypted{decoded}")
    return decoded


def main():
    while True:
        password = getpass.getpass(prompt='Password: ', stream=None)
        password_confirmation = getpass.getpass(prompt='Password confirmation: ', stream=None)
        if password == password_confirmation:
            generate_keys(password)
            break
        else:
            print("As senhas não coincidem, tente novamente...\n")
            continue


if __name__ == "__main__":
    main()
