---
name: teklif-degerlendirme
description: Satınalma tekliflerini karşılaştırıp doğru satınalma kararını destekleyen analiz üretir. PDF, Excel, Word, görsel, mail ve ZIP girdilerini içerikten tanır; inşaat/yapım, makine/ekipman ve genel mal/hizmet alımlarında kapsam, maliyet, ticari koşul ve riskleri inceler; şartname varsa uygunluğu değerlendirir. Çok sekmeli Excel ve istenirse işin niteliğine göre kısa veya ayrıntılı PDF raporu üretir. "teklifleri değerlendir", "teklifleri incele", "en uygun teklifi ver", "teklifleri analiz et", "teklifleri karşılaştır", "tekliflere bak", "teklif karşılaştırma", "bu teklifleri kıyasla", "şartnameye uygunluk çıkar", "hangi firmayı seçmeliyiz", "teklif analizi yap" ve satınalma tekliflerini inceleme/seçme niyeti taşıyan benzer ifadelerde kullan; tekil/çoğul ve küçük yazım farklılıklarını da kapsar.
---

# Teklif Değerlendirme

Bu skill Ozan Beşinci tarafından oluşturulmuştur.

## Başlangıç mesajı — script ile

Her yeni teklif değerlendirmesine başlarken, dosya okuma ve analiz adımlarından önce
skill klasöründeki `scripts/baslangic_mesaji.py` dosyasını bir kez çalıştır:

```text
python "<skill-klasörünün-tam-yolu>/scripts/baslangic_mesaji.py"
```

`<skill-klasörünün-tam-yolu>` yer tutucusunu çalışılan ortamdaki gerçek skill yolu ile
değiştir. Script'in standart çıktısını **aynen, kullanıcıya görünen ilk sohbet
mesajında** göster; yalnız araç/terminal çıktısında bırakma. Mesajın tek kaynağı
script'tir; yeniden yazma, özetleme veya çevirme. Aynı analizin devam sorularında
ve yeniden denemelerde mesajı tekrarlama. Script yalnız tanıtım satırı üretir;
analiz akışı bu satır gösterildikten sonra devam eder.

Kod çalıştırma kullanılamıyorsa script'i çalıştırmış gibi davranma. Script dosyasındaki
`BASLANGIC_MESAJI` sabitini okuyup aynen göster ve çalıştırma kısıtını kısaca belirt.

## Amaç: doğru satınalma

Bu skill **en ucuz teklifi bulmak için değil, doğru satınalmayı yapmak için** vardır.
Doğru satınalma dört şeyin birlikte sağlanmasıdır:

1. **İhtiyaca uygunluk** — teklif edilen şey gerçekten istenen şey mi (şartname varsa ona
   göre, yoksa bu belirsizliğin kendisi bulgudur).
2. **Karşılaştırılabilirlik** — farklı kapsam, farklı miktar, farklı para birimi, farklı
   teslim şekli aynı zemine getirilmeden fiyatlar kıyaslanamaz.
3. **Yönetilmiş risk** — teslim, kalite, servis, mali yeterlilik ve sözleşme riskleri
   görünür ve karşılığı yazılı olmalı.
4. **İzlenebilir gerekçe** — her sayının kaynağı, her varsayımın işareti, her kararın
   dayanağı belli olmalı. Analiz sonradan denetlenebilir olmalı.

**Bu skill karar vermez, kararı hazırlar.** Nihai seçim yetkili karar merciine
(satınalma yönetimi / ihale komisyonu) aittir.

## Kimler kullanır

Satınalma yöneticileri ve **satınalma personeli** — Claude ve ChatGPT kurumsal üyelikleri üzerinden.
Kullanıcı teknik uzman olmak zorunda değildir: skill ne yaptığını açıklar, anlaşılmayan
yerde **analize başlamadan soru sorar**, varsayımlarını işaretler.

Kullanıcı iletişiminde sade, saygılı ve resmî dil kullanılır; kişiye özel hitaplardan
kaçınılır. Cevaplar Türkçedir (kullanıcı başka dilde yazarsa ona uyulur).

Skill dokümanları, sürüm kayıtları ve raporlarda nesnel, kurumsal anlatım kullanılır.
Değişiklikler kapsamı, gerekçesi ve sonucu üzerinden açıklanır; kişisel talep
hikâyeleri, sohbet aktarımları ve birinci tekil şahıs anlatımı kullanılmaz.
Oluşturucu bilgisi ve script ile gösterilen standart başlangıç mesajı korunur.

## Girdi ve çıktı

**Girdi:** bir klasör veya sohbete yüklenmiş dosyalar. Ne olduklarını kullanıcının
söylemesi gerekmez — **içerikten tanınır** (bkz. `references/dosya-tanima-ve-siniflandirma.md`).
Desteklenen biçimler: PDF (metin ve taranmış), XLSX/XLS/CSV, DOCX/DOC, JPEG/PNG/HEIC,
MSG/EML, ZIP. Okunamayan biçim (DWG/DXF/IFC) sessizce yok sayılmaz, kullanıcıya bildirilir.

