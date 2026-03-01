# 이벤트 트래킹 플랫폼 비교 분석

> 분석일: 2026-03-01
> 목적: Go/No-Go 측정을 위한 이벤트 트래킹 인프라 선정
> 대상: Mixpanel, Amplitude, GA4, PostHog, Plausible

---

## 배경

마스터 플랜의 Go/No-Go 기준:
- 첫 단계 진입율 >= 40%
- 초기 이탈률 < 60%

현재 측정 불가. 이벤트 트래킹 퍼널 필요:
```
roadmap_created → step_viewed → action_toggled → paywall_triggered → subscription_started
```

---

## 1. Mixpanel

### 개요
이벤트 기반 제품 분석 도구. 퍼널/코호트/리텐션 분석이 가장 강력.

### 가격

| 티어 | 한도 | 비용 |
|------|------|------|
| Free | 월 100만 이벤트 | $0 (카드 불필요) |
| Growth | 100만+ 이벤트 | $0.00028/이벤트 (~$280/100만) |
| Enterprise | 커스텀 | ~$25,000+/년 |
| **스타트업 프로그램** | **연 10억 이벤트, 50만 세션리플레이, 1년 무료** | **$0 (설립 5년 미만, 투자유치 $8M 미만)** |

스타트업 프로그램 2025.01 리뉴얼로 $150K+ 가치 제공.

### 주요 기능
- 퍼널, 리텐션, 코호트, 사용자 경로, 플로우
- 세션 리플레이 (2024/2025 추가)
- 히트맵 (2024/2025 추가)
- A/B 테스트: Experimentation 2.0 + Feature Flags (2025.06 출시)
- 이상 탐지 (유료만)

### Next.js 통합
- `mixpanel-browser` SDK, App Router 지원
- `'use client'` MixpanelProvider 컴포넌트 패턴
- 공식 문서: `docs.mixpanel.com/docs/tracking-methods/integrations/nextjs`
- **성숙도: 양호**

### FastAPI 통합
- 공식 Python SDK (`mixpanel` PyPI 패키지)
- `mp.track(distinct_id, event_name, properties)` 패턴
- JWT user ID를 distinct_id로 매핑
- **성숙도: 우수**

### 데이터 주권 / 개인정보
- EU 데이터 레지던시: 네덜란드 (모든 플랜, 무료)
- GDPR 준수 (DPA, 삭제/내보내기 API)
- 한국 데이터센터 없음 (EU 적정성 인정으로 커버)
- **셀프호스팅 불가** (클라우드 전용)

### 장점
- 퍼널/리텐션 UI 5개 중 최고
- 비기술 이해관계자(PM/사업팀) 셀프서브 가능
- 스타트업 프로그램 가치 최대 ($150K+)
- Experimentation 2.0으로 A/B 테스트까지 통합

### 단점
- 클라우드 전용 (한국 데이터 주권 강화 시 리스크)
- 그룹 애널리틱스 추가 비용
- 대규모 시 비용 급증 ($2,520/월 at 1천만 이벤트)

---

## 2. Amplitude

### 개요
엔터프라이즈급 행동 분석 도구. MTU(Monthly Tracked Users) 기반 과금.

### 가격

| 티어 | 한도 | 비용 |
|------|------|------|
| Starter (Free) | 5만 MTU, 1천만 이벤트, 1천 세션리플레이 | $0 |
| Plus | 1천~30만 MTU | $49/월~ |
| Growth | 커스텀 | ~$5,000–$70,000/년 |
| Enterprise | 커스텀 | 영업 문의 |
| **스타트업 프로그램** | **1년 Growth 플랜 무료** | **$0 (20명 미만, 투자유치 $5M 미만)** |

MTU 기반이라 무료 티어가 생각보다 제한적 (5만 MTU 상한).

### 주요 기능
- 행동 코호트/세그먼테이션 최강
- Experiment (A/B 테스트, 별도 제품)
- 세션 리플레이 (Starter 포함)
- Feature Flags 무제한 (Starter)
- 웨어하우스 네이티브 쿼리 (Growth/Enterprise)
- AI 인사이트

### Next.js 통합
- `@amplitude/analytics-browser` SDK
- App Router: `'use client'` 컨텍스트 프로바이더 패턴
- **성숙도: 양호**

### FastAPI 통합
- 공식 Python SDK (`amplitude-python-sdk` PyPI)
- 이벤트 배칭 내장 (flush_queue_size, flush_interval 설정)
- **성숙도: 양호**

### 데이터 주권 / 개인정보
- EU 데이터센터: 프랑크푸르트 (AWS eu-central-1)
- GDPR 준수 (DPA)
- 한국 데이터센터 없음
- **셀프호스팅 불가**

