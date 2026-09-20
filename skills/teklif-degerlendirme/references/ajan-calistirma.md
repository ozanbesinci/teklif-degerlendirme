# Ajan Çalıştırma ve Nihai Kontrol — v3.0.1

`scripts/ajan_yonetimi.py` teklif dosyalarını yorumlayan bir motor değildir. Görevi; kaynakları ve skill sürümünü byte seviyesinde dondurmak, rol/model seçimini sabitlemek ve kanıtsız bir sonucu **FINAL** durumuna geçirmemektir.

## Sınırlar

- Çağıran rolü bir iş akışı beyanıdır; kimlik doğrulaması veya yetki kanıtı değildir.
- Dosyanın varlığı, hash'inin tutması ya da JSON biçiminde olması, Excel/PDF'in görsel veya ticari doğruluğunu kanıtlamaz.
- Kaynak dizinine yazmaz. Her koşu için açıkça belirtilmiş izole çıktı dizini kullanılır.
- `skills/.teklif-analysis.lock` ve `skills/.teklif-update.lock` paylaşılan atomik kilitlerdir. `prepare` analiz kilidini koşu boyunca korur; `close` FINAL sonrası, `close --abort` açık iptal ile kaldırır. Her mutasyon ayrıca `skills/.teklif-analysis.operation.lock` ile tekilleşir. Eski kilit kendiliğinden silinmez.

## Zorunlu akış

```powershell
python scripts/ajan_yonetimi.py prepare --source-dir "D:\Kaynaklar" --output-dir "D:\Cikti\teklif-001"
python scripts/ajan_yonetimi.py dispatch --output-dir "D:\Cikti\teklif-001" --caller-role coordinator --role extraction --prompt-file "D:\Cikti\teklif-001\extract-prompt.md"
python scripts/ajan_yonetimi.py verify --output-dir "D:\Cikti\teklif-001"
python scripts/ajan_yonetimi.py close --output-dir "D:\Cikti\teklif-001"
```

`dispatch` varsayılan olarak **dry-run**'dır: çalıştıracağı tam Codex komutunu manifestte kaydeder ama model çağırmaz. Gerçek koşu ancak açık `--run` ile yapılır. Worker çağrıları `--sandbox read-only`, izole `--cd`, belirlenmiş model/efor ve `-c agents.enabled=false` ile kurulur; bu yüzden worker yeni ajan başlatamaz. Coordinator yalnız `--caller-role controller --role coordinator` ile başlatılır ve gerekirse aynı izole dizinde `workspace-write` alır; ana çalışma alanı için genişletilmiş yazma yetkisi bu araçtan verilmez. Bu araç `--ignore-user-config`, onay atlama veya genel ayar değişikliği kullanmaz.

Yerleşik paralel alt ajanlarda üst sınır üçtür; CLI worker çağrıları senkron çalışır
ve aynı anda bir işlem kilidi alır. Toplam görev sayısı üçle sınırlı değildir.
Coordinator alt ajan aracını kullanabilir; worker çağrılarında bu araç kapalıdır.
Kritik hüküm ihtilafında `critical_adjudicator`, yalnız açık `--critical` ile çağrılır.
Sessiz tekrar deneme/fallback ve Luna rolü yoktur.

## Sabit rol politikası

| Rol | Model | Efor |
|---|---|---|
| coordinator / reviewer | gpt-5.6-sol | high |
| extraction | gpt-5.6-terra | medium |
| extraction_difficult, requirements, technical, financial, contracts | gpt-5.6-terra | high |
| classifier / classifier_complex | gpt-5.6-terra | medium |
| critical_adjudicator (koşullu) | gpt-6-astra | high |

Rol `--role` ile seçilir; serbest model veya efor değişikliği parametresi yoktur.
Eşleşmeler yalnız `config/ajan-politikasi.json` izin listesinden alınır.

## FINAL kapısı

`prepare`, kaynak envanteri (dosya yolu, SHA-256, boyut), byte-eşdeğer kopya grupları, dataset hash'i ve skill dosyaları/sürümü için snapshot üretir. Kaynak veya skill daha sonra değişirse `verify` FINAL'i bloke eder.

Üç artefakt zorunludur: `analysis_record`, `review_attestation` ve gerçek `.xlsx` çalışma kitabı (`workbook`). Rapor istenmişse ayrıca `%PDF-` başlıklı gerçek `.pdf` (`report_pdf`) zorunludur. `analysis_record` JSON'unda her olgu için `fact_id`, `claim`, `source_id`, `source_sha256`, `location`, `evidence_status` bulunur. Kritik olgular `verified` olmalı ve ayrı kontrol kaydı taşımalıdır; `unknown` veya `assumption` kritik olguyu bloke eder. `review_attestation`, Sol/high reviewer rolüyle, analizden farklı `task_id` ile; bütün kritik kanıtları, rakipleri ve eleme gerekçelerini özgün kaynaklara karşı incelediğini açıkça beyan etmelidir. Self-approval kabul edilmez.

`cikti_denetimi.py` XLSX çekirdek XML/ilişki/sayfa yapısını, formül önbelleklerini ve
hata hücrelerini kontrol eder. Yalnız PK başlığı yeterli değildir. PDF ayrıca pypdf
ile açılmalı, sayfa içermeli ve Sonuç/Öneri metni okunmalıdır. Şifreli, bozuk veya
parsersiz PDF geçmez. Bunlar görsel inceleme ve gerçek yeniden hesaplama yerine geçmez.

