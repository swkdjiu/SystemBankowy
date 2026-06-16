import socket
import json
import threading
import time
import random

def bot_client(nazwa, login, haslo, operacje):
    # Symuluje zachowanie pojedynczego klienta
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 65432))
    
    # Logowanie bota
    sock.sendall(json.dumps({"action": "login", "login": login, "haslo": haslo}).encode('utf-8'))
    sock.recv(1024) # Pomijamy odczyt odp z logowania dla uproszczenia kodu
    
    for op in operacje:
        # Usypiamy watek na ułamek sekundy by udawać prawdziwego człowieka
        time.sleep(random.uniform(0.1, 0.5))
        sock.sendall(json.dumps(op).encode('utf-8'))
        resp = json.loads(sock.recv(1024).decode('utf-8'))
        print(f"[WĄTEK {nazwa}] Zlecenie: {op['action']} -> Serwer: {resp.get('message', resp.get('status'))}")
        
    sock.close()

def uruchom_testy():
    print("=== START TESTU AUTOMATYCZNEGO (3 KLIENTÓW JEDNOCZEŚNIE) ===")
    # Wszyscy logują się na konto Jana, żeby sprawdzić czy Mutex w bazie zadziała
    # i czy kasa nie zostanie naliczona podwójnie
    
    zadania_1 = [{"action": "deposit", "kwota": 100}, {"action": "withdraw", "kwota": 50}]
    zadania_2 = [{"action": "deposit", "kwota": 200}, {"action": "transfer", "do_konta": "2222", "kwota": 50}]
    zadania_3 = [{"action": "deposit", "kwota": 300}, {"action": "withdraw", "kwota": 100}]

    t1 = threading.Thread(target=bot_client, args=("Bot-A", "jan", "jan123", zadania_1))
    t2 = threading.Thread(target=bot_client, args=("Bot-B", "jan", "jan123", zadania_2))
    t3 = threading.Thread(target=bot_client, args=("Bot-C", "jan", "jan123", zadania_3))

    t1.start(); t2.start(); t3.start()
    t1.join(); t2.join(); t3.join()
    
    print("=== KONIEC TESTU. Sprawdź w historii klienta czy saldo się zgadza. ===")

if __name__ == "__main__":
    uruchom_testy()