**Çıktı:**
- `<PROJE>_Teklif_Karsilastirma.xlsx` — çok sekmeli, **formüllerle çalışan** karar dosyası
  (kullanıcı ağırlığı/kuru/oranı değiştirince sonuç güncellenir).
- İstenirse `<PROJE>_Teklif_Degerlendirme_Raporu.pdf` — yazılı raporun nihai teslimidir.
  Markdown yalnız ara çalışma dosyasıdır; **PDF başarıyla doğrulandıktan sonra bu rapor
  için oluşturulan `.md` silinir** (bkz. Adım 10). Rapor kısa veya uzun olabilir.

**Kaynak dosyalara dokunulmaz:** değiştirilmez, silinmez, yeniden adlandırılmaz.
Çıktı her zaman yeni dosyadır. Ortama göre teslim ve araç farkları:
`references/excel-ve-rapor-uretimi.md` → "Platform notları".

## Referans dosyaları — ne zaman okunacak

**Hepsini baştan okuma.** Her dosya yalnız ilgili olduğu adımda okunur.

| Dosya | Ne zaman |
|---|---|
| `references/dosya-tanima-ve-siniflandirma.md` | **Adım 1 — her zaman.** Biçimlere göre okuma, dosya rolü, alım dalı tespiti, envanter tablosu |
| `references/teklif-sayisi-modlari.md` | **Adım 0c — her zaman.** Kaç geçerli teklif var: tek teklif, ikili, tam, kısa liste modu; alternatif teklif sayımı |
| `references/sartname-yoksa.md` | **Şartname bulunmadığında — her zaman.** Şartnamesiz modun kuralları |
| `references/sartname-gereksinim-cikarimi.md` | Adım 2 — şartname/gereksinim listesi varsa: 19 maddelik çerçeve, zorunlu↔tercih ayrımı, iç çelişkiler |
| `references/poz-eslestirme-normalizasyon.md` | Adım 2-3 — kalem/poz bazlı teklifler: poz haritası, birim eşitleme, metraj mutabakatı, dengesiz teklif |
| `references/is-turu-celik-konstruksiyon.md` | Çelik yapı, hangar, çekek yeri, depo, platform, çelik çatı |
| `references/is-turu-betonarme-altyapi.md` | Temel, betonarme karkas, saha betonu, istinat, kanal/altyapı |
| `references/is-turu-cati-cephe.md` | Sandviç panel, trapez sac, membran, cephe kaplama, yağmur sistemi |
| `references/ekipman-tank-basincli-kap.md` | Tank, silo, basınçlı kap, kazan, eşanjör |
| `references/ekipman-doner-ekipman.md` | Pompa, kompresör, fan, blower, karıştırıcı, separatör |
| `references/ekipman-uretim-paketleme-hatti.md` | Üretim/paketleme hattı, dolum, tasnif, robotik, konveyör |
| `references/ekipman-pano-otomasyon.md` | Elektrik panosu, MCC, PLC/SCADA, enstrümantasyon |
| `references/dal-genel-mal-hizmet.md` | İnşaat/makine dışı alım: sarf, ambalaj, kimyasal, hizmet, kiralama, yazılım |
| `references/ithalat-maliyet-koprusu.md` | En az bir teklif yurt dışı kaynaklı veya Incoterms'ler farklı |
| `references/tco-omur-boyu-maliyet.md` | Adım 5f — enerji/bakım/sarf tüketen ekipman |
| `references/hesaplama-kontrolleri.md` | **Adım 3, 5 ve 11 — her zaman.** Net fiyat, ortak miktar, maliyet tekilleştirme, NBD mutabakatı, belirsizlik ve sayısal kontrol örnekleri |
| `references/nakit-kalite-stok.md` | Adım 5 — ödeme takvimi varsa tepe nakit; kalite kaybı anlamlıysa kalite maliyeti; tekrarlayan/toplu alım varsa sipariş ve stok senaryoları |
| `references/finansal-degerlendirme.md` | Adım 5g — ödeme/hakediş planı NBD, teminat komisyonu, eskalasyon, kur riski |
| `references/puanlama-metodolojisi.md` | Adım 6 — elemeli kapı, normalizasyon, ağırlık duyarlılığı |
| `references/tedarikci-yeterlilik-risk.md` | Adım 7 — yeterlilik, referans, servis/şantiye kapasitesi, risk matrisi |
| `references/sozlesme-maddeleri.md` | Adım 8 — teminat, sigorta ve ceza ihtiyacı; gerekçeli tutar/süre önerileri; fiyat revizyonu, kabuller, garanti, İSG/SGK |
| `references/excel-ve-rapor-uretimi.md` | Adım 9-10 — sekme seti, biçim kuralları, tuzaklar, PDF yolu, platform notları |

## Maliyet Köprüsü Zinciri (bu skill'in omurgası)

**Teklif fiyatları asla doğrudan kıyaslanmaz.** Her teklif sırayla aşağıdaki basamaklardan
geçirilir ve sonunda tek bir **Karşılaştırılabilir Toplam Maliyet (KTM)** üretilir. Zincir
Excel'de **görünür satırlar** hâlinde kurulur; her basamak formülle bir öncekine bağlanır.

