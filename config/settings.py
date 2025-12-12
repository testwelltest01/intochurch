"""
Django 설정 파일입니다.
이 파일은 웹사이트의 모든 구성을 담당합니다. 데이터베이스 연결, 설치된 앱, 비밀번호 보안 등
프로젝트 전반에 걸친 중요한 설정들이 모두 여기에 모여 있습니다.
"""
import os
import dj_database_url
from pathlib import Path

# 프로젝트의 기본 경로를 설정합니다.
# BASE_DIR은 현재 파일(settings.py)의 부모의 부모 폴더, 즉 프로젝트의 최상위 폴더(인투처치)를 가리킵니다.
# 어디서든 파일 경로를 찾을 때 이 BASE_DIR을 기준으로 찾으면 편합니다.
BASE_DIR = Path(__file__).resolve().parent.parent


# 개발 모드 설정 (중요!)
# SECURITY WARNING: 실제 배포할 때는 비밀키를 절대 노출하면 안 됩니다.
# .env 파일에서 SECRET_KEY를 가져오되, 없으면 기본값을 사용합니다(개발 환경용).
env_path = BASE_DIR / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-for-dev-only-12345')

# 디버그 모드 설정
# True면 에러 발생 시 상세한 에러 페이지를 보여줍니다 (개발할 때 좋음).
# False면 "서버 에러입니다" 같은 일반적인 문구만 보여줍니다 (실제 서비스할 때 필수).
# 프로덕션(배포) 환경에서는 반드시 False여야 보안상 안전합니다.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# 접속을 허용할 도메인 주소들입니다.
# intochurch.vercel.app: 배포될 사이트 주소
# 127.0.0.1: 내 컴퓨터 (숫자 주소)
# localhost: 내 컴퓨터 (영어 주소)
# [::1]: 내 컴퓨터 (IPv6 주소, 혹시 몰라 넣어둠)
ALLOWED_HOSTS = ['intochurch.vercel.app', '127.0.0.1', 'localhost', '[::1]', "*"]

# 설치된 앱(Application) 정의
# Django는 '앱' 단위로 기능을 쪼개서 관리합니다.
# 여기에 등록되지 않은 앱은 프로젝트에서 사용할 수 없습니다.
INSTALLED_APPS = [
    'jazzmin',  # 관리자 페이지를 예쁘게 꾸며주는 라이브러리 (최상단에 위치해야 함)
    
    # Django 기본 앱들 (건드리지 않아도 됨)
    'django.contrib.admin',         # 관리자 페이지 기능
    'django.contrib.auth',          # 회원가입, 로그인 등 인증 시스템
    'django.contrib.contenttypes',  # 데이터 모델 간의 관계 관리
    'django.contrib.sessions',      # 로그인 정보를 유지하는 세션 기능
    'django.contrib.messages',      # 알림 메시지 기능
    'django.contrib.staticfiles',   # CSS, 이미지 등 정적 파일 관리
    
    # 내가 만든 앱
    'ministry',  # 사역 관련 기능이 들어있는 앱
    
    # 외부 라이브러리 앱
    'storages',  # AWS S3 같은 외부 저장소를 쓰기 위한 앱
]

# 미들웨어(Middleware) 정의
# 사용자 요청이 들어오고 나갈 때 거쳐가는 '문지기'들입니다.
# 보안 검사, 로그인 여부 확인 등을 처리합니다. 위에서부터 순서대로 실행됩니다.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',           # 정적 파일(CSS 등)을 효율적으로 서빙해주는 도구
    'django.contrib.sessions.middleware.SessionMiddleware', # 세션 관리
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',            # CSRF 보안 공격 방지
    'django.contrib.auth.middleware.AuthenticationMiddleware', # 사용자 인증 처리 
    'django.contrib.messages.middleware.MessageMiddleware', # 메시지 처리
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # 보안 관련(클릭재킹 방지)
]

# URL 설정 파일 위치 지정
# "누가 이 사이트에 접속하면 어떤 주소로 안내할까?"를 결정하는 파일이 어디 있는지 알려줍니다.
ROOT_URLCONF = 'config.urls'