### 장점
- 행동 세그먼테이션/코호트 분석 시장 최고
- 무료 이벤트 한도 넉넉 (1천만)
- 웨어하우스 네이티브 쿼리 강력
- AI 기능 포함

### 단점
- MTU 기반 과금 혼란스러움
- A/B 테스트는 별도 제품 (고가 플랜)
- 스타트업 프로그램 조건 가장 엄격 ($5M, 20명)
- 학습 곡선 높음, 엔터프라이즈 지향

---

## 3. GA4 (Google Analytics 4)

### 개요
웹 분석 도구. **제품 분석 도구가 아님.** Google 생태계 연동이 핵심 가치.

### 가격

| 티어 | 한도 | 비용 |
|------|------|------|
| Standard (Free) | 무제한 | $0 |
| GA4 360 | 월 2,500만 이벤트 포함 | $50,000+/년 |

### 주요 기능
- 이벤트 기반 데이터 모델
- 크로스 플랫폼 트래킹 (웹+앱)
- BigQuery 무료 내보내기
- AI 예측 분석 (구매 확률, 이탈 확률)
- Google Ads/Search Console 연동
- 퍼널 탐색 리포트 (Explore)

### Next.js 통합
- `@next/third-parties/google` (Next.js 공식 패키지)
- **성숙도: 최고** (Next.js 팀 직접 지원)

### FastAPI 통합
- Measurement Protocol API (HTTP POST)
- **공식 Python SDK 없음** (`requests` 직접 호출)
- client_id 매칭으로 서버/클라이언트 이벤트 연결 복잡
- **성숙도: 낮음**

### 데이터 주권 / 개인정보
- Google 글로벌 인프라, 저장 위치 제어 제한
- GDPR: Consent Mode v2 필수
- **한국 PIPC 감시 대상** - 규정 준수 리스크 가장 높음
- 데이터 소유권 우려 (Google이 자체 목적 사용)

### 장점
- 완전 무료
- Google Ads/검색 마케팅 연동 최강
- 한국어 UI 지원
- 한국 커뮤니티 자료 풍부 (네이버, 티스토리)

### 단점
- **제품 분석 도구가 아님** - 사용자 레벨 행동 분석 불가
- 퍼널 분석 제한적 (히스토리 백필 불가)
- 리텐션 코호트 제대로 못함
- A/B 테스트 없음, Feature Flags 없음
- 무료 티어 데이터 보관 14개월 제한
- 서버사이드 이벤트 연결 복잡

---

## 4. PostHog

### 개요
올인원 개발자 분석 플랫폼. 오픈소스(MIT). 분석+세션리플레이+A/B테스트+Feature Flags+설문+에러트래킹.

### 가격

| 기능 | 무료 포함 | 초과 시 |
|------|----------|---------|
| 분석 이벤트 | 월 100만 | $0.00005/이벤트 |
| 세션 리플레이 | 월 5,000 | ~$0.005/건 |
| Feature Flags | 월 100만 요청 | ~$0.0001/요청 |
| A/B 실험 | 월 100만 요청 | 종량제 |
| 설문 | 월 1,500 응답 | 종량제 |
| 에러 트래킹 | 월 10만 예외 | 종량제 |
| **셀프호스팅 (MIT)** | **무제한** | **인프라 비용만** |
| **스타트업 프로그램** | **$50K 크레딧** | **설립 2년 미만, $5M 미만** |

90% 이상의 고객이 무료 티어로 유지.

### 주요 기능
- 퍼널, 리텐션, 코호트, 사용자 경로, 세션 리플레이
- Feature Flags (무료 티어에 포함)
- A/B 실험 (무료 티어에 포함)
- 히트맵/스크롤맵
- 설문
- 에러 트래킹
- **LLM 분석** (AI 모델 사용량, 토큰 비용, 성능 추적)
- 데이터 웨어하우스 연결
- CDP (Customer Data Platform)

### Next.js 통합
- **5개 중 최고.** 공식 전용 문서: `posthog.com/docs/libraries/next-js`
- App Router, Server Components, SSR 패턴 명시 지원
- `PostHogProvider` 클라이언트 컴포넌트 + `posthog-node` 서버사이드
- SSR Flag 하이드레이션 부트스트랩 패턴 제공
- Vercel 공식 PostHog 가이드 존재
- **성숙도: 최고**

### FastAPI 통합
- **5개 중 최고.** 공식 `posthog` Python SDK
- FastAPI 미들웨어 통합 문서화

