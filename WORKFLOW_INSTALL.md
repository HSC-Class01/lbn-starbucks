# GitHub 업로드 순서

이 ZIP에서는 업로드 편의를 위해 workflow 폴더를 `github/workflows/`로 넣었습니다.

GitHub에서 repository 루트에 다음처럼 배치하세요:

- `github/workflows/update.yml` → `.github/workflows/update.yml`
- `github/workflows/pages.yml` → `.github/workflows/pages.yml`

`.github`는 GitHub Actions가 workflow를 인식하기 위해 필요한 특수 폴더입니다. ZIP에는 macOS/Windows가 자동 생성하는 불필요한 숨김 파일을 넣지 않았습니다.

## Pages

Repository → Settings → Pages → Source: **GitHub Actions**

배포 후 주소:

`https://HSC-Class01.github.io/lbn-starbucks/`

## About

Repository 첫 화면 → About의 톱니바퀴 → Website에 위 Dashboard URL 입력.

README 상단 배지는 이미 같은 URL을 가리킵니다.
