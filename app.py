import sqlite3
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    return response
DB_FILE = "smarthome.db"
# --- VERİ TABANI ALTYAPISI (REAL SQL) ---
def init_db():
    """Uygulama açılırken veri tabanını ve tabloları gerçek dünyadaki gibi oluşturur."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Ev durum tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_status (
                home_id TEXT PRIMARY KEY,
                kapi_kilitli INTEGER,
                wifi_aktif INTEGER,
                son_senkronizasyon TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Kullanıcıdan cihaza gidecek emir kuyruğu tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_commands (
                home_id TEXT PRIMARY KEY,
                kapi_emri TEXT,
                wifi_emri TEXT
            )
        """)
        # Eğer ilk defa çalışıyorsa varsayılan ev verisini SQL'e ekle
        cursor.execute("INSERT OR IGNORE INTO device_status (home_id, kapi_kilitli, wifi_aktif) VALUES ('EV_BURSA_16', 1, 1)")
        cursor.execute("INSERT OR IGNORE INTO pending_commands (home_id, kapi_emri, wifi_emri) VALUES ('EV_BURSA_16', 'YOK', 'YOK')")
        conn.commit()

init_db()

# --- GÖRSEL KULLANICI ARAYÜZÜ (FRONTEND) ---
HTML_SAYFASI = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enes Real Cloud Panel</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0d1117; color: #c9d1d9; text-align: center; padding: 50px; }
        .container { background-color: #161b22; padding: 30px; border-radius: 12px; display: inline-block; border: 1px solid #30363d; }
        h1 { color: #58a6ff; }
        .durum { font-size: 1.1rem; margin: 15px 0; padding: 12px; border-radius: 6px; background: #21262d; }
        .btn { background-color: #238636; border: 1px solid rgba(240,246,252,0.1); color: white; padding: 10px 20px; font-size: 0.9rem; border-radius: 6px; cursor: pointer; font-weight: bold; margin: 5px; }
        .btn:hover { background-color: #2ea44f; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Enes Gerçek Bulut Kontrol Merkezi</h1>
        <p>Sistem Mimarisi: <b>SQL Veri Tabanı + API Broker</b></p>
        <hr style="border-color: #30363d;">
        
        <div class="durum">🚪 Fiziksel Kapı Durumu: <b id="kapi-yazi">Yükleniyor...</b></div>
        <div class="durum">🌐 Fiziksel Wi-Fi Durumu: <b id="wifi-yazi">Yükleniyor...</b></div>

        <button class="btn" onclick="emirGonder('kapi')">🚪 Kapı Kilidini Değiştirme Emri Ver</button>
        <button class="btn" onclick="emirGonder('wifi')">🌐 Wi-Fi Durumunu Değiştirme Emri Ver</button>
    </div>

    <script>
        function durumGuncelle() {
            fetch('/api/user/status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('kapi-yazi').innerText = data.kapi_kilitli ? "KİLİTLİ 🔒" : "AÇIK 🔓";
                    document.getElementById('kapi-yazi').style.color = data.kapi_kilitli ? "#f85149" : "#58a6ff";
                    document.getElementById('wifi-yazi').innerText = data.wifi_aktif ? "AKTİF ✅" : "KAPALI ❌";
                    document.getElementById('wifi-yazi').style.color = data.wifi_aktif ? "#58a6ff" : "#f85149";
                });
        }

        function emirGonder(islem) {
            fetch('/api/user/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ "home_id": "EV_BURSA_16", "islem": islem })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.mesaj);
            });
        }

        setInterval(durumGuncelle, 2000); // Her 2 saniyede bir SQL'deki gerçek durumu ekrana yansıtır
        durumGuncelle();
    </script>
</body>
</html>
"""

@app.route('/')
def ana_sayfa():
    return render_template_string(HTML_SAYFASI)

# --- 1. PROTOKOL: KULLANICI API UÇLARI ---
@app.route('/api/user/status', methods=['GET'])
def user_get_status():
    """Kullanıcının ekranına veri tabanındaki en güncel durumu basar."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT kapi_kilitli, wifi_aktif FROM device_status WHERE home_id = 'EV_BURSA_16'")
        row = cursor.fetchone()
        return jsonify({"kapi_kilitli": bool(row[0]), "wifi_aktif": bool(row[1])})

@app.route('/api/user/command', methods=['POST'])
def user_post_command():
    """Kullanıcı butona bastığında doğrudan cihaza gitmez, SQL'deki emir kuyruğuna yazar."""
    veri = request.json
    home_id = veri.get("home_id")
    islem = veri.get("islem")
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if islem == "kapi":
            cursor.execute("UPDATE pending_commands SET kapi_emri = 'TETIKLE' WHERE home_id = ?", (home_id,))
        elif islem == "wifi":
            cursor.execute("UPDATE pending_commands SET wifi_emri = 'TETIKLE' WHERE home_id = ?", (home_id,))
        conn.commit()
    return jsonify({"durum": "Başarılı", "mesaj": f"Bulut Veri Tabanına {islem.upper()} emri güvenli bir şekilde yazıldı. Cihazın senkronize olması bekleniyor..."})

# --- 2. PROTOKOL: GERÇEK CİHAZ API UÇLARI (DEVICE SYNC) ---
@app.route('/api/device/sync', methods=['POST'])
def device_sync():
    """Evdeki cihaz internete bağlanıp bu uca gelir. Gerçek durumunu yazar ve emirleri geri götürür."""
    veri = request.json
    home_id = veri.get("home_id")
    cihaz_kapi = veri.get("current_kapi")
    cihaz_wifi = veri.get("current_wifi")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 1. Cihazın fiziksel durumunu SQL veri tabanına işle
        cursor.execute("""
            UPDATE device_status 
            SET kapi_kilitli = ?, wifi_aktif = ?, son_senkronizasyon = CURRENT_TIMESTAMP 
            WHERE home_id = ?
        """, (cihaz_kapi, cihaz_wifi, home_id))
        
        # 2. Bu cihaz için veri tabanında bekleyen bir kullanıcı emri var mı kontrol et
        cursor.execute("SELECT kapi_emri, wifi_emri FROM pending_commands WHERE home_id = ?", (home_id,))
        emirler = cursor.fetchone()
        
        kapi_emri, wifi_emri = emirler[0], emirler[1]
        
        # Eğer emir varsa, cihaza teslim edileceği için kuyruğu temizle (YOK yap)
        if kapi_emri == "TETIKLE" or wifi_emri == "TETIKLE":
            cursor.execute("UPDATE pending_commands SET kapi_emri = 'YOK', wifi_emri = 'YOK' WHERE home_id = ?", (home_id,))
        
        conn.commit()
        
    # Evdeki fiziksel cihaza emirleri paketleyip gönderiyoruz
    return jsonify({
        "kapi_komutu": kapi_emri,
        "wifi_komutu": wifi_emri
    }), 200
