# Kryptex Panel

Marka: **Kryptex** — bayi (reseller) VPN sitesi + PasarGuard entegrasyonlu giriş sistemi.

## Nasıl çalışıyor

- `frontend/index.html` — tanıtım sayfası. "Giriş Yap" bayi girişine, küçük "Yönetici Girişi" linki
  sadece sana ait yönetici girişine gider. Telegram linki sadece "yeni bayi olmak / plan satın almak
  isteyenler" için kalmaya devam ediyor.
- `frontend/login.html` — bayilerin PasarGuard'daki kendi kullanıcı adı/şifresiyle giriş yaptığı sayfa.
- `frontend/admin-login.html` — sadece senin PasarGuard sudo hesabınla girebileceğin ayrı sayfa.
- `frontend/reseller-dashboard.html` — bir bayi giriş yaptığında: kendi kullanıcılarının listesi,
  kullanım/kota özeti, yeni VPN kullanıcısı oluşturma formu.
- `frontend/admin-dashboard.html` — sen (yönetici) giriş yaptığında: yeni bayi oluşturma formu +
  mevcut bayi listesi.
- `backend/` — FastAPI uygulaması. Şifreleri **hiçbir zaman kendi tarafımızda saklamıyoruz** — her
  giriş isteği doğrudan PasarGuard panelinin kendi `/api/admin/token` uç noktasına gidiyor. Biz sadece
  başarılı girişten sonra tarayıcıya güvenli, http-only bir oturum çerezi veriyoruz.
  - Sudo (senin) hesabınla giriş yapıldığında → Yönetici Paneli açılır → PasarGuard'ın "admin" (bayi)
    hesaplarını oluşturma/listeleme/silme uç noktalarını kullanır.
  - Normal admin (bayi) hesabıyla giriş yapıldığında → Bayi Paneli açılır → PasarGuard sadece o bayinin
    kendi oluşturduğu kullanıcıları döndürür (bu ayrım PasarGuard'ın kendi yetki sisteminden geliyor,
    bizim ekstra bir şey yapmamıza gerek yok).
  - `backend/kryptex.db` adlı küçük bir SQLite dosyasında sadece görünen ad / plan / not gibi ekstra
    bilgileri tutuyoruz — şifre asla buraya yazılmıyor.

## Kurulum

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını aç, PASARGUARD_BASE_URL'i kendi panelinin adresiyle değiştir
```

`.env` içinde en az şunu doldurman gerekiyor:

```
PASARGUARD_BASE_URL=https://panelin-adresi.com
```

## Çalıştırma (geliştirme / test)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Sonra tarayıcıda `http://localhost:8000` adresini aç — hem site hem de bayi/yönetici girişleri aynı
adresten çalışır (frontend otomatik olarak backend tarafından servis ediliyor).

## Sunucuya (VPS) kurulum — özet

1. Bir VPS al (Hetzner CX22 ~€4/ay gayet yeterli, Almanya/Finlandiya lokasyonu iyi bir seçim).
2. VPS'e Python 3.11+ kur, bu klasörü sunucuya yükle, yukarıdaki kurulum adımlarını uygula.
3. `uvicorn`'u arka planda kalıcı çalıştırmak için `systemd` servisi ya da `pm2`/`supervisor` kullan.
4. Önüne bir **Nginx reverse proxy + Let's Encrypt (HTTPS)** koy — sonra `.env` içinde
   `COOKIE_SECURE=true` yap (HTTPS olmadan bunu true yapma, çerez tarayıcıya hiç gitmez).
5. Alan adını (domain) Nginx'e yönlendir, DNS A kaydını VPS IP'sine çevir.

İstersen bu adımların hepsini (systemd servis dosyası + Nginx config + Let's Encrypt komutları) tek tek
de yazabilirim — sadece VPS'i aldığında ve domainini bana söylediğinde hazırlarım.

## Önemli notlar / kontrol etmen gerekenler

- **Grup ID'leri**: PasarGuard'ın yeni sürümlerinde kullanıcılar "grup" altında oluşturuluyor. Bayi
  paneli, kullanıcı oluşturma formunda PasarGuard'daki gerçek grupları (`/api/users/groups` uç noktası
  üzerinden) çekip dropdown'da gösteriyor — panelinde en az bir grup tanımlı olduğundan emin ol.
- **Panel sürümü**: Entegrasyon, PasarGuard'ın resmi `pasarguard` Python istemcisi (PyPI, sürüm 2.1.0)
  üzerinden yapıldı. Eğer panelin çok eski bir sürümdeyse bazı uç noktalar (`get_all_groups` gibi)
  bulunmayabilir — bu durumda panel sürümünü güncellemen ya da bana panel sürümünü söylemen gerekir.
  Bu ortamda internet erişimim olmadığı için kodu senin gerçek panelin karşısında test edemedim;
  ilk denemede küçük uç nokta farkları çıkarsa (ör. hata mesajı, 404), o hatayı bana yapıştır, hemen
  düzeltirim.
  - Kullanıcı sırlarını asla üçüncü bir tarafa göndermiyoruz; tüm istekler doğrudan
    senin belirttiğin `PASARGUARD_BASE_URL` adresine gidiyor.
- **Oturumlar şu an sunucu belleğinde tutuluyor** (`backend/app/sessions.py`). Tek sunucu/tek işlemle
  çalıştırdığın sürece sorun yok. İleride birden fazla işlem/sunucuya büyürsen Redis'e taşımak gerekir.
- Bayi şifrelerini biz hiçbir yerde saklamıyoruz; bayi oluştururken girdiğin şifre sadece PasarGuard'a
  gönderiliyor. Bu yüzden bir bayinin şifresini unutursan, tekrar görüntüleyemezsin — PasarGuard
  panelinden ya da "Bayi Oluştur" formunu tekrar kullanarak (varsa "şifre sıfırlama" ile) değiştirmen
  gerekir.

## Sırada ne var?

Şu an paylaştığım kod, PasarGuard'ın belgelenmiş resmi API istemcisine göre yazıldı ve mantıksal olarak
eksiksiz, ama senin gerçek panelin karşısında canlı test edilmedi (bu ortamda dışarıya ağ erişimim yok).
VPS'ini kurup ilk denemeyi yaptığında çıkan herhangi bir hatayı bana ilet — birlikte düzeltiriz.
