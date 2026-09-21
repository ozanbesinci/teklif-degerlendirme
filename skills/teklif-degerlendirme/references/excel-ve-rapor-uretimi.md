# Excel ve Rapor Üretimi — Sekme Seti, Biçim Kuralları, Platform Notları

Bu skill kendi Excel/rapor kurallarını taşır; başka bir skill'e veya ortama özgü bir araca
bağımlı değildir.

---

## 1. Sekme seti (Adım 9)

**Sekme seti dala, kapsama, şartnamenin varlığına ve teklif sayısına göre
daraltılır/genişletilir. Uygulanmayan sekme oluşturulmaz ama Özet'te "uygulanmadı —
gerekçe" olarak belirtilir.**

**Teklif sayısına göre düşen sekmeler** (bkz. `teklif-sayisi-modlari.md`):
tek teklifte Puanlama Matrisi, Ağırlık Duyarlılığı, Poz Bazlı Birim Fiyat ve Eşit Kapsam
Senaryosu'nun firmalar arası kısmı kurulmaz — Özet'te "TEK TEKLİF — REKABET YOK" uyarısı
ve pazarlık gündemi durur. İki teklifte Poz Bazlı Birim Fiyat sekmesi medyan/sapma yerine
**fark tablosu** olarak kurulur. Yedi ve üzeri teklifte kısa liste dışındaki teklifler
Özet'te tek satır olarak durur (firma, KTM, kapsam durumu, kısa listeye alınmama gerekçesi).

