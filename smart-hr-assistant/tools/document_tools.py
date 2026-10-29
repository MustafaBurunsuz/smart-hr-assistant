"""
Tools for Document Agent.
Handles document generation, retrieval, document upload, and HR policy queries with RAG.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from langchain_core.tools import tool
except ImportError:
    def tool(fn):
        fn.invoke = lambda args: fn(**args) if isinstance(args, dict) else fn(args)
        return fn

from utils.helpers import load_json, save_json, get_current_employee_id, format_currency

BASE_DIR = Path(__file__).resolve().parent.parent


@tool
def find_document(doc_type: str = "service_certificate", employee_id: str = "") -> Dict[str, Any]:
    """Çalışana ait resmi İK belgelerini (hizmet dökümü, bordro, vergi levhası vb.) sorgular veya hazırlar.

    Args:
        doc_type: Belge türü ('service_certificate' / hizmet dökümü, 'payslip' / bordro, 'tax_plate' / vergi levhası).
        employee_id: Çalışan ID'si (Örn: 'EMP-001').

    Returns:
        Belge detayları ve indirme dosya yolu.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    type_mapping = {
        "hizmet": "service_certificate",
        "hizmet dökümü": "service_certificate",
        "service_certificate": "service_certificate",
        "bordro": "payslip",
        "maaş bordrosu": "payslip",
        "payslip": "payslip",
        "vergi": "tax_plate",
        "vergi levhası": "tax_plate",
        "tax_plate": "tax_plate"
    }

    normalized_type = type_mapping.get(doc_type.lower().strip(), "service_certificate")

    documents = load_json("documents.json", default=[])
    target = next((d for d in documents if d.get("employee_id") == employee_id and d.get("doc_type") == normalized_type), None)

    title_map = {
        "service_certificate": "Hizmet Dökümü",
        "payslip": "Maaş Bordrosu",
        "tax_plate": "Vergi Levhası"
    }
    title = title_map.get(normalized_type, "Resmi Belge")

    today_str = datetime.now().strftime("%d.%m.%Y")
    file_rel_path = f"documents/{employee_id}_{normalized_type}.pdf"

    # Ensure documents directory exists
    try:
        docs_dir = BASE_DIR / "documents"
        docs_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = docs_dir / f"{employee_id}_{normalized_type}.pdf"
        if not pdf_path.exists():
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write(f"%PDF-1.4\n% Smart HR Assistant Mock Document: {title}\nDate: {today_str}\nOwner: {employee_id}\n")
    except Exception:
        pass

    if not target:
        new_doc = {
            "document_id": f"DOC-{len(documents) + 2001}",
            "employee_id": employee_id,
            "doc_type": normalized_type,
            "title": title,
            "file_path": file_rel_path,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "ready"
        }
        documents.append(new_doc)
        save_json("documents.json", documents)

    return {
        "status": "success",
        "doc_type": title,
        "created_at": today_str,
        "file_path": file_rel_path,
        "message": (
            f"✅ Belge hazır!\n"
            f"📄 Tür: {title}\n"
            f"📅 Düzenlenme: {today_str}\n"
            f"📥 İndirme: [PDF oluşturuldu: {file_rel_path}]\n\n"
            f"Başka bir belge ister misiniz?"
        )
    }


@tool
def generate_offer_letter(position: str, salary: float, start_date: str) -> Dict[str, Any]:
    """Yeni bir aday için resmi iş teklif mektubu oluşturur.

    Args:
        position: Teklif edilen pozisyon/unvan.
        salary: Aylık net maaş tutarı.
        start_date: Planlanan işe başlama tarihi (YYYY-MM-DD).

    Returns:
        Oluşturulan teklif mektubunun içeriği ve belge yolu.
    """
    docs_dir = BASE_DIR / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"teklif_mektubu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    file_path = docs_dir / filename

    content = (
        f"====================================================\n"
        f"                  İŞ TEKLİF MEKTUBU                  \n"
        f"====================================================\n"
        f"Tarih: {datetime.now().strftime('%d.%m.%Y')}\n"
        f"Pozisyon: {position}\n"
        f"Başlangıç Tarihi: {start_date}\n"
        f"Aylık Net Maaş: {format_currency(salary)}\n\n"
        f"Sayın Aday,\n"
        f"Şirketimiz bünyesindeki {position} rolü için yapmış olduğumuz\n"
        f"görüşmeler sonucunda sizi ekibimizde görmekten mutluluk duyarız.\n"
        f"====================================================\n"
    )

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

    return {
        "status": "success",
        "position": position,
        "salary": salary,
        "start_date": start_date,
        "file_path": f"documents/{filename}",
        "message": f"{position} pozisyonu için iş teklif mektubu başarıyla hazırlandı."
    }


