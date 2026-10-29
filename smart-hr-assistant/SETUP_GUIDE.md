# Smart HR Assistant - Adım Adım Kurulum ve Çalıştırma Rehberi

Bu rehber, projenin sıfırdan sorunsuz şekilde kurulması ve çalıştırılması için gerekli tüm adımları içerir.

---

## 1. Sistem Gereksinimleri
- **İşletim Sistemi**: Windows 10/11, macOS veya Linux
- **Python**: 3.9 veya üstü (Tavsiye edilen: Python 3.10 / 3.11)
- **Ollama**: (İsteğe bağlı, yerel LLM çalıştırmak için: https://ollama.com)

---

## 2. Ollama Modellerinin Hazırlanması (İsteğe Bağlı)
Eğer yerel modelleri Ollama ile çalıştırmak isterseniz bir terminal açarak şu komutları verin:

```bash
ollama pull qwen3:4b
ollama pull qwen3-embedding:0.6b
```

Modellerin indiğini doğrulamak için:
```bash
ollama list
```

---

## 3. Sanal Ortam (Virtual Environment) Kurulumu

Masaüstündeki proje dizinine geçin:
```bash
cd C:\Users\90535\Desktop\smart-hr-assistant
```

Sanal ortamı oluşturun:
```bash
python -m venv venv
```

Sanal ortamı aktif edin:
- **PowerShell**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Eğer script çalıştırma kısıtlaması hatası alırsanız: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` komutunu çalıştırabilirsiniz.)*
- **CMD**:
  ```cmd
  venv\Scripts\activate.bat
  ```

---

## 4. Bağımlılıkların Yüklenmesi

Gereken tüm paketleri tek seferde yükleyin:
```bash
pip install -r requirements.txt
```

---

## 5. Çevre Değişkenleri (.env) Kontrolü

Proje kökünde `.env` dosyası hazır olarak gelmektedir. Gerekirse parametreleri güncelleyebilirsiniz:
```env
LLM_MODEL=qwen3:4b
EMBEDDING_MODEL=qwen3-embedding:0.6b
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_EMPLOYEE_ID=EMP-001
DATA_DIR=data
VECTOR_DB_DIR=vector_db/hr_policies
```

---

## 6. Vektör Veritabanı ve Test Verilerinin Oluşturulması

İK politikalarını (25 politika metni) vektörize edip FAISS indeksine kaydetmek için:
```bash
python scripts/create_vector_db.py
```

Test verilerini sıfırlamak veya tazelemek için:
```bash
python scripts/seed_data.py
```

---

## 7. Uygulamayı Başlatma (CLI)

Smart HR Assistant'ı interaktif konsol üzerinden başlatmak için:
```bash
python main.py
```

Karşınıza çıkacak arayüzde asistanla doğrudan Türkçe konuşabilirsiniz.

---

## 8. Otomatik Testleri Koşma

10 farklı test senaryosunun (Yönlendirme, Onboarding, İzin bakiyesi, Çok turlu talep oluşturma, Belge üretimi, RAG politika sorgusu, Mülakat iptali, Hafıza, Hata yönetimi, Fallback) doğrulanması için:
```bash
python scripts/run_tests.py
```
Tüm testler yeşil onay işaretiyle geçecektir.
