# Generate CA private key (PK)
openssl req -newkey rsa:4096 -nodes -keyout PK.key -new -x509 -sha256 -days 3650 -subj "/CN=My Platform Key/" -out PK.crt
# Generate KEK private key
openssl req -newkey rsa:4096 -nodes -keyout KEK.key -new -x509 -sha256 -days 3650 -subj "/CN=My Key Exchange Key/" -out KEK.crt
# Generate DB private key (for signing binaries)
openssl req -newkey rsa:4096 -nodes -keyout DB.key -new -x509 -sha256 -days 3650 -subj "/CN=My Signature Database Key/" -out DB.crt

# Convert all certificates to ESL format
cert-to-efi-sig-list PK.crt PK.esl
cert-to-efi-sig-list KEK.crt KEK.esl
cert-to-efi-sig-list DB.crt DB.esl

# Sign the ESL files with their respective keys
sign-efi-sig-list -k PK.key -c PK.crt PK PK.esl PK.auth
sign-efi-sig-list -k PK.key -c PK.crt KEK KEK.esl KEK.auth
sign-efi-sig-list -k KEK.key -c KEK.crt db DB.esl DB.auth

# Generate PCR keys
ukify genkey --pcr-private-key=tpm2-pcr-private-key-system.pem --pcr-public-key=tpm2-pcr-public-key-system.pem