| # | Basamak | Ne yapar | Ne zaman devrede |
|---|---|---|---|
| 1 | Teklif fiyatı | kendi para birimi, kendi teklif tipi, kendi Incoterms'i, kendi kapsamı, kendi miktarı | her zaman |
| 2 | Kur çevrimi | tek para birimi (TCMB Döviz Satış Kuru; erişim yoksa kullanıcıdan) | farklı para birimi varsa |
| 3 | Miktar düzeltmesi | ortak referans metraja / ortak adede getirme | firmalar arası miktar farkı varsa |
| 4 | İthalat köprüsü | DDP eşdeğer maliyet (navlun, sigorta, gümrük, vergi, müşavirlik, iç nakliye) | ithal teklif veya farklı Incoterms |
| 5-A | Eşit kapsam düzeltmesi — **firmalar arası** | bir firmanın verip diğerinin vermediği kalemleri tam kapsama getirme (montaj, vinç, iskele, test/NDT, sigorta, İSG, 3. taraf denetim, eğitim, as-built) | her zaman |
| 5-B | Eşit kapsam düzeltmesi — **ortak boşluk** | **hiçbir** firmanın fiyatlamadığı ama işin gerektirdiği kalemler (çoğunlukla şartname/keşif cetveli onları hiç istemediği için) | dalın kontrol listesinde olup hiçbir teklifte olmayan kalem varsa |
| 6 | Vergisel düzeltme | **indirilemeyen** vergiler (gümrük vergisi/İGV, damga vergisi, SGK yükümlülükleri) toplama girer; **indirilebilir KDV maliyete girmez; indirilemeyen kısmı girer; tevkifat ek vergi değildir** — ayrı satırda nakit akışı olarak durur | yapım/hizmet işinde her zaman; malda fark varsa |
| 7 | Finansman düzeltmesi | NBD − nominal tutar + yalnız alıcının ödediği banka masrafları; avans/kesinti ödeme planında tek kez | her zaman |
| 8 | Ömür boyu maliyet (TCO) | enerji, bakım, yedek parça, sarf, fire, duruş (N yıl, **reel oranla** iskonto edilmiş) | ekipman ömür boyu tüketim yaratıyorsa |
| 9 | Eskalasyon / fiyat rejimi riski | eskalasyonlu ve sabit teklifleri ortak riske getirme (senaryolu) | süre ve fiyat rejimi bunu anlamlı kılıyorsa |
| = | **KARŞILAŞTIRILABİLİR TOPLAM MALİYET (KTM) — indirilebilir KDV hariç** | | |

**5-A / 5-B ayrımı:** 5-A firmaya özgü kapsam farkıdır. 5-B ancak aynı tutar,
para birimi ve ödeme tarihinde bütün seçeneklere ekleniyorsa ortak proje maliyetidir.
Bu koşulda **KTM maliyet sırası değişmez; oransal fiyat puanları sıkıştığı için toplam
puan sırası değişebilir.** Ortak bedel dahil/hariç puan duyarlılığı gösterilir
(`puanlama-metodolojisi.md`). Teknik çözüme göre değişen altyapı, montaj veya işletme
maliyeti, hiçbir firma fiyatlamasa bile eşit dağıtılmaz.

**Muhatap kapsam belgesine göre belirlenir:** şartname istememişse İDARE; açıkça
istemiş ama firmalar fiyatlamamışsa ilgili FİRMALAR; genel dahil beyanı varsa önce teyit.
Rayiç yoksa tutar boş ve **FİYATLANMADI** olur. Ara toplamın adı "bilinen maliyetler
ara toplamı"dır; eksik maliyet sıfırmış gibi nihai KTM ve kesin öneri üretilmez.

**Devre dışı kalan basamak Excel'de "uygulanmadı" olarak gerekçesiyle yazılır, gizlenmez.**
Puanlamada fiyat kriteri **KTM üzerinden** hesaplanır, teklif fiyatı üzerinden değil.

**KTM'nin vergi zemini: indirilebilir KDV hariç.** İndirilemeyen KDV kısmı ve
alıcının gerçekten taşıdığı diğer vergiler maliyete girer; indirim hakkı otomatik
varsayılmaz. İndirilebilir KDV'nin tahsil/mahsup tarihine kadar finansman etkisi ayrı
hesaplanır. Teklifler aynı indirim hakkı ve vergi zeminiyle karşılaştırılır; KDV dahil
fiyat satırın kendi oranıyla ayrıştırılır, genel bir %20 oranı uygulanmaz.
Ayrıntı: `ithalat-maliyet-koprusu.md` §2b ve `hesaplama-kontrolleri.md`.

---

## İş Akışı

### Adım 0 — Anlamadan başlama: soru kapısı (ZORUNLU)

**Analize başlamadan** belirsizlikler toplanır. Kural üçtür:

