#!/usr/bin/env python
"""
Django의 커맨드라인 유틸리티입니다.
이 파일은 Django 프로젝트 관리를 위한 다양한 명령어를 실행하는 진입점(Entry Point)입니다.
서버 실행(runserver), 데이터베이스 마이그레이션(migrate), 앱 생성(startapp) 등의 명령을 여기서 처리합니다.
"""
import os
import sys
# python-dotenv 라이브러리를 임포트합니다. .env 파일에 정의된 환경 변수를 불러오는 역할을 합니다.
from dotenv import load_dotenv

def main():
    """관리 작업을 실행하는 메인 함수입니다."""
    
    # .env 파일이 있다면 그 내용을 환경 변수로 로드합니다.
    # 비밀키나 데이터베이스 접속 정보 같은 민감한 정보를 코드와 분리해서 관리하기 위함입니다.
    load_dotenv()
    
    # Django에게 프로젝트의 설정 파일(settings.py) 위치를 알려줍니다.
    # 'config.settings'는 config 폴더 안의 settings.py 파일을 의미합니다.
    # 이 부분이 프로젝트 설정의 핵심 연결고리입니다.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    try:
        # Django의 핵심 관리 모듈을 가져옵니다.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Django가 설치되어 있지 않거나 가상환경이 활성화되지 않았을 때 발생하는 에러를 처리합니다.
        raise ImportError(
            "Django를 임포트할 수 없습니다. "
            "Django가 설치되어 있는지, 그리고 가상환경을 활성화했는지 확인해주세요."
        ) from exc
        
    # 커맨드라인에서 입력받은 인자(sys.argv)를 Django에게 전달하여 실행합니다.
    # 예: "python manage.py runserver"라고 입력하면 ['manage.py', 'runserver']가 전달됩니다.
    execute_from_command_line(sys.argv)


# 이 파일이 직접 실행될 때만 main() 함수를 호출합니다.
# 다른 코드에서 이 파일을 임포트할 때는 실행되지 않도록 하는 파이썬의 관례입니다.
if __name__ == '__main__':
    main()
