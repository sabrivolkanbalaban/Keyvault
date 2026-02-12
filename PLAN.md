# Oracle Yetki Yönetimi Sayfası - Uygulama Planı

## Genel Bakış
KeyVault uygulamasına Oracle Database yetki yönetimi sayfası eklenecek. Admin kullanıcılar, Oracle DB kullanıcılarına tablo ve view bazında yetki verebilecek, mevcut yetkileri listeleyebilecek ve yetkiler kaldırılabilecek.

---

## Oluşturulacak/Değiştirilecek Dosyalar

### 1. Yeni Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `app/services/oracle_service.py` | Oracle DB bağlantısı ve yetki SQL sorguları |
| `app/views/oracle_admin.py` | Route'lar (Blueprint: `/admin/oracle`) |
| `app/templates/admin/oracle/privileges.html` | Ana sayfa: Yetki listesi + Grant/Revoke |
| `app/templates/admin/oracle/grant.html` | Yetki verme formu |

### 2. Değiştirilecek Dosyalar

| Dosya | Değişiklik |
|-------|-----------|
| `requirements.txt` | `oracledb` paketi eklenecek |
| `.env` / `.env.example` | Oracle bağlantı bilgileri eklenecek |
| `app/config.py` | Oracle config parametreleri eklenecek |
| `app/__init__.py` | `oracle_admin_bp` blueprint kaydı |
| `app/templates/base.html` | Sidebar'a "Oracle Privileges" linki |

---

## Detaylı Plan

### Adım 1: `requirements.txt` - oracledb Paketi Ekleme
```
oracledb==2.5.1
```
> `oracledb` Oracle'ın resmi Python driver'ıdır. **Thin mode** ile Oracle Client kurulumu gerektirmez.

### Adım 2: `.env` ve `.env.example` - Oracle Bağlantı Bilgileri
```env
# Oracle Database
ORACLE_HOST=195.206.236.179
ORACLE_PORT=1521
ORACLE_SERVICE=PRODPDB
ORACLE_USER=svbalaban
ORACLE_PASSWORD=1234
```

### Adım 3: `app/config.py` - Oracle Config Parametreleri
BaseConfig sınıfına Oracle ayarları eklenecek:
```python
ORACLE_HOST = os.environ.get("ORACLE_HOST", "")
ORACLE_PORT = int(os.environ.get("ORACLE_PORT", "1521"))
ORACLE_SERVICE = os.environ.get("ORACLE_SERVICE", "")
ORACLE_USER = os.environ.get("ORACLE_USER", "")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")
```

### Adım 4: `app/services/oracle_service.py` - Oracle Service
Oracle DB işlemleri için service sınıfı. Mevcut LDAPService pattern'ini takip eder.

**Metodlar:**
- `get_connection()` → Oracle bağlantısı oluşturur (oracledb thin mode)
- `test_connection()` → Bağlantı testi
- `get_users()` → Oracle kullanıcılarını listeler (`ALL_USERS`)
- `get_schemas()` → Schema listesi (`SELECT DISTINCT owner FROM all_tables`)
- `get_tables(schema)` → Belirli schema'daki tabloları listeler (`ALL_TABLES`)
- `get_views(schema)` → Belirli schema'daki view'ları listeler (`ALL_VIEWS`)
- `get_user_privileges(username)` → Kullanıcının tüm yetkilerini listeler (`DBA_TAB_PRIVS`)
- `grant_privilege(grantee, privilege, schema, object_name)` → Yetki verir (`GRANT ... ON ... TO ...`)
- `revoke_privilege(grantee, privilege, schema, object_name)` → Yetki kaldırır (`REVOKE ... ON ... FROM ...`)

**Desteklenen Yetkiler:** SELECT, INSERT, UPDATE, DELETE, ALL PRIVILEGES

### Adım 5: `app/views/oracle_admin.py` - Route'lar
Blueprint: `oracle_admin_bp` prefix: `/admin/oracle`

**Route'lar:**
| Route | Method | Açıklama |
|-------|--------|----------|
| `/admin/oracle/` | GET | Ana sayfa - kullanıcı seç ve yetkilerini gör |
| `/admin/oracle/privileges/<username>` | GET | Seçili kullanıcının yetkileri (AJAX) |
| `/admin/oracle/objects/<schema>` | GET | Schema'daki tablo/view listesi (AJAX/JSON) |
| `/admin/oracle/grant` | POST | Yetki ver |
| `/admin/oracle/revoke` | POST | Yetki kaldır |

Tüm route'lar `@login_required` ve `@admin_required` ile korunacak.
Tüm işlemler `AuditService.log()` ile kaydedilecek.

### Adım 6: `app/templates/admin/oracle/privileges.html` - Ana Sayfa
Tek sayfada tüm işlemler:

**Sol Panel:** Oracle kullanıcı listesi (arama ile filtrelenebilir)
**Sağ Panel:** Seçili kullanıcının yetkileri tablosu + Yetki ekleme formu

**Yetki Tablosu Kolonları:**
- Schema (Owner)
- Object Name (Tablo/View)
- Object Type (TABLE / VIEW)
- Privilege (SELECT, INSERT, UPDATE, DELETE)
- Grantor (Kim vermiş)
- Grantable (WITH GRANT OPTION var mı)
- Action (Revoke butonu)

**Yetki Ekleme Formu:**
- Schema seçimi (dropdown)
- Tablo/View seçimi (dropdown - schema'ya göre AJAX ile yüklenir)
- Yetki tipi seçimi (SELECT, INSERT, UPDATE, DELETE, ALL - checkbox)
- Grant butonu

### Adım 7: `app/__init__.py` - Blueprint Kaydı
```python
from app.views.oracle_admin import oracle_admin_bp
app.register_blueprint(oracle_admin_bp)
```

### Adım 8: `app/templates/base.html` - Sidebar Güncelleme
Admin bölümüne "Oracle Privileges" linki eklenecek:
```html
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('oracle_admin.index') }}">
        <i class="bi bi-database-fill-gear"></i>Oracle Privileges
    </a>
</li>
```

---

## Teknik Detaylar

### Oracle Bağlantı Yöntemi
```python
import oracledb
# Thin mode - Oracle Client gerektirmez
conn = oracledb.connect(
    user=config["ORACLE_USER"],
    password=config["ORACLE_PASSWORD"],
    dsn=f"{config['ORACLE_HOST']}:{config['ORACLE_PORT']}/{config['ORACLE_SERVICE']}"
)
```

### Güvenlik Önlemleri
- Tüm SQL parametreleri bind variable ile kullanılacak (SQL injection koruması)
- GRANT/REVOKE komutlarında object isimleri whitelist kontrolünden geçecek
- Sadece admin kullanıcılar erişebilecek
- Tüm işlemler audit log'a kaydedilecek
- CSRF koruması aktif

### UI/UX
- Mevcut Bootstrap 5.3 + Bootstrap Icons tasarımı korunacak
- Mevcut admin sayfalarındaki tablo/form pattern'i kullanılacak
- AJAX ile dinamik schema→object yükleme
- Flash mesajları ile geri bildirim
