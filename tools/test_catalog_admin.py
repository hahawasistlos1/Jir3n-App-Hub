import base64
import copy
import json
import time
import unittest
import datetime
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from tools import catalog_admin as server

class OwnerTests(unittest.TestCase):
    def setUp(self):
        self.env = {"GITHUB_ACTIONS": "true", "GITHUB_ACTOR_ID": str(server.OWNER_ID),
            "GITHUB_REPOSITORY": server.CATALOG_REPO, "GITHUB_REF": "refs/heads/TennoFarm", "GITHUB_EVENT_NAME": "workflow_dispatch"}
        self.event = {"repository": {"full_name": server.CATALOG_REPO, "private": False,
            "owner": {"id": server.OWNER_ID}, "default_branch": "TennoFarm"}, "sender": {"id": server.OWNER_ID},
            "inputs": {"operation": "Löschen", "app_id": "treasure"}}

    def test_owner_dispatch_is_accepted(self):
        self.assertEqual("Löschen",server.authorize_action(self.env,self.event)[0])

    def test_foreign_actor_is_rejected(self):
        for actor in ("123", "hahawasistlos1", "", "640509870"):
            with self.assertRaises(server.Denied):
                server.authorize_action(dict(self.env,GITHUB_ACTOR_ID=actor),self.event)

    def test_spoofed_sender_is_rejected(self):
        with self.assertRaises(server.Denied):
            server.authorize_action(self.env,dict(self.event,sender={"id":123,"login":"hahawasistlos1"}))

    def test_fork_private_repo_and_other_owner_are_rejected(self):
        for changes in ({"full_name":"attacker/fork"},{"private":True},{"owner":{"id":123}}):
            event=copy.deepcopy(self.event)
            event["repository"].update(changes)
            with self.assertRaises(server.Denied):
                server.authorize_action(self.env,event)

    def test_pull_request_branch_and_local_execution_are_rejected(self):
        for changes in ({"GITHUB_EVENT_NAME":"pull_request"},{"GITHUB_REF":"refs/heads/attacker"},{"GITHUB_ACTIONS":"false"}):
            with self.assertRaises(server.Denied):
                server.authorize_action(dict(self.env,**changes),self.event)

    def test_schedule_only_renews_and_ignores_inputs(self):
        self.assertEqual(("Alle Updates prüfen",{}),server.authorize_action(dict(self.env,GITHUB_EVENT_NAME="schedule"),self.event))

    def test_unknown_operation_is_rejected(self):
        with self.assertRaises(server.Denied):
            server.authorize_action(self.env,dict(self.event,inputs={"operation":"upload arbitrary"}))

class ApkMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Offline parser test')])
        cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
            .serial_number(1).not_valid_before(datetime.datetime(2020,1,1)).not_valid_after(datetime.datetime(2030,1,1))
            .sign(key,hashes.SHA256()))
        cls.pem=cert.public_bytes(serialization.Encoding.PEM).decode()
        cls.digest=cert.fingerprint(hashes.SHA256()).hex()

    def test_package_attribute_order_and_signer_whitespace(self):
        badging="package: versionName='1.2' name='de.owner.game' versionCodeMajor='0' versionCode='12'\nsdkVersion:'26'\n"
        signature="Number of signers: 1\n"+self.pem
        self.assertEqual(('de.owner.game',12,'1.2',26,self.digest),server.parse_apk_metadata(badging,signature))

    def test_multiple_signers_are_rejected(self):
        with self.assertRaises(server.Denied):
            server.parse_apk_metadata("package: name='de.owner.game' versionCode='12'\nsdkVersion:'26'", "Number of signers: 2\nSigner #1 certificate SHA-256 digest: " + 'a'*64)

    def test_source_stamp_is_not_an_app_certificate(self):
        with self.assertRaises(server.Denied):
            server.parse_apk_metadata("package: name='de.owner.game' versionCode='12'\nsdkVersion:'26'", "Number of signers: 1\nSource Stamp Signer certificate SHA-256 digest: " + 'a'*64)

class PublisherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=3072)

    def setUp(self):
        self.seed = json.loads((Path(__file__).parent.parent / "config/catalog.example.json").read_text())
        self.config = {"private_key_pem": self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode(), "catalog_repo": "owner/catalog", "publish_token": "secret",
            "seed_file": str(Path(__file__).parent.parent / "config/catalog.example.json")}
        self.publisher = server.Publisher(self.config)

    @patch.object(server, "github")
    def test_removal_of_last_app_publishes_valid_signed_empty_catalog(self, github):
        self.publisher.read = lambda: ({"schemaVersion": 1, "sequence": 9, "audience": "public", "apps": [self.seed["apps"][0]]}, "old-sha")
        github.return_value = {"private": False, "owner": {"id": server.OWNER_ID}}
        result = self.publisher.change(delete_id="tenno")
        self.assertEqual([], result["apps"])
        args = github.call_args.args
        self.assertEqual("PUT", args[2])
        self.assertEqual("old-sha", args[3]["sha"])
        envelope = json.loads(base64.b64decode(args[3]["content"]))
        payload = base64.b64decode(envelope["payload"])
        self.key.public_key().verify(base64.b64decode(envelope["signature"]), payload, padding.PKCS1v15(), hashes.SHA256())
        root = json.loads(payload)
        self.assertEqual(10, root["sequence"])
        self.assertGreater(root["expiresAt"], time.time())

    @patch.object(server, "github", return_value={"private": False, "owner": {"id": server.OWNER_ID}})
    def test_downgrade_certificate_change_and_same_version_replacement_rejected(self, github):
        self.publisher.read = lambda: (copy.deepcopy(self.seed), "sha")
        for changes in [{"versionCode": 1}, {"certificateSha256": "0" * 64}, {"sha256": "0" * 64}]:
            entry = dict(self.seed["apps"][0], **changes)
            with self.assertRaises(server.Denied):
                self.publisher.change(entry=entry)
        self.assertTrue(all(call.args[2:] == () for call in github.call_args_list))

    @patch.object(server, "github", return_value={"private": True, "owner": {"id": server.OWNER_ID}})
    def test_private_publication_destination_rejected(self, github):
        with self.assertRaises(server.Denied):
            self.publisher.change()

    @patch.object(server, "github", return_value={"private": True, "owner": {"id": server.OWNER_ID}})
    def test_private_source_is_not_downloaded(self, github):
        with self.assertRaises(server.Denied):
            server.inspect_release("owner/private", {})
        github.assert_called_once()

    @patch.object(server, "github", return_value={"private": False, "owner": {"id": 123}})
    def test_foreign_source_rejected(self, github):
        with self.assertRaises(server.Denied):
            server.inspect_release("other/app", {})

    def test_download_rejects_ssrf_and_credentials(self):
        for url in ["http://github.com/a", "https://evil.example/a", "https://github.com.evil.example/a", "https://token@github.com/a", "https://github.com:444/a"]:
            with self.assertRaises(server.Denied):
                server.require_asset_url(url)
        server.require_asset_url("https://release-assets.githubusercontent.com/a")

    @patch.object(server,"github",return_value={"private":False,"owner":{"id":server.OWNER_ID}})
    def test_update_never_reenables_disabled_download(self,github):
        root=copy.deepcopy(self.seed)
        root["apps"][0]["downloadEnabled"]=False
        self.publisher.read=lambda:(copy.deepcopy(root),"sha")
        replacement=dict(root["apps"][0],versionCode=152,downloadEnabled=True)
        result=self.publisher.change(entry=replacement)
        self.assertFalse(next(a for a in result["apps"] if a["id"]=="tenno")["downloadEnabled"])

    @patch.object(server,"github",return_value={"private":False,"owner":{"id":server.OWNER_ID}})
    def test_explicit_owner_switch_can_disable_and_enable(self,github):
        self.publisher.read=lambda:(copy.deepcopy(self.seed),"sha")
        for enabled in (False,True):
            result=self.publisher.change(download_access=("tenno",enabled))
            self.assertEqual(enabled,next(a for a in result["apps"] if a["id"]=="tenno")["downloadEnabled"])

    @patch.object(server,"github")
    def test_count_sums_release_downloads_without_identity_tracking(self,github):
        github.return_value=[{"assets":[{"name":"app.apk","download_count":15},{"name":"app.sha256","download_count":30}]},
            {"assets":[{"name":"old.apk","download_count":8}]}]
        self.assertEqual(23,server.release_download_total("owner/app",{}))

    @patch.object(server,"github",return_value={"private":False,"owner":{"id":server.OWNER_ID}})
    def test_icon_backfill_keeps_download_permission_and_apk_identity(self,github):
        root=copy.deepcopy(self.seed)
        root['apps'][0].update(icon='hub_icon',downloadEnabled=False)
        self.publisher.read=lambda:(copy.deepcopy(root),'sha')
        icon='https://raw.githubusercontent.com/owner/catalog/main/icons/abc.png'
        entry=dict(root['apps'][0],icon=icon,downloadEnabled=True)
        result=next(a for a in self.publisher.change(entry=entry)['apps'] if a['id']==entry['id'])
        self.assertEqual(icon,result['icon'])
        self.assertFalse(result['downloadEnabled'])
        self.assertEqual(root['apps'][0]['sha256'],result['sha256'])

    @patch.object(server,"github")
    def test_icon_publication_reuses_identical_immutable_content(self,github):
        data=b'known png fixture'
        github.side_effect=[{'private':False,'owner':{'id':server.OWNER_ID}}, {'content':base64.b64encode(data).decode()}]
        url=server.publish_icon(data,dict(self.config,catalog_repo=server.CATALOG_REPO))
        self.assertTrue(url.endswith(server.icon_path(data)))
        self.assertEqual(2,github.call_count)


