import os
import subprocess
import tempfile
from logging import Logger

from adeploy.common.kubectl import kubectl_create_secret
from adeploy.common.secrets.secret import Secret

_DUMMY_DATA_CRT = """
-----BEGIN CERTIFICATE-----
MIIEDTCCAfUCFAGFXSSH5VQqWAOkjXbbsFU+89CQMA0GCSqGSIb3DQEBCwUAMEMx
CzAJBgNVBAYTAkRFMQswCQYDVQQIDAJCVzESMBAGA1UEBwwJS2FybHNydWhlMRMw
EQYDVQQKDApEdW1teSBJbmMuMB4XDTIxMDEwNzExNTExMloXDTIyMDUyMjExNTEx
MlowQzELMAkGA1UEBhMCREUxCzAJBgNVBAgMAkJXMRIwEAYDVQQHDAlLYXJsc3J1
aGUxEzARBgNVBAoMCkR1bW15IEluYy4wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
ggEKAoIBAQDXtmzy3L2FNlvPu/u8wu6arC7GnXkhIkOtuS3HydrSrfzcO/YjUafr
o9Yw9SfYK1gfHcTYCCCKr1DOLOVmyU5ZkVUtJpljmg97l4ljvoNX6P4STWbOmCRE
mPuOOlBruqabc478QUTz840RVRpUOEg3BDTgZ/AgetqJUcVJW+FBk3kIlO8AaEKx
n9jZPhlZovuWJZdxk4qjsM1xnTs4Xlj/QyJzYsxuD7tXbNvWflQh1AKLkZ5aOj9x
4XhV2hizB82Lszn5lX6SReAKeR9BH6SfEjGHlNoC3DKRC82fJVUAhdLFcbl2if3r
GneeIQ/ghkOXc+eXPU6vN4xqBFyBp/J/AgMBAAEwDQYJKoZIhvcNAQELBQADggIB
AIJ2ta5YPwqYlCb4N3AkqLURC0a3BxRqeElLsGQRVekLGzUn/rp+vGJ3B38reC/7
lW6LKXFU8D96hWPggzYJjVBIkrv5EZo12DfXv0z7UPOgy2piaRvrfpmkiwCgEZPQ
R+d34rPY3rYcs7YIa7kbO0wAKSwdeUMhz1fhQuiJKgIKr0vFRrLHOdM5G0czPL7d
Qc3QGfJ8Y8nJjg8DcbRNKNWuL5BWmCXD/WWFS9N3EUzVsnOQu4/4d0zXxw1LVIH8
nClhhu92PgeFd067hWNH6iRTI79a/8mI3M5J+2OE71IIDqj5JNDKvD0bMf8oLuQj
znNXTwH/V9z3iemsJXbqzzRLf8Uqt81V28L6fPdAShUnLCCXS1rz6RHYpkBqbUso
hEY2wbvYl6SPvrsqCJ5PMzqH0EZcbx86V1Fd+CqbBlKMS1/rMBUQ+12/gxsJ0WcY
IKFHyhNFgeUNpZt3uo2KmiotrCFS+IOd/Jdcjbn9O3JvhTQFXmdXaP2Pdqm6rVeu
KxcQayRbw5HSQp9T08xJFuUfF2i5Vk6xgMlwWx9qNzHslKJjmcT5bYkDCv/L7cS6
6IWEggQai1pEs++U8rTHZHKBSL3Q63LgLMVSEgEsXLNPS+VQkU+2tLIsqFFR6FiP
YZFF4v0S0UKute95q56ftVLEQhDJGrofWy3sZKlla52b
-----END CERTIFICATE-----
"""

