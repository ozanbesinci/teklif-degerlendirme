# Teslim ve Doğrulama

### Adım 9 — Excel üretimi

`references/excel-ve-rapor-uretimi.md` — sekme seti, biçim kuralları, formül zorunluluğu,
bilinen tuzaklar. Sekme seti dala, kapsama ve şartnamenin varlığına göre daraltılır;
uygulanmayan sekme oluşturulmaz ama Özet'te "uygulanmadı" olarak belirtilir.

### Adım 10 — Yazılı rapor (istenirse) — PDF **zorunlu**

Rapor üretiliyorsa nihai çıktı **PDF'tir**; kullanıcıdan ayrı istek beklemez.
Markdown yalnız ara dosyadır ve PDF doğrulandıktan sonra silinir. Üretim yolu,
dönüştürme zinciri, doğrulama ve güvenli temizleme:
`references/excel-ve-rapor-uretimi.md` §5. Zincirin bütün
basamakları tükendiyse PDF eksikliği **sessizce geçilmez** — kullanıcıya nedeniyle
birlikte yazılır ve elle PDF alma adımı verilir.

**Sabit sayfa sayısı veya zorunlu uzunluk yoktur.** Alımın içeriği, mal/hizmetin durumu,
tutarı, karmaşıklığı ve riskine göre kısa veya ayrıntılı yaz. Basit alımda ilgili
bulguları birleştir; riskli/karmaşık işte gerekçe ve hesapları ayrıntılandır.
İlgisiz başlıklarla sayfa doldurma; kritik belirsizlikleri ve kaynakları kısaltma uğruna çıkarma.

İhtiyaca göre seçilecek/birleştirilecek bölümler: Yönetici Özeti · Yöntem ve Kapsam (şartname var/yok bilgisi burada) · Teklif Tipi
ve Miktar Mutabakatı Bulgusu · Maliyet Köprüsü ve KTM Analizi (+kritik uyarı, kur dipnotu,
varsayım listesi) · Kalem/Poz Bazlı Fiyat Analizi · Ömür Boyu Maliyet · Ticari ve Finansal
Değerlendirme · Sözleşmesel Riskler · Firma Bazında Güçlü/Zayıf Yönler · Uygunluk
Boşlukları · Yeterlilik ve Risk · Şartname İç Tutarsızlıkları · Netleştirilecek Noktalar
(RFI) · Sonuç ve Öneri.

### Adım 11 — Doğrulama pası (ZORUNLU)

`references/hesaplama-kontrolleri.md` içindeki mutabakat ve sınır kontrolleri de uygulanır.

1. Her firmanın Excel'deki toplamı, kaynak belgede **beyan ettiği toplamla** tutuyor mu.
2. Maliyet köprüsü: her basamak bir öncekine formülle bağlı mı, atlanan basamak
   "uygulanmadı" işaretli mi, KTM elle hesapla tutuyor mu.
3. Miktar mutabakatı: ortak referans tüm firmalara **aynı** uygulanmış mı; kalem
   tutarlarının toplamı sekme toplamıyla tutuyor mu.
4. Mod doğru mu: bağımsız geçerli tedarikçi sayısı ile kurulan sekmeler uyuşuyor mu (tek teklifte
   puanlama/duyarlılık **kurulmamış** olmalı; iki teklifte medyan/sapma satırı olmamalı;
   7+ teklifte kısa liste ölçütü yazılı olmalı).
5. Puanlama: elenmiş firma sıralamaya girmiş mi (**girmemeli**), ağırlık toplamı 100 mü,
   normalizasyon yönü doğru mu (düşük fiyat/kısa süre → yüksek puan), SUMPRODUCT elle
   hesapla tutuyor mu.
6. Duyarlılık tablosunun **her** senaryosunda ağırlık toplamı 100 mü; sonuç yorumu
   **ayırt edici orana koşullu** yazılmış mı (oran <%60 iken "sonuç sağlamdır" cümlesi
   kullanılmamış olmalı).
7. NBD: dönem sayısı tutarlı mı, **t=0 avans iskonto edilmemiş mi**, aynı para biriminde
   ödeme yapan firmalar aynı oran hücresine mi bağlı, **vadeli döviz ödemesi TL oranıyla
   iskonto edilmemiş mi** (`finansal-degerlendirme.md` §1b), TCO'da **oranın cinsi akışın
   cinsine uyuyor mu** — sabit fiyatlı akış ↔ reel oran (`tco-omur-boyu-maliyet.md` §3a).
