"""Authenticated local encryption for credentials and private trading records."""
import base64
import json
import os
import secrets

from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import scrypt

from storage import account_lock, atomic_text

PREFIX = "EMA1:"
METADATA = ".vault.json"
ORDERS = "operacoes-lighter.jsonl"


class VaultError(ValueError):
    pass


def encode(value):
    return base64.b64encode(value).decode("ascii")


def decode(value):
    return base64.b64decode(value, validate=True)


class Vault:
    def __init__(self, root, key):
        self.root = root
        self.key = key

    @classmethod
    def open(cls, root, passphrase):
        root = root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        path = root / METADATA
        with account_lock(root / ".vault.lock"):
            if not passphrase or len(passphrase) > 1024 or (not path.exists() and len(passphrase) < 12):
                raise VaultError("Use uma frase secreta de pelo menos 12 caracteres para o cofre.")
            try:
                meta = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
                salt = decode(meta["salt"]) if meta else secrets.token_bytes(16)
                if len(salt) != 16:
                    raise ValueError
            except (TypeError, KeyError, ValueError) as error:
                raise VaultError("Metadados do cofre inválidos.") from error
            key = scrypt(passphrase.encode("utf-8"), salt, 32, N=2**16, r=8, p=2)
            vault = cls(root, key)
            if meta is None:
                meta = {"salt": encode(salt), "check": vault.seal(path, {"migrated": False})}
                vault.save_metadata(path, meta)
            try:
                status = vault.unseal(path, meta["check"])
            except (KeyError, VaultError) as error:
                raise VaultError("Frase secreta incorreta ou cofre danificado.") from error
            if status != {"migrated": True}:
                vault.migrate()
                meta["check"] = vault.seal(path, {"migrated": True})
                vault.save_metadata(path, meta)
        return vault

    @staticmethod
    def save_metadata(path, meta):
        with atomic_text(path) as file:
            json.dump(meta, file)

    def aad(self, path):
        name = path.resolve().relative_to(self.root).as_posix()
        return ("EMA Trader local vault v1\0" + name).encode("utf-8")

    def seal(self, path, value):
        nonce = secrets.token_bytes(12)
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        cipher.update(self.aad(path))
        ciphertext, tag = cipher.encrypt_and_digest(payload)
        return PREFIX + encode(nonce + ciphertext + tag)

    def unseal(self, path, value):
        try:
            if not value.startswith(PREFIX):
                raise ValueError
            raw = decode(value[len(PREFIX):])
            if len(raw) < 28:
                raise ValueError
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=raw[:12])
            cipher.update(self.aad(path))
            return json.loads(cipher.decrypt_and_verify(raw[12:-16], raw[-16:]))
        except (AttributeError, ValueError) as error:
            raise VaultError("Registro privado inválido ou adulterado.") from error

    def read(self, path, default=None):
        try:
            ciphertext = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return default
        return self.unseal(path, ciphertext)

    def write(self, path, value):
        with atomic_text(path, durable=True) as file:
            file.write(self.seal(path, value))

    def append_order(self, value):
        path = self.root / ORDERS
        with account_lock(self.root / ".orders.lock"):
            with path.open("a", encoding="utf-8") as file:
                file.write(self.seal(path, value) + "\n")
                file.flush()
                os.fsync(file.fileno())

    def orders(self):
        path = self.root / ORDERS
        with account_lock(self.root / ".orders.lock"):
            end = path.stat().st_size if path.exists() else 0
        if end:
            with path.open("rb") as file:
                while file.tell() < end:
                    yield self.unseal(path, file.readline().decode("ascii").strip())

    def migrate(self):
        for pattern in ("profiles/*.json", "Lighter/*.json", "Lighter/risk/*.json"):
            for path in self.root.glob(pattern):
                content = path.read_text(encoding="utf-8")
                if content.startswith(PREFIX):
                    self.unseal(path, content)
                else:
                    self.write(path, json.loads(content))
        path = self.root / ORDERS
        with account_lock(self.root / ".orders.lock"):
            if path.exists():
                with atomic_text(path) as encrypted:
                    with path.open(encoding="utf-8") as plaintext:
                        for line in plaintext:
                            record = line.strip()
                            if record:
                                value = self.unseal(path, record) if record.startswith(PREFIX) else json.loads(record)
                                encrypted.write(self.seal(path, value) + "\n")
