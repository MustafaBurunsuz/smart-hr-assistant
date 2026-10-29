# Smart HR Assistant - Test Senaryoları ve Doğrulama Raporu

Bu dokümanda projenin mimari ve işlevsel yeteneklerini sınayan **10 Temel Test Senaryosu** yer almaktadır.

---

### Test 1: Karşılama ve Yönlendirme (Greeting & Routing)
- **Girdi:** `"Merhaba"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `greeting_agent`
- **Beklenen Davranış:** Asistan sıcak bir karşılama mesajı ile birlikte uzman olduğu alanları (onboarding, izin, belge, mülakat) özetler.
- **Sonuç:** ✅ Başarılı

---

### Test 2: Onboarding Kontrol Listesi (Onboarding Checklist)
- **Girdi:** `"Yeni işe başladım, ne yapmam lazım?"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `onboarding_agent` -> `check_onboarding_checklist()`
- **Beklenen Davranış:** Çalışanın ilk gün yapması gereken IT ekipman teslimi, İK oryantasyonu ve buddy/mentor bilgisi listelenir.
- **Sonuç:** ✅ Başarılı

---

### Test 3: İzin Bakiyesi Sorgulama (Leave Balance)
- **Girdi:** `"Kaç gün iznim var?"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `leave_agent` -> `get_leave_balance()`
- **Beklenen Davranış:** 2026 yılı için kalan yıllık izin (14 gün), hastalık ve mazeret izinleri detaylıca gösterilir.
- **Sonuç:** ✅ Başarılı

---

### Test 4: Çok Adımlı İzin Başvurusu (Multi-Step Reasoning)
- **1. Adım:** `"5 gün izin kullanmak istiyorum"`
  - *Asistan Yanıtı:* Eksik olan başlangıç tarihini sorar: `"Hangi tarihler arasında izin kullanmak istersiniz?"`
- **2. Adım:** `"1 Kasım, 5 gün"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `leave_agent` -> `request_leave()`
- **Beklenen Davranış:** Talep başarıyla oluşturulur, yönetici onayına gönderilir ve yeni talep özeti sunulur.
- **Sonuç:** ✅ Başarılı

---

### Test 5: Resmi Belge Üretimi (Document Generation)
- **Girdi:** `"Hizmet dökümü belgesi lazım"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `document_agent` -> `find_document()`
- **Beklenen Davranış:** Sistem resmi çalışma/hizmet dökümü belgesini üretir ve indirme yolunu (`documents/EMP-001_service_certificate.pdf`) döner.
- **Sonuç:** ✅ Başarılı

---

### Test 6: RAG ile Şirket İK Politikası Sorgusu (Policy Query)
- **Girdi:** `"Evlilik izni kaç gün?"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `document_agent` -> `get_policy_document()` -> RAG / FAISS Arama
- **Beklenen Davranış:** Şirket İK El Kitabı Bölüm 4.2'deki bilgi taranır ve çalışana 5 gün ücretli evlilik izni hakkı olduğu ve gerekli evraklar belirtilir.
- **Sonuç:** ✅ Başarılı

---

### Test 7: Mülakat İptali ve Takvim Yönetimi (Interview Cancellation)
- **Girdi:** `"Yarın saat 14:00'te mülakatım var, iptal et"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `interview_agent` -> `cancel_interview()`
- **Beklenen Davranış:** INT-123 numaralı aday mülakatı iptal edilir, takvimden düşürülür ve katılımcı bilgilendirme bildirimi oluşturulur.
- **Sonuç:** ✅ Başarılı

---

### Test 8: Konuşma Hafızası (Conversation Memory)
- **1. Mesaj:** `"5 gün izin kullanmak istiyorum"`
- **2. Mesaj:** `"1 Kasım'da"`
- **Beklenen Davranış:** Asistan önceki mesajdaki "5 gün" bilgisini oturum hafızasından kaybetmeden 1 Kasım başlangıçlı 5 günlük izin talebini onaylar.
- **Sonuç:** ✅ Başarılı

---

### Test 9: Hata Yönetimi (Error Handling & Negative Testing)
- **Girdi:** `"XXX-999 çalışanının izin bakiyesi"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `leave_agent` -> Doğrulama
- **Beklenen Davranış:** Sistem çökmek yerine zarif bir hata ile `'XXX-999' çalışan bulunamadı` uyarısı verir.
- **Sonuç:** ✅ Başarılı

---

### Test 10: Kapsam Dışı Soru / Fallback (Unknown Query)
- **Girdi:** `"Yemekhanede bugün ne var?"`
- **Yönlendirme Akışı:** `[SUPERVISOR]` -> `fallback_agent`
- **Beklenen Davranış:** Asistan kapsam dışı bir soru olduğunu nazikçe belirtir ve uzmanlık alanları hakkında kullanıcıyı bilgilendirir.
- **Sonuç:** ✅ Başarılı