8. Eşit kapsam, ithalat köprüsü ve birim maliyet metrikleri doğru mu. **5-A ile 5-B
   ayrı satırda mı**; 5-B'nin tutar, zaman ve kapsam eşitliği teyitli mi? KTM maliyet
   sırası ile toplam puan sırası ayrılmış mı; ortak gider puan duyarlılığı var mı?
9. Çifte sayım: KTM'ye para olarak girmiş bir konu puanlamada ikinci kez cezalandırılmış
   mı (`puanlama-metodolojisi.md` "Çifte sayım yasağı" tablosu); "uygulanmadı" işaretli
   basamağın konusu niteliksel kritere geçmiş mi.
10. Kur çevrimi varsa kaynağı, tarihi ve türü yazılı mı; TCMB'den alındıysa yayınla tutuyor mu.
11. Her nicel tabloda **Kaynak sütunu dolu mu**; boş olanlar varsayım işaretli mi.
12. Görselden okunan değerler çapraz doğrulanmış mı, işaretli mi.
13. Tüm sekmelerde bozuk karakter (`�`) taraması; formül hücrelerinin görüntülenecek
    değeri var mı.
14. Metinsel iddialar kaynakta teyit edildi mi (dahil/hariç, garanti, geçerlilik,
    miktar/adet, teklif tipi, Incoterms, fiyat revizyon maddesi).
15. **Tazelik:** her teklif için hem geçerlilik testi hem **yaş testi** çalıştırıldı mı
    (Adım 1). Geçerlilik beyanı olmayan bir teklif "sorunsuz" görünüyorsa bu bir
    hatadır — yaş testi beyandan bağımsız çalışır.
16. **Ayırt edici ağırlık oranı** hesaplandı ve Puanlama + Karar Özeti'nde yazıldı mı;
    nötr (5,0) puanlı her kriterin karşılığı RFI'da bir madde olarak var mı.
17. **Muhatap doğru mu:** hiçbir firmanın karşılayamayacağı bir eksiklik (şartnamede
    olmayan kalem, tanımsız teknik parametre) firma satırına değil **İDARE** satırına
    yazılmış mı.
18. **PDF teslimi:** yazılı rapor üretildiyse `.pdf` dosyası **gerçekten diskte var mı**,
    boyutu 0 byte'tan büyük mü, sayfa sayısı makul mü ve son bölüm ("Sonuç ve Öneri")
    PDF'in içinde mi. Dosya yoksa veya kesikse dönüştürme zinciri bir sonraki basamakla
    yeniden denenir. "Rapor hazır" cümlesi PDF doğrulanmadan kurulmaz. Teminat, sigorta
    ve ceza gerekiyorsa gerekçe/tutar/süre açıklamaları PDF'te var mı; eksik girdiler
    açık mı? Doğrulama başarılıysa bu rapor için oluşturulan ara `.md` silinmiş mi?

19. Nakit/kalite/stok modülleri ilgiliyse: tepe nakit tarihi ve birikimli/tek dönem
    ayrımı doğru mu; kalite miktar dengesi tutuyor mu; stok tükenmesi, kapasite ve
    raf ömrü kontrol edildi mi; sipariş ile teslim sayısı ayrılmış mı; yeni giderler
    KTM ve nakit akışında bir kez mi yer alıyor? Ayrıntı: `nakit-kalite-stok.md`.

Hata bulunursa düzelt ve **yeniden doğrula**; bulguları kullanıcıya kısaca raporla.

## RFI sonrası sürüm yönetimi

Revize teklifler geldiğinde analiz sıfırdan yazılmaz, **sürümlenir**:
`<PROJE>_Teklif_Karsilastirma_v2.xlsx`. v2'de **Değişim Kaydı** sekmesi açılır: firma ×
değişen kalem × v1 × v2 × KTM etkisi × sıralama etkisi. **Hangi RFI sorusuna hangi firmanın
cevap vermediği de bu sekmede kalır — cevapsızlık başlı başına bir bulgudur.** Miktar
mutabakatı veya şartname eksikliği v2'de çözüldüyse "ÖN SONUÇ" etiketi kaldırılır ve bu
açıkça yazılır.

## Kalite İlkeleri

