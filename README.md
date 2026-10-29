# Kostenlose App-Verwaltung

## Eine App oder ein Windows-Tool hinzufügen

Im Launcher **Profil → Adminbereich** öffnen. Nur das serverseitig freigegebene Google-Konto sieht diesen Bereich.

1. Falls nötig einmal **GitHub verbinden** wählen und den Code bei GitHub bestätigen.
2. Den öffentlichen GitHub-Link des eigenen Projekts einfügen, beispielsweise `https://github.com/hahawasistlos1/TreasureRunner-Updates`.
3. Für Android **Spiele**, **Tools** oder **Editoren** wählen; für die ZIP **Windows** wählen.
4. **App hinzufügen** drücken und das bestätigte Ergebnis abwarten.
5. Den eigenen Schalter **Download-Button** einschalten, sobald andere die Datei herunterladen dürfen.

Für TreasureRunner kannst du denselben Projektlink ein zweites Mal mit **Windows** hinzufügen. Die vorhandene `TreasureRunner-Windows-Editor.zip` liegt neben der APK im neuesten Release. Daraus wird ein eigener Windows-Eintrag; die Android-App bleibt erhalten. Du brauchst keine einzelne Datei-Adresse einzutragen. Die Windows-ZIP wird auf dem Handy heruntergeladen und über **ZIP teilen** zum PC weitergegeben; auf Android wird sie nicht installiert.

Voraussetzungen: öffentliche Projekte des Eigentümers und im neuesten Release genau eine signierte APK für Android beziehungsweise genau eine ZIP mit einem Windows-Programm (.exe oder .msi). APK und ZIP dürfen im selben Release liegen. Private Projekte werden hier nicht veröffentlicht. Die Windows-Archivprüfung liest nur die Struktur; sie führt keine Programme aus.

Eine Beschreibung kannst du freiwillig eintragen. Ein leeres Feld übernimmt die Projektbeschreibung von GitHub. Releasehinweise stammen aus der Veröffentlichung. Unterstützte Android-Icons werden aus der geprüften APK übernommen; der Windows-Eintrag kann das Icon der Android-App desselben Projekts verwenden.

## Download freigeben oder sperren

Neue Einträge beginnen mit ausgeschaltetem Download-Button. Android und Windows haben jeweils einen eigenen Schalter. Eine vorhandene Freigabe bleibt bei einem Versionsupdate erhalten. Nach einer Änderung warten, bis **eingeschaltet und bestätigt** oder **ausgeschaltet und bestätigt** erscheint. Falls nur das Nachladen scheitert, **Gespeicherte Änderung laden** wählen; dadurch wird der Auftrag nicht erneut gesendet.

**Aus Launcher entfernen** entfernt nur den Katalogeintrag. Installierte Programme und die Dateien bei GitHub bleiben erhalten. Eine Download-Sperre steuert den Hub; öffentliche Dateien sind bei GitHub weiterhin erreichbar.

## Update-Einstellungen für Nutzer

Ab 0.1.11 beginnen alle Update-Automatiken und Benachrichtigungen ausgeschaltet. Auch vorhandene ältere Einstellungen werden einmal auf eine bewusste Auswahl umgestellt. Unter **Profil → Update-Einstellungen** gibt es:

- **Manuell**: Downloads starten nach Antippen. Dies ist der Anfangszustand und gilt auch für den Launcher.
- **Automatisch**: Neue freigegebene Versionen installierter Android-Apps und des Launchers werden bei einer Prüfung geladen. Windows-ZIPs werden manuell geladen.
- **Updates im Hintergrund prüfen**: erlaubt Prüfungen bei geschlossener Oberfläche. Der Launcher wird stündlich, andere Apps im gewählten Intervall geprüft.
- **Installation automatisch versuchen**: erscheint bei automatischen Downloads und erlaubt zusätzliche Installationsversuche. Android kann dennoch eine Bestätigung verlangen.
- **Benachrichtigungen**: freiwillig; Android muss sie zusätzlich erlauben.

Der neongrüne **Aktualisieren**-Button neben dem Namen erscheint nur bei einer neueren freigegebenen Launcher-Version. Die App-Liste enthält den Launcher selbst nicht. Android kann Hintergrundarbeit verschieben; ein erzwungener Stopp hält sie bis zum nächsten Öffnen an. Vollständig unbeaufsichtigte Selbstinstallation ist geräteabhängig und nicht zugesichert.

WLAN und mobile Daten sind in allen Bereichen gleichgestellt. Prüfungen beim Öffnen laufen ohne kleine Statusmeldung. Ab 100 MB über eine Verbindung mit Datenbegrenzung erscheint **WLAN empfohlen**. **Jetzt herunterladen** erlaubt die aktuelle Verbindung, **Später** verschiebt den Download.

## Automatische Katalogpflege und Zähler

GitHub prüft bekannte öffentliche Apps und Windows-ZIPs zweimal pro Stunde. Neue Versionen und Downloadzahlen erscheinen nach dem signierten Katalogabruf. Android-Zahlen zählen APK-Dateidownloads, Windows-Zahlen ZIP-Dateidownloads über die veröffentlichten Releases. Das sind keine eindeutigen Personen und nicht ausschließlich Hub-Downloads.

## Technische Einrichtung und Kosten

Die GitHub-App ist auf `hahawasistlos1/Jir3n-App-Hub` begrenzt. Sie benötigt Actions lesen/schreiben und Metadaten lesen, Device Flow und ablaufende Nutzertokens. Keine allgemeinen Contents-, Konto-, Organisations- oder Administrationsrechte. Der Hub prüft die feste Eigentümer-ID zusätzlich. Mobile Tokens sind mit Android Keystore verschlüsselt und werden beim Abmelden oder Trennen gelöscht.

Der signierte Katalog wird ausschließlich durch den abgesicherten GitHub-Ablauf veröffentlicht. Private Signierschlüssel, Eigentümer-E-Mail und Firebase-UID gehören nicht in APK oder öffentlichen Katalog. Der Google-Adminzugriff wird serverseitig geprüft. Weitere Schreibberechtigte am Hub sollten nicht hinzugefügt werden.

Firebase bleibt im kostenlosen Spark-Tarif für Anmeldung und Adminfreigabe. Öffentliche GitHub-Releases und Standard-Linux-Actions übernehmen Katalog und Downloads. Kein Blaze-Tarif, kostenpflichtiger Server oder privater Download-Proxy ist eingerichtet; kostenlose Nutzungsgrenzen gelten weiterhin.

Die GitHub-Verwaltung bleibt als Ausweichmöglichkeit unter [Apps verwalten](https://github.com/hahawasistlos1/Jir3n-App-Hub/actions/workflows/catalog.yml) erreichbar.
