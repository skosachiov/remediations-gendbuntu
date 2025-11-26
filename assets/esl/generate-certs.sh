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

# Convert Microsoft certificates to PEM
find ms-* -type f -name '*.crt' -exec sh -c 'openssl x509 -in "$1" -out "${1%.crt}.pem" -outform PEM' _ {} \;

# Convert Microsoft certificates to ESL format DB
cert-to-efi-sig-list "ms-db/windows uefi ca 2023.pem" ms-db-2023.esl
cert-to-efi-sig-list "ms-db/microsoft uefi ca 2023.pem" ms-db-2023-2.esl
cert-to-efi-sig-list "ms-db/MicCorUEFCA2011_2011-06-27.pem" ms-db-2011.esl
cert-to-efi-sig-list "ms-db/MicWinProPCA2011_2011-10-19.pem" ms-db-2011-2.esl
# Convert Microsoft certificates to ESL format KEK
cert-to-efi-sig-list "ms-KEK/microsoft corporation kek 2k ca 2023.pem" ms-kek-2023.esl
cert-to-efi-sig-list "ms-KEK/MicCorKEKCA2011_2011-06-24.pem" ms-kek-2011.esl

# Combine Microsoft DB certificates with your custom DB
cat DB.esl ms-db-2023.esl ms-db-2023-2.esl ms-db-2011.esl ms-db-2011-2.esl > combined-db.esl
# Combine Microsoft KEK certificates with your custom KEK
cat KEK.esl ms-kek-2023.esl ms-kek-2011.esl > combined-kek.esl

# Sign the combined ESL files with their respective keys
sign-efi-sig-list -k PK.key -c PK.crt PK PK.esl PK.auth
sign-efi-sig-list -k PK.key -c PK.crt KEK combined-kek.esl KEK.auth
sign-efi-sig-list -k KEK.key -c KEK.crt db combined-db.esl DB.auth

# Ukify generate the certificate and keys
ukify genkey --pcr-private-key=tpm2-pcr-private-key-system.pem --pcr-public-key=tpm2-pcr-public-key-system.pem
