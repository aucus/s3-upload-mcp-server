# AWS S3 Upload MCP Server PRD
## Product Requirements Document

**문서 버전:** v1.0  
**작성일:** 2025년 9월 18일  
**작성자:** AI Agent Development Team  
**프로젝트명:** AWS S3 Upload MCP Server  

---

## 📋 **1. 프로젝트 개요**

### **1.1 배경**
현재 Figma → MCP → HTML → Cursor Rules 워크플로우에서 이미지 파일들을 AWS S3에 자동 업로드하는 기능이 필요합니다. 기존 공개된 S3 MCP 서버들은 모두 읽기 전용 기능만 제공하여, 업로드 기능을 포함한 커스텀 MCP 서버 개발이 필수적입니다.

### **1.2 목표**
- Figma에서 추출된 이미지를 AWS S3에 자동 업로드
- 업로드된 이미지의 공개 URL을 즉시 반환
- MCP 표준을 준수하는 안정적이고 확장 가능한 서버 구현
- Cursor IDE와의 원활한 연동

### **1.3 프로젝트 범위**
- **포함**: S3 업로드, URL 생성, 기본 이미지 최적화, MCP 표준 준수
- **제외**: 고급 이미지 편집, 사용자 인증 시스템, 웹 UI

---

## 🎯 **2. 비즈니스 요구사항**

### **2.1 핵심 가치 제안**
- **개발 생산성 향상**: 수동 이미지 업로드 작업 완전 자동화
- **워크플로우 통합**: 기존 Figma-Cursor 파이프라인에 seamless 통합
- **표준화**: MCP 프로토콜 활용으로 다른 AI 도구와의 호환성 보장

### **2.2 성공 지표**
- **업로드 성공률**: 99% 이상
- **평균 업로드 시간**: 이미지당 3초 이내
- **MCP 호환성**: Claude Desktop, Cursor IDE 완전 호환
- **에러 복구**: 네트워크 오류 시 자동 재시도 성공

---

## 👥 **3. 사용자 스토리**

### **3.1 Primary User: 개발자**

**As a** Figma-Cursor 워크플로우를 사용하는 개발자  
**I want to** Figma에서 추출한 이미지를 자동으로 S3에 업로드하고  
**So that** HTML 코드에서 바로 사용할 수 있는 공개 URL을 얻을 수 있다

### **3.2 User Stories**

#### **Story 1: 단일 이미지 업로드**
- **Given** 로컬에 이미지 파일이 있고
- **When** MCP 클라이언트를 통해 업로드를 요청하면
- **Then** S3에 업로드되고 공개 URL이 반환된다

#### **Story 2: 일괄 이미지 업로드**
- **Given** 여러 개의 이미지 파일이 있고
- **When** 일괄 업로드를 요청하면
- **Then** 모든 파일이 S3에 업로드되고 각각의 URL이 배열로 반환된다

#### **Story 3: 이미지 최적화**
- **Given** 최적화가 필요한 이미지 파일이 있고
- **When** 최적화 옵션을 포함하여 업로드하면
- **Then** WebP 변환, 압축이 적용된 후 S3에 업로드된다

#### **Story 4: 오류 처리**
- **Given** 네트워크 오류나 S3 접근 오류가 발생하고
- **When** 업로드가 실패하면
- **Then** 명확한 에러 메시지와 함께 자동 재시도가 수행된다

---

## 🔧 **4. 기능 요구사항**

### **4.1 Core Features (Must Have)**

#### **4.1.1 MCP Tools**
1. **upload_image_to_s3**
   - 단일 이미지 파일 S3 업로드
   - 입력: 파일 경로, 버킷명, 키명(선택)
   - 출력: 공개 URL, 업로드 메타데이터

2. **batch_upload_images**
   - 여러 이미지 일괄 업로드 (병렬 처리)
   - 입력: 파일 경로 배열, 버킷명, 폴더 프리픽스(선택)
   - 출력: URL 배열, 업로드 결과 상태

3. **list_s3_buckets** 
   - 사용 가능한 S3 버킷 목록 조회
   - 입력: 없음
   - 출력: 버킷명 배열

#### **4.1.2 이미지 처리**
- **지원 포맷**: PNG, JPG, JPEG, SVG, WebP
- **자동 WebP 변환**: 옵션으로 제공
- **기본 압축**: 품질 80% 기본값
- **파일명 정규화**: 안전한 URL 호환 파일명 생성

