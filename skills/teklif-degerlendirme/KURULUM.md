# Kurulum ve dağıtım — ana skill v4.0.0 / güncelleyici v1.1.0

Bu kaynak **yerel canlı test adayıdır**. Dosyadaki sürüm numarası GitHub'da
yayımlandığı veya canlı kabul testinin geçtiği anlamına gelmez.
Resmî dağıtım deposu:
[ozanbesinci/teklif-degerlendirme](https://github.com/ozanbesinci/teklif-degerlendirme).

## Paket

İki skill birlikte kurulur; `VERSION` dosyaları bağımsızdır:
ana skill 4.0.0, güncelleyici 1.1.0. Paket manifesti şema 2'dir;
`skill_versions` iki sürümü, `version` paket etiketini taşır.

```text
skills/
  teklif-degerlendirme/
    SKILL.md
    VERSION
    requirements.txt
    config/
    references/
    scripts/
  teklif-degerlendirme-guncelle/
    SKILL.md
    VERSION
    scripts/
```

Paketin çalışma modülleri ve requirements.txt eksik/boşsa v4 kurulumu reddedilir;
`ajan_yonetimi.py` girişine ek olarak `ajan_v4.py` ve `kayit_temeli.py` de
zorunlu modül listesine dahildir.
Yalnız metadata/sürüm dosyası içeren bir arşiv çalışan eski ağacın yerine geçemez.
Kaynak depo ZIP'i, doğrulanmış dağıtım ZIP'iyle aynı kurulum biçimi sayılmaz.

## Gereksinimler

- Windows, yerel Codex masaüstü / ChatGPT Work, model/efor seçebilen yerleşik alt ajanlar.
- Çalıştırılarak doğrulanmış Python **3.14**; Store kısayolu yeterli değildir.
- `requirements.txt` içindeki tam sürümler: openpyxl, pypdf, pdfplumber,
  pypdfium2 ve pywin32. Sürüm kaynağı `program-guncelle` paket listesidir.
- Masaüstü Microsoft Excel; Python + pywin32 ile görünmez bağımsız örnekte gerçek
  yeniden hesaplama ve temiz kapanış.
- Gerçek güncel araç kataloğunda erişilebilir Sol ve Terra aileleri, rollerin medium/high
  eforları. Her yeni analiz erişilebilir en yeni aile sürümünü çözer. Luna yoktur.
- Gerçek oturum JSONL kayıtlarına, model/efora ve token sayaçlarına erişim.

Python/kütüphane eksikliği `program-guncelle` işidir. Python kurucusu veya wheel
dosyaları teklif paketine gömülmez; bu skill ikinci pip/winget kurulum yolu açmaz.
Katalog, efor, Excel veya telemetri yoksa “tam doğrulanmış v4” denmez.

## İlk kurulum ve güncelleme

Komutların güncel kaynağı `../teklif-degerlendirme-guncelle/SKILL.md` ve
`scripts/guncelle.py --help` çıktısıdır.

```text
python "<guncelle.py>" check --root "<fiziksel-skills>"
python "<guncelle.py>" install --root "<fiziksel-skills>" --archive "<paket.zip>" --sha256 "<64-karakter-hash>"
python "<guncelle.py>" verify --root "<fiziksel-skills>"
```

“Sürümü kontrol et” yalnız okuma; “kur/güncelle” iki yönetilen skill ağacını yenileme
yetkisidir. Normal çevrimiçi güncelleme resmî kararlı Release'i kullanır. Geliştirme
yetkisiyle doğrulanmış yerel aday aynı install yolundan kurulabilir; henüz
yayımlanmamış sürümü GitHub'dan indirmeye çalışma.

Paket doğrulanmadan mevcut kurulum değiştirilmez. İki ağaç dosyalar üst üste
eklenmeden tamamen değiştirilir; işlem hatasında önceki ağaçlar geri konur.
Windows geçici kilitleri sınırlı yeniden denemeye tabidir; kalıcı hata gizlenmez.
İki ağaç tek atomik dosya değildir; işlem günlüğü, kurtarma ve kilit kontrolleri atlanmaz.

Yönetimsiz/değiştirilmiş eski kurulum otomatik silinmez. `register` yalnız paketle
birebir eşleşen kaynak kurulumunu yönetilen envantere alır. Açık geliştirme kapsamındaki
aynı sürüm adayını yenilemek için `install --replace-local` mevcut kurallarıyla
kullanılabilir; normal update buna başvurmaz. Yayımlanmış sürüm içeriği değiştirilmez.

Ortak fiziksel skill kökü ve mevcut junction düzeni korunur. Başka skill'ler, global
model/ajan ayarları ve kullanıcı dosyaları değiştirilmez. Yeni skill sonraki turda
keşfedilir; kullanıcıya görünmesi başarılı analiz koşusunun kanıtı değildir.

## Analizi başlatma

1. Personel ana sohbet için güncel Sol veya Terra ailesini seçer; efor tercihi kendisinindir.
2. `$teklif-degerlendirme` ile kaynak dosyaları/klasörü verir.
3. Skill envanter ve öneriyi gösterir; personel hızlı, standart veya yüksek güvence seçer.
4. Gerçek katalog ve ana oturum sayacıyla `prepare` değişmez koşu kopyasını oluşturur.
5. Sonraki işlemler manifestin `runner` yoluyla yürür. `task` yalnız görev kaydıdır;
   model yerleşik alt ajan aracıyla açık model/efor kullanılarak çağrılır.
6. Gerçek model/efor makbuzları, kod QA, bağımsız kaynak okuma, hakem, karar özeti
   ve Excel kontrolü tamamlandığında `verify` / `close` çalışır.

Komut yaşam döngüsü: `references/ajan-calistirma.md`.
Model talimatını yazmak aktif sohbet modelini değiştirmez. CLI model yürütme veya
oturum devamıyla düzeltme kullanılmaz. Tam sohbet her alt ajana aktarılmaz.

Hazırlanmış analiz sabit kopyasından yürür; sonraki ortak kurulum değişikliği bu
kopyayı değiştirmez. Güncelleme kilidinde yeni snapshot alınmaz. Eski global analiz
kilidi veya yarım işlem kilidi otomatik silinmez. Kaynak değişirse yeni revizyon koşusu gerekir.

## Yerel kontrol ve canlı kabul

- Her bileşenin VERSION, SKILL metadata ve CHANGELOG'u eşleşmelidir.
- Hesap örnekleri, merkezi veri, model çözümü, oturum kanıtı, bütçe, Excel ve
  güncelleme testleri çalıştırılır. Sadece başlık/metin eşleşmesi yeterli değildir.
- Gerçek Excel yeniden hesaplama, bağımsız motor mutabakatı ve parametreyi geri alma
  testi, formül XML'ine cache yazmaktan farklıdır; fiilen çalıştırılmalıdır.
- Gerçek kullanıcı verili canlı kabul ayrı kayıttır. Hızlı: 8M/25 dk; standart:
  25M/60 dk; yüksek güvence: 50M/120 dk. Bunlar tavan, süre tahmini değildir.
- Kabulte kaynak bulguları, açık konular, doğru son birikimli sayaçlar ve süre kaydedilir.
  Sentetik birim testleri gerçek model davranışı veya tasarruf oranı kanıtlamaz.
- Kullanıcı bu aday için canlı veriyi verecektir. Kabul tamamlanmadan personele
  yaygınlaştırılmaz; GitHub yayını ayrıca yetki ister.

## Paket hazırlama ve yayın

`scripts/paket_olustur.py` yalnız iki skill'in izinli kaynak dosyalarını alır.
Çıktı skill ağacının dışında olmalıdır. requirements.txt pakete girer; şirket
teklifleri, fiyatlar, raporlar, sohbet/oturum/hafıza, kimlik bilgileri ve gerçek test
verileri girmez. Paket hash'i bütünlüğü doğrular; bağımsız yayıncı imzası değildir.

Yalnız güncelleyici değişirse `--release-version` ile paket etiketi ilerletilebilir;
ana skill zorla artırılmaz. Release etiketi ve paket version alanı aynı olmalıdır.
Yerel kurulum, commit/push/tag/Release/yükleme yetkisi değildir. Kullanıcı yayın
talep etmeden yayın yapılmaz; yerel durum ile yayımlanmış durum ayrı raporlanır.

Eski ortak 3.0.1 güncelleyici şema 2'yi okuyamaz. Böyle bir kurulumdan ilk geçiş
yeni güncelleyicinin doğrulanmış kaynak kopyasıyla yapılır; eski script'in yeni
şemayı desteklediği varsayılmaz.

v4 bu ortam için tasarlanır; Claude Teams ve diğer web istemcileri doğrulanmış
çalışma kapsamı dışındadır. İş kılavuzlarını okuyabilmeleri aynı model/araç/Excel
doğrulama yeteneğine sahip olduklarını göstermez.
