# Sieciowy System Bankowy (Projekt Zaliczeniowy)

System realizuje założenia architektury Klient-Serwer przy użyciu gniazd sieciowych (TCP Sockets). 
Aplikacja została napisana z zachowaniem dobrych praktyk czystej architektury (oddzielenie logiki DB od serwera).

## Diagram Architektury

[ Terminal Klienta ] <--- JSON (TCP Sockets) ---> [ Serwer Bankowy ]
                                                       | (Wątki)
[ Terminal Bankiera] <--- JSON (TCP Sockets) ---> [ DB Manager ]
                                                       | (Mutex Lock)
[ Testy Automatyczne]                             [ Baza SQLite ]

## Instrukcja Uruchomienia
Brak konieczności instalowania zewnętrznych bibliotek (użyto wbudowanych `socket`, `sqlite3`, `threading`).

1. Uruchom serwer jako pierwszy (z katalogu projektu):
   `python server/server_main.py`
   (Serwer sam utworzy bazę `bank.db` i wygeneruje dane testowe).
   
2. Otwórz nowy terminal i uruchom Terminal Klienta:
   `python client/client_main.py`
   *Dane logowania dla klienta: login: `jan`, hasło: `jan123`*

3. Aby zarządzać bankiem, uruchom Terminal Bankiera:
   `python admin/admin_main.py`
   *Dane logowania dla bankiera: login: `admin`, hasło: `admin123`*

4. Test wielodostępności:
   `python tests/auto_test.py`

## Protokół Komunikacyjny
Wymiana komunikatów odbywa się wyłącznie z użyciem formatu JSON przesyłanego jako zdekodowany ciąg bajtów (`utf-8`). Serwer po otrzymaniu żądania w formacie `{"action": "typ", "param": "wartosc"}` przetwarza je i zawsze odsyła słownik w formacie `{"status": "ok/error", "message": "opis"}`.