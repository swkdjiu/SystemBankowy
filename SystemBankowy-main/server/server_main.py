import socket
import threading
import json
from db_manager import DBManager

HOST = '127.0.0.1'
PORT = 65432

db = DBManager()

def client_thread(conn, addr):
    print(f"[+] Nowe połączenie od: {addr}")
    current_account = None 
    is_admin = False
    
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break 
                
            request = json.loads(data.decode('utf-8'))
            action = request.get("action")
            response = {"status": "error", "message": "Nieznana komenda"}

            # Routing zapytań Klienta 
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

            # Funkcje Administratora 
            elif action == "admin_add_user" and is_admin:
                success, msg = db.add_user(
                    request["imie"], request["nazwisko"], request["pesel"],
                    request["login"], request["haslo"], request["nr_konta"]
                )
                response = {"status": "ok" if success else "error", "message": msg}
                
            elif action == "admin_get_users" and is_admin:
                users = db.get_all_users()
                response = {"status": "ok", "users": users}

            elif action == "admin_edit_user" and is_admin:
                success, msg = db.edit_user(request["nr_konta"], request["imie"], request["nazwisko"], request["pesel"])
                response = {"status": "ok" if success else "error", "message": msg}

            elif action == "admin_block_user" and is_admin:
                success, msg = db.deactivate_user(request["nr_konta"])
                response = {"status": "ok" if success else "error", "message": msg}

            
            conn.sendall(json.dumps(response).encode('utf-8'))
            
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"[-] Błąd połączenia z {addr}: {e}")
            break

    conn.close()
    print(f"[-] Rozłączono: {addr}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Serwer Bankowy uruchomiony na {HOST}:{PORT}")
    
    # Dane startowe
    db.add_user("Admin", "Szef", "00000000000", "admin", "admin123", "0000", is_admin=1)
    db.add_user("Jan", "Kowalski", "12345678901", "jan", "jan123", "1111", is_admin=0)

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=client_thread, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Wyłączanie serwera...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()