| Sekme | İçerik | Koşul |
|---|---|---|
| Özet Karşılaştırma | dosya envanteri (hangi dosyadan ne okundu), teklif kimliği (no/tarih/revizyon/geçerlilik), teklif tipi, Incoterms, kapsanan ana gruplar/adetler, **Maliyet Köprüsü Zinciri tablosu** (basamak × firma, formülle bağlı), KTM satırı, **KRİTİK UYARI kutusu**, renk lejantı | her zaman |
| Karar Özeti | puan/sıra/KTM/kapsam satırları (formül bağlantılı), **KIRMIZI ÇİZGİLER** listesi, sorumlu + zamanlı yol haritası (zeyilname → RFI → revize teklif → puan güncelleme → pazarlık/fabrika-referans ziyareti → sözleşme), SONUÇ paragrafı | her zaman |
| Elemeli Değerlendirme | idari ve (varsa) asgari teknik şartlar × firma; GEÇTİ/ELENDİ/EKSİK BİLGİ + gerekçe + verbatim alıntı | her zaman |
| Puanlama Matrisi | kriter × ağırlık % × puan × gerekçe; ağırlık ve öznel puan hücreleri **mavi font + sarı dolgu**, ölçülebilir kriterler formülle; `=SUM(ağırlıklar)`=100 kontrolü ve `=SUMPRODUCT(...)/100`. Kriter 2, ortak 5-B hariç bütün tahmini giderlerin brüt NBD payına bağlanır (`puanlama-metodolojisi.md` §3); KTM'ye parasallaşan konu ikinci kez puanlanmaz (`puanlama-metodolojisi.md` → Çifte sayım yasağı). **Sütun başlıklarında ölçek yazılır** ("Puan (0-10)", "Toplam (0-10)"); seçilen normalizasyon yöntemi ve fiyat yayılımı (`MAKS/MIN − 1`) sekmeye not düşülür. **AYIRT EDİCİ AĞIRLIK ORANI sekmenin altına zorunlu olarak yazılır** (`puanlama-metodolojisi.md` §2b): kaç ağırlık puanı bütün tekliflere aynı puanı veriyor, sıralamayı fiilen hangi kriterler belirliyor. Oran %30'un altındaysa "puan tablosu tek başına karar gerekçesi değildir" uyarısı kalın yazılır | her zaman |
| Ağırlık Duyarlılığı | ≥3 ağırlık senaryosu × firma sırası; her senaryoda `=SUM(ağırlıklar)`=100 görünür. Sonuç yorumu **ayırt edici orana koşulludur** (`puanlama-metodolojisi.md` §4): oran <%60 iken sınırlı ayrışma belirtilir; hiçbir durumda matematiksel olarak sıra değişemez denmez. Kur/eskalasyon senaryosu sıralamayı değiştiriyorsa burada da | her zaman |
| Fiyat Detayı | firma bazlı kalem tabloları: miktar × birim fiyat, `=B*C` tutar, `=SUM` toplam; iskonto/opsiyon ayrı satır; kur hücreleri (kur, tarih, tür) sayfanın üstünde düzenlenebilir girdi | her zaman |
| Eşit Kapsam Senaryosu | **iki ayrı blok:** (a) basamak 5-A firmalar arası ilave kalemler — **sıralamayı değiştirebilir, vurgula**; (b) basamak 5-B ortak kapsam boşluğu — hiçbir firmanın fiyatlamadığı kalemler, aynı tutar ve ödeme tarihi teyitliyse ortak maliyet; *"KTM maliyet sırası korunur, toplam puan sırası değişebilir"* etiketiyle, muhatabı şartnameye göre. Blok (b)'nin toplamı Özet'teki KTM parametresine **formülle** bağlanır (tek kaynak); rayiç yoksa tutar boş/FİYATLANMADI kalır; bilinen ara toplam nihai KTM olarak sunulmaz. Ayrıca işe uygun birim maliyet metriği (₺/kg çelik, ₺/m² kapalı alan, ₺/m³ beton, $/adet, $/ton kapasite, $/kW, ₺/kg ambalaj, ₺/kişi-vardiya) | her zaman |
| Ticari Koşullar ve Finansman | ödeme/hakediş planları, avans oranı ve avans teminatı, teminat kesintileri, ödeme planı NBD'si, teminat/akreditif komisyonları, geçerlilik, ceza, damga vergisi, KDV tevkifatı; **NAKİT AKIŞI YORUMU** kutusu. Sayfanın üstünde **para birimi başına ayrı iskonto oranı hücresi** (`i_TL`, `i_EUR`, `i_USD`) ve kullanılan yöntemin adı; vadeli döviz ödemesi TL oranına bağlanmaz (`finansal-degerlendirme.md` §1b) | her zaman |
| Nakit İhtiyacı | tarih bazlı nominal ödeme/giriş; tek dönem ve birikimli tepe, tepe tarihi; varsa tahsisli nakde göre finansman açığı/limit. KDV mahsubu gerçek nakit girişi sayılmaz; KTM'ye tepe tutar eklenmez (`nakit-kalite-stok.md` §1) | ödeme takvimi varsa; eksikse kısmi/hesaplanamadı kaydı |
| Kalite Maliyeti | kusurlu/yeniden işlenen/iade/ikame miktar dengesi, ilave kontrol ve hata giderleri, teyitli tazminler, kullanılabilir birim maliyeti; benzersiz giderler KTM'ye bağlanır (`nakit-kalite-stok.md` §2) | kalite kaybı maliyet/karar açısından anlamlıysa |
| Sipariş ve Stok | ortak tüketim için toplu/kademeli teslim seçenekleri; stok dengesi, sipariş/teslim sayısı, MOQ/kapasite/raf ömrü, depolama, nominal bütçe ve NBD; nakit tepe bağlantısı (`nakit-kalite-stok.md` §3) | tekrarlayan tüketim veya toplu alım seçeneği varsa |
| Sözleşme Maddeleri | madde × firma; riskli maddeler kırmızı; eskalasyon, iş artışı, PLC şifresi, otomatik yenileme ayrı vurgulu | her zaman |
| Uymayan Noktalar | **muhatap** × uygunsuzluk × önem (KRİTİK/YÜKSEK/ORTA/DÜŞÜK renk kodlu) × istenen neydi × etki. Muhatap yalnız firma değildir: **TÜM FİRMALAR** (hepsinde ortak eksiklik) ve **İDARE** (şartnamenin/keşif cetvelinin kendi eksikliği — basamak 5-B kalemleri, tanımsız teknik parametreler, teyit edilmemiş revizyon) ayrı satırlardır. Firma kusuru olmayan bir eksikliği firma satırına yazmak, yanlış tarafa yüklenmiş bir bulgudur | her zaman |
| Yeterlilik ve Risk | mali/kurumsal veriler, iş bitirmeler, referanslar, ekipman parkı/servis ağı, olasılık × etki risk matrisi | her zaman |
| İstenecek Bilgiler (RFI) | muhatap (her firma + TÜM FİRMALAR + İDARE) × istenecek netleştirme × öncelik; şartname yoksa **taslak şartname maddeleri** bu sekmenin altına | her zaman |
| Şartname Uygunluğu | gereksinim × şartname değeri × firma hücreleri (Adım 4 matrisi), renk kodlu, Kaynak sütunu | **yalnız şartname/gereksinim listesi varsa** |
| Teknik Detay | parametre × [Şartname \| Firma1 \| Firma2 …] + dala özgü nicel kıyas. Tasarım farkı yorumu: konservatif ↔ optimize; nihai değerlerin **onaylı hesap/veri sayfasıyla teyidi şartı** | teknik veri varsa |
| Miktar/Metraj Mutabakatı | ana poz veya ekipman × [Keşif/İdare \| Firma1 \| Firma2 …], fark %, ortak referans, teorik/kantar esası satırı + **teyitli kantar/net miktar katsayısı** düzenlenebilir hücrede (otomatik %3-7 artış uygulanmaz, `poz-eslestirme-normalizasyon.md` §3) | miktar farkı varsa |
| Poz Bazlı Birim Fiyat | ana poz × firma birim fiyatları, min/medyan/max, medyandan sapma % (koşullu renk), dengesiz teklif ve anormal düşük fiyat flag'leri | kalem bazlı teklif varsa |
| İthalat Maliyet Köprüsü | Incoterms basamakları × firma; oran/tutar hücreleri düzenlenebilir | ithal/farklı Incoterms |
| Ömür Boyu Maliyet (TCO) | yıllık kalemler, iskonto tablosu, NBD, KTM'ye katkı, başabaş süresi. Üstte **üç görünür hücre**: `r_nominal`, `π` (enflasyon) ve formülle kurulmuş `r_reel` (`=(1+r_nom)/(1+π)-1`); iskonto satırının başlığında hangi cinsin kullanıldığı yazılı, ayrıca **π duyarlılık satırı** (`tco-omur-boyu-maliyet.md` §3a) | TCO devrede |
| Değişim Kaydı | firma × değişen kalem × v1 × v2 × KTM etkisi × sıralama etkisi; cevaplanmayan RFI maddeleri | v2+ sürümlerde |

