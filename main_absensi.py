from typing import Tuple, Union
from twilio.rest import Client
from bs4 import BeautifulSoup
from pathlib import Path
from lxml import html
import configparser
import datetime
import requests
import openpyxl
import os
import re


class Notifikasi:
    def notif_wa(self, nomer_hp: str, pesan: str):
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            from_="whatsapp:+14155238886",
            body=pesan,
            to=f"whatsapp:{nomer_hp}",
        )
        # print(message.sid)


class Elearning(Notifikasi):
    URL_LOGIN = "https://e-learning.asia.ac.id/login/index.php"
    URL_HALAMAN_UTAMA = "https://e-learning.asia.ac.id/my"

    def __init__(self, nim: str, password: str, nomer_hp: str):
        super().__init__()
        self.session = requests.session()
        self.nim = nim
        self.password = password
        self.nomer_hp = nomer_hp

    def return_session(self):
        return self.session

    #########################################################
    # BLOK PROSES LOGIN KE ELEARNING
    #########################################################
    def ambil_nama_akun(self) -> Tuple[bool, Union[str, list]]:
        respon = self.session.get(self.URL_HALAMAN_UTAMA)
        tree = html.fromstring(respon.text)

        nama_akun = tree.xpath('//header[@id="page-header"]//div[@class="page-header-headings"]/h1/text()')

        if len(nama_akun) != 0:
            print("[OK] Login Berhasil")
            return True, nama_akun[0]

        else:
            print("[X] Login Gagal")
            return False, nama_akun

    def ambil_nama_matkul(self, url_matkul_hari_ini: str):
        response = self.session.get(url_matkul_hari_ini)
        tree = html.fromstring(response.text)
        nama_matkul = tree.xpath('//div[@class="page-header-headings"]/h1/text()')[0]
        format_pesan = f"Kamu aktif dihalaman *{nama_matkul}*\n\nMencoba mencari url untuk absensi..."
        super().notif_wa(self.nomer_hp, format_pesan)

    def notif_login_elearing(self, status_login: bool, hari: str, tgl: str, nama_akun: str = ""):
        if status_login:
            nama_akun = nama_akun.title()
            format_tgl = tgl.strftime("%d/%m/%Y, %H:%M:%S")
            format_pesan = f"Selamat datang *{nama_akun}* kamu berhasil login e-learning ASIA,\npada hari, tanggal dan waktu *{hari}, {format_tgl}*"

        else:
            format_pesan = "Maaf kamu belum berhasil login di e-learning ASIA, pastikan username dan password Betul Ya!"
        super().notif_wa(self.nomer_hp, format_pesan)

    def logout_elearning(self):
        response = self.session.get(self.URL_HALAMAN_UTAMA)
        tree = html.fromstring(response.text)
        url_logut = tree.xpath('//a[text()="Log out"]//@href')

        if len(url_logut) != 0:
            self.session.get(url_logut[0])
            print("[OK] Berhasil logout")

    def login_elearing(self, hari: str, tgl: str):
        payload = {
            "username": self.nim,
            "password": self.password,
            "logintoken": "",
        }

        response = self.session.get(self.URL_LOGIN)
        tree = html.fromstring(response.text)

        payload["logintoken"] = list((set(tree.xpath("//input[@name='logintoken']/@value"))))[0]

        respons = self.session.post(self.URL_LOGIN, data=payload, headers=dict(referer=self.URL_LOGIN))

        if respons.status_code == 200:
            status_login, nama_akun = self.ambil_nama_akun()
            if status_login:
                if isinstance(nama_akun, list):
                    nama_akun = nama_akun[0]
                self.notif_login_elearing(status_login, hari, tgl, nama_akun)

            else:
                self.notif_login_elearing(status_login, hari, tgl)

    #########################################################
    # BLOK PROSES EKSPLORE url ABSENSI
    #########################################################
    def mencari_semua_url_pertemuan_dimatkul(self, url_matkul_hari_ini: str) -> list:
        """Method ini akan mengambil semua data pertemuan yg dilampirkan dosen di halaman mata kuliah nya

        - Contoh hasil pengambilan data pertemuan:
            - Pertemuan 1 - Pendahuluan
            https://e-learning.asia.ac.id/mod/attendance/view.php?id=9064

            - Pertemuan 2 - Tipe data pada PHP
            https://e-learning.asia.ac.id/mod/attendance/view.php?id=9462

            - Pertemuan 3 - Struktur Kontrol dan Perulangan
            https://e-learning.asia.ac.id/mod/attendance/view.php?id=10047

            - Pertemuan 5 - Penanganan Form ($_GET dan $_POST)
            https://e-learning.asia.ac.id/mod/attendance/view.php?id=10307

            - Pertemuan 6 - Form Validasi
            https://e-learning.asia.ac.id/mod/attendance/view.php?id=10560

            - Pertemuan 7 - QUIS dan Penentuan Kelompok Hackathon
            https://e-learning.asia.ac.id/mod/attendance/view.php?id=10854
        """
        response = self.session.get(url_matkul_hari_ini)
        tree = html.fromstring(response.text)

        list_url_absensi = list()
        list_judul_pertemuan = list()

        print("[...] Mencari url absensi")
        for element in tree.xpath('//ul[@class="topics"]/li'):
            id_attrib_pesan_perpertemuan = element.attrib["aria-labelledby"]
            judul_pertemuan = element.xpath(f'//*[@id="{id_attrib_pesan_perpertemuan}"]//a/text()')[0]

            list_url_tiap_pertemuan = element.xpath('.//ul[@class="section img-text"]/li[@class="activity attendance modtype_attendance "]//a/@href')
            if len(list_url_tiap_pertemuan) != 0:
                list_url_absensi.append(list_url_tiap_pertemuan[0])
                list_judul_pertemuan.append(judul_pertemuan)

        # mencoba menacri absensi yg aktif di 2 pertemuan terakhir
        # jika absensi tidak ditemukan keluar
        list_url_absensi.reverse()
        list_judul_pertemuan.reverse()
        if len(list_url_absensi) != 0:
            for idx, url_absensi in enumerate(list_url_absensi):
                if idx == 2:
                    format_pesan = "Notifikasi pencarian url untuk absensi sudah mencapai batas, *program ini tetap berjalan dilatar belakang*, jika waktu telah sampai *jam 23:59* maka program akan menghapus data sekarang dan fokus melakukan pencarian absensi untuk esok hari!"
                    self.notif_wa(self.nomer_hp, format_pesan)
                    break

                status = self.mencari_url_untuk_submit_absensi(url_absensi, list_judul_pertemuan[idx])

                if status != None:
                    break

    def mencari_url_untuk_submit_absensi(self, url_absensi: str, judul_pertemuan: str) -> Union[bool, None]:
        """Method untuk mencari url yg aktif untuk melakukan absensi

        - Contoh jika di pertemuan 1 terdapat kata:
            "Submit attendance"
            maka disana terdapat nilai url yg valid untuk absensi
        """
        response = self.session.get(url_absensi)
        tree = html.fromstring(response.text)

        # mencari tag terdapat kata Submit attendance dan mengambil url submit kehadiran
        url_submit_kehadiran = tree.xpath('//*[text()="Submit attendance"]//parent::a/@href')
        if len(url_submit_kehadiran) != 0:
            format_pesan = f"Url absensi dipertemuan *{judul_pertemuan}*\n*Ditemukan!* mencoba mencari metode absensi..."
            self.notif_wa(self.nomer_hp, format_pesan)
            status = self.cek_metode_absensi(url_submit_kehadiran, url_absensi)
            return status

        else:
            format_pesan = f"Url absensi dipertemuan *{judul_pertemuan}*\n*Tidak ditemukan!*"
            self.notif_wa(self.nomer_hp, format_pesan)
            return None

    def cek_metode_absensi(self, list_url_sumbit: list, url_absensi: str, password: str = None) -> bool:
        """Method untuk melakukan pengecekan apakah metode absensi menggunakan,
        password atau tidak"""
        header = {
            "Host": "e-learning.asia.ac.id",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://e-learning.asia.ac.id",
            "Alt-Used": "e-learning.asia.ac.id",
            "Connection": "keep-alive",
        }

        for url_submit in list_url_sumbit:
            # melakuan regex untuk megambil nilai
            #  sessid dan sesskey pada url submit
            sessid_value, sesskey_value = re.findall(fr"sessid=(.+)&sesskey=(.+)", url_submit)[0]
            response = self.session.get(url_submit)
            tree = html.fromstring(response.text)

            # mencari input password di halaman absensi
            is_absensi_menggunakan_password = tree.xpath('//*[@id="id_studentpassword"]')

            # mencari tag label yg memiliki tag span dg kata Present,
            # kemudian naik ke tag input untuk mengambil nilai attribute value
            for kata_kehadiran in ["Present", "Hadir"]:
                status_value = tree.xpath(f'//label//span[text()="{kata_kehadiran}"]//preceding::input[1]/@value')
                if len(status_value) != 0:
                    status_value = status_value

                    # jika attribute id id_studentpassword ditemukan
                    # maka absensi membutuhkan password
                    if len(is_absensi_menggunakan_password) != 0:
                        payload = [
                            ("sessid", sessid_value),
                            ("sesskey", sesskey_value),
                            ("sesskey", sesskey_value),
                            ("studentpassword", "1234"),
                            ("_qf__mod_attendance_student_attendance_form", "1"),
                            ("mform_isexpanded_id_session", "1"),
                            ("status", status_value),
                            ("submitbutton", "Save changes"),
                        ]
                        self.session.post(url_submit, headers=header, data=payload)

                        format_pesan = "Metode absensi menggunakan password, mencoba absensi menggunakan password..."
                        self.notif_wa(self.nomer_hp, format_pesan)

                        format_pesan = f"Horaa... telah berhasil melakukan absensi,\nLebih lanjut {url_absensi}"
                        self.notif_wa(self.nomer_hp, format_pesan)
                        return True

                    else:
                        payload = [
                            ("sessid", sessid_value),
                            ("sesskey", sesskey_value),
                            ("sesskey", sesskey_value),
                            ("_qf__mod_attendance_student_attendance_form", "1"),
                            ("mform_isexpanded_id_session", "1"),
                            ("status", status_value),
                            ("submitbutton", "Save changes"),
                        ]
                        print(status_value)
                        print(url_submit)
                        self.session.post(url_submit, headers=header, data=payload)

                        format_pesan = "Metode absensi tidak menggunakan password, mencoba untuk absensi..."
                        super().notif_wa(self.nomer_hp, format_pesan)

                        format_pesan = f"Horaa... telah berhasil melakukan absensi,\nLebih lanjut {url_absensi}"
                        super().notif_wa(self.nomer_hp, format_pesan)
                        return True
            print("Tidak ditemukan kata Present atau Hadir saat mau submit,cek ulang kata kehadiran dan informasikan ke admin untuk memperbaharui!")
            return None


