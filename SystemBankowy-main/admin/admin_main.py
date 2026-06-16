import socket
import json
import random

HOST = '127.0.0.1'
PORT = 65432

def send_req(sock, req_dict):
    sock.sendall(json.dumps(req_dict).encode('utf-8'))
    return json.loads(sock.recv(4096).decode('utf-8'))

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except:
        print("Brak połączenia z serwerem.")
        return

    print("=== TERMINAL BANKIERA (TB) ===")
    login = input("Login admina: ")
    haslo = input("Hasło: ")

    auth = send_req(client, {"action": "login", "login": login, "haslo": haslo})
    if auth["status"] != "ok" or not auth.get("is_admin"):
        print("Brak uprawnień lub zły login.")
        client.close()
        return

    print("[+] Zalogowano jako Administrator.")

    while True:
        print("\n1. Zarejestruj nowego klienta | 0. Wyjście")
        opcja = input("Wybierz: ")

        if opcja == '1':
            imie = input("Imię: ")
            nazw = input("Nazwisko: ")
            pesel = input("PESEL: ")
            log = input("Nowy login: ")
            has = input("Nowe hasło: ")
            # Generujemy losowy 4-cyfrowy numer konta
            nr = str(random.randint(1000, 9999)) 
            
            resp = send_req(client, {
                "action": "admin_add_user",
                "imie": imie, "nazwisko": nazw, "pesel": pesel,
                "login": log, "haslo": has, "nr_konta": nr
            })
            print(f"--> {resp['message']} Wygenerowany nr konta: {nr}")

        elif opcja == '0':
            break

    client.close()

if __name__ == "__main__":
    main()