---

## 2. Excel biçim kuralları (openpyxl)

**Yazı ve düzen**
- Yazı tipi **Arial**; başlıklar kalın, kurumsal lacivert `1F3864` üzerine beyaz yazı.
- Sütun genişlikleri içeriğe göre; uzun metinlerde `wrap_text=True` ve satır yüksekliği.
- Sayı biçimi: para `#,##0.00`, yüzde `0.0%`, tarih `dd.mm.yyyy`. Sayıyı **metin olarak
  yazma** — Türkçe Excel yerelinde biçim kendisi uyar.
- İlk satır dondurulur (`freeze_panes`), geniş tablolarda ilk sütun da.

**Renk sözlüğü (tüm sekmelerde aynı)**

| Anlam | Dolgu | Yazı |
|---|---|---|
| UYGUN / DAHİL | `C6EFCE` | `006100` |
| KISMEN / BELİRTİLMEMİŞ | `FFEB9C` | `9C6500` |
| UYGUN DEĞİL / EKSİK / HARİÇ | `FFC7CE` | `9C0006` |
| Düzenlenebilir girdi veya varsayım | `FFEB9C` (sarı) | mavi `0000FF` |

Her sekmede veya en az Özet'te **renk lejantı** bulunur.

**Formül zorunluluğu**
- Hesaplanabilen hiçbir değer sabit yazılmaz: tutar `=B5*C5`, toplam `=SUM(...)`,
  puan `=SUMPRODUCT(...)/100`, kur çevrimi `=D5*$B$2`.
- Kur, iskonto oranı, ağırlık, vergi oranı gibi parametreler **tek bir hücrede** tanımlanır;
  her yer ona referans verir — kullanıcı parametreyi değiştirince tüm analiz güncellenir.
  **Bu skill'in en çok işe yarayan özelliği budur:** rapor değil, oynanabilir bir model.
- **Sıfır formül hatası hedefi:** `#REF!`, `#DIV/0!`, `#VALUE!` kalmayacak. `IFERROR` ile
  gizleme yapma — payda boşsa o satırı hiç kurma; gizlenen hata yanlış sonuca güven üretir.

---

## 3. Bilinen tuzaklar ve çözümleri

**Formül değerleri boş görünüyor.** openpyxl formülü yazar, **değerini yazmaz**. Excel
dosyayı açınca kendi hesaplar (kullanıcı sorun görmez), ama önizleme, PDF'e dökme veya
`load_workbook(data_only=True)` ile geri okuma **boş** görür. Gerekiyorsa değeri Python'da
hesapla ve xlsx zip'i içindeki sheet XML'ine `<f>...</f>` sonrasına `<v>değer</v>` enjekte
et (formüller korunur, önizleme dolu görünür):

