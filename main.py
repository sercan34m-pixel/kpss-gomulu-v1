import flet as ft
import random
import time
import threading
import re

# =============================================================================
# 1. VERİTABANI (DOSYA YERİNE KODUN İÇİNE GÖMDÜK)
# =============================================================================
# Buraya örnek soruları ekledim. APK çalıştığında burayı kendi sorularınla doldurabilirsin.
TUM_SORULAR = [
    {
        "soru": "Türkiye'nin en doğusu ile en batısı arasında kaç dakikalık zaman farkı vardır?",
        "siklar": ["A) 60", "B) 76", "C) 45", "D) 90", "E) 30"],
        "dogru": "B",
        "konu": "Coğrafi Konum",
        "aciklama": "Türkiye 26-45 doğu meridyenleri arasındadır. 45-26=19 meridyen farkı vardır. 19x4=76 dakika."
    },
    {
        "soru": "Aşağıdakilerden hangisi Türkiye'de dağların kıyıya paralel uzanmasının sonuçlarından biri değildir?",
        "siklar": ["A) Kıyı ile iç kesim arası ulaşım zordur", "B) Kıyıda yağış fazladır", "C) Ege'de girinti çıkıntı fazladır", "D) Boyuna kıyı tipi görülür", "E) Kıta sahanlığı dardır"],
        "dogru": "C",
        "konu": "Yerşekilleri ve Özellikleri",
        "aciklama": "Ege'de dağlar kıyıya dik uzanır, bu yüzden girinti çıkıntı fazladır. Paralel uzanmanın sonucu değildir."
    },
    {
        "soru": "Türkiye'de heyelan olaylarının en sık görüldüğü bölge hangisidir?",
        "siklar": ["A) Karadeniz", "B) Akdeniz", "C) Doğu Anadolu", "D) Ege", "E) İç Anadolu"],
        "dogru": "A",
        "konu": "Yerşekilleri ve Özellikleri",
        "aciklama": "Yağışın ve eğimin fazla olması, toprağın killi yapısı nedeniyle en çok Karadeniz'de görülür."
    }
]

PRATIK_BILGILER = [
    "Türkiye'nin en uzun kara sınırı Suriye iledir.",
    "Bor rezervinde dünyada 1. sıradayız.",
    "En fazla yağış alan ilimiz Rize'dir.",
    "Türkiye'nin en büyük gölü Van Gölü'dür."
]

MUFREDAT = [
    "Coğrafi Konum", "Yerşekilleri ve Özellikleri", "İklim ve Bitki Örtüsü",
    "Nüfus ve Yerleşme", "Tarım, Hayvancılık ve Ormancılık",
    "Madenler, Enerji Kaynakları", "Ulaşım, Ticaret ve Turizm", "Coğrafi Bölgeleri"
]

# --- RENK PALETİ ---
class Renk:
    bg = "#F0F4F8"; card = "#FFFFFF"; primary = "#6C5CE7"; text = "#2D3436"
    sub_text = "#636E72"; success = "#00B894"; error = "#FF7675"; bookmark = "#0984E3"
    white = "#FFFFFF"; info_bg = "#DFE6E9"

