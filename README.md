

---

# 🧱 Infrastructure Architecture

## 1. 프로젝트 개요

본 프로젝트는 **On-Premise 환경과 AWS를 연동한 Hybrid Infrastructure**를 직접 설계하고 구축하는 것을 목표로 한다.
단순한 애플리케이션 배포를 넘어, **실제 운영 환경을 가정한 네트워크 분리, 보안 계층, CI/CD, 관측(Observability), GitOps** 구조를 구현하였다.

특히 ESXi 기반의 On-Premise 환경을 중심으로 Management, CI/CD, Service, LAB 영역을 명확히 분리하고,
AWS는 외부 트래픽 진입점 및 보안 계층으로 활용하는 구조를 채택하였다.

---

## 2. 전체 아키텍처 개요

본 인프라는 크게 다음 두 영역으로 구성된다.

* **AWS Cloud 영역**

  * 외부 사용자 트래픽 수신
  * TLS 인증, WAF, CDN, DDoS 방어
* **On-Premise (ESXi 기반) 영역**

  * 실제 서비스 운영
  * CI/CD, 모니터링, 인증, 실습 환경 제공

외부 사용자는 On-premise를 통해 서비스에 접근하고, AWS에서 실습 환경을 제공받는다.
AWS와 On-Premise 간에는 **Site-to-Site VPN**으로 안전한 통신을 구성하였다.

이 구조를 통해:

* 외부 공격 표면을 최소화
* 내부 서비스 직접 노출 방지
* 실제 기업 환경과 유사한 Hybrid 구조 구현
  을 목표로 하였다.

---

## 3. 물리 / 가상화 계층 (ESXi Layer)

On-Premise 환경은 **VMware ESXi Host** 위에서 구성되었다.

### ESXi 기반 구성 이유

* 물리 서버 자원 효율적 사용
* VM 단위 역할 분리
* 네트워크/보안 실험에 용이

### VM 역할 분리

ESXi 상의 VM들은 기능별로 명확히 분리하였다.

* Management VM
* CI/CD VM
* Kubernetes Worker / Control Plane VM
* LAB VM
* Network Gateway VM (pfSense)

이러한 분리는 장애 대처를 쉽게 하고, 운영 관점에서 책임 범위를 명확히 하기 위함이다.

---

## 4. 네트워크 & 보안 아키텍처

### pfSense 중심 네트워크 설계

On-Premise 환경의 핵심 네트워크 장비로 **pfSense**를 사용하였다.

pfSense의 주요 역할:

* Default Gateway
* NAT
* Firewall
* 내부망 ↔ 외부망 트래픽 제어

### 네트워크 분리 전략

* Management Zone
* Service Zone
* CI/CD Zone
* LAB Zone

각 영역은 논리적으로 분리되며, 필요한 트래픽만 방화벽 규칙을 통해 허용하였다.

### VPN 구성

* AWS VPC ↔ On-Premise pfSense 간 **Site-to-Site VPN**
* AWS 내부 리소스에서 On-Prem 서비스로 안전한 접근 가능

---

## 5. AWS 연계 인프라

AWS는 **외부 진입점 및 보안 계층**으로 활용된다.

### 주요 구성 요소

* **Route53**

  * 도메인 관리
* **ACM (AWS Certificate Manager)**

  * TLS 인증서 발급
* **CloudFront**

  * CDN 및 HTTPS 종단점
* **WAF**

  * 웹 공격 방어
* **Shield**

  * DDoS 보호

### 트래픽 흐름

1. User → Route53
2. CloudFront (TLS 종료)
3. WAF / Shield 보안 검사
4. VPN을 통해 On-Premise 서비스로 전달

AWS를 전면에 배치함으로써 On-Prem 서비스는 외부에 직접 노출되지 않는다.

---

## 6. Management 영역

Management 영역은 **운영 및 관측 전용 영역**이다.

### 구성 요소

* **Prometheus**

  * 메트릭 수집
* **Grafana**

  * 시각화 대시보드
* **Loki**

  * 로그 수집
* **Keycloak**

  * 인증 및 사용자 관리

### 분리 이유

* 운영 도구와 서비스 영역의 책임 분리
* 장애 발생 시 관리 시스템 독립성 유지
* 보안 사고 시 영향 범위 최소화

---

## 7. CI/CD 영역