```
regex: (<c r="KOORD"[^>]*>)(<f>[^<]*</f>)(<v>[^<]*</v>)?(</c>)
```

Lambda içinde `v=val` ile **erken bağla** — geç bağlanırsa tüm hücrelere son değer yazılır.

**Sheet–dosya eşleme.** XLSX içindeki `xl/workbook.xml` sheet `r:id` kaydı,
`xl/_rels/workbook.xml.rels` üzerinden gerçek worksheet yoluna çözülür. Sekme sırası,
dosya numarası veya benzersiz olduğu sanılan formül metniyle eşleme yapılmaz.

**Formül argüman ayrıcısı her zaman virgül.** Türkçe Excel ekranda noktalı virgül
gösterir, ama xlsx biçiminde formüller **virgülle** saklanır. openpyxl ne yazdıysan onu
dosyaya koyar; `=SUMPRODUCT(C5:C15;D5:D15)` yazarsan Excel formülü okuyamaz ve hücre
bozuk görünür. Kural: **kodda daima virgül** (`=SUMPRODUCT(C5:C15,D5:D15)/100`) —
ondalık ayırıcı ise sayı hücrelerinde nokta olarak yazılır, görünüm biçimle ayarlanır.

**MergedCell hatası.** Birleştirilmiş alana yazarken önce `merge_cells`, sonra **yalnız
sol-üst hücreye** değer yaz. Satır döngüsünde bölüm satırlarını ayrı işle.

**Dosya kilidi.** Hedef dosya açıksa veya bulut istemcisi kilitlediyse yazma
"Permission denied" verir. `_v2`, `_v3` adıyla kaydet ve kullanıcıya bildir.

**Türkçe karakter ve kodlama**
- CSV yazarken **`utf-8-sig` + noktalı virgül** ayırıcı; ikisi birlikte olmazsa Excel bozuk
  gösterir.
- Türkçe büyük/küçük harf: `İ`/`ı` dönüşümü `lower()`/`casefold()` ile beklenmedik sonuç
  verir; dosya adı/başlık eşlemesinde karakter bazında kontrol et.

---

## 3b. PDF ve tablo çıkarım tuzakları

**Çok sayfalı keşif/metraj tablosu (BoQ).** Tablo başlıkları **yalnızca ilk sayfada**
olabilir; sayfa geçişlerinde sütun hizalaması kayar. Her sayfanın **satır toplamlarını ara
toplamlarla** doğrula; genel toplam firmanın beyanıyla tutmuyorsa tabloyu görselden oku.

**Yatay (landscape) ve dar sütunlu tablolar.** `extract_table()` varsayılanı hücreleri
birleştirir; `table_settings` ile çizgi bazlı (`"vertical_strategy": "lines"`) dene,
olmazsa sayfayı görsele çevirip oku.

**Bozuk rakam boşlukları.** `6 65.000,00` = 665.000. Yorumlanan her rakam firmanın kendi
**beyan ettiği TOPLAM** ile çapraz doğrulanır.

**Kur kaynağı (TCMB).** `today.xml` içinde her `<Currency>` düğümünde `ForexSelling`
(döviz satış) ve `ForexBuying` alanları vardır; `CurrencyCode="USD"`, `"EUR"` ile filtrele.
**Dönüşüm `tutar × ForexSelling / Unit` olur**; Unit göz ardı edilirse 100 JPY
gibi kurlar 100 kat hata üretir. **Kur tarihi kök öğenin `Date` özniteliğinden** alınır. Hafta sonu/tatilde o günün dosyası
yoktur (bir önceki iş günü yayımlanır); geçmiş tarih:
`https://www.tcmb.gov.tr/kurlar/YYYYMM/GGAAYYYY.xml`.
**İnternet erişimi yoksa kuru kullanıcıdan iste** — tahmin edilen kur kullanılmaz.

---

## 4. Doğrulama (Excel yazıldıktan sonra)

Ana `SKILL.md` Adım 11'deki listeye ek mekanik kontroller:
1. Hesap içeren sekmelerde hesaplar formüllü mü? Envanter/RFI gibi yalnız metin
   sekmelerine yapay formül konmaz. Formül sayısı tek başına doğruluk kanıtı değildir.
2. Tüm sekmelerde bozuk karakter (`�`) taraması.
3. `=SUM(ağırlıklar)` = 100 — her duyarlılık senaryosu için de.
4. Çapraz referanslar (Özet ↔ Puanlama ↔ Fiyat Detayı) gerçekten `=SheetAdı!Hücre` mi,
   kopya sabit mi.