```python
import posthog

posthog.api_key = 'YOUR_API_KEY'
posthog.host = 'https://eu.i.posthog.com'  # EU 리전

posthog.capture(
    distinct_id=user_id,
    event='purchase_completed',
    properties={'amount': 99.00, 'currency': 'KRW'}
)
```

- **성숙도: 최고**

### 데이터 주권 / 개인정보
- PostHog Cloud EU: 프랑크푸르트 (AWS eu-central-1), 데이터 EU 외 이동 없음
- IP 캡처 기본 비활성화 (EU 인스턴스)
- GDPR 준수; 셀프호스팅 시 PostHog 접근 제로
- **셀프호스팅: AWS 서울 리전(ap-northeast-2) 또는 NHN/KT 클라우드 배포 → PIPA 완벽 준수**
- MIT 라이선스

### 장점
- 올인원: PostHog + LaunchDarkly(Feature Flags) + Hotjar(세션리플레이) + 설문 도구 대체
- A/B 테스트 무료 포함 (유일)
- Next.js App Router 통합 문서 최고
- FastAPI Python SDK 최고
- MIT 오픈소스: 벤더 락인 없음
- 셀프호스팅으로 한국 데이터 주권 확보 가능
- LLM 분석 (AI 코치 모니터링에 활용 가능)
- $50K 스타트업 크레딧

### 단점
- UI 세련도 Mixpanel보다 낮음 (개발자 미학)
- 셀프호스팅은 DevOps 투자 필요 (월 100만 이벤트 초과 시 권장)
- 퍼널 시각화 기능적이나 Mixpanel보다 덜 세련
- 비기술 이해관계자에게 인터페이스 진입장벽

---

## 5. Plausible

### 개요
프라이버시 중심 웹 분석. 쿠키 없음. **제품 분석 도구가 아님.**

### 가격

| 티어 | 한도 | 비용 |
|------|------|------|
| Starter | 월 1만 페이지뷰 | $9/월 |
| Growth | 1만 페이지뷰 + 3사이트 + 팀 | $14/월 |
| Business | 고급 기능 | 상위 티어 |
| Community Edition | 셀프호스팅, 무제한 | $0 (인프라만) |

무료 클라우드 티어 없음.

### 주요 기능
- 쿠키리스 트래킹 (EU 동의 배너 불필요)
- 페이지뷰, 리퍼러, UTM 캠페인 트래킹
- 커스텀 이벤트 (이벤트당 최대 30 속성)
- 기본 퍼널 분석 (제한적)
- 목표/전환 트래킹

### Next.js 통합
- `next-plausible` 패키지, `usePlausible()` 훅
- **성숙도: 기본 사용에 양호, 제품 분석에 부족**

### FastAPI 통합
- Events API (HTTP POST) 직접 호출
- **공식 Python SDK 없음**
- **성숙도: 낮음**

### 장점
- 프라이버시 최고 (쿠키 없음, 동의 배너 불필요)
- 초경량 스크립트 (~1KB vs GA4 45KB+)
- 셀프호스팅 CE 무료
- GDPR/PIPA 준수 가장 용이

### 단점
- **제품 분석 도구가 아님** - Go/No-Go 측정 불가
- 코호트/퍼널/사용자 레벨 분석 없음
- A/B 테스트, Feature Flags, 세션 리플레이 없음
- 사용자 식별 불가
- 공식 Python SDK 없음

---

## 크로스 플랫폼 비교표

| 기준 | Mixpanel | Amplitude | GA4 | PostHog | Plausible |
|------|----------|-----------|-----|---------|-----------|
| **무료 이벤트/월** | 100만 | 1,000만 (5만 MTU 상한) | 무제한 | 100만 | 없음 (CE만) |
| **스타트업 프로그램** | $150K+ (1년) | $6-12K (1년) | N/A | $50K 크레딧 | N/A |
| **Next.js App Router** | 양호 | 양호 | 최고 | **최고** | 양호 |
| **FastAPI Python SDK** | 공식 | 공식 | HTTP만 | **공식 (최고)** | HTTP만 |
| **퍼널 분석** | **최고** | 우수 | 제한적 | 양호 | 기초 |
| **A/B 테스트** | 네이티브 | 별도 제품 | 없음 | **네이티브 무료** | 없음 |
| **Feature Flags** | 네이티브 | 네이티브 | 없음 | **네이티브 무료** | 없음 |
| **세션 리플레이** | 유료 | 무료 제한 | 없음 | 무료 5천건 | 없음 |
| **셀프호스팅** | 불가 | 불가 | 불가 | **가능 (MIT)** | 가능 (CE) |
| **EU 데이터 레지던시** | 네덜란드 | 프랑크푸르트 | 제한 | 프랑크푸르트 | EU 전용 |
| **한국 데이터 주권** | 불가 | 불가 | 불가 | **셀프호스팅** | CE 셀프호스팅 |
| **한국어 UI** | 없음 | 없음 | **있음** | 없음 | 없음 |
| **PIPA 준수 경로** | EU 적정성 | EU 적정성 | **고위험** | **셀프호스팅 (최고)** | CE (최고) |
| **비기술자 친화도** | **최고** | 양호 | 양호 | 보통 | 최고 |
| **과금 모델** | 이벤트당 | MTU당 | 무료/$50K+ | 이벤트+제품별 | 페이지뷰당 |

