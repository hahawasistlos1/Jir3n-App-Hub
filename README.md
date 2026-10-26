# Kostenlose App-Verwaltung

GitHub-Repository: https://github.com/hahawasistlos1/Jir3n-App-Hub

Verwaltung: https://github.com/hahawasistlos1/Jir3n-App-Hub/actions/workflows/catalog.yml

## Neue App oder neues Release

1. Signierte APK wie bisher als GitHub-Release hochladen.
2. Im Hub **Profil → GitHub-Verwaltung öffnen** wählen und bei GitHub anmelden.
3. **Run workflow** öffnen und **Hinzufügen / Aktualisieren** auswählen.
4. Repository-Link und Kategorie eintragen, dann **Run workflow** drücken.

Der Ablauf lädt die APK, prüft ihre Signatur und liest Name, Paket, Version und
Mindest-Android aus. SHA-256 und Dateigröße werden selbst berechnet. Das Release
muss genau eine APK enthalten. Nur öffentliche Repositories deines Kontos sind
erlaubt. Windows-Programme und private Apps werden so noch nicht veröffentlicht.

Bestehende Apps werden anhand ihres Paketnamens erkannt. Ihre ID und ihr Icon
bleiben erhalten. Neue Apps erhalten zunächst das Hub-Standardsymbol. Wechselnde
App-Zertifikate, Downgrades und ausgetauschte APKs bei gleichem VersionCode werden
abgewiesen. Die Signaturprüfung ist kein Virenscan oder inhaltlicher App-Test.

## App entfernen

Im selben Formular **Löschen** auswählen und die App-ID angeben. Aktuell:

| App | ID |
|---|---|
| TennoFreunde | tenno |
| TreasureRunner | treasure |

Neue IDs stehen im Ergebnis des letzten Ablaufs. Löschen entfernt die App aus
dem Hub-Katalog, auch wenn es die letzte App ist. Es löscht weder GitHub-Dateien
noch installierte Programme. Der nächste Katalogabruf übernimmt die Änderung.

## Nur der Eigentümer

Der Ablauf akzeptiert ausschließlich GitHubs feste Konto-ID **64050987**, auf dem
Default-Branch des festen Repositories. Die Prüfung erfolgt sowohl im Workflow
als auch im Python-Programm. Andere Nutzer, Forks und Pull Requests erhalten
keinen Zugriff auf die Veröffentlichung. Ein lokaler Profilname erteilt keine
Rechte. Das öffentliche APK enthält weder GitHub-Zugangsdaten noch den privaten
Katalogschlüssel. Das öffentliche Repository darf keine weiteren Personen mit
Schreib-/Administratorrechten erhalten: Solche Rechte würden auch das Ändern
der Schutzregeln und Workflows ermöglichen.

Die Prüfsignatur wird serverseitig in GitHub Actions erstellt. Dafür muss einmalig
der erzeugte private Katalogschlüssel im Repository unter **Settings → Secrets
and variables → Actions → New repository secret** als `CATALOG_PRIVATE_KEY`
gespeichert werden. Der Schlüssel liegt lokal im ausgeschlossenen Ordner
`owner-private/catalog-signing.pem`. Niemals ins Repository, in Issues, in einen
öffentlichen Upload oder hier in den Chat kopieren. Eine sichere lokale Kopie
behalten; ein Schlüsselwechsel erfordert eine neue Vertrauenskonfiguration im Hub.

Ein initialer Katalog kann lokal signiert werden; ohne eingerichtetes Actions-
Secret funktionieren spätere Änderungen und Erneuerungen nicht. Der Hub bekommt
die feste GitHub-Feedadresse und den passenden öffentlichen Schlüssel ab Werk.
Bestehende bewusst gesetzte andere Releasequellen werden nicht überschrieben.

## Kosten und Betrieb

Der Ablauf läuft ausschließlich im **öffentlichen** Repository auf einem
Standard-Ubuntu-Runner, ohne hochgeladene Workflow-Artefakte und ohne Cache.
Diese Runner-Laufzeit ist laut GitHub kostenlos. Keine größeren Runner,
kostenpflichtigen Zusatzdienste, Firebase-Funktionen, Cloud Run oder Blaze.
Es wurde kein Bezahltarif eingerichtet. APKs bleiben GitHub-Release-Dateien.

Ein wöchentlicher geplanter Lauf erneuert die 30 Tage gültige Katalogsignatur.
GitHub kann geplante Workflows bei länger inaktiven öffentlichen Repositories
deaktivieren. Bei einer Warnung unter **Actions** wieder aktivieren oder manuell
**Gültigkeit erneuern** starten. Ein abgelaufener Feed wird nicht mehr als neue
vertrauenswürdige Version übernommen; der lokale Katalog bleibt erhalten.

Die Android-Build-CI ist separat und wird nicht für diese reine Katalogverwaltung
benötigt. Im Verwaltungs-Repository liegt ausschließlich der kleine Katalog-
Workflow mit seinen Hilfsdateien; keine privaten Projektnamen oder APK-Testdateien.

Quelle: https://docs.github.com/en/billing/concepts/product-billing/github-actions
