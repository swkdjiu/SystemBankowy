import socket
import threading
import json
from db_manager import DBManager

HOST = '127.0.0.1'
PORT = 65432

db = DBManager()

def client_thread(conn, addr):
    print(f"[+] Nowe połączenie od: {addr}")
    current_account = None # Na początku klient nie jest zalogowany
    is_admin = False
    
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break # Klient się rozłączył
                
            request = json.loads(data.decode('utf-8'))
            action = request.get("action")
            response = {"status": "error", "message": "Nieznana komenda"}

            # --- Routing zapytań ---
            if action == "login":
                success, result = db.auth_user(request["login"], request["haslo"])
                if success:
                    current_account = result["nr_konta"]
                    is_admin = bool(result["is_admin"])
                    response = {"status": "ok", "message": "Zalogowano", "is_admin": is_admin, "nr_konta": current_account}
                else:
                    response = {"status": "error", "message": result}

            elif action == "balance" and current_account:
                saldo = db.get_balance(current_account)
                response = {"status": "ok", "saldo": saldo}

            elif action == "deposit" and current_account:
                success, msg = db.update_balance(current_account, float(request["kwota"]), "WPŁATA")
                response = {"status": "ok" if success else "error", "message": msg}

            elif action == "withdraw" and current_account:
                success, msg = db.update_balance(current_account, -float(request["kwota"]), "WYPŁATA")
                response = {"status": "ok" if success else "error", "message": msg}

            elif action == "transfer" and current_account:
                success, msg = db.transfer(current_account, request["do_konta"], float(request["kwota"]))
                response = {"status": "ok" if success else "error", "message": msg}
                
            elif action == "history" and current_account:
                hist = db.get_history(current_account)
                response = {"status": "ok", "history": hist}

            # --- Funkcje Administratora (wymagają uprawnień) ---
            elif action == "admin_add_user" and is_admin:
                success, msg = db.add_user(
                    request["imie"], request["nazwisko"], request["pesel"],
                    request["login"], request["haslo"], request["nr_konta"]
                )
                response = {"status": "ok" if success else "error", "message": msg}

            # Odsyłamy odpowiedź JSONem
            conn.sendall(json.dumps(response).encode('utf-8'))
            
        except ConnectionResetError:
            break # Zerwanie połączenia przez klienta
        except Exception as e:
            print(f"[-] Błąd połączenia z {addr}: {e}")
            break

    conn.close()
    print(f"[-] Rozłączono: {addr}")

def start_server():
    # Tworzymy gniazdo TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Rozwiązuje problem z zablokowanym portem po restarcie skryptu
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Serwer Bankowy uruchomiony na {HOST}:{PORT}")
    
    # Generowanie danych testowych (żeby było na czym pracować od razu)
    db.add_user("Admin", "Szef", "00000000000", "admin", "admin123", "0000", is_admin=1)
    db.add_user("Jan", "Kowalski", "12345678901", "jan", "jan123", "1111", is_admin=0)
    db.add_user("Anna", "Nowak", "10987654321", "anna", "anna123", "2222", is_admin=0)

    try:
        while True:
            # Akceptujemy nowe połączenie i przekazujemy je do nowego wątku
            conn, addr = server.accept()
            thread = threading.Thread(target=client_thread, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Wyłączanie serwera...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()