5. Renk kodlaması sözlükle tutuyor mu.
6. Excel/LibreOffice gibi hesap motoruyla yeniden hesapla; formül önbelleği ve
   bağımsız hesap sonuçlarını karşılaştır. Elle XML değer önbelleği doldurmak formül
   çalıştırma testi değildir. Hesap motoru yoksa bu sınır açıkça yazılır.
7. Bir kur, miktar, vade ve ağırlık değişikliğiyle yeniden hesaplama denemesi yap;
   ilgili KTM, fiyat puanı ve sıralama beklenen yönde güncellenmeli. Eksik/elenen
   satırlar MIN/MAX referansına girmemeli. `hesaplama-kontrolleri.md` de uygulanır.

---

## 5. Yazılı rapor üretimi

**Yol:** Markdown (`.md`) → HTML → PDF (veya uygun araçla doğrudan PDF).
**Nihai rapor teslimi PDF'tir.** Markdown yalnız geçici çalışma dosyasıdır; PDF
doğrulandıktan sonra silinir. Kullanıcının ayrıca "PDF de ver" demesi gerekmez —
**rapor istendiyse PDF de istenmiş sayılır.**

**Uzunluk ve içerik:** sabit sayfa hedefi yoktur. Teklifin içeriği, mal/hizmetin durumu,
karmaşıklığı ve riskine göre kısa veya ayrıntılı rapor üret. Basit alımda özet, kritik
farklar, kaynaklar ve sonuç yeterli olabilir; karmaşık işte hesap ve gerekçeleri genişlet.
Ana skill'deki bölüm listesi seçilerek/birleştirilerek kullanılır; ilgisiz bölümler
uzatılmaz. Teminat, sigorta veya ceza gerekiyorsa `sozlesme-maddeleri.md` uyarınca
mevcut koşul, önerilen tutar/limit/oran, hesap dayanağı, süre ve gerekçeler PDF'te
ayrıntılı yer alır. Gerekmediğinde kısa gerekçe; veri yoksa eksik girdi/formül ve
işaretli senaryo gösterilir. Önemli hesaplar yalnız silinecek Markdown'da bırakılmaz.

**HTML biçimi:** A4, sayfa numarası, kurumsal lacivert (`1F3864`) başlıklar, renk kodlu
tablolar, Arial. Unicode alt/üst simgeyi m²/m³ dışında kullanma — dönüştürücüde kaybolur.

