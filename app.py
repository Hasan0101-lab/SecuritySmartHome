from flask import Flask, jsonify, request, make_response
import datetime
import os
# Yeni eklenen kütüphane
from dotenv import load_dotenv

# Yerel bilgisayardaki .env dosyasını yükler. 
# Sunucuda (Render) bu dosya olmayacağı için bu satır sunucuda pasif kalır, hata vermez.
load_dotenv()

app = Flask(__name__)

# --- GÜVENLİK ANAHTARI (TOKEN) ---
# Sistem, gizli anahtarı artık kodun içinden değil, tamamen dışarıdan okur.
# Eğer sistemde bu anahtar bulunamazsa, güvenlik için varsayılan güçlü bir geçici token atar.
DEVICE_SECRET_TOKEN = os.getenv("ESP32_SECRET_TOKEN", "Varsayilan_Gecici_Guvenli_Token_2026")

smart_home_status = {
    "door_locked": True,
    "wifi_active": True,
    "last_motion_detected": None,
    "system_mode": "ARMED"
}

# ... (Kodun geri kalan API uçları ve apply_security_headers kısımları tamamen aynı kalıyor)