- **Tek bir toplam puan asla tek başına karar gerekçesi olarak sunulmaz.** Öneri her zaman
  üç ayağı birlikte gösterir: puan sıralaması + KTM + kırmızı çizgi/uygunsuzluk durumu.
  Üçü aynı firmayı göstermiyorsa çelişki açıkça yazılır.
- **Teklifin tazeliği beyana bırakılmaz.** Geçerlilik süresi yazılmamışsa test atlanmış
  olmaz — teklifin **yaşı** ölçülür (Adım 1). Eski bir teklifin sessizce analize girmesi,
  analizin bütün sayılarını dayanaksız bırakır.
- **Bir eksikliğin muhatabı kapsam belgesinden belirlenir.** İstenmemiş ihtiyaç İDARE'ye;
  açıkça istenip fiyatlanmamış kalem FİRMALAR'a sorulur. Hiçbirinin fiyatlamamış olması
  tek başına idare kusurunu kanıtlamaz; genel dahil beyanı önce teyit edilir.
- **Puanın ne kadarının gerçekten çalıştığı yazılır.** Ağırlık toplamı 100 olsa bile,
  bütün tekliflere aynı puanı veren kriterler sıralamaya katkı yapmaz. Ayırt edici oran
  hesaplanmadan puan sunulmaz; oran düşükken "sıralama değişmedi, sonuç sağlam" denmez —
  o cümle doğru bir hesabın yanlış yorumudur.
- **Teklif sayısı varsayılmaz.** Bir teklif de gelebilir, on iki de. Medyan, sapma,
  sıralama ve duyarlılık belirli sayıların altında anlamını yitirir; o durumda **olmayan
  rekabet varmış gibi gösterilmez** — mod değişir ve modun ne olduğu çıktıda yazılır.
- **Analiz öncesinde kapsam netleştirilir; dayanaksız veri kullanılmaz.** Belirsizlik varsa analiz öncesi sorulur;
  cevapsız kalan her varsayım işaretli ve gerekçeli olur. İşaretlenmemiş varsayım toplama
  girmez.
- Tahmin içeren her hücre görsel olarak işaretli (sarı dolgu + mavi font); tahminler
  "gösterge amaçlı, revize tekliflerle doğrulanmalı" uyarısıyla sunulur.
- Farklı teklif tipli, farklı Incoterms'li, farklı miktarlı, farklı kapsamlı veya farklı
  ömür boyu maliyetli teklifler için **asla düz fiyat sıralaması verme** — önce maliyet
  köprüsünü kur.
- Miktar uyuşmazlığı (>%5) çözülmeden verilen her sonuç **"ÖN SONUÇ"** etiketi taşır.
- Şartname yoksa teknik uygunluk **değerlendirilmez**; olmayan ölçüte göre puan verilmez ve
  bu eksiklik raporda görünür kalır.
- **"Belirtilmemiş" ile "açıkça hariç/reddedilmiş" ayrımını koru**; genel uygunluk
  beyanlarını hakkaniyetle not et.
- Elemeli kapı puanlamadan önce gelir; asgari şartı sağlamayan ucuz teklif hiçbir koşulda
  sıralamaya girmez. Anormal düşük teklif eleme sebebi değildir — açıklama istenir.
- Kriter ağırlıklarını alımın niteliğine göre uyarla, gerekçesini yaz ve kullanıcı
  değiştirebilsin diye **düzenlenebilir bırak**.
- Her nicel değer kaynağıyla (dosya + sayfa) izlenebilir olmalı.
- Bu skill **hukuki, mali veya mühendislik danışmanlığı yerine geçmez**; ilgili bulgular
  "hukuk / mali müşavir / teknik teyit önerilir" notuyla işaretlenir.
- **Rapor PDF'i olmadan teslim edilmez.** Markdown geçici çalışma biçimidir ve PDF
  doğrulandıktan sonra silinir; karar
  merciine, komisyona ve arşive giden biçim PDF'tir. Üretilemediyse bu bir **teslim
  eksiğidir** ve öyle yazılır — PDF üretilmiş gibi davranılmaz.
- Firma verileri ve fiyatlar **ticari sırdır**: rapor dağıtımı genişse maskeleme önerilir,
  bir firmanın teklifi diğerine gösterilmez.
- Nihai öneri her zaman şu çerçevede: kırmızı çizgiler sağlanmadan, miktar mutabakatı
  yapılmadan ve eşit kapsamlı revize teklifler alınmadan **sipariş/sözleşme kararı
  verilmemesi.** Nihai seçim yetkili karar merciine aittir.
