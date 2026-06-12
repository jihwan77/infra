# Ansible Linux Initial Setup Automation

## 1. 개요

 **Ansible을 사용하여 Linux 서버의 초기 운영 설정을 자동화**하는 것을 목표로 한다.

VMware 또는 vSphere 환경에서 Linux VM을 템플릿 기반으로 생성한 뒤, Ansible Control Node에서 여러 Linux 서버에 동일한 초기 설정을 일괄 적용한다. 이를 통해 수동으로 반복해야 하는 사용자 생성, 패키지 설치, SSH 보안 설정, 방화벽 설정, 시간 동기화 등의 작업을 코드 기반으로 표준화하였다.


---

## 2. 목적

Linux 서버를 여러 대 운영할 경우, 초기 설정을 수동으로 반복하면 설정 누락이나 서버 간 환경 차이가 발생할 수 있다.

본 프로젝트의 목적은 다음과 같다.

* Linux 서버 초기 설정 자동화
* 여러 서버에 동일한 운영 표준 적용
* 사용자 및 sudo 권한 설정 자동화
* 기본 패키지 설치 자동화
* chrony 기반 시간 동기화 설정
* firewalld 기반 방화벽 서비스 활성화
* SSH 보안 설정 자동화
* SELinux 상태 확인
* VMware Template 기반 VM 생성 이후 후속 설정 자동화

---



## 3. VMware Template과 Ansible의 관계

VMware 또는 vSphere의 Linux VM Template 구성과 함께 사용하기 적합하다.

```text
VMware Template
= 동일한 Linux VM을 빠르게 생성하기 위한 Base Image

Ansible
= 생성된 Linux VM을 운영 표준 상태로 맞추는 자동화 도구
```

권장 흐름은 다음과 같다.

```text
1. Rocky Linux / RHEL 기반 VM 설치
2. 기본 계정 및 네트워크 설정
3. VM Template 생성
4. Template 기반으로 linux-node1, linux-node2 등 복제
5. Ansible Inventory에 대상 서버 등록
6. Ansible Playbook 실행
7. 공통 초기 설정 자동 적용
```

즉, VMware Template은 서버 생성의 시작점이고, Ansible은 생성된 서버의 설정을 표준화하는 후속 자동화 도구이다.

---

## 4. 디렉터리 구조

```text
ansible-linux-init/
├── inventory.ini
├── site.yml
├── group_vars/
│   └── all.yml
├── roles/
│   ├── users/
│   │   └── tasks/main.yml
│   ├── sudoers/
│   │   └── tasks/main.yml
│   ├── packages/
│   │   └── tasks/main.yml
│   ├── chrony/
│   │   └── tasks/main.yml
│   ├── firewalld/
│   │   └── tasks/main.yml
│   ├── ssh/
│   │   ├── tasks/main.yml
│   │   └── handlers/main.yml
│   └── selinux/
│       └── tasks/main.yml
└── README.md
```

---

## 5. 주요 파일 설명

| 파일                   | 설명                                          |
| -------------------- | ------------------------------------------- |
| `inventory.ini`      | Ansible이 관리할 Linux 서버 목록                    |
| `site.yml`           | 전체 Role을 실행하는 메인 Playbook                   |
| `group_vars/all.yml` | 전체 서버에 적용할 공통 변수                            |
| `roles/users`        | 관리자 사용자 생성                                  |
| `roles/sudoers`      | sudo 권한 설정                                  |
| `roles/packages`     | 기본 패키지 설치                                   |
| `roles/chrony`       | chrony 설치 및 시간 동기화 서비스 활성화                  |
| `roles/firewalld`    | firewalld 설치 및 SSH/HTTP 서비스 허용              |
| `roles/ssh`          | SSH root 로그인 차단 및 PasswordAuthentication 설정 |
| `roles/selinux`      | SELinux 상태 확인                               |

---

## 6. Inventory 구성

`inventory.ini` 파일은 Ansible이 접속할 대상 Linux 서버를 정의한다.

