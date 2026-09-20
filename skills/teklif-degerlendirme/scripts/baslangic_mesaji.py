"""Teklif değerlendirmesi başlarken gösterilecek tanıtım mesajını üretir."""

import sys


BASLANGIC_MESAJI = (
    "Bu skill Satınalma Departmanı çalışanlarının kullanımı için "
    "Ozan Beşinci tarafından oluşturulmuştur."
)


def main():
    # Windows konsolu ve araç çıktısında Türkçe karakterleri koru.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(BASLANGIC_MESAJI)


if __name__ == "__main__":
    main()