1. **Belirsizlikler netleştirilir; dayanaksız veri üretilmez.** Anlaşılmayan bir dosya, çelişkili bir bilgi, eksik
   bir parametre varsa analiz başlamaz.
2. **Soruları tek seferde, numaralı ve kısa sor.** Kullanıcıyı adım adım yormak yerine
   bir blok hâlinde: "Başlamadan 4 şeyi netleştirmem gerekiyor: 1) … 2) …"
3. **Cevap gelmeyen soruyu varsayımla geçebilirsin ama sessizce geçemezsin** — varsayımı
   açıkça söyle, Excel'de sarı+mavi işaretle, gerekçesini yaz.

Adım 1'in envanter tablosu çıkarıldıktan sonra tipik olarak şunlar sorulur (yalnız
gerçekten belirsiz olanlar):

- **Dosya rolü belirsizse:** "X dosyası hangi firmanın teklifi / şartname mi?"
- **Alım kapsamı:** kaç kalem/adet alınacak, opsiyonlar dahil mi
- **Şartname yoksa:** elinizde gereksinim listesi veya RFQ metni var mı
- **Para birimi ve kur:** hangi para biriminde karşılaştırılsın; internet erişimi yoksa
  kullanılacak kur ve tarihi
- **Karar ölçütlerinde öncelik:** fiyat mı, teslim süresi mi, kalite/teknik mi, servis mi
- **Finansal parametreler:** iskonto oranı ve teminat komisyon oranı; **vadeli döviz
  ödemesi varsa o para biriminin oranı da** (EUR/USD) — TL oranıyla iskonto edilmez,
  bkz. `finansal-degerlendirme.md` §1b. Bilinmiyorsa varsayılanlar işaretli kullanılır
- **TCO gerekiyorsa:** yıllık çalışma saati, birim enerji fiyatı, değerlendirme ömrü,
  duruş maliyeti ve **yıllık enflasyon beklentisi** (reel iskonto oranı için zorunlu
  girdi, bkz. `tco-omur-boyu-maliyet.md` §3a)
- **Nakit ihtiyacı için:** ödeme/teslim/iade tarihleri; mevcutsa alıma tahsisli nakit
  ve kullanılabilir finansman limiti. Şirketin toplam banka bakiyesi gerekmez.
- **Kalite/stok gerekiyorsa:** hata/iade geçmişi, yeniden işleme ve ikame koşulları;
  tüketim takvimi, başlangıç stok, raf ömrü, MOQ ve sipariş/teslim/depo giderleri.
- **Çıktı:** yalnız Excel mi, yazılı rapor da mı; rapor firma dışına gidecek mi (maskeleme).
  Rapor isteniyorsa PDF üretilir; doğrulandıktan sonra ara `.md` silinir — PDF için ayrıca sorulmaz.

**Dosyalar ve amaç açıksa soru sorma, doğrudan başla.** Gereksiz soru da kullanıcıyı
yorar; ölçü şu: *cevabı bilmeden verilecek karar yanlış olabiliyorsa sor.*

### Adım 0b — Alım dalı ve teklif tipi kapısı

**Dal:** `dosya-tanima-ve-siniflandirma.md` ile içerikten tespit edilir — inşaat/yapım,
makine/ekipman, genel mal/hizmet veya **karma**. Karma ise ilgili tüm referanslar okunur,
kapsam sınırları (ara yüzler) baştan ayrı bir tabloya yazılır. Dal belirlenemiyorsa
"genel mod"da yürünür ve bu Özet'te belirtilir. **Alım dalı dayanaksız olarak belirlenmez.**

**Teklif tipi** (yapım işinde zorunlu, diğerlerinde kapsam karşılığı vardır) analizden önce
tespit edilir ve raporun ilk bulgusudur:
- **Götürü bedel (anahtar teslim):** miktar riski yüklenicide; fiyat farkının bir bölümü
  risk primidir.
- **Birim fiyatlı:** miktar riski işverende; toplam tutar "tahmini keşif toplamı"dır,
  **taahhüt değildir** — bu ayrım Özet'te açıkça yazılır.
- **Karma:** hangi kalem hangi rejimde, tablo hâlinde.

Firmalar **farklı rejimlerde** teklif vermişse bu en kritik bulgudur: doğrudan kıyas
yapılamaz; KTM "ortak rejim varsayımı" üzerine kurulur (hangisi olduğu yazılır) ve RFI'da
tüm firmalardan **aynı rejimde revize teklif** istenmesi önerilir.

### Adım 0c — Teklif sayısı kapısı

**Kaç teklif olduğu varsayılmaz.** Bir tane de olabilir, on iki tane de; yöntem buna göre
değişir çünkü medyan, sapma, sıralama ve duyarlılık belirli sayıların altında **anlamını
yitirir**. `references/teklif-sayisi-modlari.md` okunur ve mod seçilir:

