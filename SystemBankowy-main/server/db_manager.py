import sqlite3
import hashlib
import threading
from datetime import datetime

class DBManager:
    def __init__(self, db_name="bank.db"):
        self.db_name = db_name
        self.lock = threading.Lock()
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    imie TEXT,
                    nazwisko TEXT,
                    pesel TEXT UNIQUE,
                    login TEXT UNIQUE,
                    haslo TEXT,
                    nr_konta TEXT UNIQUE,
                    saldo REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nr_konta TEXT,
                    typ_operacji TEXT,
                    kwota REAL,
                    saldo_po REAL,
                    data TEXT
                )
            ''')
            conn.commit()
            conn.close()

    def _hash_pw(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, imie, nazwisko, pesel, login, haslo, nr_konta, is_admin=0):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                hashed = self._hash_pw(haslo)
                cursor.execute(
                    "INSERT INTO users (imie, nazwisko, pesel, login, haslo, nr_konta, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (imie, nazwisko, pesel, login, hashed, nr_konta, is_admin)
                )
                conn.commit()
                return True, "Klient dodany pomyślnie."
            except sqlite3.IntegrityError:
                return False, "Błąd: Dane (PESEL/Login/Nr konta) nie są unikalne."
            finally:
                conn.close()

    def auth_user(self, login, haslo):
        conn = self.get_connection()
        cursor = conn.cursor()
        hashed = self._hash_pw(haslo)
        cursor.execute("SELECT nr_konta, is_admin FROM users WHERE login=? AND haslo=? AND is_active=1", (login, hashed))
        user = cursor.fetchone()
        conn.close()
        if user:
            return True, {"nr_konta": user[0], "is_admin": user[1]}
        return False, "Błędne dane logowania lub konto zablokowane."

    def get_balance(self, nr_konta):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT saldo FROM users WHERE nr_konta=?", (nr_konta,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else 0.0

    def update_balance(self, nr_konta, kwota, typ_operacji):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT saldo FROM users WHERE nr_konta=? AND is_active=1", (nr_konta,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Konto nie istnieje lub jest nieaktywne."
            nowe_saldo = row[0] + kwota
            if nowe_saldo < 0:
                conn.close()
                return False, "Brak wystarczających środków na koncie."
            cursor.execute("UPDATE users SET saldo=? WHERE nr_konta=?", (nowe_saldo, nr_konta))
            data_teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO history (nr_konta, typ_operacji, kwota, saldo_po, data) VALUES (?, ?, ?, ?, ?)",
                           (nr_konta, typ_operacji, kwota, nowe_saldo, data_teraz))
            conn.commit()
            conn.close()
            return True, f"Operacja udana. Nowe saldo: {nowe_saldo}"

    def transfer(self, od_konta, do_konta, kwota):
        if kwota <= 0:
            return False, "Kwota przelewu musi być większa niż 0."
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM users WHERE nr_konta=? AND is_active=1", (do_konta,))
                if not cursor.fetchone():
                    return False, "Konto docelowe nie istnieje."
                cursor.execute("SELECT saldo FROM users WHERE nr_konta=?", (od_konta,))
                saldo_od = cursor.fetchone()[0]
                if saldo_od < kwota:
                    return False, "Brak środków na przelew."
                nowe_saldo_od = saldo_od - kwota
                cursor.execute("UPDATE users SET saldo=? WHERE nr_konta=?", (nowe_saldo_od, od_konta))
                cursor.execute("SELECT saldo FROM users WHERE nr_konta=?", (do_konta,))
                nowe_saldo_do = cursor.fetchone()[0] + kwota
                cursor.execute("UPDATE users SET saldo=? WHERE nr_konta=?", (nowe_saldo_do, do_konta))
                data_teraz = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO history (nr_konta, typ_operacji, kwota, saldo_po, data) VALUES (?, ?, ?, ?, ?)",
                               (od_konta, f"PRZELEW DO {do_konta}", -kwota, nowe_saldo_od, data_teraz))
                cursor.execute("INSERT INTO history (nr_konta, typ_operacji, kwota, saldo_po, data) VALUES (?, ?, ?, ?, ?)",
                               (do_konta, f"PRZELEW OD {od_konta}", kwota, nowe_saldo_do, data_teraz))
                conn.commit()
                return True, "Przelew zrealizowany pomyślnie."
            except Exception as e:
                conn.rollback()
                return False, f"Błąd serwera przy przelewie: {str(e)}"
            finally:
                conn.close()

    def get_history(self, nr_konta):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT data, typ_operacji, kwota, saldo_po FROM history WHERE nr_konta=? ORDER BY id DESC LIMIT 10", (nr_konta,))
        history = cursor.fetchall()
        conn.close()
        return history


    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT imie, nazwisko, pesel, nr_konta, saldo, is_active FROM users WHERE is_admin=0")
        users = cursor.fetchall()
        conn.close()
        return users

    def edit_user(self, nr_konta, imie, nazwisko, pesel):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE users SET imie=?, nazwisko=?, pesel=? WHERE nr_konta=?", (imie, nazwisko, pesel, nr_konta))
                rowcount = cursor.rowcount 
                conn.commit()
                if rowcount > 0:
                    return True, "Dane klienta zostały zaktualizowane."
                return False, "Nie znaleziono klienta o takim numerze konta."
            except sqlite3.IntegrityError:
                return False, "Błąd: Ten PESEL jest już przypisany do kogoś innego."
            finally:
                conn.close()

    def deactivate_user(self, nr_konta):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active=0 WHERE nr_konta=?", (nr_konta,))
            rowcount = cursor.rowcount
            conn.commit()
            conn.close()
            if rowcount > 0:
                return True, "Konto zostało pomyślnie zablokowane (usunięte)."
            return False, "Nie znaleziono konta."
        
    def reactivate_user(self, nr_konta):
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active=1 WHERE nr_konta=?", (nr_konta,))
            rowcount = cursor.rowcount
            conn.commit()
            conn.close()
            if rowcount > 0:
                return True, "Konto zostało pomyślnie odblokowane."
            return False, "Nie znaleziono takiego konta."