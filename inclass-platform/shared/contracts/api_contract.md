# API Contract (Phase 1)

Bu dosya, ekip ici ortak ve denetlenebilir API sozlesmesidir.
Kaynak dokuman: `TermProject_InClass_Phase1` (API Contract bolumu).

## Sozlesme Onceligi

- Esas kontrol noktasi: `app/services.py` icindeki fonksiyon adlari ve parametre sirasi.
- Instructor testleri bu fonksiyonlari direkt cagiracagi icin imzalar birebir korunmalidir.
- Imza uyumsuzlugu her endpoint icin ceza yaratir; isim, tip ve parametre sirasi degistirilmez.

## Global Kurallar

- Token/JWT/cookie yoktur.
- Korumali cagrilarda `email` ve `password` her istekte dogrulanir.
- Aktivite kapandiktan sonra hicbir kosulda yeni skor loglanamaz.
- Skor, ogrenme hedefi yakalandigi anda anlik kaydedilir.

## Service Layer Fonksiyon Imzalari (Exact)

```python
# Student auth APIs

def studentLogin(email: str, password: str) -> dict: ...


# Student password APIs

def changeStudentPassword(email: str, password: str, new_password: str, old_password: str) -> dict: ...
def setStudentPassword(email: str, password: str) -> dict: ...
# Not: setStudentPassword sadece ogrencinin DB'de sifresi yoksa (first run) calisir.


# Main student APIs

def getActivity(email: str, password: str, course_id: str, activity_no: int) -> dict: ...
def logScore(
    email: str,
    password: str,
    course_id: str,
    activity_no: int,
    score: float,
    meta: str | None = None,
) -> dict: ...


# Instructor auth APIs

def instructorLogin(email: str, password: str) -> dict: ...


# Instructor password APIs

def changeInstructorPassword(email: str, password: str, old_password: str, new_password: str) -> dict: ...
def setInstructorPassword(email: str, password: str | None = None) -> dict: ...
# Not: setInstructorPassword sadece instructor'un DB'de sifresi yoksa (first run) calisir.


# Main instructor APIs

def listMyCourses(email: str, password: str) -> dict: ...
def listActivities(email: str, password: str, course_id: str) -> dict: ...
def createActivity(
    email: str,
    password: str,
    course_id: str,
    activity_text: str,
    learning_objectives: list[str],
    activity_no_optional: int | None = None,
) -> dict[str, object]: ...
def updateActivity(email: str, password: str, course_id: str, activity_no: int, patch: dict) -> dict: ...
def startActivity(email: str, password: str, course_id: str, activity_no: int) -> dict: ...
def endActivity(email: str, password: str, course_id: str, activity_no: int) -> dict: ...


# Reporting / reset APIs

def exportScores(email: str, password: str, course_id: str, activity_no: int) -> dict: ...
def resetActivity(email: str, password: str, course_id: str, activity_no: int) -> dict: ...
def resetStudentPassword(
    email: str,
    password: str,
    course_id: str,
    student_email: str,
    new_password: str,
) -> dict: ...
```

## HTTP Route Eslesmeleri (`app/main.py`)

- `POST /student/login` -> `studentLogin`
- `POST /student/change-password` -> `changeStudentPassword`
- `POST /student/set-password` -> `setStudentPassword`
- `POST /student/get-activity` -> `getActivity`
- `POST /student/log-score` -> `logScore`
- `POST /instructor/login` -> `instructorLogin`
- `POST /instructor/change-password` -> `changeInstructorPassword`
- `POST /instructor/set-password` -> `setInstructorPassword`
- `POST /instructor/list-my-courses` -> `listMyCourses`
- `POST /instructor/list-activities` -> `listActivities`
- `POST /instructor/create-activity` -> `createActivity`
- `POST /instructor/update-activity` -> `updateActivity`
- `POST /instructor/start-activity` -> `startActivity`
- `POST /instructor/end-activity` -> `endActivity`
- `POST /instructor/export-scores` -> `exportScores`
- `POST /instructor/reset-activity` -> `resetActivity`
- `POST /instructor/reset-student-password` -> `resetStudentPassword`

## Fonksiyon Bazli Kisa Aciklamalar

- `studentLogin`: Ogrenci kimlik bilgilerini dogrular.
- `changeStudentPassword`: Ogrencinin mevcut sifresini yeni sifre ile degistirir.
- `setStudentPassword`: Ilk kurulumda (sifre yoksa) ogrenci sifresini tanimlar.
- `getActivity`: Ogrenciye yalnizca uygun durumda aktivite icerigini dondurur.
- `logScore`: Aktivite acikken puani ve istege bagli metayi kaydeder.
- `instructorLogin`: Instructor kimlik bilgilerini dogrular.
- `changeInstructorPassword`: Instructor sifresini degistirir.
- `setInstructorPassword`: Ilk kurulumda instructor sifresini tanimlar.
- `listMyCourses`: Instructor'a ait dersleri listeler.
- `listActivities`: Dersin aktivitelerini listeler.
- `createActivity`: Yeni aktivite ve ogrenme hedeflerini olusturur.
- `updateActivity`: Aktivite icerigini/hedeflerini patch ile gunceller.
- `startActivity`: Aktiviteyi ACTIVE duruma getirir.
- `endActivity`: Aktiviteyi kapatir; ogrenci erisimi ve yeni skor kaydi sonlanir.
- `exportScores`: Aktivite skorlarini CSV ureterek disa aktarir.
- `resetActivity`: Aktiviteye ait skor kayitlarini sifirlar/temizler.
- `resetStudentPassword`: Instructor yetkisiyle ogrenci sifresini resetler.

## Uygulama Notu

Kod degisikligi yaparken once bu dosyayi ve `app/services.py` imzalarini kontrol edin.
Imzalarda en kucuk bir sapma bile test uyumsuzluguna neden olabilir.