class JadwalMataKuliah(Elearning):
    def __init__(self, nim: str, password: str, nomer_hp: str, jadwal_file: str):
        super().__init__(nim, password, nomer_hp)
        self.session = self.return_session()
        self.jadwal_file = Path(jadwal_file)
        self.nomer_hp = nomer_hp
        self.tgl_sekarang = datetime.datetime.today()
        self.hari_ini = datetime.datetime.today().strftime("%A")

    def return_session(self):
        return super().return_session()

    def logout_elearning(self):
        return super().logout_elearning()

    def login_elearing(self, hari: str, tgl: str):
        return super().login_elearing(hari, tgl)

    def mencari_semua_url_pertemuan_dimatkul(self, url_matkul_hari_ini: str) -> list:
        return super().mencari_semua_url_pertemuan_dimatkul(url_matkul_hari_ini)

    def baca_matkul_hari_ini(self):
        wb = openpyxl.load_workbook(filename=self.jadwal_file, read_only=True)
        ws = wb.active

        try:
            self.login_elearing(self.hari_ini, self.tgl_sekarang)
            if self.hari_ini == "Monday":
                list_url_matkul = ["https://e-learning.asia.ac.id/course/view.php?id=341"]
                for url_matkul in list_url_matkul:
                    self.ambil_nama_matkul(url_matkul)
                    self.mencari_semua_url_pertemuan_dimatkul(url_matkul)

            elif self.hari_ini == "Tuesday":
                list_url_matkul = ["", ""]
                for url_matkul in list_url_matkul:
                    self.ambil_nama_matkul(url_matkul)
                    self.mencari_semua_url_pertemuan_dimatkul(url_matkul)

            elif self.hari_ini == "Wednesday":
                list_url_matkul = ["https://e-learning.asia.ac.id/course/view.php?id=341"]
                for url_matkul in list_url_matkul:
                    self.ambil_nama_matkul(url_matkul)
                    self.mencari_semua_url_pertemuan_dimatkul(url_matkul)

            elif self.hari_ini == "Thursday":
                list_url_matkul = ["https://e-learning.asia.ac.id/course/view.php?id=374"]

                for url_matkul in list_url_matkul:
                    self.ambil_nama_matkul(url_matkul)
                    self.mencari_semua_url_pertemuan_dimatkul(url_matkul)

            elif self.hari_ini == "Friday":
                list_url_matkul = ["", ""]
                for url_matkul in list_url_matkul:
                    self.ambil_nama_matkul(url_matkul)
                    self.mencari_semua_url_pertemuan_dimatkul(url_matkul)
        except Exception as e:
            print("error", e)
            self.logout_elearning()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("settings.ini")

    nim = config["AKUN_ELEARNING"]["nim"]
    password = config["AKUN_ELEARNING"]["password"]
    nomer_hp = config["NOMER_HP"]["nomer_hp"]
    jadwal_file = config["JADWAL_FILE"]["file"]

    absen = JadwalMataKuliah(nim, password, nomer_hp, jadwal_file)
    absen.baca_matkul_hari_ini()
    absen.logout_elearning()