```ini
[linux_servers]
linux-nodeX ansible_host=172.16.X.XX

[linux_servers:vars]
ansible_user=ansible
ansible_become=true
ansible_become_method=sudo
```

### Inventory 항목 설명

| 항목                      | 설명                       |
| ----------------------- | ------------------------ |
| `linux-nodeX`           | Ansible에서 사용할 Host Alias |
| `ansible_host`          | 실제 접속할 대상 서버 IP          |
| `ansible_user`          | SSH 접속 사용자               |
| `ansible_become`        | sudo 권한 상승 사용 여부         |
| `ansible_become_method` | 권한 상승 방식                 |

실제 다음과 같이 여러 서버를 등록할 수 있다.

```ini
[linux_servers]
linux-node1 ansible_host=172.16.X.XXX
linux-node2 ansible_host=172.16.X.XXX
linux-node3 ansible_host=172.16.X.XXX

[linux_servers:vars]
ansible_user=ansible
ansible_become=true
ansible_become_method=sudo
```

---

## 7. 공통 변수 구성

`group_vars/all.yml`에는 전체 Linux 서버에 적용할 공통 변수를 정의한다.

```yaml
admin_users:
  - name: devops
    groups: wheel
    shell: /bin/bash

base_packages:
  - vim
  - git
  - wget
  - curl
  - net-tools
  - bind-utils
  - bash-completion
  - chrony
  - firewalld
  - nginx
  - audit

ssh_port: 22
permit_root_login: "no"
password_authentication: "yes"
```

### 변수 설명

| 변수                        | 설명                 |
| ------------------------- | ------------------ |
| `admin_users`             | 생성할 관리자 사용자 목록     |
| `base_packages`           | 기본 설치 패키지 목록       |
| `ssh_port`                | SSH 포트             |
| `permit_root_login`       | root SSH 로그인 허용 여부 |
| `password_authentication` | SSH 패스워드 인증 허용 여부  |

현재 설정에서는 `devops` 사용자를 생성하고, 해당 사용자를 `wheel` 그룹에 추가한다.

---

## 8. Playbook 실행 흐름

`site.yml`은 전체 Role을 순서대로 실행하는 메인 Playbook이다.

```yaml
---
- name: Initial Linux server setup
  hosts: linux_servers
  become: true

  roles:
    - users
    - sudoers
    - packages
    - chrony
    - firewalld
    - nginx
    - ssh
    - selinux
```

실행 순서는 다음과 같다.

```text
1. users
2. sudoers
3. packages
4. chrony
5. firewalld
6. nginx
7. ssh
8. selinux
```

---

## 9. Role 구성

## 9.1 users Role

`users` Role은 관리자 계정을 생성한다.

```yaml
- name: Create admin users
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
    append: true
    shell: "{{ item.shell }}"
    state: present
  loop: "{{ admin_users }}"
```

현재 설정에서는 다음 사용자가 생성된다.

| User     | Group   | Shell       |
| -------- | ------- | ----------- |
| `devops` | `wheel` | `/bin/bash` |

`append: true`를 사용하여 기존 보조 그룹을 유지하면서 `wheel` 그룹을 추가한다.

---

## 9.2 sudoers Role

`sudoers` Role은 `wheel` 그룹 사용자가 sudo 명령을 사용할 수 있도록 설정한다.

```yaml
- name: Allow wheel group to use sudo
  ansible.builtin.lineinfile:
    path: /etc/sudoers
    regexp: '^%wheel'
    line: '%wheel ALL=(ALL) ALL'
    validate: '/usr/sbin/visudo -cf %s'
```

`validate` 옵션을 통해 `/etc/sudoers` 파일 문법을 `visudo`로 검증한 뒤 적용한다.

현재 설정은 다음과 같다.

```text
%wheel ALL=(ALL) ALL
```

이 설정은 `wheel` 그룹 사용자가 sudo를 사용할 수 있지만, sudo 실행 시 비밀번호를 요구할 수 있다.

자동화 환경에서 비밀번호 없이 sudo를 사용하려면 다음과 같이 변경할 수 있다.

