"""Owner-only publisher for the free public GitHub Actions workflow."""
import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding, rsa
OWNER_ID = 64050987
CATALOG_REPO = "hahawasistlos1/Jir3n-App-Hub"
MAX_APK = 512 * 1024 * 1024
ASSET_HOSTS = {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
class Denied(Exception):
    def __init__(self, message, status=403):
        super().__init__(message)
        self.status = status

def repository(value):
    value = value.strip().removeprefix("https://github.com/").rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise Denied("Bitte einen GitHub-Repository-Link eingeben.", 400)
    return value


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_asset_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def require_asset_url(url):
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or u.hostname not in ASSET_HOSTS or u.username or u.password or u.port not in (None, 443) or u.fragment:
        raise Denied("Nicht erlaubte Downloadadresse.", 400)


def github(path, token="", method="GET", data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Jir3nHub-OwnerAdmin"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request("https://api.github.com" + path, data=body, method=method, headers=headers)
    # API redirects are deliberately not followed with credentials.
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(req, timeout=40) as response:
        raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise Denied("GitHub-Antwort zu groß.", 502)
        return json.loads(raw)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def release_download_total(repo, config):
    total = 0
    for page in range(1,21):
        releases=github(f"/repos/{repository(repo)}/releases?per_page=100&page={page}",config.get("publish_token",""))
        for release in releases:
            for asset in release.get("assets",[]):
                if asset.get("name", "").lower().endswith((".apk", ".exe", ".msi", ".zip", ".appimage", ".dmg")):
                    total += max(0,int(asset.get("download_count",0)))
        if len(releases)<100:
            return total
    return -1  # Do not show an incomplete total as a real count.


def inspect_release(repo, config):
    """Public GitHub reads only. Inspect actual APK; never trust tag/version text."""
    meta = github("/repos/" + repo, config.get("publish_token", ""))
    if meta.get("private") is not False or meta.get("owner", {}).get("id") != OWNER_ID:
        raise Denied("Hier sind nur öffentliche Repositories deines Kontos erlaubt.")
    release = github("/repos/" + repo + "/releases/latest", config.get("publish_token", ""))
    assets = [a for a in release.get("assets", []) if a["name"].lower().endswith(".apk")]
    if len(assets) != 1:
        raise Denied("Das neueste Release muss genau eine universelle APK enthalten.", 400)
    asset = assets[0]
    if not 0 < asset["size"] <= MAX_APK:
        raise Denied("APK fehlt oder ist größer als 512 MB.", 400)
    url = asset["browser_download_url"]
    require_asset_url(url)
    digest = hashlib.sha256()
    with tempfile.TemporaryDirectory() as directory:
        apk = Path(directory) / "release.apk"
        req = urllib.request.Request(url, headers={"User-Agent": "Jir3nHub-OwnerAdmin"})
        total = 0
        with urllib.request.build_opener(SafeRedirect()).open(req, timeout=60) as response, apk.open("wb") as output:
            while chunk := response.read(65536):
                total += len(chunk)
                if total > asset["size"] or total > MAX_APK:
                    raise Denied("APK-Größe stimmt nicht.", 400)
                digest.update(chunk)
                output.write(chunk)
        if total != asset["size"]:
            raise Denied("APK ist unvollständig.", 400)
        badging = subprocess.run([config["aapt"], "dump", "badging", str(apk)],
            capture_output=True, text=True, check=True, timeout=120, encoding="utf-8", errors="replace").stdout
        signature = subprocess.run([config["apksigner"], "verify", "--verbose", "--print-certs-pem", str(apk)],
            capture_output=True, text=True, check=True, timeout=120).stdout
    pkg, code, version, minimum, certificate = parse_apk_metadata(badging, signature)
    label = re.search(r"^application-label:'([^']+)'", badging, re.M)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+", pkg):
        raise Denied("Ungültiger Paketname.", 400)
    return {"id": hashlib.sha256(pkg.encode()).hexdigest()[:24], "name": (label[1] if label else meta["name"])[:100],
        "subtitle": "", "description": str(meta.get("description") or "")[:12000], "category": "Tools",
        "platform": "Android", "visibility": "public", "icon": "hub_icon", "packageName": pkg,
        "repository": repo, "channel": "stable", "version": version, "versionCode": int(code),
        "apkUrl": url, "bytes": total, "sha256": digest.hexdigest(), "certificateSha256": certificate,
        "minSdk": minimum, "published": release.get("published_at", ""), "status": "Veröffentlicht",
        "notes": str(release.get("body") or "")[:20000], "website": release["html_url"], "screenshots": [],
        "downloadEnabled": False, "downloadCount": release_download_total(repo,config)}


def parse_apk_metadata(badging, signature):
    package_line = next((line.strip() for line in badging.splitlines() if line.strip().startswith("package:")), "")
    attributes = dict(re.findall(r"(\w+)='([^']*)'", package_line))
    minimum = re.search(r"^(?:sdkVersion|minSdkVersion):\s*'(\d+)'", badging, re.M)
    signer_count = re.search(r"^Number of signers:\s*(\d+)\s*$", signature, re.M)
    certificates = re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", signature, re.S)
    certs = {x509.load_pem_x509_certificate(pem.encode()).fingerprint(hashes.SHA256()).hex() for pem in certificates}
    if (not attributes.get("name") or not attributes.get("versionCode", "").isdigit()
            or int(attributes["versionCode"]) <= 0 or not minimum or not signer_count
            or int(signer_count[1]) != 1 or len(certs) != 1):
        raise Denied(f"APK-Metadaten nicht unterstützt: Paket={bool(attributes.get('name'))}, API={bool(minimum)}, Einzelsignatur={bool(signer_count and signer_count[1]=='1')}, Zertifikate={len(certs)}.", 400)
    return attributes["name"], int(attributes["versionCode"]), attributes.get("versionName", ""), int(minimum[1]), next(iter(certs))


class Publisher:
    def __init__(self, config):
        self.config = config
        self.key = serialization.load_pem_private_key(config["private_key_pem"].encode(), password=None)
        if not isinstance(self.key, rsa.RSAPrivateKey) or self.key.key_size < 3072:
            raise ValueError("RSA-Schlüssel mit mindestens 3072 Bit erforderlich")
        self.repo = repository(config["catalog_repo"])
        self.path = "/repos/" + self.repo + "/contents/catalog.json"
        self.lock = threading.Lock()

    def read(self):
        try:
            file = github(self.path, self.config["publish_token"])
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            # Existing repo must be public and belong to the owner even on bootstrap.
            self.check_destination()
            seed = json.loads(Path(self.config["seed_file"]).read_text(encoding="utf-8"))
            return seed, None
        envelope = json.loads(base64.b64decode(file["content"]))
        payload = base64.b64decode(envelope["payload"], validate=True)
        self.key.public_key().verify(base64.b64decode(envelope["signature"], validate=True), payload, padding.PKCS1v15(), hashes.SHA256())
        root = json.loads(payload)
        if root.get("schemaVersion") != 1 or root.get("audience") != "public" or any(a.get("visibility") != "public" for a in root["apps"]):
            raise Denied("Öffentlicher Katalog ungültig.", 409)
        return root, file["sha"]

    def check_destination(self):
        meta = github("/repos/" + self.repo, self.config["publish_token"])
        if meta.get("private") is not False or meta.get("owner", {}).get("id") != OWNER_ID:
            raise Denied("Ziel muss ein öffentliches Repository deines Kontos sein.")
        return meta

    def change(self, entry=None, delete_id=None, download_access=None):
        with self.lock:
            self.check_destination()
            root, sha = self.read()
            apps = root["apps"]
            if entry is not None:
                entry.setdefault("downloadEnabled",False)
                if entry.get("visibility") != "public":
                    raise Denied("Private Einträge werden hier nicht veröffentlicht.")
                old = next((a for a in apps if a["packageName"] == entry["packageName"]), None)
                if old:
                    if old["certificateSha256"] != entry["certificateSha256"] or entry["versionCode"] < old["versionCode"]:
                        raise Denied("Zertifikatwechsel oder Versionsrückschritt abgewiesen.", 409)
                    if entry["versionCode"] == old["versionCode"] and entry["sha256"] != old["sha256"]:
                        raise Denied("Gleiche Versionsnummer mit anderer APK abgewiesen.", 409)
                    entry["id"] = old["id"]
                    entry["icon"] = old.get("icon", "hub_icon")
                    entry["subtitle"] = old.get("subtitle", entry.get("subtitle", ""))
                    entry["downloadEnabled"] = old.get("downloadEnabled",True)
                    apps = [a for a in apps if a["id"] != old["id"]]
                apps = apps + [entry]
            elif delete_id is not None:
                if not any(a["id"] == delete_id for a in apps):
                    raise Denied("App nicht gefunden.", 404)
                apps = [a for a in apps if a["id"] != delete_id]
            elif download_access is not None:
                identifier, enabled = download_access
                if not isinstance(enabled,bool) or not any(a["id"]==identifier for a in apps):
                    raise Denied("Ungültige Downloadfreigabe.",400)
                apps = [dict(a,downloadEnabled=enabled) if a["id"]==identifier else a for a in apps]
            if len(apps) > 200:
                raise Denied("Maximal 200 Apps erlaubt.", 400)
            root.update(apps=apps, sequence=int(root["sequence"]) + 1, expiresAt=int(time.time()) + 30 * 86400)
            payload = json.dumps(root, ensure_ascii=False, separators=(",", ":")).encode()
            envelope = json.dumps({"payload": base64.b64encode(payload).decode(), "signature": base64.b64encode(
                self.key.sign(payload, padding.PKCS1v15(), hashes.SHA256())).decode()}).encode()
            if len(envelope) > 2_000_000:
                raise Denied("Katalog zu groß.", 400)
            request = {"message": "Update signed App Hub catalog", "content": base64.b64encode(envelope).decode()}
            if sha:
                request["sha"] = sha
            github(self.path, self.config["publish_token"], "PUT", request)
            return root


def authorize_action(env, event):
    repo = event.get("repository", {})
    if (env.get("GITHUB_ACTIONS") != "true" or env.get("GITHUB_ACTOR_ID") != str(OWNER_ID)
            or env.get("GITHUB_REPOSITORY") != CATALOG_REPO
            or repo.get("full_name") != CATALOG_REPO or repo.get("private") is not False
            or repo.get("owner", {}).get("id") != OWNER_ID
            or env.get("GITHUB_REF") != "refs/heads/" + repo.get("default_branch", "")):
        raise Denied("Nur der Eigentümer darf den öffentlichen Katalog auf dem Default-Branch verwalten.")
    name = env.get("GITHUB_EVENT_NAME")
    if name == "workflow_dispatch":
        if event.get("sender", {}).get("id") != OWNER_ID:
            raise Denied("GitHub-Absender nicht freigeschaltet.")
        inputs = event.get("inputs", {})
        operation = inputs.get("operation")
        if operation not in ("Hinzufügen / Aktualisieren", "Löschen", "Gültigkeit erneuern", "Alle Updates prüfen", "Downloads freigeben", "Downloads sperren"):
            raise Denied("Unbekannter Vorgang.", 400)
        return operation, inputs
    if name == "schedule":
        return "Alle Updates prüfen", {}
    raise Denied("Dieser Ereignistyp darf keinen Katalog veröffentlichen.")


def publish_public_key(publisher):
    public = publisher.key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    encoded = base64.b64encode(public).decode()
    path = "/repos/" + CATALOG_REPO + "/contents/catalog-public-key.txt"
    try:
        current = github(path, publisher.config["publish_token"])
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        github(path, publisher.config["publish_token"], "PUT", {"message": "Publish catalog verification key",
            "content": base64.b64encode((encoded + "\n").encode()).decode()})
    else:
        if base64.b64decode(current["content"]).decode().strip() != encoded:
            raise Denied("Öffentlicher Katalogschlüssel passt nicht. Kein automatischer Schlüsselwechsel.")


def main():
    global stage
    stage = "Eigentümerprüfung"
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    operation, inputs = authorize_action(os.environ, event)
    config = {"catalog_repo": CATALOG_REPO, "publish_token": os.environ["GITHUB_TOKEN"],
        "private_key_pem": os.environ["CATALOG_PRIVATE_KEY"], "aapt": os.environ.get("AAPT", ""), "apksigner": os.environ.get("APKSIGNER", ""),
        "seed_file": str(Path(__file__).parent.parent / "config/catalog.example.json")}
    stage = "Signierschlüssel laden"
    publisher = Publisher(config)
    # Validate existing feed before any metadata publication.
    stage = "Vorhandenen Katalog prüfen"
    publisher.read()
    stage = "Öffentlichen Prüfschlüssel veröffentlichen"
    publish_public_key(publisher)
    if operation == "Hinzufügen / Aktualisieren":
        stage = "GitHub-Release und APK prüfen"
        entry = inspect_release(repository(inputs.get("repository", "")), config)
        category = inputs.get("category", "Tools")
        if category not in ("Spiele", "Tools", "Editoren"):
            raise Denied("Unbekannte Kategorie.")
        entry["category"] = category
        if inputs.get("description", "").strip():
            entry["description"] = inputs["description"].strip()[:12000]
            entry["descriptionOverride"] = True
        stage = "Signierten Katalog speichern"
        root = publisher.change(entry=entry)
    elif operation == "Löschen":
        identifier = inputs.get("app_id", "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", identifier):
            raise Denied("Zum Löschen eine gültige App-ID eingeben.")
        root = publisher.change(delete_id=identifier)
    elif operation in ("Downloads freigeben", "Downloads sperren"):
        identifier = inputs.get("app_id", "").strip()
        root = publisher.change(download_access=(identifier,operation=="Downloads freigeben"))
    elif operation == "Alle Updates prüfen":
        current = publisher.read()[0]
        for old in list(current["apps"]):
            if not old.get("repository") or old.get("platform") != "Android":
                continue
            stage = "Öffentliche Updates prüfen"
            release = github("/repos/" + repository(old["repository"]) + "/releases/latest", config["publish_token"])
            assets = [a for a in release.get("assets", []) if a["name"].lower().endswith(".apk")]
            if len(assets) == 1 and (assets[0]["browser_download_url"] != old["apkUrl"] or assets[0]["size"] != old["bytes"]):
                entry = inspect_release(old["repository"],config)
                entry["category"] = old["category"]
                if old.get("descriptionOverride"):
                    entry["description"] = old["description"]
                    entry["descriptionOverride"] = True
                publisher.change(entry=entry)
            elif not old.get("descriptionOverride"):
                metadata = github("/repos/" + old["repository"], config["publish_token"])
                description = str(metadata.get("description") or "")[:12000]
                if description and description != old.get("description"):
                    publisher.change(entry=dict(old, description=description))
            latest = next(a for a in publisher.read()[0]["apps"] if a["id"]==old["id"])
            count = release_download_total(old["repository"],config)
            if count != latest.get("downloadCount",-1):
                publisher.change(entry=dict(latest, downloadCount=count))
        root = publisher.change()
    else:
        root = publisher.change()
    summary = "## App-Katalog aktualisiert\n\n| App | ID | Version | Downloads freigegeben |\n|---|---|---|---|\n"
    for app in root["apps"]:
        # Keep release-controlled text from injecting Markdown links/HTML into job summaries.
        name = re.sub(r"[^\w .-]", "", app["name"])[:100]
        version = re.sub(r"[^\w .-]", "", app["version"])[:80]
        summary += f"| {name} | `{app['id']}` | {version} | {'Ja' if app.get('downloadEnabled',True) else 'Nein'} |\n"
    if not root["apps"]:
        summary += "\nDer Katalog ist jetzt leer. Installierte Programme werden nicht deinstalliert.\n"
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
        output.write(summary)
    print("Signierter Katalog erfolgreich gespeichert.")


if __name__ == "__main__":
    stage = "Start"
    try:
        main()
    except Denied as error:
        print(str(error))
        raise SystemExit(1)
    except urllib.error.HTTPError as error:
        print(f"{stage}: GitHub antwortet mit HTTP {error.code}. Keine Geheimnisse werden protokolliert.")
        raise SystemExit(1)
    except subprocess.CalledProcessError as error:
        print(f"{stage}: APK-Prüfprogramm meldet Fehler {error.returncode}.")
        raise SystemExit(1)
    except Exception as error:
        print(f"{stage}: {type(error).__name__}. Keine Geheimnisse werden protokolliert.")
        raise SystemExit(1)


