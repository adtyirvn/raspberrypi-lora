from src import ascon
import binascii
asc = ascon.Ascon()

key = 'testtesttest1123'
nonce_g = 'testtesttest1123'


def decryption(ascon, ciphertext, key, nonce, mode="ECB"):
    key_bytes = key.encode('utf-8')
    if type(nonce) == str:
        nonce = nonce.encode('utf-8')
    print(f"key: {key_bytes} len: {len(key_bytes)}")
    print(f"nonce: {nonce} len: {len(nonce)}")
    plaintext = ascon.ascon_decrypt(
        key_bytes, nonce, associateddata="", ciphertext=ciphertext,  variant="Ascon-128")
    if mode == "CBC":
        global nonce_g
        nonce_g = ciphertext[:16]
    return plaintext


a = decryption(asc, b'\xe8=PC\x88\xfbV\n\xc6\x04\xec\xc2D\xb6\xf1>\'\xca\xa5W\xa902\x94.55s\x12\xa0V0\x01\xc3gM\xb0b\x19\x98U\xbc\xceB\xd1\xd3\xa3\x87f\x1dK\t;j\xaf\x9f\x8bG\xe8\xb0\x95\x9b\x19\xb8D\xc6ruU\xac\x8el\xbd\x88\x8b\xe3H\xd5\xa1\t"\xbfJ\xae\xc7\x1fyT\x14.\xdbr\xe6R\xa3\xeeK\xae\x0f\\\xac\xb7V0\nM',
               key, nonce_g, "ECB")
print(a)
