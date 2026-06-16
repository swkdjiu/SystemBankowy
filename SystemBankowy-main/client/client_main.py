import socket
import json

HOST = '127.0.0.1'
PORT = 65432

def send_req(sock, req_dict):
    # Pomocnicza funkcja do pakowania w JSON i wysyłania
    sock.sendall(json.dumps(req_dict).encode('utf-8'))
    resp = sock.recv(4096).decode('utf-8')
    return json.loads(resp)

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("[-] Serwer jest wyłączony. Uruchom najpierw serwer!")
        return

    print("=== TERMINAL KLIENTA (TK) ===")
    login = input("Login: ")
    haslo = input("Hasło: ")

    auth = send_req(client, {"action": "login", "login": login, "haslo": haslo})
    
    if auth["status"] != "ok":
        print(f"Błąd logowania: {auth['message']}")
        client.close()
        return

    if auth.get("is_admin"):
        print("Zalogowano jako Administrator. Użyj Terminala Bankiera (admin_main.py)!")
        client.close()
        return

    print(f"[+] Zalogowano pomyślnie. Twój numer konta: {auth['nr_konta']}")

    # Główna pętla menu
    while True:
        print("\n1. Saldo | 2. Wpłata | 3. Wypłata | 4. Przelew | 5. Historia | 0. Wyjście")
        opcja = input("Wybierz opcję: ")

        if opcja == '1':
            resp = send_req(client, {"action": "balance"})
            print(f"--> Twoje obecne saldo: {resp.get('saldo')} PLN")

        elif opcja == '2':
            kwota = input("Podaj kwotę do wpłaty: ")
            resp = send_req(client, {"action": "deposit", "kwota": kwota})
            print(f"--> {resp['message']}")

        elif opcja == '3':
            kwota = input("Podaj kwotę do wypłaty: ")
            resp = send_req(client, {"action": "withdraw", "kwota": kwota})
            print(f"--> {resp['message']}")

        elif opcja == '4':
            do_konta = input("Numer konta odbiorcy: ")
            kwota = input("Kwota przelewu: ")
            resp = send_req(client, {"action": "transfer", "do_konta": do_konta, "kwota": kwota})
            print(f"--> {resp['message']}")
            
        elif opcja == '5':
            resp = send_req(client, {"action": "history"})
            print("--> Ostatnie operacje:")
            for wpis in resp.get('history', []):
                print(f"  {wpis[0]} | {wpis[1]} | {wpis[2]} PLN | po: {wpis[3]} PLN")

        elif opcja == '0':
            print("Wylogowywanie...")
            break
        else:
            print("Niepoprawna opcja.")

    client.close()

if __name__ == "__main__":
    main()