Sabit kontrol kimliklerinden biri `PASS` değilse FINAL kapalıdır. Sayısal mutabakat, adil karşılaştırma, teklif tazeliği/geçerliliği, maliyet tamlığı, formül yeniden hesaplama, parametre değişim testi, çıktı tutarlılığı ve görsel inceleme; reviewer'ın kanıt etiketli tasdikini zorunlu kılar. Araç bu tasdiklerin semantik doğruluğunu yeniden hesapladığını iddia etmez; yalnız kanıt/kimlik/snapshot bağı kurar. Bu zorunlu kontroller `NA` olamaz; boş kontrol listesi başarı sayılmaz.

## Çalıştırma makbuzlu tam yol

Üstteki kısa komutlar arayüz tanıtımıdır; tek bir extraction dry-run nihai analiz
üretmez. FINAL için coordinator ve reviewer'ın **başarılı gerçek CLI sonuçları**
gerekir. Koordinatör inceleme ve hesapları bitirir; son cevabı saf analysis_record
JSON'u olur. Denetçi son cevabı saf review_attestation JSON'u olur. Bu dosyaları
yeniden yazarak hash değiştirme; doğrudan `result_file` yolunu kaydet.

1. `prepare` ile kaynakları ve izole çıktı alanını sabitle.
2. Coordinator görev dosyasında ana SKILL.md'nin tam yolunu, kaynak/kapsamı, ilgili
   referansları, çıktı dosyalarını ve analysis_record sözleşmesini belirt.
   `dispatch --caller-role controller --role coordinator --prompt-file ... --run`
   ile başlat. Çalıştırıcı task_id'yi göreve kendisi ekler. Ana JSON'u üretmeden
   reviewer kimliği uydurulmaz ve nihai teslim kapısı kapatılmaz.
   Coordinator yeniden prepare yapmaz veya ortak skill kökündeki kontrol dosyalarını
   yazmaz; çalışma dizinindeki mevcut manifesti okur. Dış kontrolü yürüten oturum
   aşağıdaki record-artifact/verify/close adımlarının sahibidir.
3. Dönen coordinator `result_file` dosyasını `record-artifact --name analysis_record
   --artifact ...` ile kaydet. Üretilmiş Excel'i `--name workbook`, istenmiş PDF'i
   `--name report_pdf` ile kaydet.
4. Bağımsız reviewer görevi önce ham kaynak kontrolünü, sonra analiz/çıktı denetimini
   yürütür. `dispatch --caller-role coordinator --role reviewer --prompt-file ...
   --run` çağrısı ayrı bağlamdadır. Dönen JSON'u `--name review_attestation` olarak kaydet.
5. `verify` sonucunda FINAL_ALLOWED + çıkış 0 gerekir. BLOCKED çıkış kodu 2'dir;
   sıfır dışı çıkışı yok sayma. Teslimden sonra `close`; iptalde `close --abort`.

### Kayıt alanları

`analysis_record`: `task_id` (coordinator dispatch_id), `report_requested` (boolean),
`competitors` (tedarikçi kimlikleri), `exclusions` (eleme ve gerekçeler),
`critical_fact_ids` (boş olmayan benzersiz kritik alan listesi), `facts`.
Her fact: `fact_id`, `claim`, `evidence_status`, `critical` (boolean).
Kanıtlı fact ayrıca `source_id`, `source_sha256`, `location` taşır. Kritik fact
`evidence_status:verified` olmalıdır; belirtilmemiş/varsayım sonuçta açık kalır.

`review_attestation`: `reviewer:{role:reviewer,model:gpt-5.6-sol,
reasoning_effort:high,task_id:<reviewer dispatch_id>}`, `run_id`, `dataset_sha256`,
`analysis_sha256`, `workbook_sha256`; PDF istenmişse `report_pdf_sha256`.
Hashleri hesap/kayıt araçlarından al, LLM ile üretme. `checked_fact_ids` incelemesi
tamamlanan kritik fact kimliklerini taşır; analysis_record listesini bütünüyle kapsar.
`all_critical_evidence_reviewed`, `all_competitors_reviewed`,
`all_exclusion_reasons_reviewed` yalnız gerçekten yapılmışsa true olur.

`control_attestations` sözlüğünde sekiz zorunlu anahtar bulunur:
`numeric_reconciliation`, `fair_comparison`, `freshness_validity`, `cost_completeness`,
`formula_recalculation`, `parameter_change_test`, `output_consistency`, `visual_review`.
Her biri `{status:PASS|FAIL|UNVERIFIED,evidence:[test/dosya/konum],reviewed_by:<reviewer
dispatch_id>}` taşır. Bu yapı boş bir başarı şablonu olarak doldurulmaz; gerçek
bulgu/test sonucu olmadığında FAIL veya UNVERIFIED kullanılır.

Araç, iki model çağrısının başarılı makbuzunu ve JSON dosyalarının hashlerini
eşleştirir. Dry-run, başarısız süreç veya yalnız elle yazılmış denetçi JSON'u kapıyı
açamaz. Yerel manifestler kriptografik imzalı değildir; kötü niyetli yerel düzenlemeye
karşı güvenlik ürünü değildir. Gerçek modelin sunucu tarafı kimliği ve incelemenin
anlamsal doğruluğu yalnız komut parametresinden kanıtlanmış olmaz.

Bu sürümde yerleşik masaüstü alt ajan makbuzlarını otomatik içe aktaran uyarlayıcı
yoktur. Yerleşik araçlarla hazırlık yapılabilir; yalnız o çıktılarla CLI makbuzlu
FINAL kapısı geçti denmez. Tam mekanik teslim yolu yukarıdaki çalıştırıcıdır.

Artefakt yeniden kaydedildiğinde eski kontrol durumları silinir; `verify` yeniden
çalışmalıdır. Değişen veri/çıktı eski reviewer hash bağıyla geçemez. Düzeltmede önce
coordinator yeni analysis_record üretir, ardından bağımsız reviewer yeni sonuç verir.
