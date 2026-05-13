# FRONTEND_INTEGRATION.md

## 1) Backend Base Info
- Base URL (local): `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Content-Type: `application/json`

## 2) Global Response Contract (ÇOK ÖNEMLİ)
Tüm endpointler normalize response döner:

### Success
```json
{
  "ok": true,
  "data": { ... }
}
```

### Failure
```json
{
  "ok": false,
  "error": "error_code"
}
```

### Validation Failure (FastAPI)
HTTP status `422` döner:
```json
{
  "detail": [ ... ]
}
```

Not: Business hatalarının büyük kısmı `200` + `ok:false` olarak gelir. UI bunu özellikle handle etmelidir.

---

## 3) Auth Model (Current)
Backend şu an token/JWT yerine request body içinde `email` + `password` bekliyor.
Frontend tarafı her protected request’te bu alanları göndermelidir.

Öneri:
- Session store:
  - `email`
  - `password`
  - `role` (`student` / `instructor`)  
- Logout’ta bunları temizleyin.

---

## 4) Endpoint Listesi

## Student Endpoints

### `POST /student/login`
Request:
```json
{
  "email": "student5@test.com",
  "password": "1234567"
}
```
Success:
```json
{
  "ok": true,
  "data": {}
}
```
Fail:
```json
{
  "ok": false,
  "error": "operation_failed"
}
```

---

### `POST /student/change-password`
Request:
```json
{
  "email": "student5@test.com",
  "password": "1234567",
  "new_password": "newpass",
  "old_password": "1234567"
}
```
Possible error codes:
- `invalid_credentials`
- `forbidden_role`
- `old_password_mismatch`
- `user_id_missing`

---

### `POST /student/get-activity`
Request:
```json
{
  "email": "student5@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1
}
```
Success `data.activity`:
```json
{
  "course_id": "...",
  "activity_no": 1,
  "text": "activity text",
  "learning_objectives": ["..."],
  "status": "ACTIVE"
}
```
Possible error codes:
- `invalid_credentials`
- `forbidden_role`
- `user_id_missing`
- `course_access_denied`
- `activity_not_found`
- `activity_not_active`

UI kuralı:
- Student’a activity text göster.
- Learning objectives UI’da öğrenciye göstermeme kararı ürün tasarımına bağlı; backend döndürüyor.

---

### `POST /student/log-score`
Genelde tutoring akışı bunu dolaylı çağırır; direkt UI’den manuel çağırmanız şart değil.

Request:
```json
{
  "email": "student5@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1,
  "score": 1,
  "meta": "Objective text"
}
```
Success `data` alanı (özet):
- `score_log` (inserted row veya `null`)
- `score_added` (`1` veya `0`)
- `duplicate_objective` (`true/false`)
- `current_score`
- `activity_completed`
- `completed_objectives`
- `total_objectives`

Önemli davranışlar:
- Aynı objective tekrar geldiyse `ok:true` + `score_added:0` + `duplicate_objective:true`
- Tüm objective’ler bitmişse yeni score engellenir: `ok:false`, `error:"activity_completed"`

Possible error codes:
- `invalid_credentials`
- `forbidden_role`
- `user_identity_missing`
- `course_access_denied`
- `activity_not_found`
- `activity_not_active`
- `invalid_score`
- `activity_completed`
- `objective_not_found`
- `score_log_insert_failed`

---

### `POST /student/tutor-chat`
Request:
```json
{
  "email": "student5@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1,
  "message": "Student answer",
  "progress_context": null
}
```
Success `data` yapısı:
- `response` (assistant text)
- `apicall` (string, boş olabilir)
- `data.parsed` (LLM parse bilgisi)
- `data.tool_result` (logScore sonucu varsa burada)
- `data.mini_lesson` (score_added>0 olduğunda gelebilir)

Önemli tutoring davranışı:
- Activity tamamlandıysa akış otomatik kapanır (completion message, `apicall:""`).
- Score trigger olduğunda mini-lesson eklenir.

Possible error codes:
- `invalid_credentials`
- `user_id_missing`
- `course_access_denied`
- `activity_not_found`
- `activity_not_active`
- `llm_call_failed: ...`
- `prompt_load_failed: ...`

---

## Instructor Endpoints

### `POST /instructor/login`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567"
}
```
Fail genelde:
- `operation_failed`

---

### `POST /instructor/list-courses`
### `POST /instructor/list-my-courses` (alias)
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "any-string-required-by-schema"
}
```
Not: `course_id` schema gereği required ama service bu endpointte kullanmıyor.
Frontend sabit placeholder geçebilir.

Success:
```json
{
  "ok": true,
  "data": {
    "courses": [ ... ]
  }
}
```
Possible error codes:
- `invalid_credentials`
- `forbidden_role`
- `user_id_missing`

---

### `POST /instructor/list-activities`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222"
}
```
Success:
```json
{
  "ok": true,
  "data": {
    "activities": [
      {
        "id": "...",
        "course_id": "...",
        "activity_no": 1,
        "text": "...",
        "learning_objectives": ["..."],
        "status": "NOT_STARTED|ACTIVE|ENDED"
      }
    ]
  }
}
```
Possible error codes:
- `invalid_credentials`
- `course_access_denied`

---

### `POST /instructor/create-activity`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_text": "Activity prompt text",
  "learning_objectives": ["Obj-1", "Obj-2"],
  "activity_no_optional": null
}
```
Possible error codes:
- `invalid_credentials`
- `course_access_denied`
- `activity_already_exists`

---

### `POST /instructor/update-activity`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1,
  "patch": {
    "text": "new text",
    "learning_objectives": ["..."],
    "status": "ACTIVE"
  }
}
```
Allowed patch keys:
- `text`
- `learning_objectives`
- `status`