_DUMMY_DATA_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA17Zs8ty9hTZbz7v7vMLumqwuxp15ISJDrbktx8na0q383Dv2
I1Gn66PWMPUn2CtYHx3E2Aggiq9QzizlZslOWZFVLSaZY5oPe5eJY76DV+j+Ek1m
zpgkRJj7jjpQa7qmm3OO/EFE8/ONEVUaVDhINwQ04GfwIHraiVHFSVvhQZN5CJTv
AGhCsZ/Y2T4ZWaL7liWXcZOKo7DNcZ07OF5Y/0Mic2LMbg+7V2zb1n5UIdQCi5Ge
Wjo/ceF4VdoYswfNi7M5+ZV+kkXgCnkfQR+knxIxh5TaAtwykQvNnyVVAIXSxXG5
don96xp3niEP4IZDl3Pnlz1OrzeMagRcgafyfwIDAQABAoIBAF0/RLVvapWtO97+
2gFtGovOJqJA7F3AXBU62Wll/qvX/liNqwb1g2s/dZXQRBsUEZHR4oeoa7jHtFyL
19ao6q+ZPYK5DtGZhVvd08xETK6xzzLGNszTw8nLf+Kpnp4TH3ZPa93rsQzrmW2G
pk0Fz2HI9bqT8592vAVkTa46g5M+izV/A4OuuY+hdUXaBq8r04EfuLFiSkh7HOA2
Ht2GYtVmGnWzThlReDdTWHKTjkXXWwR871omiz3zK24gZC6VKcGSsPFbxYxKYw4S
dIR5Rrl+r7v6U0dbNFdNxnBfuspZDQkyeQO+3g2X0kcnW/uH/ReHChk7X5ZR2o6+
NQ3o7uECgYEA+H3BKbcVfCozi1t2UjzkUefcIA3PLSsPMRku5L+1U2161MYxJXan
N/BdDLRbGInOkFduscCaK+pwvew6hBeNtix5KtNcvkn17guGTfCfew03vlTG89Ur
ArnNdJPAdGFKZy9kR4llNFtrCy+MDrC9EwnsFzoZaGnjrbqD6b4uFkkCgYEA3jsb
QdZXsrfUpXm9CanMNhRCnlOQpN6aXo+ZFo0ktUrbTJNspLOjtKS/dbp0VeCDqH7Z
dce/cBxyNzqna9g1CErtVfnPgWgs0V7YxP+gibEIuR2j/sdAanbOdkRJEjHbg5D/
IShL+IcxNHOzLQFEWX3uvcz6nTABwfHNuqNAoocCgYEAqBgBjCOCkCzIE3Q6lSUF
2nY7DR/qTwa6zx7W/vzEP3xmw/qSEmKyeX/KoiZ7HR1Ts4bBpdLBOAXuYDul1edN
ALgS+yphqYPErlPzdVPZvlbRp5oXv6gq4TwpRLwSS2fo+eYwMsg5wvI4diei2ekq
7e8fWxL9Twmab9IlHAB/kqkCgYBKT+OGeYFr7tL53qKbB5+U+eNpBDKbHyDpvAUK
KHp88SIyEh5DWRrF/k1TtdzPFruP7ZMUMo5OlASReVig1HSvaDbDCD0eXdKW1KuR
/JUXVg6/sCy1trVQpJfXrm/s2KU58pON5+a3naWTj5j71K+haV4bM98eDv6Xdx8/
aPXlIwKBgQDz9TGYW2nM3GWVQSds/y78He/9p8wsbKgvjSyU0JfulK88eYGNsNho
lnUqJtp1zChmcVqRN2f8m9XX59Kgt90RnlCQ0Vl010ovo+y8bCmbsjHzI2SlZ012
4jzbJHDRq1er3/Euz59jAoELTecROcMno/Sm+VTLLc6E2ufzXB5JGw==
-----END RSA PRIVATE KEY-----
"""


class TlsSecret(Secret):
    type: str = "tls"
    cert: str = None
    key: str = None

    def __init__(self, deployment, cert: str, key: str, name: str = None, use_pass: bool = True,
                 use_gopass_cat: bool = True, custom_cmd: bool = False):
        self.cert = cert
        self.key = key
        super().__init__(deployment, name, use_pass, use_gopass_cat, custom_cmd)

    def create(self, log: Logger = None, dry_run: str = None, output: str = None) -> subprocess.CompletedProcess:

        cert_data = _DUMMY_DATA_CRT if dry_run else self.get_value(self.cert, log, dry_run=False)
        cert = tempfile.NamedTemporaryFile(delete=False,
                                           mode='wb' if isinstance(cert_data, (bytes, bytearray)) else 'w')
        cert.write(cert_data)
        cert.close()

        key_data = _DUMMY_DATA_KEY if dry_run else self.get_value(self.key, log, dry_run=False)
        key = tempfile.NamedTemporaryFile(delete=False, mode='wb' if isinstance(key_data, (bytes, bytearray)) else 'w')
        key.write(key_data)
        key.close()

        args = [
            f'--cert={cert.name}',
            f'--key={key.name}',
        ]

        try:

            result = kubectl_create_secret(
                log=log,
                name=self.name,
                namespace=self.deployment.namespace,
                type=self.type,
                args=args,
                output=output,
                labels={
                    'adeploy.name': self.deployment.name,
                    'adeploy.release': self.deployment.release
                })

        finally:
            os.remove(cert.name)
            os.remove(key.name)

        return result