**PDF dönüştürme — sırayla dene.** İlk üç basamak hazırlanan HTML'i olduğu gibi basar,
biçim korunur; 4. basamak düzeni sıfırdan kurar, bu yüzden en sonda.
1. Yerel Windows'ta **Edge headless** — ek kurulum gerekmez, ilk tercih:
   `msedge.exe --headless --disable-gpu --print-to-pdf="…\rapor.pdf" "file:///…/rapor.html"`
   (yol: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`).
   **Sayfa numarası uyarısı:** Edge sayfa numarasını yalnız kendi başlık/altlığında basar,
   o altlıkta dosya yolu da görünür. `--no-pdf-header-footer` yolu gizler ama numarayı da
   götürür — Chromium CSS `@page` sayfa sayacını desteklemez. Kurumsal dağıtımda numara
   şartsa 2. basamağı (weasyprint, `@page` sayacını destekler) kullan; şart değilse
   `--no-pdf-header-footer` ile temiz çıktı al.
2. `weasyprint` kuruluysa onu kullan (bulut kod ortamlarında genelde kurulabilir:
   `pip install weasyprint`).
3. `pandoc` varsa `pandoc rapor.md -o rapor.pdf` (PDF motoru eksikse HTML üzerinden
   `--pdf-engine=wkhtmltopdf`).
4. `reportlab` varsa doğrudan PDF üret — **tablo düzeni kabalaşır**, yalnız yukarıdakiler
   yoksa kullan. Geniş tabloları yatay (landscape) sayfaya al veya böl; hiçbir veriyi kırpma.
5. Hiçbiri olmazsa **HTML + Markdown teslim et**, PDF'in **üretilemediğini ve nedenini
   açıkça yaz**, "tarayıcıda aç → Yazdır → PDF olarak kaydet" adımını ver.
   **Sessizce PDF üretmiş gibi davranma.**

**Üretimden sonra doğrula (zorunlu):** PDF diskte var mı, boyutu 0 byte'tan büyük mü,
sayfa sayısı makul mü, son bölüm ("Sonuç ve Öneri") PDF'in içinde mi. Edge headless
dönüştürme bittiğini bildirmeden dosyayı bırakabilir — boyut kontrolü bu yüzden
zorunludur. Ayrıca sayfaları görsel olarak kontrol et: tablolar/metin kesilmemiş,
Türkçe karakterler okunur, gereken teminat/sigorta/ceza hesap ve açıklamaları eksiksiz
olmalı. Doğrulanmamış PDF teslim edilmiş sayılmaz (`SKILL.md` Adım 11/18).

**Doğrulamadan sonra Markdown temizliği (zorunlu):** yalnız bu raporu üretirken
oluşturduğun ara `.md` dosyasının tam yolunu kullanarak sil ve artık mevcut olmadığını
kontrol et. Çıktı/geçici çalışma alanındaki bilinen dosyayı hedefle; joker karakterli
veya klasör çapında silme yapma. Kaynak teklifler, kullanıcıdan gelen Markdown,
skill/referans dosyaları ve vault notları bu temizliğe dahil değildir. PDF üretimi
veya doğrulaması başarısızsa ara dosyayı koru, eksikliği bildir; düzeltip PDF'i
doğruladıktan sonra sil. Son teslim bağlantısında PDF'i (ve üretilen Excel'i) sun,
silinmiş `.md` bağlantısı verme. Sonraki revizyon için kaynaklar/Excel korunur.

**Maskeleme.** Rapor firma dışına veya geniş bir dağıtım listesine gidecekse firma
adlarının maskelenmesini öner (Firma A/B/C); uygulanırsa eşleştirme anahtarı **ayrı bir
sayfada** verilir.

---

## 6. Platform notları (çalıştığın ortama göre)

| İş | Claude (web/masaüstü, Teams) | ChatGPT (web, Business) | Yerel CLI (Claude Code / Codex) |
|---|---|---|---|
| Dosya girişi | sohbete veya projeye yüklenir | sohbete veya projeye yüklenir | klasörden okunur |
| Kod çalıştırma | var (Linux kod ortamı) | var (Python sandbox, Linux) | yerel Python (Windows) |
| Paket kurma | `pip install …` (gerekirse `--break-system-packages`) | **internet yok** — kurulu paketlerle çalış (`pandas`, `openpyxl`, `numpy`, PDF için mevcut olanı dene) | `python -m pip install …` |
| İnternet / TCMB kuru | genelde yok → **kullanıcıdan kur iste** | yok → **kullanıcıdan kur iste** | var → XML'den çek |
| PDF metni okunamıyorsa | sayfayı görsel olarak oku (vision) | sayfayı görsel olarak oku (vision) | `pymupdf` ile PNG + görsel oku |
| Çıktı teslimi | dosya indirme bağlantısı olarak sun | dosya indirme bağlantısı olarak sun | diske yaz, yolu bildir |
| Uzun şartnameyi bölme | alt-ajan yok → kendin parçala, ara özet tut | alt-ajan yok → kendin parçala | Claude Code'da alt-ajan kullanılabilir |
| Soru sorma | sohbette sor | sohbette sor | Claude Code'da `AskUserQuestion`, Codex'te düz metin |

**Ortak kurallar (her platformda)**
- Ara dosyalar (çıkarılan `.txt`, PNG'ler) geçici çalışma alanına yazılır; ana bağlama
  uzun metin dökülmez.
- **Kaynak dosyalar salt-okunur kabul edilir:** kullanıcının yüklediği/klasördeki dosya
  değiştirilmez, silinmez, yeniden adlandırılmaz. Çıktı yeni dosyadır.
- Yerel çalışmada çıktı, kullanıcının söylediği klasöre; söylemediyse kaynak klasörün
  yanındaki `analiz/` altına yazılır.
- `python3` yerine `python` çağır (bazı Windows kurulumlarında `python3` çalışmayan bir
  kısayoldur).

---

## 7. Dosya adlandırma ve sürümleme

- `<PROJE>_Teklif_Karsilastirma.xlsx`
- `<PROJE>_Teklif_Degerlendirme_Raporu.pdf` — raporun nihai dosyası; aynı adlı ara `.md` doğrulama sonrası silinir.
- Revize tekliflerden sonra `..._v2.xlsx` (Değişim Kaydı sekmesi zorunlu)
- Proje adında Türkçe karakter ve boşluk yerine ASCII ve alt çizgi kullan.