| Bağımsız geçerli tedarikçi | Mod | Kısaca |
|---|---|---|
| **1** | Tek teklif | Karşılaştırma yok → **makullük ve kapsam denetimi** + pazarlık gündemi. Puanlama yapılmaz; Özet'te "TEK TEKLİF — REKABET YOK" uyarısı durur. Maliyet köprüsü yine kurulur |
| **2** | İkili | Medyan/sapma istatistiği yok → **fark analizi**. Anormal düşük teklif testi mutlak alt sınırla yapılır |
| **3–6** | Tam (varsayılan) | Bütün adımlar uygulanır |
| **7+** | Kısa liste | Eleme + KTM hepsine; derin analiz ilk 4-5'e, gerekçesi yazılı ve kullanıcı değiştirebilir |

**İki sayı gösterilir:** bağımsız geçerli tedarikçi ve karşılaştırılabilir seçenek.
Revizyon tek, alternatif ayrı sütundur; aynı firmanın alternatifleri rekabeti artırmaz.
Yukarıdaki mod bağımsız tedarikçi sayısına göre seçilir. Tek firmada birden çok
alternatif varsa seçenek maliyet/uygunluk kıyası yapılır, rekabet puanlaması yapılmaz.
Eleme sonrası sayılar ve mod yeniden belirlenir (`teklif-sayisi-modlari.md`).

Klasörde hiç teklif yoksa analiz başlamaz: envanter tablosu gösterilir, tek soru sorulur.
Şartname tek başına geldiyse yapılacak iş var — gereksinim listesi + teklif isteme kontrol
listesi çıkarmak; bu, sonraki turda gelen tekliflerin karşılaştırılabilir olmasını sağlar.

### Adım 1 — Dosya envanteri, okuma ve sınıflandırma

`references/dosya-tanima-ve-siniflandirma.md` okunur ve uygulanır:
biçime göre okuma → rol sınıflandırması (teklif / şartname / keşif / proje / yazışma /
belge / alakasız) → alım dalı tespiti → **envanter tablosu kullanıcıya gösterilir.**

Bu adımda ayrıca:
- **Veri kaybı kontrolü:** sayfa/tablo/görsel sayısı, boş-metinli sayfa; boş sayfa görsel
  olarak okunur. Taranmış PDF ve JPEG doğrudan görsel olarak okunur ve okunan değerler
  "görselden okundu" kaynağıyla işaretlenir.
- **Bozuk metin tespiti:** `6 65.000,00` = 665.000 gibi hataları firmanın **beyan ettiği
  genel toplamla** çapraz doğrula.
- **Sürüm ve geçerlilik kaydı:** teklif no/tarih/revizyon/geçerlilik bitişi ayrı tabloya.
  Aynı firmanın birden fazla revizyonu varsa yalnız en son değerlendirilir, eskisi
  "değerlendirme dışı" notuyla listede kalır.

  **Tazelik iki ayrı testle ölçülür; ikisi de her zaman çalıştırılır.**

  | Test | Ölçü | Eşik |
  |---|---|---|
  | **Beyan edilen geçerlilik** | teklifte yazan geçerlilik bitişi ↔ analiz tarihi | dolmuş veya <15 gün kalmış → **KRİTİK UYARI** |
  | **Teklifin yaşı** | teklif tarihi ↔ analiz tarihi — **geçerlilik beyanı olsun olmasın** | >60 gün → **KRİTİK UYARI**; 30-60 gün → uyarı |

  **İkinci test birinciye bağlı değildir.** En sık karşılaşılan durum, geçerlilik süresinin
  hiç beyan edilmemesidir: o zaman birinci test sessizce hiç çalışmaz ve **aylarca eski bir
  teklif "sorun görünmeden" analize girer.** Teklif tarihi de yoksa dosya sistemi tarihi
  kullanılır ve bunun dosya tarihi olduğu tabloya yazılır.

  Yaş testi tetiklendiğinde **teklif tarihi bilgi satırı değil, birinci bulgudur:**
  Özet'in KRİTİK UYARI kutusuna, Karar Özeti'nin kırmızı çizgilerine ve RFI'nın 1 numaralı
  maddesine girer. Metin şudur: *"Bu teklif N gün eskidir ve geçerlilik beyanı yoktur;
  imzalı-kaşeli, tarihli ve asgari 30 gün geçerli teyit/revize teklif alınmadan hiçbir sayı
  bağlayıcı değildir."* Analiz durmaz — maliyet köprüsü ve puanlama normal kurulur, ancak
  çıktı **ÖN SONUÇ** etiketi taşır.

  Malzeme fiyatı oynak dallarda (betonarme, çelik, kablo, ambalaj) yaş testi ayrıca
  **9. basamağı (eskalasyon) devreye alır**: senaryolu fiyat güncelleme kurulur ve oranın
  ancak revize teklifle belirlenebileceği yazılır — senaryo, revize teklifin yerine geçmez.

### Adım 2 — Ölçütün belirlenmesi: şartname var mı?

**Şartname (veya keşif cetveli ya da kullanıcının gereksinim listesi) VARSA:**
`references/sartname-gereksinim-cikarimi.md` ile taranır — 19 maddelik ortak çerçeve,
zorunlu↔tercih↔bilgi ayrımı, iç çelişki listesi. Dala karşılık gelen
`ekipman-*.md` / `is-turu-*.md` / `dal-genel-mal-hizmet.md` de bu adımda okunur.
Şartname uzunsa (>15 sayfa) tamamı parça parça okunur, her gereksinim **verbatim alıntı +
madde numarası** ile kaydedilir.