# 템플릿(HTML) 설정
# 화면에 보여질 HTML 파일들을 어떻게 처리할지 설정합니다.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # 추가적인 템플릿 폴더가 있다면 여기에 경로를 적습니다.
        'APP_DIRS': True, # 각 앱(ministry 등) 폴더 안의 'templates' 폴더를 자동으로 찾을지 여부
        'OPTIONS': {
            'context_processors': [ # 모든 템플릿에서 공통으로 사용할 변수들
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', # 로그인한 사용자 정보(user)를 템플릿에서 쓰게 해줌
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI 어플리케이션 위치
# 웹 서버(Nginx, Apache 등)와 Django가 소통하기 위한 진입점입니다.
WSGI_APPLICATION = 'config.wsgi.application'


# 데이터베이스 설정
# 프로젝트의 데이터를 어디에 저장할지 결정합니다.
DATABASES = {
    'default': {
        # 기본적으로 sqlite3라는 가벼운 파일 기반 데이터베이스를 사용합니다.
        # 개발할 때 설치가 필요 없어 아주 편리합니다.
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 배포 환경 설정 (Vercel + Neon DB)
# 실제 서비스될 때는 파일 기반 DB(sqlite3)를 쓸 수 없으므로,
# Neon 같은 외부 클라우드 DB 주소가 환경변수로 들어오면 그걸로 교체합니다.
DATABASE_URL = os.environ.get("DATABASE_URL") 

if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(default=DATABASE_URL, conn_max_age=600)


# 비밀번호 검증 설정
# 비밀번호를 너무 쉽게 만들지 못하게 막는 규칙들입니다.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', # 아이디랑 비슷하면 안됨
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', # 너무 짧으면 안됨
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', # "123456" 같은 흔한 비번 안됨
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', # 숫자로만 된 비번 안됨
    },
]


# 언어 및 시간 설정 (한국 맞춤)

# 사이트 언어를 한국어로 설정
LANGUAGE_CODE = 'ko-kr'

# 시간을 한국 시간(KST)으로 설정
TIME_ZONE = 'Asia/Seoul'

# 번역 기능 사용 여부
USE_I18N = True

# 시간대 기능 사용 여부
# False로 설정하면 DB에 저장되는 시간이 그냥 한국 시간으로 저장되어 직관적입니다.
# (글로벌 서비스가 아니라면 False로 두고 한국 시간만 쓰는 게 덜 헷갈립니다)
USE_TZ = False


# 정적 파일 설정 (Static files)
# CSS, JavaScript, 이미지 파일들을 어떻게 관리할지 설정합니다.

# HTML에서 정적 파일을 불러올 때 쓸 주소 (예: /static/css/style.css)
# HTML에서 정적 파일을 불러올 때 쓸 주소 (예: /static/css/style.css)
STATIC_URL = 'static/'

# 프로젝트 루트의 static 폴더를 정적 파일 경로로 추가 (Tailwind CSS 등)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# python manage.py collectstatic 명령을 치면 흩어져 있는 정적 파일들이 모이는 곳
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 미디어 파일 설정 (사용자가 업로드한 파일)
# 사용자가 올린 파일에 접근할 때 쓸 URL 주소 (예: /media/profile.jpg)
# MEDIA_URL = '/media/'  <-- 아래 AWS 설정에서 덮어씌웁니다.
# 실제 파일이 저장될 컴퓨터(서버) 내의 폴더 경로
MEDIA_ROOT = BASE_DIR / 'media'


# Jazzmin 설정 (관리자 페이지 디자인 테마)
# 딱딱한 기본 관리자 페이지를 예쁘게 꾸며줍니다.
JAZZMIN_SETTINGS = {
    "site_title": "투명한 사역 교회",
    "site_header": "Ministry Admin",
    "welcome_sign": "환영합니다, 목사님! (관리자 모드)",
    "copyright": "Antigravity Ministry Ltd",
    
    # 상단 검색창에서 바로 검색할 모델들
    "search_model": ["ministry.FinancialTransaction"],
    
    # 메뉴 아이콘 설정 (FontAwesome 아이콘 사용)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "ministry.WeeklyReport": "fas fa-chart-line",
        "ministry.FinancialTransaction": "fas fa-file-invoice-dollar",
        "ministry.ChurchReview": "fas fa-comments",
    },
}


# ==========================================
# 파일 저장소 & URL 설정 (기본 로컬 저장소 사용)
# ==========================================

# AWS S3를 사용하지 않고, 서버(내 컴퓨터)의 파일 시스템을 사용합니다.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# 배포 환경에서 WhiteNoise 사용 (정적 파일만)
if not DEBUG:
    STORAGES['staticfiles'] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'