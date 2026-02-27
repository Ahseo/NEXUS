# 이벤트 플랫폼 참여자 조회 API 문서

## 1. Partiful

[https://partiful.com/](https://partiful.com/)

### getGuests API

`POST https://api.partiful.com/getGuests`

**Payload:**

```json
{
  "data": {
    "params": {
      "eventId": "SdcM6xiOu3iHyuGr6CUk",
      "includeInvitedGuests": true
    },
    "paging": { "cursor": null, "maxResults": 500 },
    "userId": "vucR4ogSMRcXA70mgnQHaFlGamH3"
  }
}
```

**Response:**

```json
{
  "result": {
    "data": [
      {
        "id": "LSUhux7PSHjoyQnNNHI1",
        "status": "GOING",
        "user": {
          "id": "vucR4ogSMRcXA70mgnQHaFlGamH3",
          "name": "Junghyeon Park",
          "email": "junghyeon@example.com",
          "socials": {
            "instagram": { "visibility": "MUTUALS", "value": "username" },
            "linkedin": { "visibility": "PUBLIC", "value": "in/username" },
            "twitter": { "visibility": "PUBLIC", "value": "username" }
          }
        },
        "name": "Junghyeon Park"
      }
    ]
  }
}
```

**인증:** Firebase Auth 필요 (userId 필수)

**데이터 추출 포인트:** `user.name` (이름), `user.email` (이메일 - 주최자 권한 필요 가능), `user.socials` (SNS)

**비고:** RSVP 후에만 Guest list 열람 가능. 소셜 링크는 유저의 privacy 설정(visibility)에 따라 노출 여부가 다름.

---

## 2. Meetup

[https://www.meetup.com/](https://www.meetup.com/)

### GraphQL API

`POST https://www.meetup.com/gql2`

**Headers:**

```
Content-Type: application/json
Cookie: (session cookie required)

```

**Payload (attendees 조회):**

```json
{
  "operationName": "getEventAttendees",
  "variables": { "eventId": "312251076" },
  "query": "query getEventAttendees($eventId: ID!) { event(id: $eventId) { attendees { edges { node { id name email socialProfiles { network url } } } } } }"
}
```

**Response:**

```json
{
  "data": {
    "event": {
      "attendees": {
        "edges": [
          {
            "node": {
              "id": "479504038",
              "name": "Fonzi",
              "email": "fonzi@example.com",
              "socialProfiles": [
                {
                  "network": "LinkedIn",
                  "url": "https://www.linkedin.com/in/fonzi"
                },
                { "network": "Twitter", "url": "https://twitter.com/fonzi" }
              ]
            }
          }
        ]
      }
    }
  }
}
```

**인증:** 세션 쿠키 필요 (로그인 필수)

**데이터 추출 포인트:** `node.name` (이름), `node.email` (이메일 - 주최자 권한 필요), `node.socialProfiles` (SNS)

**비고:** 일반 유저로 조회 시 `email` 필드는 null이거나 권한 에러를 반환할 수 있음.

---

## 3. Kommunity

[https://kommunity.com/](https://kommunity.com/)

### Attendees API

`GET https://api.kommunity.com/api/v1/{community}/events/{event-slug}/attendees`

**Query Params:**

```
?limit=20&page=1&status=1

```

**Response:**

```json
{
  "data": [
    {
      "id": "abc123",
      "name": "John Doe",
      "email": "johndoe@example.com",
      "social_links": {
        "linkedin": "https://linkedin.com/in/johndoe",
        "twitter": "https://twitter.com/johndoe",
        "github": "https://github.com/johndoe"
      },
      "status": 1
    }
  ],
  "meta": { "total": 84 }
}
```

**인증:** 공개 (인증 불필요)

**데이터 추출 포인트:** `data[].name` (이름), `data[].email` (이메일), `data[].social_links` (SNS)

**비고:** 가장 데이터 접근이 용이한 플랫폼. 프로필에 SNS를 연동한 유저의 정보가 공개 API로 노출됨.

---

## 4. Supermomos

[https://www.supermomos.com/](https://www.supermomos.com/)

### Event API

`GET https://www.supermomos.com/api/socials/slug/{event-slug}`

**Response:**

```json
{
  "data": {
    "id": "abc123",
    "title": "International Founders Happy Hour",
    "attendees": [
      {
        "id": "att1",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "socials": {
          "linkedin": "https://linkedin.com/in/alicesmith"
        }
      }
    ],
    "isGuestListHidden": false
  }
}
```

**인증:** 이벤트 정보는 공개, 참가자 상세 데이터(이메일, SNS 등)는 로그인 및 승인된 유저만 접근 가능.

**데이터 추출 포인트:** `attendees[].name` (이름), `attendees[].email` (이메일), `attendees[].socials` (SNS)

**비고:** `isGuestListHidden: true`인 경우 참석자 배열 자체가 노출되지 않음.

---

## 5. Peatix

[https://peatix.com/](https://peatix.com/)

### Attendees API

`GET https://peatix-api.com/v4/events/{eventId}/attendees`

**Response:**

```json
{
  "totalAttendees": 1,
  "attendees": [
    {
      "user_id": "u89123",
      "name": "Taro Yamada",
      "email": "taro.yamada@example.com",
      "sns": {
        "twitter": "taroy",
        "facebook": "taroy.fb"
      }
    }
  ]
}
```

**인증:** 오거나이저(주최자) 권한 토큰 필수.

**데이터 추출 포인트:** `attendees[].name` (이름), `attendees[].email` (이메일), `attendees[].sns` (SNS)

**비고:** 외부인(일반 참가자)이 해당 API를 호출하면 `attendees` 배열이 비어있는 상태(`[]` 또는 `""`)로 반환됨. 주최자 연동 필수.

---

## 6. Startup Grind (Bevy)

[https://www.startupgrind.com/](https://www.startupgrind.com/)

### ⚠️ Attendees 데이터 (API 없음, HTML 스크래핑 필요)

**접근 방법:** 이벤트 상세 페이지 HTML 스크래핑 (예: `GET https://www.startupgrind.com/events/details/{event-slug}/`)

**데이터 추출 포인트 (스크래핑):**

- **Name & Socials:** HTML 내 참석자 리스트 UI(`.attendee-card`, `.avatar-container` 등)에서 이름 텍스트와 연동된 LinkedIn/Twitter 프로필 링크(`href`) 추출.
- **Email:** 퍼블릭 웹페이지에서는 절대 노출되지 않음 (수집 불가).

**인증:** 공개 페이지 스크래핑 (단, 주최자가 참가자 목록을 비공개 처리한 경우 스크래핑 불가)

---

## 7. 10Times

[https://10times.com/](https://10times.com/)

### ⚠️ Attendees 데이터 (API는 통계만 제공, 개별 정보는 HTML 스크래핑 필요)

**접근 방법:** 참석자 탭 HTML 목록 및 개별 프로필 페이지 크롤링

- `GET https://10times.com/{event-slug}/visitors`
- `GET https://10times.com/profile/{user-slug}`

**데이터 추출 포인트 (스크래핑):**

- **Name:** 방문자 리스트의 `.visitor-name` 또는 프로필 페이지의 `<h1 itemprop="name">` 태그 파싱.
- **Socials:** 개별 프로필 페이지 내의 LinkedIn 뱃지 링크나 회사 URL 정보 수집.
- **Email:** 비공개 (플랫폼 내 자체 메시지 전송 기능만 제공하여 수집 불가).

**인증:** 세션 쿠키 필요 (로그인 후 스크래핑)

---

## 8. AllEvents.in

[https://allevents.in/](https://allevents.in/)

### ⚠️ Attendees 데이터 (API 없음, HTML 스크래핑 필요)

**접근 방법:** 이벤트 상세 페이지의 참석자(Attendees) 섹션 HTML 파싱

**데이터 추출 포인트 (스크래핑):**

- **Name:** 참석자 리스트 모달이나 UI 내 `<li>` 또는 `<div>` 태그의 텍스트 파싱.
- **Email & Socials:** 화면에 대부분 공개되지 않아 추출이 매우 까다로움. 페이스북 연동 비중이 높아 프로필 이미지 URL에서 페이스북 ID를 유추하는 방식 활용 필요.

**인증:** 공개 페이지 스크래핑

---

## 9. Devpost

[https://devpost.com/](https://devpost.com/)

### ⚠️ Attendees 데이터 (100% HTML 스크래핑 필요)

**접근 방법:**
`GET https://{hackathon}.devpost.com/participants?page=1` (페이지네이션 순회 필요)

**데이터 추출 포인트 (스크래핑):**

- **Name:** 참가자 카드 내 `<div class="user-profile-link">` 하위의 텍스트 추출.
- **Socials:** 참가자 프로필 썸네일이나 상세 페이지(`/software/{project}` 또는 개별 유저 페이지) 내의 GitHub (`href="https://github.com/..."`), LinkedIn, 웹사이트 링크 파싱.
- **Email:** 일반 참가자 및 외부인에게는 숨김 처리됨.

**인증:** 세션 쿠키 필요 (일부 해커톤은 로그인된 상태에서만 참가자 열람 가능)

---

## 10. LinkedIn Events

[https://www.linkedin.com/events/](https://www.linkedin.com/events/)

### ⚠️ Attendees 데이터 (공식 API 없음, 동적 렌더링 스크래핑 고난이도)

**접근 방법:** Puppeteer / Selenium 등 Headless 브라우저를 이용한 자동화 스크래핑 필수

**데이터 추출 포인트 (스크래핑):**

- **Name & Socials:** 이벤트 페이지 내 'Networking(참가자)' 탭에서 스크롤을 내리며 비동기로 로드되는 참석자 카드의 이름 텍스트와 프로필 링크(`href`) 추출. (기본적으로 모두 LinkedIn 프로필 URL)
- **Email:** 1촌(Connection)이 아니면 이메일 열람 불가.

**인증:** 🔒 완전 잠김 (로그인 세션 필수)

**비고:** LinkedIn은 봇 탐지(Bot Detection)가 매우 강력하여 일반적인 크롤링 시 IP 차단이나 계정 정지(Ban) 리스크가 매우 큽니다.

---

# 📊 요약 테이블

| 플랫폼               | 데이터 획득 방식    | 참석자 상세 데이터 | 이름/이메일/SNS 추출                            | 난이도     |
| -------------------- | ------------------- | ------------------ | ----------------------------------------------- | ---------- |
| **1. Partiful**      | REST API            | ✅ 제공            | ⚠️ 이메일 제한적 / 이름, SNS 용이               | ⭐⭐⭐     |
| **2. Meetup**        | GraphQL             | ✅ 제공            | 🔒 주최자 권한 필요 / 이름, SNS 용이            | ⭐⭐       |
| **3. Kommunity**     | REST API            | ✅ 제공            | ✅ 공개 API로 이름, 이메일, SNS 획득 용이       | ⭐         |
| **4. Supermomos**    | REST API            | 제한적 (통계 위주) | 🔒 로그인 및 승인된 유저만 획득 가능            | ⭐⭐       |
| **5. Peatix**        | REST API            | 주최자만 제공      | 🔒 주최자 권한 필수                             | ⭐⭐       |
| **6. Startup Grind** | **HTML 스크래핑**   | 리스트 UI 긁기     | 이름, SNS 파싱 / 이메일 불가                    | ⭐⭐⭐     |
| **7. 10Times**       | **HTML 스크래핑**   | 프로필 개별 크롤링 | 이름, 제한적 SNS 파싱 / 이메일 불가             | ⭐⭐⭐     |
| **8. AllEvents**     | **HTML 스크래핑**   | 리스트 UI 긁기     | 이름 파싱 / 이메일, SNS 어려움                  | ⭐⭐⭐     |
| **9. Devpost**       | **HTML 스크래핑**   | 페이지네이션 긁기  | 이름, Github, LinkedIn 파싱 / 이메일 불가       | ⭐⭐⭐⭐   |
| **10. LinkedIn**     | **브라우저 자동화** | 동적 로딩 긁기     | 이름, LinkedIn 링크 / IP차단 위험 / 이메일 불가 | ⭐⭐⭐⭐⭐ |