---

## Step Zero 추천

### 메인: PostHog (Cloud EU)

**선정 이유:**
1. **Next.js 15 App Router 통합 최고** - 공식 전용 문서, SSR/Server Components 지원
2. **FastAPI Python SDK 최고** - 미들웨어 통합, 비동기 패턴 문서화
3. **A/B 테스트 + Feature Flags 무료** - Phase별 롤아웃에 활용
4. **올인원** - 분석/세션리플레이/A/B/Feature Flags/설문/에러트래킹
5. **LLM 분석** - Phase 2 AI 코치 모니터링에 직접 활용
6. **셀프호스팅** - 향후 한국 데이터 주권 필요 시 AWS 서울 배포
7. **$50K 스타트업 크레딧** - 1년 충분

**즉시 액션:**
- 스타트업 프로그램 신청 (설립 2년 미만, $5M 미만)
- `posthog-js` + `PostHogProvider` (Next.js 15)
- `posthog` Python SDK (FastAPI 백엔드)
- Cloud EU (프랑크푸르트) 선택

### 보조: GA4 (무료, 마케팅용)

**용도:**
- Google Ads/Search Console 연동
- 마케팅 어트리뷰션
- 한국 SEO/검색 분석
- `@next/third-parties/google`로 병행 설치 (비용 $0)

**주의:** GA4를 제품 분석 의사결정에 사용하지 말 것.

### 대안: Mixpanel

**조건:** PostHog UI가 비기술 이해관계자에게 부족할 경우 전환 검토.
스타트업 프로그램 ($150K+ 가치) 병행 신청 추천.

---

## Go/No-Go 퍼널 측정 설계 (PostHog 기준)

```
이벤트 퍼널:
roadmap_created          ← 로드맵 생성 완료
  → step_viewed          ← 첫 단계 조회 (진입율 측정)
    → action_toggled     ← 액션 체크 (참여도)
      → step_completed   ← 단계 완료
        → paywall_triggered  ← 페이월 노출
          → subscription_started  ← 구독 전환

Go/No-Go 기준:
- roadmap_created → step_viewed 전환율 >= 40% (첫 단계 진입율)
- roadmap_created 후 7일 내 재방문 < 60% 이탈 (초기 이탈률)
```

---

## 소스

**Mixpanel:**
- [Mixpanel Pricing](https://openpanel.dev/articles/mixpanel-pricing)
- [Startup Program ($150K+, 2025.01)](https://docs.mixpanel.com/changelogs/2025-01-21-revamped-startup-program)
- [EU Data Residency](https://mixpanel.com/legal/eu-data-residency/)
- [Next.js Integration](https://docs.mixpanel.com/docs/tracking-methods/integrations/nextjs)

**Amplitude:**
- [Pricing](https://www.g2.com/products/amplitude-analytics/pricing)
- [Python SDK](https://amplitude.com/docs/sdks/analytics-sdks/python/python-sdk)
- [Next.js Guide](https://amplitude.com/docs/sdks/frameworks/nextjs-installation-guide)

**GA4:**
- [Pricing](https://analytify.io/google-analytics-pricing/)
- [Limitations](https://www.rudderstack.com/learn/GA4/benefits-and-limitations-of-google-analytics-4-ga4/)

**PostHog:**
- [Pricing](https://posthog.com/pricing)
- [Next.js Docs](https://posthog.com/docs/libraries/next-js)
- [Python SDK](https://posthog.com/docs/libraries/python)
- [Startup Program ($50K)](https://posthog.com/startups)
- [GDPR Compliance](https://posthog.com/docs/privacy/gdpr-compliance)
- [Self-Hosting](https://posthog.com/docs/self-host)

**Plausible:**
- [Pricing](https://plausible.io/docs/subscription-plans)
- [Next.js Integration](https://plausible.io/docs/nextjs-integration)

---

*분석 작성: Claude Code*
*분석일: 2026-03-01*
