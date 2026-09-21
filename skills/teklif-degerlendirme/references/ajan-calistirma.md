# Çalıştırıcı ve teslim kapıları — v3.1.1

`scripts/ajan_yonetimi.py` belge yorumlamaz. Kaynak, rol/model, kanıt ve çıktı
bağlarını kaydeder. Makbuz kriptografik imza veya anlamsal doğruluk kanıtı değildir.

## Hazırlık ve tek koordinatör

Önce `preflight --source-dir <kaynak> --output-dir <çalışma> --run` kaynak metnini
modele vermeden gerçek Codex/model/ağ erişimini sınar ve geçici makbuz yolu döndürür.
`prepare --source-dir <kaynak> --output-dir <çalışma> --preflight-receipt <makbuz>`
kaynakları dondurur. Erişim yoksa hedef dizin ve manifest oluşturulmaz. Ticari sır için
ikinci bir onay kapısı değildir; yalnız platformun zorunlu dış erişim iznini erkene alır.
`--source-list <JSON>` isteğe bağlı, benzersiz göreli dosya listesi alır. Varsayılan
tarama `analiz/`, gizli/çıktı klasörleri ve geçici dosyaları dışlar. Çalışma alanı
`analiz/.work/<koşu>` olabilir. Yeni belgeyi mevcut koşuya sessiz ekleme; revizyon hazırla.

Manifestteki `runner` sonraki komutların yoludur: koşunun değişmez `skill-snapshot/`
kopyası. Kurulu skill güncellense de bu koşu eski sürümü kullanır. Kilitler çalışma
alanındadır; farklı projeler birbirini engellemez. Eski kilidi körlemesine silme.

Mevcut ana ajan Sol/high ise kendisi koordinatördür. Sonuç dosyasında `task_id`
gerçek oturum kimliği olsun. Önce uygun modelde sonucu kabul eden mühür komutunu
çalıştır; bu araç çıktısı oturum günlüğüne geldikten sonra ayrı çağrıyla kaydet:

```text
python <runner> seal-result --output-dir <çalışma> --role coordinator --phase work --artifact <analysis_record.json>
python <runner> register-session --output-dir <çalışma> --role coordinator --phase work --session-log <gerçek-jsonl> --artifact <analysis_record.json>
```

Adaptör bu run/rol/aşama/dosya karmasına ait mühür araç çıktısı anındaki model/eforu,
oturum kimliğini, çalışma dizinini ve log önek karmasını okur. Sonradan yalnız model
değiştirmek önceki sonucu doğrulamaz; uygun model sonucu gerçekten inceleyip kabul
etmelidir. Mühür düşünce kökenini kanıtlamaz, kabul anını bağlar.
Model adını elle yazmak yeterli değildir; log yoksa kimlik uydurma. Yerel kaydı
sunucu tarafı kimlik imzası diye sunma. Uygun oturum yoksa bir CLI koordinatörü
açılabilir; dış yönetici yalnız dar çalıştırma/kayıt işi yapar, analizi tekrarlamaz.

## CLI ve bekleme

`dispatch --caller-role controller --role coordinator --prompt-file <görev> --run`
gerçek koşudur; `--run` yoksa dry-run. Diğer rolleri `--caller-role coordinator`
başlatır. Model/efor politikadan gelir; Luna ve sessiz fallback yok. Görev yalnız
ilgili kaynak/referansları taşır; tam sohbeti devretme.

Her mantıksal görevin sabit `task_id` değeri vardır; devam turunda yalnız deneme
`dispatch_id` değeri değişir. Tamamlanan coordinator sonucu otomatik
`analysis_record`, reviewer compare/revision sonucu otomatik `review_attestation`
olarak kaydedilir. Elle mühür/kayıt yalnız yerleşik oturum yolunda gerekir.

Çalıştırıcı `--json` olaylarını model dışında bekler; başlangıcı hemen, bitiş/hata,
süre/kullanımı sonuçta kaydeder. Boş terminal sorgusuyla modeli her 30 saniyede
uyandırma; tek deterministik beklemede topla, anlamlı olay/bitiş/engeli döndür.
Kullanıcıya ilerleme bildirimini mevcut olaylardan yap; CPU'dan sonuç çıkarma.

Manifest yazma çakışmasında kod en çok 30 saniye bekler. Biten görevin terminal
makbuzu önce `dispatches/<id>/receipt.json` içine yazılır. Manifest kaydı kesildiyse
`recover-dispatch --output-dir <çalışma> --dispatch-id <id>` bu yerel makbuz ve
artefakt karmasını denetleyip kaydı tamamlar; modeli yeniden çağırmaz. Makbuz yoksa
çalışıyor/bitti varsayımıyla kilit veya RUNNING kaydı silinmez.

İsteğe bağlı `--timeout-seconds` CLI sürecine sınır koyar. Zaman aşımı tam sonuç
değildir; alt görevlerin de durduğunu doğrulamadan temiz kapanış iddia etme. Token
bütçesini kullanıcı/ortam belirlemediyse uydurma; kayıtları fatura/kotaya dönüştürme.
Politikadaki varsayılan üst sınırlar güvenlik freni olarak uygulanır; kullanıcı daha
dar sınır koyabilir. Ctrl+C alt süreci sonlandırır ve manifest güncellenemese bile
terminal makbuzunu kurtarma için yazar.