```text
%wheel ALL=(ALL) NOPASSWD: ALL
```

운영 환경에서는 보안 정책에 따라 `NOPASSWD` 사용 여부를 신중히 결정해야 한다.

---

## 9.3 packages Role

`packages` Role은 공통 패키지를 설치한다.

```yaml
- name: Install base packages
  ansible.builtin.dnf:
    name: "{{ base_packages }}"
    state: present
```

설치 대상 패키지는 `group_vars/all.yml`에서 관리한다.

```yaml
base_packages:
  - vim
  - git
  - wget
  - curl
  - net-tools
  - bind-utils
  - bash-completion
  - chrony
  - firewalld
  - audit
```

---

## 9.4 chrony Role

`chrony` Role은 시간 동기화 서비스를 설치하고 활성화한다.

```yaml
- name: Install chrony
  ansible.builtin.dnf:
    name: chrony
    state: present

- name: Enable and start chronyd
  ansible.builtin.systemd:
    name: chronyd
    enabled: true
    state: started
```

시간 동기화는 로그 분석, 인증, 인증서 검증, 분산 시스템 운영에서 중요하다.

확인 명령어:

```bash
timedatectl
chronyc sources
systemctl status chronyd
```

---

## 9.5 firewalld Role

`firewalld` Role은 방화벽 서비스를 설치하고 활성화한 뒤 SSH와 HTTP 서비스를 허용한다.

```yaml
- name: Install firewalld
  ansible.builtin.dnf:
    name: firewalld
    state: present

- name: Enable and start firewalld
  ansible.builtin.systemd:
    name: firewalld
    enabled: true
    state: started
```

허용 서비스:

```yaml
- name: Allow SSH service
  ansible.posix.firewalld:
    service: ssh
    permanent: true
    immediate: true
    state: enabled

- name: Allow HTTP service
  ansible.posix.firewalld:
    service: http
    permanent: true
    immediate: true
    state: enabled
```

현재 허용되는 서비스는 다음과 같다.

| Service | 용도               |
| ------- | ---------------- |
| `ssh`   | Ansible 및 관리자 접속 |
| `http`  | Nginx HTTP 서비스   |

`ansible.posix.firewalld` 모듈을 사용하므로 Ansible Control Node에 `ansible.posix` Collection이 필요할 수 있다.

설치 명령어:

```bash
ansible-galaxy collection install ansible.posix
```


---

## 9.6 ssh Role

`ssh` Role은 SSH 보안 설정을 적용한다.

```yaml
- name: Disable root SSH login
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PermitRootLogin'
    line: "PermitRootLogin {{ permit_root_login }}"
    backup: true
  notify: Restart sshd
```

root SSH 로그인 차단:

```text
PermitRootLogin no
```

Drop-in 설정 파일에도 root 로그인 차단을 명시한다.

```yaml
- name: Disable root SSH login in drop-in config
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config.d/01-permitrootlogin.conf
    regexp: '^#?PermitRootLogin'
    line: 'PermitRootLogin no'
    create: yes
    backup: true
  notify: Restart sshd
```

PasswordAuthentication 설정:

```yaml
- name: Configure SSH password authentication
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PasswordAuthentication'
    line: "PasswordAuthentication {{ password_authentication }}"
    backup: true
  notify: Restart sshd
```

현재 변수 설정은 다음과 같다.

```yaml
password_authentication: "yes"
```

초기 bootstrap 단계에서는 패스워드 인증을 허용할 수 있지만, SSH Key 기반 접속이 구성된 이후에는 보안상 다음 값으로 변경하는 것이 좋다.

```yaml
password_authentication: "no"
```

---

## 9.7 ssh Handler

SSH 설정이 변경되면 Handler가 실행되어 `sshd` 서비스를 재시작한다.

```yaml
- name: Restart sshd
  ansible.builtin.systemd:
    name: sshd
    state: restarted
```

Handler를 사용하면 SSH 설정 변경이 발생했을 때만 서비스를 재시작할 수 있다.

---