@tool
def upload_document(employee_id: str, doc_type: str, file_path: str) -> Dict[str, Any]:
    """Çalışanın sisteme İK evrakı yüklemesini kaydeder.

    Args:
        employee_id: Çalışan ID'si.
        doc_type: Evrak türü (Örn: 'diploma', 'saglik_raporu', 'ikametgah').
        file_path: Yüklenen dosyanın konumu.

    Returns:
        Yükleme onay mesajı.
    """
    if not employee_id:
        employee_id = get_current_employee_id()

    documents = load_json("documents.json", default=[])
    new_doc = {
        "document_id": f"DOC-UPL-{len(documents) + 3001}",
        "employee_id": employee_id,
        "doc_type": doc_type,
        "title": f"Yüklenen Belge: {doc_type}",
        "file_path": file_path,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "status": "uploaded"
    }
    documents.append(new_doc)
    save_json("documents.json", documents)

    return {
        "status": "success",
        "message": f"'{doc_type}' belgeniz başarıyla sisteme yüklendi ve İK onay havuzuna iletildi.",
        "document_id": new_doc["document_id"]
    }


@tool
def get_policy_document(policy_type: str) -> Dict[str, Any]:
    """Şirket İK politikaları ve çalışan el kitabı dokümanlarını RAG (vektör arama) yöntemiyle sorgular.

    Args:
        policy_type: Politika sorgusu veya anahtar kelimeler (Örn: 'evlilik izni', 'uzaktan çalışma', 'fazla mesai').

    Returns:
        İlgili İK politikası maddesi ve detayları.
    """
    vector_dir = BASE_DIR / os.getenv("VECTOR_DB_DIR", "vector_db/hr_policies")

    # Method 1: Try FAISS vector DB if available
    if vector_dir.exists() and (vector_dir / "index.faiss").exists():
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_ollama import OllamaEmbeddings

            embed_model = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            embeddings = OllamaEmbeddings(model=embed_model, base_url=base_url)

            vector_store = FAISS.load_local(
                str(vector_dir),
                embeddings,
                allow_dangerous_deserialization=True
            )
            docs = vector_store.similarity_search(policy_type, k=2)
            if docs:
                best_doc = docs[0]
                return {
                    "status": "success",
                    "source": "FAISS_Vector_DB",
                    "title": best_doc.metadata.get("title", "İK Politikası"),
                    "category": best_doc.metadata.get("category", "Genel"),
                    "content": best_doc.page_content,
                    "message": (
                        f"📋 İK Politikası: {best_doc.metadata.get('title', 'Politika Detayı')}\n"
                        f"{best_doc.page_content}\n"
                    )
                }
        except Exception:
            # Fallback to direct semantic keyword matching
            pass

    # Method 2: High-accuracy JSON direct search fallback
    policies = load_json("hr_policies.json", default=[])
    query = policy_type.lower()
    
    # Keyword token matching
    query_tokens = [t for t in query.replace("?", "").replace(",", "").split() if len(t) > 2]
    
    best_match = None
    max_score = 0
    
    for pol in policies:
        title = pol.get("title", "").lower()
        content = pol.get("content", "").lower()
        category = pol.get("category", "").lower()
        score = 0
        
        for token in query_tokens:
            if token in title:
                score += 5
            if token in category:
                score += 3
            if token in content:
                score += 2

        if score > max_score:
            max_score = score
            best_match = pol

    if best_match and max_score > 0:
        return {
            "status": "success",
            "source": "HR_Policy_Knowledge_Base",
            "title": best_match.get("title"),
            "category": best_match.get("category"),
            "content": best_match.get("content"),
            "message": (
                f"📋 İK Politikası: {best_match.get('title')}\n"
                f"{best_match.get('content')}"
            )
        }

    return {
        "status": "not_found",
        "query": policy_type,
        "message": f"'{policy_type}' konusu hakkında şirket İK el kitabında doğrudan bir madde bulunamadı. Lütfen İK ekibi ile doğrudan iletişime geçiniz."
    }
