# Automasi-absensi-elearning
Alat untuk mempermudah absensi di elearning Asia https://e-learning.asia.ac.id/

## Fitur kedepan 
- [ ] Logging 
- [ ] Membaca jadwal mata kuliah lewat file .xlsx
- [ ] Multi threading untuk penyesuaian absensi mata kuliah yg berbeda jam

## Installasi Kebutuhan
```
# Console mode
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```
## Installasi Twilio
Buat akun baru di [twilio](https://www.twilio.com/try-twilio)<br>
Ikuti langkah-langkah mengaktifkan fitur pesan untuk [WhatsApp](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn?frameUrl=%2Fconsole%2Fsms%2Fwhatsapp%2Flearn%3Fx-target-region%3Dus1)<br>
Salin nilai <b>Account SID</b> dan <b>Auth token</b> [API keys & tokens](https://console.twilio.com/us1/account/keys-credentials/api-keys?frameUrl=%2Fconsole%2Fproject%2Fapi-keys%3F__override_layout__%3Dembed%26bifrost%3Dtrue%26x-target-region%3Dus1)<br>
Masuk di file <b>twilio.env</b> dan pastekan nilai <b>Account SID</b> dan <b>Auth token</b> di dalam nya
```
export TWILIO_ACCOUNT_SID=''
export TWILIO_AUTH_TOKEN=''

# Console mode
# Kemudian jalankan perintah di bawah
source ./twilio.env
```

## Installasi settings.ini
Masuk kedalam file <b>settings.ini</b> dan isi data secara benar<br>
Pastikan tidak menambahkan tanda <b>petik (',")</b> saat megisi data
```
[AKUN_ELEARNING]
nim = 1921234
password = password

[NOMER_HP]
nomer_hp = +6282123

[JADWAL_FILE]
file = ./jadwal_kuliah.xlsx

```

## Cara menggunakan
```
# Console mode
python main_absensi.py
```

## Setelah Dijalankan
#### Console mode
![alt test](https://github.com/HAKN1999/automasi-absensi-elearning/blob/master/images/1.png)

#### WhatsApp mode
![alt test](https://github.com/HAKN1999/automasi-absensi-elearning/blob/master/images/2.jpg)