#### **4.1.3 S3 연동**
- **AWS SDK 활용**: boto3 라이브러리 사용
- **멀티파트 업로드**: 5MB 이상 파일 자동 적용
- **메타데이터 태깅**: 업로드 시간, 원본 파일명, 압축 정보
- **CORS 설정**: 웹 브라우저에서 직접 접근 가능

### **4.2 Secondary Features (Should Have)**

#### **4.2.1 성능 최적화**
- **병렬 업로드**: asyncio 기반 동시 업로드
- **프로그레스 모니터링**: 업로드 진행률 실시간 제공
- **캐시 검증**: 동일 파일 중복 업로드 방지

#### **4.2.2 보안**
- **IAM 역할 지원**: EC2/Lambda 환경에서 키 없는 인증
- **환경변수 인증**: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- **버킷 권한 검증**: 업로드 권한 사전 확인

### **4.3 Nice to Have Features**

#### **4.3.1 고급 기능**
- **CDN 연동**: CloudFront URL 자동 생성
- **이미지 리사이징**: 다중 해상도 자동 생성
- **스마트 압축**: AI 기반 품질-용량 최적화

---

## ⚙️ **5. 기술 요구사항**

### **5.1 기술 스택**
- **언어**: Python 3.10+
- **MCP 프레임워크**: `fastmcp` (고성능 Pythonic MCP 라이브러리)
- **AWS SDK**: `boto3` 
- **이미지 처리**: `Pillow` (PIL)
- **비동기 처리**: `asyncio`, `aiohttp`
- **타입 검증**: `pydantic` (FastMCP 내장)
- **패키지 관리**: `uv` (권장)

### **5.2 시스템 아키텍처**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  FastMCP Server  │    │   Amazon S3     │
│   (Claude/      │◄──►│  (S3 Upload)     │◄──►│    Bucket       │
│    Cursor)      │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Image Processing │
                       │   (Pillow)       │
                       └──────────────────┘
```

### **5.3 FastMCP 기반 구현 방식**
- **데코레이터 기반**: `@mcp.tool`로 간단한 도구 정의
- **자동 타입 검증**: Pydantic 모델로 입력/출력 자동 검증
- **Context 지원**: 로깅, 진행률 보고, 에러 처리 내장
- **다양한 Transport**: STDIO (기본), HTTP, SSE 지원
- **테스트 친화적**: In-memory 클라이언트로 단위 테스트 용이

### **5.4 성능 요구사항**
- **업로드 속도**: 1MB 이미지 기준 3초 이내
- **동시 업로드**: 최대 5개 파일 병렬 처리
- **메모리 사용량**: 100MB 이하 유지
- **CPU 사용률**: 단일 코어 50% 이하

### **5.5 호환성 요구사항**
- **MCP 버전**: 1.0.x 호환
- **Python 버전**: 3.10, 3.11, 3.12 지원
- **운영체제**: macOS, Linux, Windows
- **MCP 클라이언트**: Claude Desktop, Cursor IDE, Cline

---

## 📊 **6. 데이터 요구사항**

### **6.1 입력 데이터**
- **이미지 파일**: 최대 100MB, 일반적인 웹 이미지 포맷
- **S3 설정**: 버킷명, 리전, 접근 자격증명
- **업로드 옵션**: 압축 품질, WebP 변환 여부, 폴더 구조

### **6.2 출력 데이터**
- **공개 URL**: HTTPS 방식의 S3 객체 URL
- **메타데이터**: 파일 크기, 업로드 시간, ETag
- **상태 정보**: 성공/실패 상태, 오류 메시지

### **6.3 설정 데이터**
```json
{
  "aws": {
    "region": "ap-northeast-2",
    "bucket_name": "figma-assets-bucket",
    "access_key_id": "${AWS_ACCESS_KEY_ID}",
    "secret_access_key": "${AWS_SECRET_ACCESS_KEY}"
  },
  "image_processing": {
    "auto_webp_conversion": true,
    "compression_quality": 80,
    "max_width": 1920,
    "max_height": 1080
  }
}
```

---

## 🔒 **7. 보안 요구사항**

### **7.1 인증**
- **AWS IAM**: 최소 권한 원칙 적용
- **환경변수**: 민감 정보 환경변수 저장
- **키 로테이션**: 정기적인 액세스 키 갱신 지원

### **7.2 데이터 보안**
- **전송 암호화**: HTTPS/TLS 1.2 이상
- **저장 암호화**: S3 server-side encryption
- **접근 제어**: S3 버킷 정책을 통한 접근 제어

### **7.3 필수 IAM 권한**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::figma-assets-bucket",
        "arn:aws:s3:::figma-assets-bucket/*"
      ]
    }
  ]
}
```

