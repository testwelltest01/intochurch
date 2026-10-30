import json
from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import ChurchReview, FinancialTransaction, NotionNotice, WeeklyReport


class TabPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        WeeklyReport.objects.create(date=date(2025, 1, 5), worship_attendance=120, new_comers=3, offering_total=1500000)
        for i in range(12):
            FinancialTransaction.objects.create(transaction_date=date(2025, 1, i + 1), type='IN', category='헌금', description=f'주일 헌금 {i}', amount=10000)
        for i in range(8):
            NotionNotice.objects.create(title=f'공지 {i}', content=f'본문 {i}', date=date(2025, 1, i + 1))

    def test_tab_pages_render(self):
        for name in ['home', 'news', 'finance', 'reviews', 'location', 'offline']:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'aria-label="주요 메뉴"')

    def test_active_tab_is_marked(self):
        response = self.client.get(reverse('finance'))
        self.assertContains(response, 'aria-current="page"', count=1)

    def test_notice_body_is_shown(self):
        response = self.client.get(reverse('news'))
        self.assertContains(response, '본문 7')

    def test_htmx_request_returns_partial_with_next_button(self):
        response = self.client.get(reverse('finance'), {'page': 1}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<html')
        self.assertContains(response, '?page=2')
        self.assertIn('HX-Request', response['Vary'])

    def test_last_page_has_no_next_button(self):
        response = self.client.get(reverse('finance'), {'page': 2}, HTTP_HX_REQUEST='true')
        self.assertNotContains(response, 'hx-get')
        self.assertNotContains(response, '데이터가 없습니다')


class ReviewTests(TestCase):
    def test_post_creates_review_and_redirects(self):
        response = self.client.post(reverse('reviews'), {'author_name': '홍길동', 'rating': '4', 'content': '좋아요'})
        self.assertRedirects(response, reverse('reviews'))
        review = ChurchReview.objects.get()
        self.assertEqual(review.rating, 4)

    def test_second_review_same_day_is_blocked(self):
        self.client.post(reverse('reviews'), {'author_name': 'A', 'rating': '5', 'content': '첫 번째'})
        self.client.post(reverse('reviews'), {'author_name': 'A', 'rating': '5', 'content': '두 번째'})
        self.assertEqual(ChurchReview.objects.count(), 1)
        self.assertContains(self.client.get(reverse('reviews')), '소중한 의견 감사합니다')

    def test_invalid_rating_falls_back(self):
        self.client.post(reverse('reviews'), {'author_name': 'B', 'rating': 'abc', 'content': '내용'})
        self.assertEqual(ChurchReview.objects.get().rating, 5)


class PwaTests(TestCase):
    def test_manifest(self):
        response = self.client.get(reverse('manifest'))
        self.assertEqual(response['Content-Type'], 'application/manifest+json')
        data = json.loads(response.content)
        self.assertEqual(data['start_url'], '/')
        self.assertEqual(data['display'], 'standalone')
        sizes = {(icon['sizes'], icon['purpose']) for icon in data['icons']}
        self.assertIn(('192x192', 'any'), sizes)
        self.assertIn(('512x512', 'any'), sizes)
        self.assertIn(('512x512', 'maskable'), sizes)

    def test_service_worker_served_from_root(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('application/javascript'))
        self.assertEqual(response['Cache-Control'], 'no-cache')
        self.assertContains(response, "const OFFLINE_URL = '/offline/'")
        self.assertContains(response, "CACHE_VERSION = 'dev'")

    def test_base_registers_service_worker(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, "navigator.serviceWorker.register('/sw.js')")
        self.assertContains(response, '<link rel="manifest" href="/manifest.webmanifest">')