CI/CD 영역은 **애플리케이션 빌드부터 배포까지의 자동화 파이프라인**을 담당한다.

### CI/CD 파이프라인 구성

* **GitLab**

  * 소스 코드 저장소
* **Jenkins**

  * CI 파이프라인 실행
* **Cosign**

  * 컨테이너 이미지 서명
* **Harbor**

  * Private Container Registry
* **Trivy**

  * 이미지 취약점 스캔

### 흐름 요약

1. GitLab에 코드 Push
2. Jenkins 빌드 및 테스트
3. 이미지 빌드
4. Trivy 보안 스캔
5. Cosign 서명
6. Harbor에 이미지 저장

---

## 8. Service 영역 (Kubernetes)

Service 영역은 **실제 사용자 서비스가 동작하는 영역**이다.

### 구성

* Kubernetes Cluster
* Ingress Controller
* ArgoCD 기반 GitOps

### 서비스 스택

* **Next.js** (Frontend)
* **Spring Boot** (Backend)
* **MySQL** (Database)

### GitOps 구조

* Git 저장소의 선언적 YAML이 단일 진실 소스(Single Source of Truth)
* ArgoCD가 지속적으로 클러스터 상태 동기화

이를 통해 배포 이력 추적과 롤백이 용이한 구조를 구현하였다.

---

## 9. LAB / 실습 환경

LAB 영역은 **실습 및 테스트 전용 환경**이다.

### 구성

* **Apache Guacamole**

  * 웹 기반 원격 접속 환경

### 목적

* 실제 서비스 영역과 분리된 실습 환경 제공
* 보안 사고 또는 실험 실패가 운영 서비스에 영향을 주지 않도록 설계

LAB 영역은 교육·실습·테스트를 고려한 구조로,
실제 기업의 내부 실습망 개념을 반영하였다.

---

## 10. Infrastructure as Code (IaC)

본 프로젝트에서는 인프라의 일관성과 재현성을 위해 **Infrastructure as Code** 개념을 적극 활용하였다.

### Terraform 활용

* AWS 리소스(Route53, CloudFront, VPN 연계 등)를 코드로 관리
* 수동 설정으로 인한 환경 편차 제거
* 인프라 변경 이력 추적 가능

### On-Premise 환경과 IaC 병행

On-Premise 환경 특성상 모든 요소를 IaC로 관리하기는 어렵지만,

* AWS 영역은 Terraform으로 관리
* On-Premise는 표준화된 VM 템플릿과 설정 문서로 관리

하는 방식으로 **현실적인 Hybrid IaC 전략**을 적용하였다.

---

## 11. 보안 설계 요약

본 인프라는 **다계층 보안(Multi-Layer Security)**을 핵심 설계 원칙으로 삼았다.

### 네트워크 보안

* pfSense Firewall을 통한 영역 간 접근 통제
* AWS WAF를 통한 웹 공격 차단
* 외부에서 On-Prem 직접 접근 차단

### 인증 & 접근 제어

* Keycloak 기반 중앙 인증
* 서비스별 인증 분리 가능 구조

### 공급망 보안 (Supply Chain Security)

* Trivy를 통한 이미지 취약점 검사
* Cosign을 통한 이미지 서명
* 신뢰되지 않은 이미지의 배포 방지

---

## 12. 장애 대응 및 운영 전략

운영 환경에서의 장애 대응을 고려하여 **관측 가능성(Observability)**을 중심으로 설계하였다.

### 모니터링

* Prometheus로 시스템/애플리케이션 메트릭 수집
* Grafana 대시보드를 통한 시각화

### 로그 관리

* Loki를 통한 중앙 로그 수집
* 장애 발생 시 시간대별 로그 추적 가능

### 장애 대응 철학

* “장애를 막을 수는 없지만, 숨길 수는 없다”
* 빠른 원인 파악과 영향 범위 식별을 목표로 설계

---

## 13. 확장성 & 향후 개선 방향

현재 구조는 단일 클러스터 기반이지만, 확장을 고려한 설계를 적용하였다.

### 확장 가능 시나리오

* Kubernetes 노드 수평 확장
* LAB 영역 분리 클러스터화
* AWS 비중 확대 시 EKS로 이전 가능

### 향후 개선 방향

* 멀티 클러스터 GitOps 구조
* 중앙 로그/메트릭 장기 보관
* Zero Trust 네트워크 모델 일부 적용

---