## 9.8 selinux Role

`selinux` Role은 현재 SELinux 상태를 확인하고 출력한다.

```yaml
- name: Check SELinux status
  ansible.builtin.command: getenforce
  register: selinux_status
  changed_when: false

- name: Print SELinux status
  ansible.builtin.debug:
    msg: "SELinux status is {{ selinux_status.stdout }}"
```

현재 Role은 SELinux 설정을 변경하지 않고 상태만 확인한다.

확인 가능한 상태:

```text
Enforcing
Permissive
Disabled
```

운영 환경에서는 SELinux를 비활성화하기보다 Enforcing 상태를 유지하고 필요한 정책을 조정하는 것이 권장된다.

---

## 10. 실행 전 준비사항

## 10.1 Ansible Control Node 준비

Ansible Control Node에 Ansible이 설치되어 있어야 한다.

RHEL/Rocky Linux 계열:

```bash
sudo dnf install -y ansible-core
```

Ansible 버전 확인:

```bash
ansible --version
```

필요한 Collection 설치:

```bash
ansible-galaxy collection install ansible.posix
```

---

## 10.2 대상 서버 접속 계정 준비

Inventory에서는 `ansible` 사용자로 접속하도록 설정되어 있다.

```ini
ansible_user=ansible
```

따라서 대상 서버에는 다음 조건이 필요하다.

```text
- ansible 사용자 존재
- SSH 접속 가능
- sudo 권한 보유
- Ansible Control Node의 SSH Public Key 등록
```

대상 서버에서 예시:

```bash
useradd ansible
passwd ansible
usermod -aG wheel ansible
```

SSH Key 복사:

```bash
ssh-copy-id ansible@<TARGET_IP>
```

접속 확인:

```bash
ssh ansible@<TARGET_IP>
```

---

## 10.3 sudo 권한 확인

대상 서버에서 `ansible` 사용자가 sudo를 사용할 수 있어야 한다.

```bash
sudo -l
```

비밀번호 없이 sudo를 허용하려면 `/etc/sudoers.d/ansible` 파일을 생성할 수 있다.

```bash
echo 'ansible ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/ansible
sudo chmod 440 /etc/sudoers.d/ansible
```

보안상 운영 환경에서는 필요한 명령만 제한적으로 허용하는 방식이 더 적절하다.

---

## 11. 실행 방법

## 11.1 Inventory 수정

`inventory.ini`에서 대상 서버 IP를 실제 환경에 맞게 수정한다.

```ini
[linux_servers]
linux-node1 ansible_host=172.16.1.101
linux-node2 ansible_host=172.16.1.102

[linux_servers:vars]
ansible_user=ansible
ansible_become=true
ansible_become_method=sudo
```

---

## 11.2 접속 테스트

Playbook 실행 전 Ansible Ping으로 접속을 확인한다.

```bash
ansible all -i inventory.ini -m ping
```

예상 결과:

```text
linux-node1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

sudo 권한까지 확인하려면 다음 명령을 사용할 수 있다.

```bash
ansible all -i inventory.ini -m command -a "whoami" -b
```

예상 결과:

```text
root
```

---

## 12.3 Playbook 실행

```bash
ansible-playbook -i inventory.ini site.yml
```

sudo 비밀번호를 요구하는 환경이라면 다음과 같이 실행한다.

```bash
ansible-playbook -i inventory.ini site.yml --ask-become-pass
```

---

## 13. 검증 방법

Playbook 실행 후 다음 항목을 확인한다.

## 13.1 사용자 생성 확인

```bash
ansible all -i inventory.ini -m command -a "id devops"
```

예상 결과:

```text
uid=1001(devops) gid=1001(devops) groups=1001(devops),10(wheel)
```

---

## 13.2 패키지 설치 확인

```bash
ansible all -i inventory.ini -m command -a "rpm -q nginx chrony firewalld audit"
```

---

## 13.3 chrony 상태 확인

```bash
ansible all -i inventory.ini -m command -a "systemctl is-active chronyd"
```

예상 결과:

```text
chronyd active
```

---

## 13.4 firewalld 상태 확인

```bash
ansible all -i inventory.ini -m command -a "systemctl is-active firewalld"
```

허용 서비스 확인:

```bash
ansible all -i inventory.ini -m command -a "firewall-cmd --list-services" -b
```

예상 서비스:

```text
ssh http
```


---

## 13.5 SSH 설정 확인

```bash
ansible all -i inventory.ini -m command -a "sshd -T | grep -i permitrootlogin" -b
```

예상 결과:

```text
permitrootlogin no
```

PasswordAuthentication 확인:

```bash
ansible all -i inventory.ini -m command -a "sshd -T | grep -i passwordauthentication" -b
```

---

## 13.6 SELinux 상태 확인

```bash
ansible all -i inventory.ini -m command -a "getenforce"
```

예상 결과:

```text
Enforcing
```

또는:

```text
Permissive
```

---



## 14. Troubleshooting

Ansible Linux 초기 설정 과정에서 발생할 수 있는 주요 문제와 해결 방법을 정리하였다.

---

### 14.1 SSH 접속 실패

#### 문제 상황

Ansible Ping 실행 시 대상 서버가 `UNREACHABLE` 상태가 된다.

```text
UNREACHABLE! => Failed to connect to the host via ssh
```

#### 원인

* 대상 서버 IP 오류
* SSH 서비스 미실행
* 방화벽에서 SSH 차단
* `ansible` 사용자 없음
* SSH Key 미등록
* PasswordAuthentication 설정 불일치

#### 확인 방법

Control Node에서 직접 SSH 접속을 확인한다.

```bash
ssh ansible@<TARGET_IP>
```

대상 서버에서 SSH 서비스 상태 확인:

```bash
systemctl status sshd
```

#### 해결 방법

* Inventory의 `ansible_host` 확인
* 대상 서버의 `sshd` 실행 여부 확인
* `ansible` 사용자 생성
* SSH Public Key 등록
* 방화벽에서 SSH 허용

```bash
firewall-cmd --add-service=ssh --permanent
firewall-cmd --reload
```

---

### 14.2 sudo 권한 오류

#### 문제 상황

Playbook 실행 중 `Missing sudo password` 또는 `Permission denied` 오류가 발생한다.

#### 원인

Inventory에는 `ansible_become=true`가 설정되어 있으므로, 대상 서버에서 `ansible` 사용자가 sudo 권한을 가지고 있어야 한다.

#### 확인 방법

대상 서버에서 확인:

```bash
sudo -l
```

Control Node에서 확인:

```bash
ansible all -i inventory.ini -m command -a "whoami" -b
```

#### 해결 방법

`ansible` 사용자를 `wheel` 그룹에 추가한다.

```bash
usermod -aG wheel ansible
```

sudo 비밀번호 없이 실행하려면 다음 설정을 추가한다.

```bash
echo 'ansible ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/ansible
chmod 440 /etc/sudoers.d/ansible
```

또는 Playbook 실행 시 sudo 비밀번호를 입력한다.

```bash
ansible-playbook -i inventory.ini site.yml --ask-become-pass
```

---



## 15. 보안 고려사항

현재 구성은 운영 환경에서는 보안 강화를 위해 추가 조정이 필요하다.

### 15.1 SSH 보안

현재 설정:

```yaml
permit_root_login: "no"
password_authentication: "yes"
```

운영 권장 설정:

```yaml
permit_root_login: "no"
password_authentication: "no"
```

단, `PasswordAuthentication no`를 적용하기 전에 SSH Key 기반 접속이 반드시 준비되어 있어야 한다.

---

### 15.2 sudo 권한

현재 sudoers 설정:

```text
%wheel ALL=(ALL) ALL
```

자동화 편의를 위해 다음 설정을 사용할 수 있다.

```text
%wheel ALL=(ALL) NOPASSWD: ALL
```

하지만 운영 환경에서는 전체 명령 허용보다 필요한 명령만 제한적으로 허용하는 것이 더 안전하다.

---

