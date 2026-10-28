# Kostenlose App-Verwaltung

## Neue Bedienung ab 0.1.6

Im Launcher **Profil → Adminbereich** öffnen. Nur dein von Firebase freigegebenes Google-Konto sieht diesen Bereich.

1. Einmal **GitHub verbinden** wählen und den angezeigten Code bei GitHub bestätigen.
2. Den GitHub-Link deiner App einfügen und eine Kategorie auswählen.
3. **App hinzufügen** drücken und die Prüfung abwarten.
4. Bei der hinzugefügten App den Schalter **Download-Button** einschalten, wenn andere sie herunterladen dürfen.

Die App muss bereits eine öffentliche GitHub-Veröffentlichung mit genau einer signierten Android-APK haben. Eine Beschreibung kannst du freiwillig eintragen; ein leeres Feld übernimmt die Beschreibung von GitHub. Vorhandene Apps werden anhand ihres Android-Paketnamens erkannt. Neue Apps beginnen mit ausgeschaltetem Download-Button. Eine vorhandene Freigabe bleibt bei Versionsupdates erhalten.

**Aus Launcher entfernen** entfernt nur den Katalogeintrag, keine installierten Programme oder GitHub-Dateien. Der nächste Katalogabruf übernimmt die Änderung auf anderen Geräten. Der Schalter versteckt den Download im Launcher; öffentliche GitHub-Dateien bleiben bei GitHub öffentlich.

## Einmalige technische Einrichtung

Die private GitHub App „Jir3n Hub Verwaltung“ wurde am 27. Oktober 2026 erstellt und am 28. Oktober installiert. Der Eigentümer hat die Auswahl am 28. Oktober auf genau `hahawasistlos1/Jir3n-App-Hub` begrenzt und gespeichert. Benötigt werden **Actions: Read and write** und das obligatorische **Metadata: Read-only**, Device Flow und ablaufende Nutzertokens. Webhooks bleiben aus. Keine Contents-, Secrets-, Administration-, Konto- oder Organisationsrechte. Die neue Freigabe wurde ausdrücklich bestätigt und die gespeicherte Auswahl anschließend im Browser geprüft.

Nur die öffentliche Client-ID gehört in `config/github-client-id.txt`. Kein Client-Secret, privater GitHub-App-Schlüssel oder Eigentümer-Token gehört in den App-Code. Die mobile Anmeldung verwendet den Device Flow. Ihr Token wird mit Android Keystore verschlüsselt, an das lokale Google-Admin-Konto gebunden und spätestens nach acht Stunden verworfen. Abmelden oder „GitHub trennen“ entfernt die lokale Verbindung.

Die App prüft die feste GitHub-Konto-ID 64050987. Öffentliche App-Quellen werden vor dem Senden anonym geprüft; fremde oder private Projekte werden nicht übernommen. Windows-Programme und geschützte private Apps werden mit diesem Ablauf noch nicht hinzugefügt.

Der vorhandene GitHub-Ablauf prüft den Eigentümer zusätzlich unabhängig von der mobilen Oberfläche und signiert den Katalog serverseitig. Nur er hat Zugriff auf `CATALOG_PRIVATE_KEY`. Der private Katalogschlüssel bleibt in GitHub Actions und lokal unter `owner-private`, niemals in der APK. Weitere Schreibberechtigte am Hub könnten die Schutzregeln ändern und dürfen daher nicht hinzugefügt werden.

## Updates und Downloads

Unter **Profil → Update-Einstellungen** gibt es jetzt den Schalter **Updates automatisch herunterladen**. Beim Einschalten werden auch bereits bekannte neue Versionen eingereiht. Beim Öffnen des Launchers und bei Hintergrundprüfungen werden dieselben Download-Regeln verwendet. Nur installierte Android-Apps mit neuerer Version und freigegebenem Download werden automatisch heruntergeladen. Neue, noch nicht installierte Apps starten nicht von selbst.

Ab 0.1.7 erlauben neue Einstellungen automatische Downloads auch über mobile Daten. Die WLAN-Beschränkung kann freiwillig eingeschaltet werden. Bereits gespeicherte manuelle Einstellungen bleiben erhalten und können mit dem Schalter geändert werden. Android kann zum Installieren weiterhin eine Bestätigung verlangen. WLAN-Bindung und die Android-Hintergrundplanung können den tatsächlichen Start verzögern.

Der öffentliche Katalog prüft bekannte Apps zweimal pro Stunde. GitHub-Downloadzahlen zählen Dateidownloads über die Releases, keine eindeutigen Nutzer und nicht ausschließlich Downloads über den Launcher.

## Kostenloser Betrieb

Öffentliche GitHub-Releases, das öffentliche Katalogprojekt und Standard-Linux-Actions werden verwendet. Firebase bleibt im kostenlosen Spark-Tarif für die Google-Anmeldung und die kleine Admin-Freigabe. Kein Blaze-Tarif, kostenpflichtiger Server oder privater Download-Proxy ist eingerichtet. Nutzungsgrenzen der kostenlosen Dienste gelten weiterhin.

Die alte GitHub-Verwaltung bleibt als technische Ausweichmöglichkeit unter https://github.com/hahawasistlos1/Jir3n-App-Hub/actions/workflows/catalog.yml erreichbar.


Ab 0.1.7 werden manuelle Downloads unabhängig von der WLAN-Einstellung zugelassen. Die WLAN-Beschränkung betrifft automatische Downloads. Eine noch gültige GitHub-Code-Anmeldung kann nach einem App-/Prozesswechsel fortgesetzt werden; Abmelden und Abbrechen löschen diesen geschützten Zwischenstand.