Possible error codes:
- `invalid_credentials`
- `course_access_denied`
- `activity_not_found`
- `empty_patch`
- `update_failed`

---

### `POST /instructor/start-activity`
### `POST /instructor/end-activity`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1
}
```
Start errors:
- `activity_already_active`

End errors:
- `activity_already_ended`

Common errors:
- `invalid_credentials`
- `course_access_denied`
- `activity_not_found`
- `update_failed`

---

### `POST /instructor/export-scores`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1
}
```
Success data:
- `csv` (string)
- `rows` (array)

---

### `POST /instructor/manual-grade`
### `POST /instructor/grade-student` (alias)
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1,
  "student_email": "student5@test.com",
  "manual_score": 2,
  "reason": "exception case",
  "meta": {
    "note": "late join"
  }
}
```
Success data:
- `score_log`
- `manual_grade_event`
- `current_score`
- `activity_completed`

Possible error codes:
- `invalid_credentials`
- `course_access_denied`
- `instructor_id_missing`
- `student_not_found`
- `target_not_student`
- `student_id_missing`
- `student_not_in_course`
- `activity_not_found`
- `invalid_manual_score`
- `score_log_insert_failed`
- `manual_grade_event_insert_failed`

---

### `POST /instructor/reset-activity`
Request:
```json
{
  "email": "instructor@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1
}
```
Success data:
- `deleted_count`
- `progress_reset_count`
- `activity` (status `ENDED` olmalı)

Bu işlem sonrası:
- activity `ENDED`
- yeni score logging bloklanır (`activity_not_active`)

Possible error codes:
- `invalid_credentials`
- `course_access_denied`
- `activity_not_found`
- `activity_reset_failed`

---

## 5) Frontend Role-Based Page Flow

## Student Flow
1. Login (`/student/login`)
2. Course + activity seçim
3. Get activity (`/student/get-activity`)
4. Tutor chat loop (`/student/tutor-chat`)
5. `data.tool_result.score_added === 1` ise mini-lesson + score update göster
6. `activity_completed` veya completion message gelince chat input disable et

## Instructor Flow
1. Login (`/instructor/login`)
2. List courses (`/instructor/list-courses`)
3. Course activities (`/instructor/list-activities`)
4. Create/Update/Start/End/Reset
5. Export scores
6. Manual grade (exceptional cases)

---

## 6) UI Error Handling Mapping (Önerilen)
- `invalid_credentials` -> "Email veya şifre hatalı."
- `forbidden_role` -> "Bu işlem için uygun rolünüz yok."
- `course_access_denied` -> "Bu derse erişim yetkiniz yok."
- `activity_not_active` -> "Aktivite şu anda aktif değil."
- `activity_completed` -> "Bu aktivite tamamlandı."
- `duplicate_objective` durumunda (`ok:true` + `score_added:0`) -> info toast: "Bu objective daha önce kazanılmış."
- `422` -> form field validation highlight

---

## 7) TypeScript Interface Önerileri
```ts
export type ApiSuccess<T> = { ok: true; data: T };
export type ApiFail = { ok: false; error: string };
export type ApiResponse<T> = ApiSuccess<T> | ApiFail;

export type ActivityStatus = "NOT_STARTED" | "ACTIVE" | "ENDED";

export interface ActivityDto {
  id?: string;
  course_id: string;
  activity_no: number;
  text: string;
  learning_objectives: string[];
  status: ActivityStatus;
}

export interface TutorChatData {
  response: string;
  apicall: string;
  data: {
    parsed?: unknown;
    tool_result?: {
      ok?: boolean;
      score_added?: number;
      duplicate_objective?: boolean;
      current_score?: number;
      activity_completed?: boolean;
    } | null;
    mini_lesson?: string;
    completed?: boolean;
    progress?: Record<string, unknown>;
  };
  error: string | null;
}
```

---

## 8) Frontend İçin Kritik Notlar
- `/instructor/list-courses` request’inde `course_id` zorunlu görünüyor (schema kaynaklı), ama service bunu kullanmıyor.
- Business hataları çoğunlukla HTTP 200 ile geliyor; sadece `ok` flag’e bakarak karar verin.
- `tutor-chat` response text’i markdown içerebilir (`**Mini Lesson...**`). UI markdown render edebilir.
- Score kartında gerçek artış kontrolü için `score_added` kullanın; sadece `ok:true` yeterli değil.
- Activity reset sonrası instructor ekranında activity status’u ENDED olarak yenileyin.

---

## 9) Minimum Frontend Test Checklist
- Student login success/fail
- Instructor login success/fail
- Unauthorized course access error rendering
- Student get-activity only ACTIVE case
- Tutor chat: normal response, score trigger response, completion response
- Manual grade success + hata durumları
- Reset activity sonrası score log engeli UI doğrulaması

---

## 10) Örnek Tutor Chat Başlangıç Payload
```json
{
  "email": "student5@test.com",
  "password": "1234567",
  "course_id": "22222222-2222-2222-2222-222222222222",
  "activity_no": 1,
  "message": "Applications need predefined message formats, message field meanings, and communication rules so both systems can correctly interpret and process messages over the network.",
  "progress_context": null
}
```

Bu payload doğru ve mevcut backend ile uyumludur.

---

## 11) Teslim Notu
Bu dosya backend’in güncel davranışına göre hazırlanmıştır. Frontend entegrasyonda source-of-truth olarak kullanılabilir.
