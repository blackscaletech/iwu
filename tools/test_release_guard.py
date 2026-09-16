"""Synthetic negative controls for the publication-boundary scanner."""
import unittest
from check_release import inspect_bytes

class ReleaseBoundaryTests(unittest.TestCase):
    def reject(self,payload):
        with self.assertRaises(AssertionError):inspect_bytes('synthetic-fixture.txt',payload.encode())
    def test_user_path(self):self.reject('/'+'Users'+'/example-person/work')
    def test_private_path(self):self.reject('/'.join(['','private','var','folders','example']))
    def test_temporary_path(self):self.reject('/'+'var'+'/folders/example')
    def test_windows_path(self):self.reject('C:'+'\\Users\\example-person\\work')
    def test_github_token(self):self.reject('ghp_'+'A'*36)
    def test_api_token(self):self.reject('sk-'+'A'*40)
    def test_cloud_key(self):self.reject('AKIA'+'A'*16)
    def test_private_key(self):self.reject('-----BEGIN '+'OPENSSH PRIVATE KEY-----')
    def test_safe_public_identity(self):
        inspect_bytes('fixture.txt',b'blackscaletech https://swarm.services')

if __name__=='__main__':unittest.main()
