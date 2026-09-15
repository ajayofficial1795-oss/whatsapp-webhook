import json
from base64 import b64decode, b64encode
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.serialization import load_pem_private_key


@dataclass(frozen=True)
class DecryptedFlowRequest:
    payload: dict
    aes_key: bytes
    initial_vector: bytes


def is_encrypted_flow_request(payload: dict) -> bool:
    return all(key in payload for key in ("encrypted_flow_data", "encrypted_aes_key", "initial_vector"))


def decrypt_flow_request(payload: dict, private_key_pem: str) -> DecryptedFlowRequest:
    encrypted_flow_data = b64decode(payload["encrypted_flow_data"])
    encrypted_aes_key = b64decode(payload["encrypted_aes_key"])
    initial_vector = b64decode(payload["initial_vector"])

    private_key = load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        OAEP(mgf=MGF1(algorithm=SHA256()), algorithm=SHA256(), label=None),
    )

    encrypted_body = encrypted_flow_data[:-16]
    auth_tag = encrypted_flow_data[-16:]
    decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(initial_vector, auth_tag)).decryptor()
    decrypted_body = decryptor.update(encrypted_body) + decryptor.finalize()

    return DecryptedFlowRequest(
        payload=json.loads(decrypted_body.decode("utf-8")),
        aes_key=aes_key,
        initial_vector=initial_vector,
    )


def encrypt_flow_response(response: dict, aes_key: bytes, initial_vector: bytes) -> str:
    response_iv = bytes(byte ^ 0xFF for byte in initial_vector)
    encryptor = Cipher(algorithms.AES(aes_key), modes.GCM(response_iv)).encryptor()
    encrypted_body = encryptor.update(json.dumps(response).encode("utf-8")) + encryptor.finalize()
    return b64encode(encrypted_body + encryptor.tag).decode("utf-8")