**Şartname YOKSA:** `references/sartname-yoksa.md` okunur ve **şartnamesiz mod** uygulanır.
Özetle: teknik uygunluk matrisi kurulmaz, teknik elemeli kapı uygulanmaz (idari kapı
kalır), kapsam ölçütü tekliflerin birleşiminden türetilen **ortak referans kapsamdır**,
puanlamada teknik uygunluk ağırlığı yeniden dağıtılır ve raporda
**"teknik denklik doğrulanmamıştır"** uyarısı zorunludur.
**Bir firmanın kendi teklifi asla şartname yerine kullanılmaz.**
Kullanıcıya bu durum analiz başlamadan tek cümleyle bildirilir.

### Adım 3 — Teklif verisi çıkarımı ve miktar mutabakatı

**Her teklif için:** teklif no/tarih/revizyon, geçerlilik, para birimi ve KDV durumu,
teklif tipi, Incoterms ve teslim yeri, kalem/poz bazlı miktar × birim × birim fiyat,
iskonto, opsiyonlar, kapsanan adet/metraj, **dahil-hariç listeleri**, ödeme planı, istenen
teminatlar, süre **ve neye bağlı olduğu** (yer teslimi, avans, resim onayı, ruhsat),
garanti, menşe, beyan edilen enerji/verim değerleri, yedek parça fiyat listesi, eskalasyon
talebi, sapma/muafiyet beyanları, referans işler.

**Kritik kontrol — kapsam eşitliği.** Firmalar aynı kalemleri teklif etmemiş olabilir
(9 ekipmandan 6'sını verir; opsiyonu baz fiyata katar; hafriyatı hariç tutar; vinci
"işverence" yazar). Bu durumda fiyatlar **DOĞRUDAN KIYASLANAMAZ** — en kritik bulgu olarak
öne çıkarılır.

**Miktar mutabakatı.** Beyan edilen miktarlar karşılaştırılır (çelik tonajı, beton m³,
kaplama m², ekipman adedi, kg, litre, kişi-vardiya). Referans; keşif/proje metrajı yoksa
beyanların medyanıdır — **medyan yalnız 3 ve üzeri beyanla kullanılır**, iki beyanda iki
senaryo kurulur, tek beyanda referans yoktur ve miktar RFI konusudur. Fark **>%5** ise:
sonuçlar
**"ÖN SONUÇ — mutabakat bekliyor"** etiketiyle sunulur, birincil RFI maddesi miktar
netleştirmesi olur, KTM'nin 3. basamağında tüm teklifler ortak referans miktar × kendi
birim fiyatlarıyla yeniden hesaplanır (tahmin işaretli). Prosedür ve teorik/kantar tonaj
ayrımı: `poz-eslestirme-normalizasyon.md`.

**Hakkaniyet kontrolü.** "Şartnameye uygun imal edilecektir" gibi genel bir beyan varsa,
kalem bazında belirtilmemiş olsa da not edilir. **"Belirtilmemiş" ile "açıkça
hariç/reddedilmiş" farklı şeylerdir** — bu ayrım baştan sona korunur.

**İzlenebilirlik.** Her nicel değerin yanında kaynak referansı bulunur (dosya adı + sayfa
no); her veri tablosunda **"Kaynak" sütunu** açılır. Kaynağı gösterilemeyen değer ya
varsayım olarak işaretlenir ya da yazılmaz.

**Kur çevrimi.** Farklı para birimleri tek para birimine çevrilir. Kaynak **TCMB**'dir:
`https://www.tcmb.gov.tr/kurlar/today.xml` (geçmiş tarih için
`.../kurlar/YYYYMM/GGAAYYYY.xml`), varsayılan **Döviz Satış Kuru**. Kur, tarih ve tür
Excel'de **görünür ve düzenlenebilir hücrelerde** durur; tüm çevrimler ona formülle
bağlanır. **Çevrim `tutar × ForexSelling / Unit` şeklindedir.**
**İnternet erişimi yoksa kur kullanıcıdan istenir — kaynağı belirsiz veya tahmin
kur kullanılmaz.**

**Spot kur yalnız peşin ödeme için yeterlidir.** Vadeli bir döviz ödemesini spot kurla
çevirip TL iskonto oranıyla indirgemek sistematik hatadır ve **ödemeyi öteleyen döviz
teklifini haksız kazandırır**; zincirin 7. basamağında `finansal-degerlendirme.md` §1b
uygulanır (her para birimi kendi oranıyla iskonto edilir veya forward kur kullanılır).

### Adım 4 — Uygunluk değerlendirmesi (şartname varsa)

Her gereksinim × her firma için üçlü sınıflandırma:
- **UYGUN/DAHİL** — yeşil `C6EFCE`, yazı `006100`
- **KISMEN/BELİRTİLMEMİŞ** — sarı `FFEB9C`, yazı `9C6500`
- **UYGUN DEĞİL/EKSİK/HARİÇ** — kırmızı `FFC7CE`, yazı `9C0006`

