from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh

parameters = dh.generate_parameters(
    generator=2,
    key_size=1024,
    backend=default_backend()
)
dh_params = parameters.parameter_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.ParameterFormat.PKCS3
)

with open('.keys/dh_params.pem', 'wb') as param_file:
    param_file.write(dh_params)