Son model cevabı küçük `{artifact_path, artifact_sha256}` işaretçisidir. Tam
analysis/review kaydı artefakta bir kez yazılır. `result-schema.json` yalnız biçimi denetler.

## Denetçinin iki aşaması ve revizyon

1. `--role reviewer --phase blind`: yalnız ham kaynaklar, objektif gereksinimler
   ve kapsam. Ana sonuç, beklenen durum veya puan verilmez. Koordinatörle paralel
   başlayabilir. Denetçi yalnız kendi `reviews/` alt alanına yazar.
2. `--resume-task <kör-görev-id> --phase compare`: aynı denetçi şimdi analiz,
   hesap, bütün rakip/elemeler ve gerçek çıktıyla karşılaştırır; kör not değişmez.
3. Düzeltmede koordinatör/denetçi kendi oturumlarında `--resume-task` ile sürer;
   denetçi `--phase revision` kullanır. Bu ikinci kör inceleme değildir.

Compare/revision başlamadan `pre-review-qa` otomatik tazelenir. Rapor analiz ve çalışma
kitabı hash'lerine bağlıdır; bozuk Unicode, eksik kaynak konumu, formül/önbellek,
etiketli SHA-256 veya kırık yerel dosya bağlantısı kusurunda model turu açılmaz.

`--resume-task` yalnız CLI görevleri içindir. Yerleşik ajan mevcut platform
oturumunda devam eder ve yeni sonucu mühürleyip kaydeder; CLI'ye dönüştürülmez.

Yerleşik denetçi her aşamada önce `seal-result` çalıştırır; araç çıktısı günlüğe
geldikten sonra notunu `register-session --role reviewer --phase blind`, sonra
gerçek oturum kimliği task_id olan tasdikini `--phase compare` ile kaydeder.
Koordinatör ve denetçi kimlikleri farklıdır. Önceki kör kaydın varlığı/değişmezliği
denetlenir; bu, istemin tarafsızlığının tek başına semantik kanıtı değildir.

## Veri ve kontrol sözleşmesi

`analysis_record`: `task_id`, `analysis_mode`, `decision_status`, `report_requested`, `competitors`, `exclusions`,
`critical_fact_ids` (benzersiz, boş olmayan), `facts`. Her fact: `fact_id`, `claim`,
`evidence_status`, `critical`. Kanıtlı olguda `source_id`, `source_sha256`, `location`.
Kritik bilinmeyende **critical:true** ve anlamlı `open_issue` zorunlu; kritiklik azaltılmaz.
Ön sonuç ayrıca `analysis_mode:preliminary`, `decision_status:awaiting_supplier_input`,
`recommendation:null` taşır.
Nihai sonuç açıkça `analysis_mode:final`, `decision_status:ready` taşır; ön sonuç
bütün kontroller PASS olsa dahi kendiliğinden nihai karara dönüşmez.

`review_attestation`: `reviewer:{role,model,reasoning_effort,task_id}`, `run_id`,
`dataset_sha256`, `analysis_sha256`, `workbook_sha256`; istenmişse `report_pdf_sha256`.
`checked_fact_ids` kritik belirsizlikler dahil bütün kritik kimlikleri kapsar.
`all_critical_evidence_reviewed`, `all_competitors_reviewed`,
`all_exclusion_reasons_reviewed` yalnız gerçekten yapıldıysa true olur.

`control_attestations`: `numeric_reconciliation`, `fair_comparison`,
`freshness_validity`, `cost_completeness`, `formula_recalculation`,
`parameter_change_test`, `output_consistency`, `visual_review`.
Her biri `{status:PASS|FAIL|UNVERIFIED|NA,evidence:[...],reviewed_by:<task_id>}`;
PASS dışındaki durum için anlamlı `reason` gerekir. UNVERIFIED hatalı tasdik
değildir; boş kontrol başarı değildir. Zorunlu nihai kontrol NA olamaz.

`record-artifact --name analysis_record|review_attestation|workbook|report_pdf
--artifact <dosya>` gerçek dosyayı kaydeder. Aynı hash kontrolü silmez. Değişen
artefakt son tasdiki geçersizleştirir. `status.revalidation.changed_fact_ids`
etkilenen olguları gösterir; bunlar ve bağımlı sonuçlar tekrar denetlenir.
Değişmeyen kaynak tekrar çıkarılmaz; yeni dosya hash'ine yeni denetçi tasdiki bağlanır.

## Teslim ve kapanış

- `verify`: kaynak/snapshot/çıktı/oturum/tasdik bağlarını denetler.
- `FINAL_ALLOWED`: açık final/ready modu ve bütün zorunlu kontroller PASS; `close` → `FINAL_COMPLETE`.
- `PRELIMINARY_ALLOWED`: kalite ve bağımsız inceleme PASS; yalnız maliyet tamlığı
  veya kritik konunun çözümü gerekçeli UNVERIFIED olabilir. Firma önerisi yok;
  `close --preliminary` → `PRELIMINARY_COMPLETE`.
- `BLOCKED`: doğrulanmış teslim değildir. `close --abort --reason ...` yalnız
  iptaldir; `CANCELLED` olarak saklanır. Eksik tedarikçi bilgisi iptal sayılmaz.

Çalışan CLI görevi varken teslim veya iptal kapanışı yapılamaz; önce görev sonlanmalıdır.

Mekanik kontrol, gerçek Excel yeniden hesaplama/parametre değişimi ve görsel inceleme
yerine geçmez. Dayanak: [OpenAI non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).