Her hücreye durum + teklifteki karşılığın kısa özeti yazılır. Şartname yoksa bu adım
atlanır ve atlandığı Özet'te yazılır.

### Adım 5 — Maliyet köprüsünün kurulması

Önce `references/hesaplama-kontrolleri.md` okunur. Zinciri görünür basamaklarla kur;
her giderin tek kimliği ve tek maliyet sahibi olur. Basamaklar sunum sırasıdır:
eskalasyonlu tutar ödeme tarihine yerleştirilip iskonto edilir; ödeme planına zaten
giren fark ikinci kez eklenmez. KTM bugünkü değer, nominal nakit bütçesi ayrı toplamdır.

- **5a — Miktar düzeltmesi** (basamak 3). Ortak referans miktar × firmanın birim fiyatları.
  Götürü teklifte birim fiyat dökümü yoksa toplamı beyan miktara oranlayarak **zımni birim
  fiyat** türet ve tahmin işaretle; beyan da yoksa "miktar beyansız" işaretle ve RFI'ya yaz —
  **dayanaksız oran kullanılmaz.**
- **5b — İthalat köprüsü** (basamak 4). `ithalat-maliyet-koprusu.md` ile EXW/FOB/CIF/DAP/DDP
  teklifleri **DDP eşdeğerine** getirilir. Yurt içi ve yurt dışı teklif bu köprü kurulmadan
  aynı satıra yazılmaz. Yapım işinde ithal malzeme tedariki varsa köprü 5c'nin içinde alt
  satır olur.
- **5c — Eşit kapsam düzeltmesi, firmalar arası** (basamak 5-A). Her teklifi tam kapsama
  getiren ilave kalemler tahmin edilir. **Eksik kalem sıfır sayılmaz** — piyasa rayici/idare
  tahminiyle eklenir; hücre sarı dolgu + mavi font, dayanağı not sütununda. Şartname yoksa
  referans "ortak referans kapsam"dır (bkz. `sartname-yoksa.md`).
- **5c2 — Ortak kapsam boşluğu** (basamak 5-B). Dalın kontrol listesi
  (`is-turu-*.md` / `ekipman-*.md` / `dal-genel-mal-hizmet.md` ve
  `poz-eslestirme-normalizasyon.md` §6) tekliflerin **birleşimiyle** karşılaştırılır:
  listede olup **hiçbir** teklifte bulunmayan kalemler ayrı bir tabloya yazılır.
  Tutar, ödeme tarihi ve kapsam gerçekten aynıysa ortak satıra girer; aksi halde
  firmaya özgü düzeltmedir. Fiyatlanmamış tutar sıfırlanmaz; ÖN SONUÇ ve RFI kaydı
  açılır. Muhatap, şartnamenin kalemi isteyip istememesine göre belirlenir.
- **5d — Vergisel düzeltme** (basamak 6). **Toplama giren:** damga vergisi ve firma bazında
  farklılaşan ve alıcıda kalan SGK yükümlülükleri (satıcı fiyatına dahil SGK tekrar eklenmez; ithalatta gümrük vergisi/İGV zaten 4. basamakta).
  **Toplama giren ek kalem:** indirilemeyen KDV kısmı.
  **Toplama girmeyen, ayrı satırda duran:** indirilebilir KDV ve yapım işlerinde **KDV tevkifatı** —
  tevkifat KDV'nin kime ödendiğini değiştirir, tutarını değiştirmez; yalnız nakit akışı
  farkıdır. Ayırt edici soru her zaman "indirilebilir mi?" (`ithalat-maliyet-koprusu.md`
  §2b). **Vergisel konularda mali müşavir teyidi şarttır** — hücreler "teyit bekleniyor"
  işaretlenir. Mevzuat oranları (KDV oranı, tevkifat payı) **tarih damgasıyla** yazılır:
  "…tarihinde geçerli oran" — oran değişirse analizin hangi rejime dayandığı belli olur.
- **5e — Dengesiz teklif ve anormal fiyat analizi.** Poz bazlı min/medyan/max sapması,
  front-loading deseni, anormal düşük teklif alt sınır testi:
  `poz-eslestirme-normalizasyon.md`. **Anormal düşük teklif eleme sebebi değildir** —
  açıklama istenir (RFI) ve risk matrisine girer.
- **5f — Ömür boyu maliyet (TCO)** (basamak 8). `tco-omur-boyu-maliyet.md`. Ekipman
  enerji/bakım tüketmiyorsa basamak "uygulanmadı" işaretlenir, gerekçesi yazılır.
- **5g — Finansman düzeltmesi** (basamak 7). `finansal-degerlendirme.md`: ödeme/hakediş
  planı NBD − nominal farkı, alıcıya ait banka komisyonları; avans ve kesinti iadeleri ödeme akışında tek kez.
