// node_modules 안의 라이브러리를 static/vendor/ 로 복사합니다.
// CDN 대신 로컬 파일을 쓰면 오프라인(PWA)에서도 화면이 동작합니다.
// Vercel은 npm 빌드를 돌리지 않으므로, 복사된 파일은 git에 커밋해야 합니다.
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const outDir = path.join(root, 'static', 'vendor');

const files = [
  ['alpinejs/dist/cdn.min.js', 'alpine.min.js'],
  ['htmx.org/dist/htmx.min.js', 'htmx.min.js'],
  ['chart.js/dist/chart.umd.min.js', 'chart.umd.min.js'],
];

fs.mkdirSync(outDir, { recursive: true });

for (const [from, to] of files) {
  const src = path.join(root, 'node_modules', from);
  if (!fs.existsSync(src)) {
    console.error(`[vendor] ${from} 파일이 없습니다. 먼저 "npm install"을 실행하세요.`);
    process.exit(1);
  }
  fs.copyFileSync(src, path.join(outDir, to));
  console.log(`[vendor] ${from} -> static/vendor/${to}`);
}