def main(page: ft.Page):
    # --- AYARLAR ---
    page.title = "KPSS AI 2026"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = Renk.bg
    
    # --- YÜKLENİYOR EKRANI (Açılışta Güvenlik) ---
    loading = ft.Container(
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text("Veriler Yükleniyor...", color=Renk.primary)
        ], alignment="center", horizontal_alignment="center"),
        alignment=ft.alignment.center, expand=True, bgcolor=Renk.bg
    )
    page.add(loading)
    page.update()
    time.sleep(1) # Kullanıcı logoyu görsün diye minik bekleme

    # --- STATE (Hafıza) ---
    # Client Storage'ı da geçici olarak iptal ediyoruz, direkt RAM kullanacağız.
    # Böylece "Hafıza okuma hatası" riskini de sıfırlıyoruz.
    state = {
        "isim": "Öğrenci", 
        "dogru": 0, 
        "cozulen": 0, 
        "kayitlar": [], 
        "stats": {k: {"d":0, "y":0} for k in MUFREDAT},
        "tum_sorular": TUM_SORULAR,  # <-- Dosyadan değil, yukarıdaki listeden alıyor
        "pratik_bilgiler": PRATIK_BILGILER,
        "cozulen_idleri": [] 
    }

    # --- EKRAN TEMİZLİĞİ ---
    page.clean()

    # --- YARDIMCILAR ---
    def uyari_goster(baslik, mesaj):
        page.open(ft.AlertDialog(title=ft.Text(baslik), content=ft.Text(mesaj), actions=[ft.TextButton("Tamam", on_click=lambda e: page.close(dlg))]))

    test_durumu = {"index": 0, "sorular": [], "aktif": False, "baslangic": 0, "toplam_sure": 0, "test_dogru": 0, "hatali_konular": [], "soru_havuzu": [], "havuz_index": 0, "telafi_modu": False, "hedef_soru_sayisi": 20, "cevaplandi": False, "gecici_sonuclar": []}

    def router(route):
        page.views.clear()
        page.bgcolor = Renk.bg
        if page.route == "/": page.views.append(view_giris())
        elif page.route == "/home": page.views.append(view_home())
        elif page.route == "/test": page.views.append(view_test())
        elif page.route == "/sonuc": page.views.append(view_sonuc())
        elif page.route == "/profil": page.views.append(view_profil())
        elif page.route == "/info": page.views.append(view_info())
        page.update()

    def tema_degis(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        router(page.route) 

    # --- EKRANLAR ---
    def view_giris():
        isim_input = ft.TextField(label="İsminiz", border_radius=15, text_align="center", bgcolor="white", color="black", width=280)
        def giris_yap(e):
            if isim_input.value: state["isim"] = isim_input.value; page.go("/home")
        
        return ft.View("/", bgcolor=Renk.bg, padding=0, controls=[
            ft.Container(expand=True, alignment=ft.alignment.center, padding=40, content=ft.Column([
                ft.Icon("map", size=60, color=Renk.primary),
                ft.Text("KPSS AI 2026", size=28, weight="bold", color=Renk.primary),
                ft.Text("COĞRAFYA", size=36, weight="heavy", color=Renk.text),
                ft.Container(height=20),
                isim_input,
                ft.ElevatedButton("BAŞLA", on_click=giris_yap, height=55, width=200, style=ft.ButtonStyle(bgcolor=Renk.primary, color=Renk.white)),
                ft.Container(height=20),
                ft.Text("Dosyasız (Gömülü) Sürüm", size=12, color="grey")
            ], alignment="center", horizontal_alignment="center", spacing=10))
        ])

    def view_home():
        basari = int((state["dogru"] / state["cozulen"]) * 100) if state["cozulen"] > 0 else 0
        
        def baslat_test(konu):
            ham_havuz = state["kayitlar"].copy() if konu == "KAYITLI" else (state["tum_sorular"] if konu == "TÜMÜ" else [s for s in state["tum_sorular"] if konu.lower() in s.get("konu", "").lower()])
            if not ham_havuz:
                page.open(ft.SnackBar(ft.Text("Bu kategoride henüz soru yok."), open=True)); return
            
            # Soru sayısı az olduğu için örneklemi küçültüyoruz (Hata almamak için)
            secilen_sayisi = min(len(ham_havuz), 5) 
            secilen_sorular = random.sample(ham_havuz, secilen_sayisi)

            test_durumu.update({"konu": konu, "aktif": True, "baslangic": time.time(), "toplam_sure": 0, "test_dogru": 0, "hatali_konular": [], "soru_havuzu": secilen_sorular, "havuz_index": 0, "hedef_soru_sayisi": len(secilen_sorular), "cevaplandi": False, "gecici_sonuclar": []})
            page.go("/test")

        grid = ft.Row(wrap=True, spacing=10, run_spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        for konu in MUFREDAT:
            kal = len([s for s in state["tum_sorular"] if konu.lower() in s.get("konu","").lower()])
            renk = Renk.primary if kal>0 else Renk.sub_text
            grid.controls.append(ft.Container(content=ft.Column([ft.Text(konu, size=11, weight="bold", text_align="center"), ft.Container(content=ft.Text(f"{kal} Soru", size=9, color="white"), bgcolor=renk, padding=5, border_radius=5)], alignment="center"), bgcolor=Renk.card, width=165, height=85, border_radius=12, on_click=lambda e, k=konu: baslat_test(k)))

        return ft.View("/home", bgcolor=Renk.bg, padding=0, controls=[
            ft.Column([
                ft.Container(height=30),
                ft.Container(padding=20, content=ft.Row([ft.Text(f"Merhaba, {state['isim']}", size=20, weight="bold"), ft.IconButton("dark_mode", on_click=tema_degis)], alignment="spaceBetween")),
                ft.Container(content=grid, padding=15),
                ft.Container(content=ft.ElevatedButton("Karışık Başlat", on_click=lambda _: baslat_test("TÜMÜ"), width=300), alignment=ft.alignment.center)
            ], scroll=ft.ScrollMode.HIDDEN)
        ])

    def view_test():
        if not test_durumu["soru_havuzu"]: return ft.View("/test", controls=[])
        index = test_durumu["havuz_index"]
        if index >= len(test_durumu["soru_havuzu"]): 
            # Test Bitti
            for sonuc in test_durumu["gecici_sonuclar"]:
                if sonuc["durum"] == "dogru": state["dogru"] += 1
                state["cozulen"] += 1
            test_durumu["aktif"] = False; page.go("/sonuc"); return ft.View("/test", controls=[])

        soru = test_durumu["soru_havuzu"][index]; test_durumu["cevaplandi"] = False
        lbl_soru = ft.Text(soru["soru"], size=18, weight="bold", text_align="center")
        
        def cevapla(e, secilen_btn_index):
            test_durumu["cevaplandi"] = True
            dogru_idx = -1
            for i, s in enumerate(soru["siklar"]):
                if soru["dogru"] in s: dogru_idx = i; break # Basit kontrol
            
            durum = "dogru" if secilen_btn_index == dogru_idx else "yanlis"
            test_durumu["gecici_sonuclar"].append({"durum": durum})
            if durum == "dogru": test_durumu["test_dogru"] += 1
            
            e.control.bgcolor = Renk.success if durum=="dogru" else Renk.error
            e.control.color = "white"
            e.control.update()
            btn_sonraki.visible = True
            btn_sonraki.update()

        btn_siklar = []
        for i, s in enumerate(soru["siklar"]):
            btn_siklar.append(ft.ElevatedButton(s, on_click=lambda e, idx=i: cevapla(e, idx), width=350))

        btn_sonraki = ft.ElevatedButton("SONRAKİ", visible=False, on_click=lambda e: (test_durumu.update({"havuz_index": index + 1}), router(None)))
        
        return ft.View("/test", bgcolor=Renk.bg, controls=[ft.SafeArea(content=ft.Column([ft.Row([ft.IconButton("close", on_click=lambda _: page.go("/home"))]), lbl_soru, *btn_siklar, btn_sonraki], scroll=ft.ScrollMode.AUTO))])

    def view_sonuc():
        return ft.View("/sonuc", bgcolor=Renk.bg, controls=[ft.SafeArea(content=ft.Column([ft.Icon("emoji_events", size=60, color=Renk.primary), ft.Text("Bitti!", size=30), ft.Text(f"Doğru: {test_durumu['test_dogru']}"), ft.ElevatedButton("Ana Sayfa", on_click=lambda _: page.go("/home"))], alignment="center", horizontal_alignment="center"))])

    def view_profil(): return ft.View("/profil", bgcolor=Renk.bg, controls=[ft.Text("Profil")])
    def view_info(): return ft.View("/info", bgcolor=Renk.bg, controls=[ft.Text("Bilgi")])

    page.on_route_change = router
    page.go("/")

if __name__ == "__main__":
    ft.app(target=main)