- **5h — Eskalasyon riski** (basamak 9). Fiyat revizyon/eskalasyon hükmü olan teklif
  **"fiyatı sabit değildir"** uyarısı alır; hükümsüz uzun süreli teklif "risk primi gömülü
  veya revizyon talebi riski var" yorumu alır. Senaryo hesabı (%0/%X/%2X) ödeme tarihine iskonto edilerek KTM'ye girer.
  Olasılıklar tanımlanmadıkça "beklenen değer" denmez; "baz senaryo" denir.

- **5i — Nakit, kalite ve stok kontrolleri.** `references/nakit-kalite-stok.md`:
  ödeme takviminden nominal tepe nakit ve tarihi; kalite kayıpları ve ilave kontrol
  giderinden kullanılabilir birim maliyeti; tekrarlayan/toplu alımda sipariş/teslim
  senaryolarının NBD ve stok karşılaştırması. Yalnız ilgili modüller kurulur.
  Kalite/stok giderlerinin benzersiz NBD katkısı uygun mevcut KTM basamağına bağlanır;
  yeni bir mükerrer toplam oluşturulmaz. Nakit ihtiyacı tutarı KTM'ye eklenmez.

Zincir sonunda her firma için **tek bir KTM** oluşur; Özet ve Puanlama sekmelerine
**formülle** bağlanır.

### Adım 6 — Elemeli kapı ve puanlama

`references/puanlama-metodolojisi.md`. **Önce teklif sayısı kontrol edilir** (Adım 0c):
tek teklifte puanlama yapılmaz — eşik değerlendirmesi konur; yedi ve üzerinde ağırlıklı
puanlama kısa listeye uygulanır. **Sıra kesindir:** önce elemeli (knock-out) kapı,
sonra ağırlıklı puanlama. Asgari şartı sağlamayan teklif puanlamaya alınmaz; tabloda
"ELENDİ" görünür ve sıralamaya girmez. Ölçülebilir kriterler formülle normalize edilir.
**Ağırlık duyarlılık tablosu zorunludur.** Şartname yoksa yalnız idari kapı uygulanır.

**Puanı sunmadan önce ayırt edici ağırlık oranı hesaplanır** (`puanlama-metodolojisi.md`
§2b): bütün tekliflere aynı puanı veren kriterlerin ağırlığı sıralamaya katkı yapmaz.
Oran Puanlama sekmesine ve Karar Özeti'ne yazılır; **%30'un altındaysa puan tablosu tek
başına karar gerekçesi olarak sunulmaz.** Duyarlılık yorumu da bu orana koşulludur —
oran düşükken "sıralama değişmedi, sonuç sağlam" cümlesi yazılmaz (§4).

### Adım 7 — Tedarikçi/yüklenici yeterliliği ve risk

`references/tedarikci-yeterlilik-risk.md`. Mali/kurumsal yeterlilik, iş bitirme ve referans
doğrulaması, imalat/şantiye kapasitesi, servis ağı ve müdahale süresi, mevcut iş yükü, alt
yüklenici yapısı, menşe/tek kaynak riski; **olasılık × etki risk matrisi**.

### Adım 8 — Sözleşmesel koşullar

`references/sozlesme-maddeleri.md`. Cezai şart oranı **ve üst limiti**, gecikmenin başlangıç
anı, süre uzatım koşulları, teminat yapısı ve çözülme takvimi, fiyat revizyonu, iş
artış-eksilişi, riskin/mülkiyetin geçişi, kabul koşulları, garanti, sorumluluk sınırlaması,
mücbir sebep tanımının genişliği, fikri mülkiyet/PLC şifresi, İSG-SGK, alt yüklenici izni,
uyuşmazlık yeri.

**Teminat, sigorta ve ceza ihtiyacını her alımda değerlendir.** Gerekiyorsa yalnız
"alınmalı/konulmalı" deme: mevcut teklif koşulu ile öneriyi ayır; neden gerekli olduğunu,
önerilen tutarı, hesap dayanağını, süreyi ve uygulama koşullarını açıkla. Ayrıntılar
`references/sozlesme-maddeleri.md` §1, §3, §10 ve "Gerekçeli önerinin rapora aktarımı"nda.
İlgili açıklamaları yazılı rapora da taşı; yalnız Excel'de bırakma. Gerekmediğinde kısa
gerekçe yeterlidir. Veri eksikse dayanaksız tutar kullanma; formül, eksik girdi ve varsa işaretli
senaryo ver. Sabit bir oranı her mal/hizmete otomatik uygulama.

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

## Sürüm ve geri bildirim

Bu skill, satınalma personelinden gelen geri bildirimlerle **sürekli geliştirilir**.
Sürüm geçmişi: `CHANGELOG.md`.

Analiz sonunda aşağıdaki geri bildirim mesajı kullanılabilir:
*"Analize ilişkin düzeltme ve geliştirme önerilerinizi Satınalma Direktörlüğüne
iletebilirsiniz."*

Geri bildirim, skill'i yürüten kişiye değil **skill sahibine** (satınalma direktörlüğü)
gider; skill kendi kendini değiştirmez, dosyaları düzenlemez.