---

## 📈 **8. 운영 요구사항**

### **8.1 모니터링**
- **로깅**: 구조화된 JSON 로그 형식
- **메트릭**: 업로드 성공률, 응답시간, 오류율
- **알림**: 연속 실패 시 경고 메시지

### **8.2 에러 처리**
- **자동 재시도**: 지수 백오프 알고리즘
- **Circuit Breaker**: 연속 실패 시 임시 중단
- **Graceful Degradation**: 부분 실패 시에도 가능한 결과 반환

### **8.3 설정 관리**
- **환경별 설정**: dev, staging, production
- **Hot Reload**: 설정 변경 시 재시작 없이 적용
- **검증**: 설정 유효성 사전 검증

---

## 🚀 **9. 배포 및 설치**

### **9.1 패키지 구조**
```
s3-upload-mcp-server/
├── pyproject.toml
├── README.md
├── src/
│   ├── s3_upload_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── tools.py
│   │   ├── image_processor.py
│   │   └── s3_client.py
├── tests/
├── config/
│   └── claude_desktop_config.json
└── docs/
```

### **9.2 설치 방법**
```bash
# uv를 통한 설치 (권장)
uv add s3-upload-mcp-server

# pip를 통한 설치
pip install s3-upload-mcp-server

# 개발 환경 설치
git clone https://github.com/your-repo/s3-upload-mcp-server.git
cd s3-upload-mcp-server
uv sync
```

### **9.3 FastMCP 기반 서버 실행**
```python
# server.py
from fastmcp import FastMCP, Context
from s3_upload_mcp.tools import upload_image_to_s3, batch_upload_images, list_s3_buckets

mcp = FastMCP("S3 Upload Server")

# 도구 등록
mcp.tool(upload_image_to_s3)
mcp.tool(batch_upload_images)
mcp.tool(list_s3_buckets)

if __name__ == "__main__":
    mcp.run()  # STDIO transport (기본)
    # 또는 HTTP: mcp.run(transport="http", host="127.0.0.1", port=8000)
```

### **9.4 Claude Desktop 연동**
```json
{
  "mcpServers": {
    "s3-upload": {
      "command": "uv",
      "args": ["run", "s3-upload-mcp-server"],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "S3_BUCKET_NAME": "figma-assets-bucket"
      }
    }
  }
}
```

---

## ✅ **10. 수용 기준 (Definition of Done)**

### **10.1 기능 완성도**
- [ ] 모든 MCP Tools 구현 완료
- [ ] 단위 테스트 커버리지 90% 이상
- [ ] 통합 테스트 통과
- [ ] Claude Desktop 연동 확인

### **10.2 품질 기준**
- [ ] 코드 리뷰 승인
- [ ] 정적 분석 도구 통과 (pylint, mypy)
- [ ] 보안 스캔 통과
- [ ] 성능 테스트 기준 달성

### **10.3 문서화**
- [ ] API 문서 작성
- [ ] 사용자 가이드 작성
- [ ] 설치/설정 가이드 작성
- [ ] 트러블슈팅 가이드 작성

---

## 📅 **11. 일정 및 마일스톤**

### **Phase 1: 기본 구현 (2주)**
- Week 1: MCP 서버 프레임워크 구축, S3 업로드 기본 기능
- Week 2: 이미지 처리, 에러 처리, 기본 테스트

### **Phase 2: 최적화 및 안정화 (1주)**
- 성능 최적화, 보안 강화, 통합 테스트

### **Phase 3: 문서화 및 배포 준비 (3일)**
- 문서 작성, 패키징, 배포 준비

---

## 🔄 **12. 위험 요소 및 완화 방안**

### **12.1 기술적 위험**
- **위험**: MCP SDK 호환성 문제
- **완화**: 최신 MCP SDK 사용, 호환성 테스트 강화

### **12.2 운영 위험**
- **위험**: AWS 비용 급증
- **완화**: 업로드 용량 제한, 비용 모니터링 알림

### **12.3 보안 위험**
- **위험**: AWS 자격증명 노출
- **완화**: 환경변수 사용, IAM 역할 권장

---

## 📞 **13. 연락처 및 승인**

**제품 책임자**: AI Agent Development Team  
**기술 책임자**: Claude Agent  
**프로젝트 스폰서**: Master  

**승인일**: 2025년 9월 18일  
**다음 리뷰**: Phase 1 완료 후

---

*이 PRD는 living document로서 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*