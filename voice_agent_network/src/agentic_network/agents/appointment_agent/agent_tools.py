# tools.py (Güncellenmiş)
from mock_data import MOCK_DATA
from typing import Dict
import json

class ToolManager:
    """
    Tool'ların ve mock datanın ajan için yönetildiği yer.
    """

    def __init__(self):
       self.mock_data = MOCK_DATA.copy()
       self.user_data = {
            "kimlik": "345345345"
        }
       self.authenticated = False
       self.system_prompt = """
            Rolünüz ve Yönergeleriniz
            Bir hastane ve doktor randevu sistemi için akıllı bir asistansınız. Temel göreviniz, kullanıcıların hastane, doktor ve randevu bilgilerine erişimini kolaylaştırmak ve rezervasyon sürecine yardımcı olmaktır. Doğru bilgi sağlamak ve görevleri tamamlamak için sağlanan tool'ları kullanmalısınız.

            **İLK KURAL**: Kullanıcı hangi dille seninle iletişime giriyorsa, sen de aynı dille cevap vermek zorundasın.
            **KURAL**: Unutma kullanıcıya tool bahsetmek kesinlikle yasak! Zaten kullanıcının tool erişimi yoktur, kullanamaz! Sistem tool kullanmayı kullanıcıdan gizli bir şekilde arka planda ele alır, tool çağrısı mesajını kullanıcıya iletmez.
            **KURAL**: Tool isimleri, parametreleri veya "TOOL_CALL" formatı kullanıcıya asla gösterilmez.

            **KİMLİK DOĞRULAMA KURALI**:
            Randevu oluşturma işlemi başlamadan önce, kullanıcının girdiği kimlik numarasını **doğrudan ve olduğu gibi** `authenticate_user` aracına iletmelisiniz.
            Kimlik doğrulama başarıyla tamamlanana kadar başka hiçbir adıma veya araca geçmeyin.
            Başarılı olursa, kullanıcıdan hastane aramak için şehir ve ilçe bilgisi isteyin.
            Başarısız olursa, kimlik bilgisinin yanlış olduğunu nazikçe belirtin ve kullanıcıdan tekrar denemesini isteyin.


            Kullanım Talimatları
            
            1. **Gerekli Bilgilerin Sorgulanması**: Kullanıcının talebini işlemek için gereken parametreler eksikse, eksik bilgileri **açıkça ve tek tek** isteyin.
                * **ÖZEL KURAL**: Yeni bir randevu talebi başlattığınızda (örneğin, "KBB'de randevu almak istiyorum"), her zaman önce hastane konumu (şehir ve ilçe) için get_hospitals_by_city_and_district tool'unun parametrelerini sormalısınız.
                * **ÖZEL KURAL**: Hastane bilgilerini aldıktan sonra, eğer poliklinik bilgisi yoksa (yani NONE'sa) get_policlinics_by_hospital_name aracıyla poliklinikleri listelemelisın. Daha sonrasında hangi polikliniği istediğini kullanıcıya sormalı, cevabı almalısın.
                * **KRİTİK GÜNCELLEME**: Kullanıcı açıkça bir doktor listesi isterse (örneğin, "hangi doktorlar var?", "doktorları listele"), mevcut bilgilerle (hastane, poliklinik) `get_doctors_by_hospital_and_policlinic` tool'unu kullanarak önceliklendirme yapmalısınız. Bu aşamada **tarih sormayın**, çünkü kullanıcı bir rezervasyon değil, bir liste talep ediyor.

            2. **Yanıtları Açıkça Biçimlendirin**: Tool'lardaki ham verileri (JSON listeleri veya sözlükler gibi) doğrudan kullanıcıya göstermeyin. Bunun yerine, bu verileri net, iyi yapılandırılmış ve okunabilir bir metne dönüştürün.
                * **Kullanıcı için Liste Seçenekleri**: Bir tool bir öğe listesi (hastaneler, klinikler, doktorlar veya müsait saatler) döndürdüğünde, bu seçenekleri kullanıcıya açıkça sunmalı ve bir seçim yapmasını istemelisiniz. Bu, etkileşimli ve yönlendirilmiş bir konuşma yaratır. * Örnek: "A (il), B (ilçe)'deki hastaneler: C Hastanesi ve D Hastanesi. Hangisini tercih edersiniz?"

            3. **Hataları Zarifçe Yönetin**: Bir tool boş bir sonuç döndürürse (örneğin, boş bir liste [] veya '{"error": ...}' hata mesajı), bunu kullanıcıya anlayışlı ve çözüm odaklı bir şekilde iletin.
                * Örnek: "Üzgünüm, kriterlerinize uygun herhangi bir hastane bulamadım. Lütfen şehir ve ilçe adlarını kontrol edip tekrar deneyebilir misiniz?"
                * Örnek: "Bu poliklinikte şu anda müsait doktor yok. Başka bir poliklinik veya hastaneye bakmamı ister misiniz?"

            4. **Randevuları Onayla**: Bir randevu başarıyla alındığında ("status": "success"), **ilgili tüm randevu ayrıntılarını (doktor adı, hastane adı, şehir, ilçe, poliklinik, tarih ve saat)** içeren net ve onaylayıcı bir mesaj verin.
                * **Örnek**: "Randevunuz Kardiyoloji bölümünden Dr. Ayşe Yılmaz'a Ankara, Çankaya'daki Ankara Şehir Hastanesi'nde 10 Ağustos 2025, saat 09:00 için başarıyla tamamlandı. İyi günler geldi."

            5. **Randevu İptali**: Randevu iptal etme işlemi belirli bir şekilde gerçekleştirilmelidir:
                * Bir kullanıcı randevusunu iptal etmek istediğinde (örneğin, "randevumu iptal et"), önce **`get_my_appointments`** aracını kullanarak mevcut tüm randevuların listesini alın.
                * Bu listeyi, her randevu için benzersiz bir kimlikle kullanıcıya sunun.
                * Kullanıcıdan iptal etmek istediği randevunun kimliğini belirtmesini isteyin.
                * Kullanıcı bir kimlik verdikten sonra, verilen kimlikle **`cancel_appointment_by_id`** aracını kullanın.
                * Bir randevu başarıyla iptal edildiğinde ("status": "success"), açık ve onaylayıcı bir mesaj sağlayın.
                * **Örnek**: "Dr. Ayşe Yılmaz'a Ankara Şehir Hastanesi'nde 10 Ağustos 2025 tarihindeki randevunuz başarıyla iptal edildi."

            6. **Tool Seçimine Öncelik Verin**: Kullanıcının isteğine en uygun aracı seçmek için tool tanımlarını dikkatlice okuyun.
                * `get_hospitals_by_city_and_district`: Kullanıcı hem şehri hem de ilçeyi aynı anda girdiğinde her zaman bu aracı kullanın. Parametreleri doğru şekilde ayrıştırmayı unutmayın.
                * `get_available_dates_for_doctor`: **Kullanıcı bir doktor seçtikten sonra, uygun tarihleri bulup kullanıcıya sunmak için bu aracı kullanın. Manuel olarak tarih sormayın; bunun yerine, kullanıcıya aracın çıktısına göre net bir seçenek listesi sunun.**
                * `get_hospitals_by_location`: Kullanıcı hem şehri hem de ilçeyi girdiğinde bu aracı kullanmamalısınız. Bu durumlarda, `get_hospitals_by_city_and_district` tarafından istenen eksik parametreleri istemelisiniz.

            7. **Birden Fazla Randevuyu Yönetme**: Bir kullanıcının aynı doktorla birden fazla randevu veya farklı bir zaman aralığı için randevu almak isteyebileceğini unutmayın. Başarılı bir randevu alımından sonra, kullanıcıya mevcut diğer randevu aralıkları hakkında bilgi verin ve başka bir randevu almak isteyip istemediğini sorun.

            Diğer tüm tool'lar: Bu tool'ları yalnızca gerekli tüm parametreler mevcut olduğunda çağırın.
            """
    

    def get_tool_definitions(self):
        """
        LLM'e sunmak için tool'ların tanımlarının döndürür.
        """
        return [
            {
                "name": "authenticate_user",
                "description": "Bu araç, kullanıcının girdiği kimlik bilgisini kontrol eder. Bilgiler eşleşirse 'success', eşleşmezse 'error' mesajı döndürür.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "identity_number": {
                            "type": "string",
                            "description": "Kullanıcının girdiği kimlik numarası."
                        }
                    },
                    "required": ["identity_number"]
                }
            },
            {
                "name": "get_hospitals_by_city_and_district",
                "description": (
                    "Belirtilen şehir ve ilçedeki hastane listesini döner."
                    "Bu tool lokasyona göre aramalarda tercih edilir."
                    "KURAL: Kullanıcı hem şehir hem de ilçe girerse, 'şehir' ve 'ilçe'yi ayrı ayrı doldurmanız gerekir, "
                    "tek bir 'konum' parametresi olarak değil. "
                    "Eğer hastane bulunamazsa, 'Hastane bulunamadı, lütfen il/ilçeyi tekrar kontrol edin' mesajı dönecektir."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Şehrin ismi. Örneğin: 'Ankara'."
                        },
                        "district": {
                            "type": "string",
                            "description": "İlçenin ismi. Örneğin: 'Çankaya'."
                        }
                    },
                    "required": ["city", "district"]
                }
            },
            {
                "name": "get_hospitals_by_location",
                "description": "Belirtilen şehir veya ilçedeki hastanelerin listesini döndürür. Bu aracı yalnızca şehir ve ilçe aynı anda belirtilmemişse kullanın.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Aranacak şehir veya ilçenin adı. Örnek: 'Ankara' veya 'Bornova'."
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_policlinics_by_hospital_name",
                "description": "Belirtilen hastanedeki tam polikliniklerin listesini döndürür. Bu araç, bir kullanıcı belirli bir hastaneyi seçtikten sonra bölüm veya polikliniklerin listesini istediğinde kullanılmalıdır.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hospital_name": {
                            "type": "string",
                            "description": "Aranacak hastanenin tam adı."
                        }
                    },
                    "required": ["hospital_name"]
                }
            },
            {
                "name": "get_doctors_by_hospital_and_policlinic",
                "description": "Belirli bir hastane ve poliklinikte çalışan doktorların listesini döndürür.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hospital_name": {
                            "type": "string",
                            "description": "Aranacak hastanenin tam adı."
                        },
                        "policlinic": {
                            "type": "string",
                            "description": "Aranacak polikliniğin adı. Yaygın örnekler arasında 'Kulak Burun Boğaz', 'Kardiyoloji' veya 'KBB' kısaltması yer alıyor."
                        }
                    },
                    "required": ["hospital_name", "policlinic"]
                }
            },
            {
                "name": "get_available_dates_for_doctor",
                "description": "Bu araç, bir doktor seçildikten sonra, ancak belirli bir tarih istenmeden önce kullanılmalıdır.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_name": {
                            "type": "string",
                            "description": "Uygun tarihleri kontrol etmek için doktorunuzun tam adını girin."
                        }
                    },
                    "required": ["doctor_name"]
                }
            },
            {
                "name": "get_available_appointments",
                "description": "Bu fonksiyon sadece doktorun müsaitlik listesinde bulunan ve henüz rezerve edilmemiş zamanları döndürür.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_name": {
                            "type": "string",
                            "description": "Randevu almak istediğiniz doktorun tam adı."
                        },
                        "date": {
                            "type": "string",
                            "description": "Randevu arama tarihi, 'YYYY-AA-GG' biçiminde. Örnek: '2025-08-10'."
                        }
                    },
                    "required": ["doctor_name", "date"]
                }
            },
            {
                "name": "book_appointment",
                "description": "Belirli bir doktor, tarih ve saat için randevu oluşturur.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_name": {
                            "type": "string",
                            "description": "Randevu almak istediğiniz doktorun tam adı."
                        },
                        "date": {
                            "type": "string",
                            "description": "Randevu tarihi, 'YYYY-AA-GG' formatında."
                        },
                        "time": {
                            "type": "string",
                            "description": "Randevu saati, 'SS:DD' formatında."
                        }
                    },
                    "required": ["doctor_name", "date", "time"]
                }
            },
            {
                "name": "cancel_appointment_by_id",
                "description": "Randevu listesinden benzersiz tanımlayıcısını (ID) kullanarak rezerve edilmiş bir randevuyu iptal eder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {
                            "type": "integer",
                            "description": "İptal edilecek randevunun benzersiz kimliği. Bu kimlik, randevular listelenirken sağlanır."
                        }
                    },
                    "required": ["appointment_id"]
                }
            },
            {
                "name": "get_my_appointments",
                "description": "Kullanıcının mevcut tüm randevularını listeler ve her birine benzersiz bir kimlik atar. Mevcut randevuları görmek için bu aracı kullanmanız ve ardından bir randevuyu iptal etmeniz önerilir.",
                "parameters": {
                    "type": "object",
                    "properties": {} #bu toolun herhangi bir parametreye ihtiyacı yok.
                }
            }
        ]


    # --- Araç Fonksiyonları ---
    def authenticate_user(self, identity_number: str) -> Dict:
        """
        Kullanıcı kimliğini doğrular.
        """
        print(f"DEBUG: authenticate_user'a gelen identity_number: {identity_number}, tipi: {type(identity_number)}")
        print(f"DEBUG: user_data'daki kimlik: {self.user_data['kimlik']}, tipi: {type(self.user_data['kimlik'])}")

        if identity_number == self.user_data["kimlik"]:
            self.authenticated = True
            return {"status": "success", "message": "Kimlik doğrulama başarılı. Artık randevu oluşturabilirsiniz."}
        else:
            self.authenticated = False
            return {"status": "error", "message": "Kimlik doğrulama başarısız. Lütfen kimlik numaranızı kontrol edin."}


    def get_hospitals_by_city_and_district(self, city: str, district: str) -> list:
        """
        Belirtilen şehir ve ilçeye göre hastanelerin listesini alır.
        Hiçbir hastane bulunamazsa, boş bir liste yerine net bir hata mesajı döndürür.

        Args:
            şehir (str): Aranacak şehrin adı.
            ilçe (str): Aranacak ilçenin adı.

        Returns:
            list: Şehir ve ilçeyle eşleşen hastane adlarının listesi.
                Hastane bulunamazsa boş bir liste döndürür.
        """
        city = city.lower()
        district = district.lower()
        hospitals = [
            h["adi"] for h in self.mock_data["hastaneler"]
            if h["konum_il"].lower() == city and h["konum_ilce"].lower() == district
        ]
        if not hospitals:
            return [{"error": "Hastane bulunamadı, lütfen şehir/ilçeyi tekrar kontrol edin"}]
        return hospitals
    

    def get_hospitals_by_location(self, location: str) -> list:
        """
        Belirtilen şehir veya ilçeye göre hastanelerin listesini alır.

        Args:
            location (str): Aranacak şehir veya ilçenin adı. Büyük/küçük harfe duyarlı değildir.

        Returns:
            list: A list of hospital names that match the location.
                  Returns an empty list if no hospitals are found.
        """
        location = location.lower()
        return [
            h["adi"] for h in self.mock_data["hastaneler"]
            if h["konum_il"].lower() == location or h["konum_ilce"].lower() == location
        ]
    
    
    def get_policlinics_by_hospital_name(self, hospital_name: str) -> list:
        """
        Belirli bir hastanede bulunan tüm benzersiz polikliniklerin listesini alır.

        Args:
            hospital_name (str): Aranacak hastanenin tam adı.
        Returns:
            list: Benzersiz poliklinik adlarının listesi (örneğin, ['KBB', 'Kardiyoloji']).
                Hastane bulunamazsa veya doktoru yoksa boş bir liste döndürür.
        """
        hospital_id = None
        for h in self.mock_data["hastaneler"]:
            if h["adi"].lower() == hospital_name.lower():
                hospital_id = h["id"]
                break

        if not hospital_id:
            return []

        policlinics = {
            d["uzmanlik"] 
            for d in self.mock_data["doktorlar"]
            if d["hastane_id"] == hospital_id
        }

        return list(policlinics)
    

    def get_doctors_by_hospital_and_policlinic(self, hospital_name: str, policlinic: str) -> list:
        """
        Belirli bir hastane ve poliklinikte çalışan doktorları listeler.

        Bu fonksiyon önce hastanenin ID'sini bulur ve ardından doktor listesini hem hastane ID'sine hem de poliklinik adına göre filtreler.

        Args:
            hospital_name (str): Hastanenin tüm adı (e.g., 'Ankara Şehir Hastanesi').
            policlinic (str): Polikliniğin tam adı (e.g., 'KBB', 'Kardiyoloji').

        Returns:
            list: Kriterlere uyan doktor isimlerinin listesi.
                Hastane veya doktorlar bulunamazsa boş bir liste döndürür.
        """
        policlinic_map = {
            "kulak burun boğaz": "KBB",
            "kbb": "KBB",
            "kardiyoloji": "Kardiyoloji",
            "nöroloji": "Nöroloji",
            "dermatoloji": "Dermatoloji",
            "gastroenteroloji": "Gastroenteroloji",
            "plastik cerrahi": "Plastik Cerrahi",
            "ortopedi": "Ortopedi"
        }
        
        # Gelen poliklinik adını eşleme sözlüğünde ara
        mapped_policlinic = policlinic_map.get(policlinic.lower(), policlinic)

        hospital_id = None
        for h in self.mock_data["hastaneler"]:
            if h["adi"].lower() == hospital_name.lower():
                hospital_id = h["id"]
                break
        
        if not hospital_id:
            return []
            
        doctors_in_policlinic = [
            d for d in self.mock_data["doktorlar"]
            if d["uzmanlik"].lower() == mapped_policlinic.lower() and d["hastane_id"] == hospital_id
        ]

        return [d["adi"] for d in doctors_in_policlinic]


    def get_available_dates_for_doctor(self, doctor_name: str) -> list:
        """
        Belirli bir doktor için müsait randevu tarihlerinin listesini alır.

        Bu fonksiyon, verilen `doctor_name` için bir eşleşme bulmak üzere doktorların sahte verilerini yineler. 
        Doktor bulunduğunda, doktorun `musaitlik` (müsaitlik) sözlüğünden müsait tarihleri temsil eden anahtarları çıkarır. 
        Fonksiyon, doktorun adı için büyük/küçük harfe duyarlı değildir. Eşleşen bir doktor bulunamazsa, boş bir liste döndürür.

        Args:
            doctor_name (str): Müsaitlik tarihleri alınacak doktorun tam adı.
                        Arama büyük/küçük harfe duyarlı değildir.
        Returns:
            list: Her dizenin 'YYYY-AA-GG' biçiminde müsait bir tarih olduğu dizelerden oluşan bir liste (örneğin, ['2025-08-15', '2025-08-16']).
                Eşleşen bir doktor bulunamazsa boş bir liste döndürür.
        """
        for doktor in self.mock_data["doktorlar"]:
            if doktor["adi"].lower() == doctor_name.lower():
                # 'musaitlik' sözlüğünün anahtarları müsait tarihleri temsil eder.
                return list(doktor["musaitlik"].keys())
        return []


    def get_available_appointments(self, doctor_name: str, date: str) -> list:
        """
        Belirli bir tarihte bir doktor için müsait randevu aralıklarını bulur ve döndürür.

        Doktorun genel müsaitliğini kontrol eder ve önceden rezerve edilmiş randevuları kaldırır.

        Args:
            doctor_name (str): Doktorun tam adı.
            date (str): The date to check, in 'YYYY-MM-DD' format.

        Returns:
            list: Uygun zamanların listesi ('HH:MM'). eğer hiçbir doktor/tarih müsait değilse boş liste dön.
        """
        for doktor in self.mock_data["doktorlar"]:
            if doktor["adi"].lower() == doctor_name.lower():
                original_times = doktor["musaitlik"].get(date, [])
                
                booked_times = {
                    r["saat"] for r in self.mock_data["randevular"]
                    if r["doktor"].lower() == doctor_name.lower() and r["tarih"] == date
                }
                
                available_times = [
                    time for time in original_times if time not in booked_times
                ]
                
                return available_times
        return []

    def book_appointment(self, doctor_name: str, date: str, time: str) -> str:
        """
        Belirli bir tarih ve saat için bir doktorla yeni bir randevu oluşturur.

        Bu işlev, yeni randevuyu oluşturmadan önce istenen zaman aralığının müsait olup olmadığını 
        ve daha önce rezerve edilip edilmediğini doğrular.

        Args:
            doctor_name (str):Doktorun tüm adı.
            date (str): 'YYYY-MM-DD' formatında randevu tarihi.
            time (str): 'HH:MM' formatında saat tarihi.

        Returns:
            str: Rezervasyon durumunu ('success' or 'error')
                 belirten bir JSON dizesi ve sonucu açıklayan bir mesaj.
        """
        is_booked = any(
            r["doktor"].lower() == doctor_name.lower() and
            r["tarih"] == date and
            r["saat"] == time
            for r in self.mock_data["randevular"]
        )

        if is_booked:
            return json.dumps({"status": "error", "message": "Bu randevu saati zaten dolu."})
        
        available_times = self.get_available_appointments(doctor_name, date)
        if time not in available_times:
            return json.dumps({"status": "error", "message": "Belirtilen saat müsait değil veya geçersiz."})

        # Find doctor details to get hospital_id and policlinic
        doctor_info = None
        for doc in self.mock_data["doktorlar"]:
            if doc["adi"].lower() == doctor_name.lower():
                doctor_info = doc
                break

        if not doctor_info:
            return json.dumps({"status": "error", "message": "Doktor bilgisi bulunamadı."})

        # Find hospital details using hospital_id
        hospital_info = None
        for hosp in self.mock_data["hastaneler"]:
            if hosp["id"] == doctor_info["hastane_id"]:
                hospital_info = hosp
                break
        
        if not hospital_info:
            return json.dumps({"status": "error", "message": "Hastane bilgisi bulunamadı."})

        randevu_bilgisi = {
            "doktor": doctor_name,
            "tarih": date,
            "saat": time,
            "hastane_adi": hospital_info["adi"],
            "hastane_il": hospital_info["konum_il"],
            "hastane_ilce": hospital_info["konum_ilce"],
            "poliklinik": doctor_info["uzmanlik"]
        }
        self.mock_data["randevular"].append(randevu_bilgisi)
        return json.dumps({"status": "success", "message": "Randevunuz başarıyla oluşturuldu.", "randevu": randevu_bilgisi})
    

    def delete_appointment(self, doctor_name: str, hospital_name: str, policlinic: str, date: str, time: str) -> str:
        """
        Tam eşleşme için tüm ayrıntıları kullanarak, mevcut bir randevuyu sahte verilerden siler.

        Args:
            Doktorun tam adı.
            hastane_adı (dize): Hastanenin adı.
            poliklinik (dize): Polikliniğin adı.
            tarih (dize): Randevunun tarihi 'YYYY-AA-GG' biçiminde.
            saat (dize): Randevunun saati 'SS:DD' biçiminde.

        Returns:
            str:Durumu ('başarılı' veya 'hata') ve bir mesajı gösteren bir JSON dizesi.
        """
        
        # Filter out the appointment that matches all the provided details
        appointment_list_before_deletion = len(self.mock_data["randevular"])
        self.mock_data["randevular"] = [
            r for r in self.mock_data["randevular"]
            if not (r["doktor"].lower() == doctor_name.lower() and
                    r["hastane_adi"].lower() == hospital_name.lower() and
                    r["poliklinik"].lower() == policlinic.lower() and
                    r["tarih"] == date and
                    r["saat"] == time)
        ]
        
        if len(self.mock_data["randevular"]) < appointment_list_before_deletion:
            return json.dumps({"status": "success", "message": "Randevunuz başarıyla silindi."})
        else:
            return json.dumps({"status": "error", "message": "Belirtilen randevu bulunamadı veya randevu silinemedi."})
        


    def get_my_appointments(self) -> list:
        """
        Kullanıcı için hazır bulunan rezerve edilmiş tüm randevuları alır ve biçimlendirir.

        Bu işlev, başarıyla rezerve edilmiş tüm randevuları almak için dahili sahte verilerin "randevular" listesine erişir. 
        Her randevu, sonraki işlemler için çok önemli olan benzersiz bir sayısal kimlikle zenginleştirilir (`cancel_appointment_by_id` kullanılarak).

        Returns:
            list: Her sözlüğün rezerve edilmiş bir randevuyu temsil ettiği ve 'id', 'doctor_name' (doktor adı),
                'hastane_adi' (hastane adı),
                'poliklinik' (poliklinik),
                'tarih' (tarih) ve
                'saat' (saat) değerlerini içerdiği bir sözlük listesi. Randevu bulunamazsa boş bir liste döndürür.
        """
        formatted_appointments = []
        for i, appt in enumerate(self.mock_data["randevular"]):
            formatted_appointments.append({
                "id": i,
                "doktor": appt["doktor"],
                "hastane_adi": appt["hastane_adi"],
                "poliklinik": appt["poliklinik"],
                "tarih": appt["tarih"],
                "saat": appt["saat"]
            })
        return formatted_appointments
    
    
    def cancel_appointment_by_id(self, appointment_id: int) -> str:
        """
        Benzersiz tanımlayıcısını (ID) kullanarak rezerve edilmiş bir randevuyu iptal eder.
        
        Args:
            appointment_id (int): iptal edilecek randevunun benzersiz ID'si.
        
        Returns:
            str: Durumu ('başarılı' veya 'hata') ve bir mesajı gösteren JSON dizesi.
        """
        # mock_data'daki "randevular" listesini güncelleyerek randevuyu sil
        if 0 <= appointment_id < len(self.mock_data["randevular"]):
            del self.mock_data["randevular"][appointment_id]
            return json.dumps({"status": "success", "message": "Randevunuz başarıyla iptal edildi."})
        else:
            return json.dumps({"status": "error", "message": "Geçersiz randevu ID'si."})