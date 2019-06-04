from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ScrewDataView,ScrewConfigView,HelloView

# router = DefaultRouter()
# router.register(r'mouseinfo', MouseInfoViewSet)
# urlpatterns = router.urls

# if DefaultRouter exists ,urlpatterns+= [...]
urlpatterns = [
    path('screw', ScrewDataView.as_view()),
    path('screwconfig', ScrewConfigView.as_view()),
    path('hello', HelloView.as_view()),
]
