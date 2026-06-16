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
        print("Brak połączenia z serwerem. Uruchom najpierw serwer!")
        return

    print("=== TERMINAL BANKIERA (TB) ===")
    login = input("Login admina: ")
    haslo = input("Hasło: ")

    auth = send_req(client, {"action": "login", "login": login, "haslo": haslo})
    if auth["status"] != "ok" or not auth.get("is_admin"):
        print("Brak uprawnień administratora lub zły login.")
        client.close()
        return

    print("[+] Zalogowano jako Administrator systemu.")

    while True:
        print("\n=== MENU BANKIERA ===")
        print("1. Zarejestruj nowego klienta")
        print("2. Przeglądaj wszystkich klientów")
        print("3. Edytuj dane klienta")
        print("4. Zablokuj (usuń) konto klienta")
        print("5. Razblokuj konto klienta.")
        print("0. Wyloguj i wyjdź")
        opcja = input("Wybierz opcję: ")

        if opcja == '1': 
            imie = input("Imię: ")
            nazw = input("Nazwisko: ")
            pesel = input("PESEL: ")
            log = input("Nowy login: ")
            has = input("Nowe hasło: ")
            nr = str(random.randint(1000, 9999)) # Generowanie numeru konta
            
            resp = send_req(client, {
                "action": "admin_add_user",
                "imie": imie, "nazwisko": nazw, "pesel": pesel,
                "login": log, "haslo": has, "nr_konta": nr
            })
            print(f"--> {resp['message']} Wygenerowany nr konta: {nr}")

        elif opcja == '2': 
            resp = send_req(client, {"action": "admin_get_users"})
            klienci = resp.get("users", [])
            print("\n--- LISTA KLIENTÓW ---")
            for k in klienci:
                status = "Aktywny" if k[5] == 1 else "Zablokowany"
                print(f"Konto: {k[3]} | {k[0]} {k[1]} | PESEL: {k[2]} | Saldo: {k[4]} PLN | Status: {status}")
            print("----------------------")

        elif opcja == '3': 
            nr = input("Podaj numer konta klienta do edycji: ")
            imie = input("Nowe imię: ")
            nazw = input("Nowe nazwisko: ")
            pesel = input("Nowy PESEL: ")
            
            resp = send_req(client, {
                "action": "admin_edit_user",
                "nr_konta": nr, "imie": imie, "nazwisko": nazw, "pesel": pesel
            })
            print(f"--> {resp['message']}")

        elif opcja == '4': 
            nr = input("Podaj numer konta do zablokowania: ")
            pewnosc = input("Czy na pewno chcesz zablokować to konto? (t/n): ")
            if pewnosc.lower() == 't':
                resp = send_req(client, {"action": "admin_block_user", "nr_konta": nr})
                print(f"--> {resp['message']}")
            else:
                print("Anulowano.")

        elif opcja == '5': 
            nr = input("Podaj numer konta do odblokowania: ")
            resp = send_req(client, {"action": "admin_unblock_user", "nr_konta": nr})
            print(f"--> {resp['message']}")

        elif opcja == '0': 
            print("Wylogowywanie...")
            break
        else:
            print("Niepoprawna opcja.")

    client.close()

if __name__ == "__main__":
    main()