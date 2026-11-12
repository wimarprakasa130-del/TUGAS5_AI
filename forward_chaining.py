"""
Sistem Pakar - Diagnosis Masalah Kualitas Air Kolam Lele
Metode: Forward Chaining
Membaca aturan dari kb_lele.json dan menyimpulkan berdasarkan fakta dari user.
"""

import json
import sys
import os


def muat_knowledge_base(path):
    """Memuat knowledge base dari file JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def kumpulkan_fakta_dasar(aturan_list):
    """
    Mengumpulkan semua fakta dasar (fakta yang tidak pernah menjadi
    hasil/maka dari aturan manapun) untuk ditanyakan ke user.
    """
    semua_hasil = set()
    for r in aturan_list:
        semua_hasil.add(r["maka"])

    fakta_dasar = []
    sudah = set()
    for r in aturan_list:
        for syarat in r["jika"]:
            if syarat not in semua_hasil and syarat not in sudah:
                fakta_dasar.append(syarat)
                sudah.add(syarat)
    return fakta_dasar


def tanya_fakta(fakta_dasar):
    """Menanyakan fakta dasar ke user satu per satu."""
    print("\nJawab y/t untuk setiap pertanyaan.\n")
    memori = set()
    for i, fakta in enumerate(fakta_dasar, 1):
        while True:
            jawab = input(f"  {i}. Apakah {fakta}? (y/t) > ").strip().lower()
            if jawab in ("y", "t"):
                break
            print("     Masukkan 'y' atau 't'.")
        if jawab == "y":
            memori.add(fakta)
    return memori


def syarat_terpenuhi(rule, memori):
    """
    Mengecek apakah syarat aturan terpenuhi berdasarkan memori.
    mode 'dan': semua syarat harus ada di memori.
    mode 'atau': salah satu syarat cukup ada di memori.
    """
    if rule["mode"] == "dan":
        return all(s in memori for s in rule["jika"])
    elif rule["mode"] == "atau":
        return any(s in memori for s in rule["jika"])
    return False


def forward_chaining(aturan_list, memori):
    """
    Menjalankan forward chaining:
    1. Mulai dari fakta yang diketahui (memori).
    2. Cek semua aturan, jika syarat terpenuhi dan hasilnya belum ada,
       tambahkan hasilnya ke memori.
    3. Ulangi sampai tidak ada aturan baru yang bisa dijalankan.

    Mengembalikan:
    - memori: set fakta akhir
    - jejak: list of (siklus, rule_id, rule, fakta_pemicu) untuk alasan
    """
    jejak = []
    siklus = 0

    while True:
        siklus += 1
        ada_baru = False

        for rule in aturan_list:
            if rule["maka"] not in memori and syarat_terpenuhi(rule, memori):
                # Catat fakta pemicu (syarat yang ada di memori)
                if rule["mode"] == "dan":
                    pemicu = list(rule["jika"])
                else:  # atau
                    pemicu = [s for s in rule["jika"] if s in memori]

                memori.add(rule["maka"])
                jejak.append((siklus, rule["id"], rule, pemicu))
                ada_baru = True
                print(f"  Siklus {siklus}: {rule['id']} -> {rule['maka']}")

        if not ada_baru:
            print(f"  Siklus {siklus}: tidak ada aturan baru, berhenti")
            break

    return memori, jejak


def tampilkan_kesimpulan(kb, fakta_awal, memori, jejak, aturan_list):
    """Menampilkan kesimpulan beserta alasan (aturan mana yang dipakai)."""
    # Tentukan kesimpulan = fakta di memori yang merupakan hasil aturan
    semua_hasil = set(r["maka"] for r in aturan_list)
    kesimpulan = [item for item in memori if item in semua_hasil]

    print("\n" + "=" * 60)
    print(f"  KESIMPULAN")
    print("=" * 60)

    if not kesimpulan:
        print("\n  Tidak ada kesimpulan yang dapat ditarik dari fakta yang diberikan.")
    else:
        for k in kesimpulan:
            print(f"\n  >> {k.upper()}")

    # Tampilkan alasan
    if jejak:
        print("\n" + "-" * 60)
        print("  ALASAN (urutan inferensi):")
        print("-" * 60)

        # Buat dict rule_id -> sumber
        sumber_dict = {}
        for r in aturan_list:
            sumber_dict[r["id"]] = r["sumber"]

        for siklus, rule_id, rule, pemicu in jejak:
            sumber_id = sumber_dict.get(rule_id, "?")
            sumber_teks = kb["sumber"].get(sumber_id, "Tidak diketahui")
            pemicu_str = ", ".join(pemicu)
            print(f"    {rule['maka']}")
            print(f"      <- {rule_id} ({pemicu_str})")
            print(f"         Sumber: [{sumber_id}] {sumber_teks}")

    # Fakta awal
    print("\n" + "-" * 60)
    print("  FAKTA AWAL DARI USER:")
    print("-" * 60)
    if fakta_awal:
        for f in sorted(fakta_awal):
            print(f"    - {f}")
    else:
        print("    (tidak ada)")

    # Catatan batas
    print("\n" + "-" * 60)
    print("  CATATAN:")
    print("-" * 60)
    print(f"  {kb['batas']}")
    print()


def jalankan_kasus_uji(kb, kasus_fakta, nomor):
    """Menjalankan satu kasus uji otomatis (tanpa input user)."""
    aturan_list = kb["aturan"]

    print(f"\n{'#' * 60}")
    print(f"  KASUS UJI #{nomor}")
    print(f"  Fakta: {', '.join(sorted(kasus_fakta)) if kasus_fakta else '(kosong)'}")
    print(f"{'#' * 60}")

    memori = set(kasus_fakta)
    print("\n  Proses Forward Chaining:")
    memori, jejak = forward_chaining(aturan_list, memori)
    tampilkan_kesimpulan(kb, kasus_fakta, memori, jejak, aturan_list)


def mode_interaktif(kb):
    """Mode interaktif: tanya fakta ke user dan jalankan FC."""
    aturan_list = kb["aturan"]

    print("\n" + "=" * 60)
    print(f"  {kb['judul']}")
    print("=" * 60)

    # Kumpulkan dan tanyakan fakta dasar
    fakta_dasar = kumpulkan_fakta_dasar(aturan_list)
    memori = tanya_fakta(fakta_dasar)
    fakta_awal = set(memori)

    print(f"\n  Fakta awal: {', '.join(sorted(fakta_awal)) if fakta_awal else '(tidak ada)'}")
    print("\n  Proses Forward Chaining:")
    memori, jejak = forward_chaining(aturan_list, memori)
    tampilkan_kesimpulan(kb, fakta_awal, memori, jejak, aturan_list)


def mode_uji(kb):
    """Mode pengujian otomatis dengan 4 kasus uji."""
    print("\n" + "=" * 60)
    print(f"  MODE UJI OTOMATIS - {kb['judul']}")
    print("=" * 60)

    kasus_uji = daftar_kasus_uji()
    for i, kasus in enumerate(kasus_uji, 1):
        jalankan_kasus_uji(kb, kasus, i)


def daftar_kasus_uji():
    """Mengembalikan daftar kasus uji standar."""
    return [
        # Kasus 1: keracunan amonia (rantai R1 -> R2 -> R8)
        {
            "sisa pakan menumpuk di dasar kolam",
            "jarang melakukan penyiponan",
            "ikan megap-megap di permukaan",
            "nafsu makan ikan menurun",
        },
        # Kasus 2: kasus negatif - hanya 1 fakta, tidak cukup untuk kesimpulan
        {
            "ikan megap-megap di permukaan",
        },
        # Kasus 3: keracunan amonia + kekurangan oksigen + kematian massal
        {
            "air kolam berbau menyengat",
            "warna air kolam kehitaman",
            "ikan megap-megap di permukaan",
            "nafsu makan ikan menurun",
            "padat tebar ikan terlalu tinggi",
            "tidak ada aerator",
        },
        # Kasus 4: stres pH + air terlalu panas
        {
            "pH air di bawah 6",
            "ikan sering melompat",
            "suhu air di atas 32 derajat",
            "ikan berkumpul di dasar kolam",
        },
    ]


def main():
    # Tentukan path knowledge base
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(script_dir, "kb_lele.json")

    if not os.path.exists(kb_path):
        print(f"Error: File '{kb_path}' tidak ditemukan!")
        sys.exit(1)

    kb = muat_knowledge_base(kb_path)

    # Cek argumen command-line: --test N untuk kasus uji tertentu
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        nomor = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        kasus_list = daftar_kasus_uji()
        if 1 <= nomor <= len(kasus_list):
            print("\n" + "=" * 60)
            print("  SISTEM PAKAR: DIAGNOSIS MASALAH KUALITAS AIR KOLAM LELE")
            print("  Metode: Forward Chaining")
            print("=" * 60)
            jalankan_kasus_uji(kb, kasus_list[nomor - 1], nomor)
        else:
            print(f"Nomor kasus uji harus 1-{len(kasus_list)}")
            sys.exit(1)
        return

    print("\n" + "=" * 60)
    print("  SISTEM PAKAR: DIAGNOSIS MASALAH KUALITAS AIR KOLAM LELE")
    print("  Metode: Forward Chaining")
    print("=" * 60)

    # Pilih mode
    print("\n  Pilih mode:")
    print("    1. Interaktif (jawab pertanyaan)")
    print("    2. Uji otomatis (4 kasus uji)")

    while True:
        pilihan = input("\n  Masukkan pilihan (1/2): ").strip()
        if pilihan in ("1", "2"):
            break
        print("  Masukkan '1' atau '2'.")

    if pilihan == "1":
        mode_interaktif(kb)
    else:
        mode_uji(kb)


if __name__ == "__main__":
    main()

